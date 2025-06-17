"""API client for Loggamera."""

import logging
import platform
import ssl
import sys
from datetime import datetime  # noqa: F401
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


class LoggameraAPI:
    """API client for Loggamera.

    Note on update frequency:
    The PowerMeter endpoint typically updates data approximately every 30 minutes.
    Setting a more frequent polling interval will not result in more data updates.
    """

    def __init__(
        self, api_key: str, organization_id: Optional[Union[str, int]] = None
    ) -> None:
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

    def _make_request(  # noqa: C901
        self, endpoint: str, data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make a request to the Loggamera API.

        Args:
            endpoint: The API endpoint to call (without leading slash)
            data: Optional request data dict (ApiKey will be added automatically)

        Returns:
            Dict containing the API response

        Raises:
            LoggameraAPIError: If the request fails or returns an error
        """
        url = f"{API_URL}/{endpoint}"
        headers = {"Content-Type": "application/json"}

        # Initialize data if not provided
        if data is None:
            data = {}

        # Always include the API key
        if "ApiKey" not in data:
            data["ApiKey"] = self.api_key

        try:
            _LOGGER.debug(f"Making request to {endpoint}")
            response = requests.post(url, headers=headers, json=data, timeout=30)

            if response.status_code != 200:
                _LOGGER.error(f"HTTP error {response.status_code}: {response.text}")
                raise LoggameraAPIError(
                    f"HTTP error {response.status_code}: {response.text}"
                )

            try:
                # Handle endpoints that return no response body
                if not response.text.strip():
                    return {"Data": None, "Error": None}
                result = response.json()
            except ValueError:
                _LOGGER.error(f"Invalid JSON response: {response.text}")
                raise LoggameraAPIError(f"Invalid JSON response: {response.text}")

            # Check for API errors
            if "Error" in result and result["Error"] is not None:
                if isinstance(result["Error"], dict) and "Message" in result["Error"]:
                    error_message = result["Error"]["Message"]
                    if error_message == "invalid endpoint":
                        _LOGGER.debug(
                            f"Endpoint {endpoint} is not valid for this device"
                        )
                        self._endpoint_cache[endpoint] = False
                    else:
                        _LOGGER.error(f"API error: {error_message}")
                        raise LoggameraAPIError(f"API error: {error_message}")
                else:
                    _LOGGER.error(f"Unknown API error: {result['Error']}")
                    raise LoggameraAPIError(f"Unknown API error: {result['Error']}")

            return result
        except requests.exceptions.RequestException as err:
            _LOGGER.error(f"Request error: {err}")
            raise LoggameraAPIError(f"Request error: {err}")

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

        return self._make_request(
            API_ENDPOINT_DEVICES, {"OrganizationId": self.organization_id}
        )

    def _validate_device_params(
        self, device_id: Union[str, int], device_type: str
    ) -> int:
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

        # If we have a primary endpoint, try it first
        if primary_endpoint:
            try:
                # Skip if we know this endpoint is invalid
                if not (
                    primary_endpoint in self._endpoint_cache
                    and self._endpoint_cache[primary_endpoint] is False
                ):
                    response = self._make_request(
                        primary_endpoint, {"DeviceId": device_id}
                    )

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
                if (
                    endpoint in self._endpoint_cache
                    and self._endpoint_cache[endpoint] is False
                ):
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

    def get_device_data(
        self, device_id: Union[str, int], device_type: str
    ) -> Dict[str, Any]:
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
            return self._make_request(
                API_ENDPOINT_CAPABILITIES, {"DeviceId": device_id}
            )
        except LoggameraAPIError as e:
            # Don't raise error if endpoint is not available
            if "invalid endpoint" in str(e):
                _LOGGER.warning(
                    f"Capabilities endpoint not available for device {device_id}"
                )
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
                    f"Scenarios endpoint not available for organization "
                    f"{self.organization_id}"
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
