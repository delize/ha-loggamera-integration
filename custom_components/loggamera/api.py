"""API client for Loggamera."""

import asyncio
import logging
import platform
import ssl
import sys
import time
from datetime import datetime  # noqa: F401
from enum import Enum
from typing import Any, Dict, Optional, Union

import certifi
import requests

from .const import (
    API_ENDPOINT_CAPABILITIES,
    API_ENDPOINT_COOLING_UNIT,
    API_ENDPOINT_DEVICES,
    API_ENDPOINT_EXECUTE_SCENARIO_ASYNC,
    API_ENDPOINT_GENERIC_DEVICE,
    API_ENDPOINT_HEAT_PUMP,
    API_ENDPOINT_ORGANIZATIONS,
    API_ENDPOINT_POWER_METER,
    API_ENDPOINT_RAW_DATA,
    API_ENDPOINT_ROOM_SENSOR,
    API_ENDPOINT_SCENARIOS,
    API_ENDPOINT_USER_ACCESS,
    API_ENDPOINT_WATER_METER,
    API_URL,
)

_LOGGER = logging.getLogger(__name__)


class LoggameraAPIError(Exception):
    """Exception for Loggamera API errors."""

    pass


class ErrorType(Enum):
    """Classification of different error types for retry strategies."""

    NETWORK = "network"  # Network connectivity issues - retry with backoff
    HTTP_ERROR = "http_error"  # HTTP errors (4xx, 5xx) - limited retries
    API_ERROR = "api_error"  # API-specific errors - no retry
    TIMEOUT = "timeout"  # Request timeout - retry with backoff
    INVALID_ENDPOINT = "invalid_endpoint"  # Invalid endpoint - no retry


class CircuitBreaker:
    """Circuit breaker to prevent hitting failing endpoints repeatedly."""

    def __init__(self, failure_threshold: int = 6, timeout: int = 300):
        """Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            timeout: Time in seconds to wait before trying again
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = "closed"  # closed, open, half_open

    def is_open(self) -> bool:
        """Check if circuit is open (should block requests)."""
        if self.state == "open":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "half_open"
                _LOGGER.debug("Circuit breaker moving to half-open state")
                return False
            return True
        return False

    def record_success(self):
        """Record successful request."""
        self.failure_count = 0
        if self.state == "half_open":
            self.state = "closed"
            _LOGGER.debug("Circuit breaker closed after successful request")

    def record_failure(self):
        """Record failed request."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            _LOGGER.warning(
                f"Circuit breaker opened after {self.failure_count} failures. "
                f"Will retry in {self.timeout} seconds"
            )


class RetryConfig:
    """Configuration for retry behavior."""

    def __init__(self):
        self.max_retries = 3
        self.backoff_delays = [15, 30, 60]  # seconds
        self.retryable_errors = {
            ErrorType.NETWORK,
            ErrorType.TIMEOUT,
            ErrorType.HTTP_ERROR,  # Some HTTP errors may be retryable
        }

    def should_retry(self, error_type: ErrorType, attempt: int) -> bool:
        """Determine if we should retry based on error type and attempt number."""
        if attempt >= self.max_retries:
            return False
        return error_type in self.retryable_errors

    def get_delay(self, attempt: int) -> int:
        """Get delay for given attempt (0-based)."""
        if attempt < len(self.backoff_delays):
            return self.backoff_delays[attempt]
        return self.backoff_delays[-1]  # Use last delay for any additional attempts


class LoggameraAPI:
    """API client for Loggamera.

    Note on update frequency:
    The PowerMeter endpoint typically updates data approximately every 30 minutes.
    Setting a more frequent polling interval will not result in more data updates.
    """

    def __init__(self, api_key: str, organization_id: Optional[Union[str, int]] = None) -> None:
        """Initialize API client.

        Args:
            api_key: The API key for authentication
            organization_id: Optional organization ID for device/scenario access
        """
        self.api_key = api_key
        self.organization_id = organization_id
        self.session = requests.Session()
        self.session.verify = certifi.where()

        # Cache for endpoint availability
        self._endpoint_cache = {}

        # Keep track of last data timestamp to log changes
        self._last_data_timestamp = {}

        # Retry and circuit breaker configuration
        self.retry_config = RetryConfig()
        self.circuit_breakers = {}  # Per-endpoint circuit breakers

        # Log basic environment info
        _LOGGER.info(f"Python version: {sys.version}")
        _LOGGER.info(
            f"OpenSSL version: {getattr(ssl, 'OPENSSL_VERSION', 'Unknown')}"
            if platform.python_implementation() == "CPython"
            else "OpenSSL info not available"
        )
        _LOGGER.info(f"System: {platform.system()} {platform.release()}")
        _LOGGER.info(f"Certifi location: {certifi.where()}")
        _LOGGER.info(f"API URL: {API_URL}")

        # For debugging - enable this if needed
        # from http.client import HTTPConnection
        # HTTPConnection.debuglevel = 1

    def _get_circuit_breaker(self, endpoint: str) -> CircuitBreaker:
        """Get or create circuit breaker for endpoint."""
        if endpoint not in self.circuit_breakers:
            self.circuit_breakers[endpoint] = CircuitBreaker()
        return self.circuit_breakers[endpoint]

    def _classify_error(self, exception: Exception) -> ErrorType:
        """Classify error type for retry strategy."""
        if isinstance(exception, requests.exceptions.Timeout):
            return ErrorType.TIMEOUT
        elif isinstance(
            exception,
            (
                requests.exceptions.ConnectionError,
                requests.exceptions.ConnectTimeout,
                requests.exceptions.ReadTimeout,
            ),
        ):
            return ErrorType.NETWORK
        elif isinstance(exception, requests.exceptions.HTTPError):
            return ErrorType.HTTP_ERROR
        elif isinstance(exception, LoggameraAPIError):
            if "invalid endpoint" in str(exception).lower():
                return ErrorType.INVALID_ENDPOINT
            return ErrorType.API_ERROR
        else:
            return ErrorType.NETWORK  # Default to network error for unknown exceptions

    async def _sleep_async(self, delay: int):
        """Async sleep for retry delays."""
        await asyncio.sleep(delay)

    def _sleep_sync(self, delay: int):
        """Sync sleep for retry delays."""
        time.sleep(delay)

    def _make_request(  # noqa: C901
        self, endpoint: str, data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make a request to the Loggamera API with retry and circuit breaker.

        Args:
            endpoint: The API endpoint to call (without leading slash)
            data: Optional request data dict (ApiKey will be added automatically)

        Returns:
            Dict containing the API response

        Raises:
            LoggameraAPIError: If the request fails or returns an error
        """
        # Check circuit breaker
        circuit_breaker = self._get_circuit_breaker(endpoint)
        if circuit_breaker.is_open():
            raise LoggameraAPIError(
                f"Circuit breaker is open for endpoint {endpoint}. " f"Too many recent failures."
            )

        url = f"{API_URL}/{endpoint}"
        headers = {"Content-Type": "application/json"}

        # Initialize data if not provided
        if data is None:
            data = {}

        # Always include the API key
        if "ApiKey" not in data:
            data["ApiKey"] = self.api_key

        last_exception = None

        # Retry loop
        for attempt in range(self.retry_config.max_retries + 1):
            try:
                if attempt > 0:
                    _LOGGER.debug(f"Retry attempt {attempt} for {endpoint}")
                else:
                    _LOGGER.debug(f"Making request to {endpoint}")

                response = self.session.post(url, headers=headers, json=data, timeout=30)

                if response.status_code != 200:
                    error_msg = f"HTTP error {response.status_code}: {response.text}"
                    _LOGGER.error(error_msg)

                    # For HTTP errors, determine if retryable
                    if response.status_code >= 500:  # Server errors are retryable
                        exception = LoggameraAPIError(error_msg)
                        last_exception = exception
                        error_type = self._classify_error(exception)
                    elif response.status_code == 429:  # Rate limiting
                        exception = LoggameraAPIError(error_msg)
                        last_exception = exception
                        error_type = self._classify_error(exception)
                    else:  # Client errors (4xx) are not retryable
                        circuit_breaker.record_failure()
                        raise LoggameraAPIError(error_msg)

                    # Check if we should retry this HTTP error
                    if self.retry_config.should_retry(error_type, attempt):
                        delay = self.retry_config.get_delay(attempt)
                        _LOGGER.warning(
                            f"Request to {endpoint} failed (attempt {attempt + 1}): {error_msg}. "
                            f"Retrying in {delay} seconds... "
                            f"(HTTP {response.status_code})"
                        )
                        self._sleep_sync(delay)
                        continue
                    else:
                        circuit_breaker.record_failure()
                        raise exception
                else:
                    # Parse successful response
                    try:
                        # Handle endpoints that return no response body
                        if not response.text.strip():
                            result = {"Data": None, "Error": None}
                        else:
                            result = response.json()
                    except ValueError as e:
                        error_msg = f"Invalid JSON response: {response.text}"
                        _LOGGER.error(error_msg)
                        circuit_breaker.record_failure()
                        raise LoggameraAPIError(error_msg) from e

                    # Check for API errors
                    if "Error" in result and result["Error"] is not None:
                        if isinstance(result["Error"], dict) and "Message" in result["Error"]:
                            error_message = result["Error"]["Message"]
                            if error_message == "invalid endpoint":
                                _LOGGER.debug(f"Endpoint {endpoint} is not valid for this device")
                                self._endpoint_cache[endpoint] = False
                                circuit_breaker.record_failure()
                                raise LoggameraAPIError(f"API error: {error_message}")
                            else:
                                _LOGGER.error(f"API error: {error_message}")
                                circuit_breaker.record_failure()
                                raise LoggameraAPIError(f"API error: {error_message}")
                        else:
                            error_msg = f"Unknown API error: {result['Error']}"
                            _LOGGER.error(error_msg)
                            circuit_breaker.record_failure()
                            raise LoggameraAPIError(error_msg)

                    # Success!
                    circuit_breaker.record_success()
                    if attempt > 0:
                        _LOGGER.info(f"Request to {endpoint} succeeded after {attempt} retries")
                    return result

            except Exception as e:
                last_exception = e
                error_type = self._classify_error(e)

                # Check if we should retry
                if self.retry_config.should_retry(error_type, attempt):
                    delay = self.retry_config.get_delay(attempt)
                    _LOGGER.warning(
                        f"Request to {endpoint} failed (attempt {attempt + 1}): {e}. "
                        f"Retrying in {delay} seconds... "
                        f"(Error type: {error_type.value})"
                    )
                    self._sleep_sync(delay)
                    continue
                else:
                    # No more retries or non-retryable error
                    circuit_breaker.record_failure()
                    if error_type in self.retry_config.retryable_errors:
                        _LOGGER.error(
                            f"Request to {endpoint} failed after {attempt + 1} attempts: {e}"
                        )
                    else:
                        _LOGGER.error(f"Request to {endpoint} failed with non-retryable error: {e}")
                    break

        # If we get here, all retries failed
        circuit_breaker.record_failure()
        if isinstance(last_exception, LoggameraAPIError):
            raise last_exception
        else:
            raise LoggameraAPIError(f"Request failed: {last_exception}") from last_exception

    def get_organizations(self) -> Dict[str, Any]:
        """Get organizations.

        Returns:
            Dict containing organizations data
        """
        return self._make_request(API_ENDPOINT_ORGANIZATIONS)

    def get_devices(self) -> Dict[str, Any]:
        """Get devices for the configured organization.

        Returns:
            Dict containing devices data

        Raises:
            LoggameraAPIError: If organization_id is not set
        """
        if not self.organization_id:
            _LOGGER.error("Organization ID is required for get_devices")
            raise LoggameraAPIError("Organization ID is required for get_devices")

        return self._make_request(API_ENDPOINT_DEVICES, {"OrganizationId": self.organization_id})

    def _validate_device_params(self, device_id: Union[str, int], device_type: str) -> int:
        """Validate and convert device parameters.

        Args:
            device_id: Device ID to validate
            device_type: Device type to validate

        Returns:
            Validated device_id as integer

        Raises:
            LoggameraAPIError: If parameters are invalid
        """
        try:
            device_id = int(device_id)
        except (ValueError, TypeError):
            _LOGGER.error(f"Invalid device ID: {device_id}")
            raise LoggameraAPIError(f"Invalid device ID: {device_id}")

        if not device_type or not isinstance(device_type, str):
            _LOGGER.error(f"Invalid device type: {device_type}")
            raise LoggameraAPIError(f"Invalid device type: {device_type}")

        return device_id

    def _has_valid_data(self, response: Dict[str, Any]) -> bool:
        """Check if API response contains valid data.

        Args:
            response: API response dictionary

        Returns:
            True if response contains valid data values
        """
        return (
            "Data" in response
            and response["Data"] is not None
            and "Values" in response["Data"]
            and response["Data"]["Values"]
        )

    def _get_primary_endpoint_for_device(  # noqa: C901
        self, device_id: int, device_type: str
    ) -> Dict[str, Any]:
        """Get data from the primary endpoint for a specific device type.

        Args:
            device_id: Device ID to fetch data for
            device_type: Type of device to determine primary endpoint

        Returns:
            Primary device data response

        Raises:
            LoggameraAPIError: If primary endpoint fails
        """
        # Determine primary endpoint based on device type
        primary_endpoint = None

        if device_type == "PowerMeter":
            primary_endpoint = API_ENDPOINT_POWER_METER
        elif device_type == "RoomSensor":
            primary_endpoint = API_ENDPOINT_ROOM_SENSOR
        elif device_type == "WaterMeter":
            primary_endpoint = API_ENDPOINT_WATER_METER
        elif device_type == "CoolingUnit":
            primary_endpoint = API_ENDPOINT_COOLING_UNIT
        elif device_type == "HeatPump":
            primary_endpoint = API_ENDPOINT_HEAT_PUMP
        elif device_type == "HeatMeter":
            # HeatMeter has no dedicated endpoint - use RawData directly
            primary_endpoint = None

        # If we have a primary endpoint, try it first
        if primary_endpoint:
            try:
                # Skip if we know this endpoint is invalid
                if not (
                    primary_endpoint in self._endpoint_cache
                    and self._endpoint_cache[primary_endpoint] is False
                ):
                    response = self._make_request(primary_endpoint, {"DeviceId": device_id})

                    # Check if this endpoint is invalid
                    if not (
                        "Error" in response
                        and response["Error"]
                        and isinstance(response["Error"], dict)
                        and "Message" in response["Error"]
                        and response["Error"]["Message"] == "invalid endpoint"
                    ):
                        # Check if we got valid data
                        if self._has_valid_data(response):
                            # Add endpoint info for debugging/tracking
                            response["_endpoint_used"] = primary_endpoint
                            return response

            except LoggameraAPIError as e:
                _LOGGER.debug(f"Primary endpoint {primary_endpoint} failed: {e}")

        # Fallback to generic endpoints
        fallback_endpoints = [API_ENDPOINT_RAW_DATA, API_ENDPOINT_GENERIC_DEVICE]

        for endpoint in fallback_endpoints:
            try:
                # Skip if we know this endpoint is invalid
                if endpoint in self._endpoint_cache and self._endpoint_cache[endpoint] is False:
                    continue

                response = self._make_request(endpoint, {"DeviceId": device_id})

                # Check if this endpoint is invalid
                if (
                    "Error" in response
                    and response["Error"]
                    and isinstance(response["Error"], dict)
                    and "Message" in response["Error"]
                    and response["Error"]["Message"] == "invalid endpoint"
                ):
                    continue

                # Check if we got valid data
                if self._has_valid_data(response):
                    # Add endpoint info for debugging/tracking
                    response["_endpoint_used"] = endpoint
                    return response

            except LoggameraAPIError as e:
                _LOGGER.debug(f"Fallback endpoint {endpoint} failed: {e}")
                continue

        # If we get here, all endpoints failed
        raise LoggameraAPIError(f"All endpoints failed for device {device_id}")

    def get_device_data(self, device_id: Union[str, int], device_type: str) -> Dict[str, Any]:
        """Get device data from the primary endpoint for the device type.

        This method gets data from the primary endpoint only (e.g., PowerMeter
        endpoint for PowerMeter devices). RawData is collected separately via
        get_raw_data() to provide additional detailed sensors.

        Args:
            device_id: Device ID to fetch data for
            device_type: Type of device (PowerMeter, RoomSensor, etc.)

        Returns:
            Primary device data response

        Raises:
            LoggameraAPIError: If primary endpoint fails
        """
        # Validate input parameters
        device_id = self._validate_device_params(device_id, device_type)

        # Get data from primary endpoint for this device type
        return self._get_primary_endpoint_for_device(device_id, device_type)

    def get_raw_data(self, device_id: Union[str, int]) -> Dict[str, Any]:
        """Get raw device data.

        Args:
            device_id: Device ID to fetch raw data for

        Returns:
            Raw device data response
        """
        device_id = self._validate_device_params(device_id, "Unknown")
        return self._make_request(
            API_ENDPOINT_RAW_DATA,
            {"DeviceId": device_id},
        )

    def get_capabilities(self, device_id: Union[str, int]) -> Dict[str, Any]:
        """Get device capabilities.

        Args:
            device_id: Device ID to get capabilities for

        Returns:
            Device capabilities data
        """
        device_id = self._validate_device_params(device_id, "Unknown")
        try:
            return self._make_request(API_ENDPOINT_CAPABILITIES, {"DeviceId": device_id})
        except LoggameraAPIError as e:
            # Don't raise error if endpoint is not available
            if "invalid endpoint" in str(e):
                _LOGGER.warning(f"Capabilities endpoint not available for device {device_id}")
                return {
                    "Data": {"ReadCapabilities": [], "WriteCapabilities": []},
                    "Error": None,
                }
            else:
                raise

    def get_scenarios(self) -> Dict[str, Any]:
        """Get scenarios for the configured organization.

        Returns:
            Scenarios data
        """
        if not self.organization_id:
            _LOGGER.error("Organization ID is required for get_scenarios")
            return {"Data": {"Scenarios": []}, "Error": None}

        try:
            return self._make_request(
                API_ENDPOINT_SCENARIOS, {"OrganizationId": self.organization_id}
            )
        except LoggameraAPIError as e:
            # Don't raise error if endpoint is not available
            if "invalid endpoint" in str(e):
                _LOGGER.warning(
                    f"Scenarios endpoint not available for organization " f"{self.organization_id}"
                )
                return {"Data": {"Scenarios": []}, "Error": None}
            else:
                raise

    def execute_scenario_async(
        self, scenario_id: Union[str, int], duration_minutes: Optional[int] = None
    ) -> Dict[str, Any]:
        """Execute a scenario asynchronously.

        Args:
            scenario_id: ID of scenario to execute
            duration_minutes: Optional duration in minutes

        Returns:
            Execution result (typically empty for async endpoints)
        """
        data = {"ScenarioId": scenario_id}

        if duration_minutes is not None:
            data["DurationMinutes"] = duration_minutes

        return self._make_request(API_ENDPOINT_EXECUTE_SCENARIO_ASYNC, data)

    def user_access(self, user_id: Union[str, int]) -> Dict[str, Any]:
        """Get user access information.

        Args:
            user_id: User ID to get access info for

        Returns:
            User access data (typically empty for this endpoint)
        """
        data = {"UserId": user_id}
        return self._make_request(API_ENDPOINT_USER_ACCESS, data)

    # Convenience methods for easier API usage

    def is_endpoint_available(self, endpoint: str) -> bool:
        """Check if an endpoint is available (cached result).

        Args:
            endpoint: Endpoint name to check

        Returns:
            True if endpoint is available, False if cached as unavailable
        """
        return self._endpoint_cache.get(endpoint, True)

    def get_all_device_data(self) -> Dict[str, Any]:
        """Get data for all devices in the organization.

        Returns:
            Dict mapping device_id -> device_data for all devices
        """
        if not self.organization_id:
            raise LoggameraAPIError("Organization ID is required")

        devices_response = self.get_devices()
        if not self._has_valid_data(devices_response):
            return {}

        all_device_data = {}
        for device in devices_response["Data"]["Values"]:
            device_id = device["Id"]
            device_type = device["Class"]

            try:
                device_data = self.get_device_data(device_id, device_type)
                all_device_data[str(device_id)] = device_data
            except LoggameraAPIError as e:
                _LOGGER.warning(f"Failed to get data for device {device_id}: {e}")
                continue

        return all_device_data

    def clear_endpoint_cache(self) -> None:
        """Clear the endpoint availability cache."""
        self._endpoint_cache.clear()
        _LOGGER.debug("Endpoint cache cleared")
