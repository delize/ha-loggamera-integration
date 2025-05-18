"""API client for Loggamera."""

import logging
import requests
import ssl
import sys
import platform
import json
from datetime import datetime, timedelta
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context

from .const import (
    BASE_API_URL,
    ORGANIZATIONS_ENDPOINT,
    DEVICES_ENDPOINT,
    POWER_METER_ENDPOINT,
    ROOM_SENSOR_ENDPOINT,
    GENERIC_DEVICE_ENDPOINT,
    WATER_METER_ENDPOINT,
    COOLING_UNIT_ENDPOINT,
    HEAT_PUMP_ENDPOINT,
    RAW_DATA_ENDPOINT,
    GET_CAPABILITIES_ENDPOINT,
    SET_PROPERTY_ENDPOINT,
    SCENARIOS_ENDPOINT,
    USER_ACCESS_ENDPOINT,
    EXECUTE_SCENARIO_ENDPOINT,
)

_LOGGER = logging.getLogger(__name__)

class TLSAdapter(HTTPAdapter):
    """HTTP adapter that forces TLS version."""
    
    def __init__(self, tls_version=ssl.PROTOCOL_TLS, **kwargs):
        """Initialize the adapter with specific TLS version."""
        self.tls_version = tls_version
        super().__init__(**kwargs)
    
    def init_poolmanager(self, *args, **kwargs):
        """Initialize the pool manager with our TLS context."""
        context = create_urllib3_context(ciphers=None)
        # Force the specified TLS version
        context.options |= (ssl.OP_NO_SSLv2 | ssl.OP_NO_SSLv3 | ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1)
        kwargs['ssl_context'] = context
        return super().init_poolmanager(*args, **kwargs)

class LoggameraAPIError(Exception):
    """Exception for Loggamera API errors."""
    pass

class LoggameraAPI:
    """API client for Loggamera."""
    
    def __init__(self, api_key, organization_id=None, user_id=None):
        """Initialize the API client.
        
        Args:
            api_key: The API key for authenticating with Loggamera
            organization_id: Optional organization ID for filtering
            user_id: Optional user ID for user access
        """
        self.api_key = api_key
        self.organization_id = organization_id
        self.user_id = user_id
        self.base_url = BASE_API_URL
        
        # Create a session with custom SSL/TLS settings
        self.session = requests.Session()
        
        # Add custom TLS adapter to force TLS 1.2+
        adapter = TLSAdapter()
        self.session.mount('https://', adapter)
        
        # Log system information for diagnostics
        self._log_system_info()

    def _log_system_info(self):
        """Log system information for diagnostics."""
        _LOGGER.info(f"Python version: {sys.version}")
        _LOGGER.info(f"OpenSSL version: {ssl.OPENSSL_VERSION}")
        _LOGGER.info(f"System: {platform.system()} {platform.release()}")
        _LOGGER.info(f"Connecting to Loggamera API at: {self.base_url}")

    def _headers(self):
        """Return the headers for API requests."""
        return {
            "Content-Type": "application/json"
        }

    def _make_request(self, endpoint, data=None):
        """Make a POST request to the Loggamera API.
        
        All requests to Loggamera API require the ApiKey in the body.
        """
        url = f"{self.base_url}/{endpoint}"
        
        # Ensure data is a dictionary and add ApiKey
        if data is None:
            data = {}
        
        # Add API key to all requests
        data["ApiKey"] = self.api_key
        
        try:
            _LOGGER.debug(f"Making request to {url}")
            
            # Format data exactly as shown in their examples - using json.dumps
            json_data = json.dumps(data)
            _LOGGER.debug(f"Request payload: {json_data}")
            
            response = self.session.post(
                url,
                headers=self._headers(),
                data=json_data,  # Use data parameter with stringified JSON as shown in examples
                timeout=30  # Add a timeout to prevent hanging requests
            )
            
            return self._handle_response(response)
        except requests.exceptions.SSLError as ssl_error:
            # Special handling for SSL errors with more detailed logging
            _LOGGER.error(f"SSL Error communicating with Loggamera API: {ssl_error}")
            
            # Try to determine more specific SSL error details
            error_str = str(ssl_error)
            if "CERTIFICATE_VERIFY_FAILED" in error_str:
                _LOGGER.error("Certificate verification failed. This could be due to a missing CA certificate.")
            elif "WRONG_VERSION_NUMBER" in error_str:
                _LOGGER.error("Wrong TLS protocol version. The server might not support the TLS version being used.")
            elif "TLSV1_ALERT_INTERNAL_ERROR" in error_str:
                _LOGGER.error("TLS internal error. This could be a server-side issue or incompatible TLS configuration.")
                _LOGGER.error("The Loggamera API might require a specific TLS version. Try manually checking with:")
                _LOGGER.error("openssl s_client -connect platform.loggamera.se:443 -tls1_2")
                
            raise LoggameraAPIError(f"SSL/TLS error: {ssl_error}")
        except requests.RequestException as error:
            _LOGGER.error(f"Error communicating with Loggamera API: {error}")
            raise LoggameraAPIError(f"Communication error: {error}")

    def _handle_response(self, response):
        """Handle the API response."""
        if response.status_code == 200:
            # Log raw response for debugging
            _LOGGER.debug(f"Raw response: {response.text}")
            
            # Some endpoints don't return a body, handle that case
            if not response.text:
                return {"success": True}
                
            try:
                data = response.json()
                
                # Check for API error
                if data.get("Error") is not None and data.get("Error") != "null" and data.get("Error") != "":
                    error_message = f"API error: {data.get('Error')}"
                    _LOGGER.error(error_message)
                    raise LoggameraAPIError(error_message)
                    
                return data
            except ValueError as e:
                _LOGGER.error(f"Failed to parse JSON response: {e}")
                _LOGGER.debug(f"Response text: {response.text}")
                raise LoggameraAPIError(f"Invalid JSON response: {e}")
        else:
            error_message = f"API error {response.status_code}: {response.text}"
            _LOGGER.error(error_message)
            raise LoggameraAPIError(error_message)

    def get_organizations(self):
        """Get organization data."""
        return self._make_request(ORGANIZATIONS_ENDPOINT)

    def get_devices(self):
        """Get device data."""
        data = {}
        if self.organization_id:
            data["OrganizationId"] = self.organization_id
        return self._make_request(DEVICES_ENDPOINT, data)

    def get_power_meter_data(self, device_id=None, date_time_utc=None):
        """Get power meter data."""
        data = self._prepare_device_request_data(device_id, date_time_utc)
        return self._make_request(POWER_METER_ENDPOINT, data)

    def get_water_meter_data(self, device_id=None, date_time_utc=None):
        """Get water meter data."""
        data = self._prepare_device_request_data(device_id, date_time_utc)
        return self._make_request(WATER_METER_ENDPOINT, data)

    def get_room_sensor_data(self, device_id=None, date_time_utc=None):
        """Get room sensor data."""
        data = self._prepare_device_request_data(device_id, date_time_utc)
        return self._make_request(ROOM_SENSOR_ENDPOINT, data)

    def get_generic_device_data(self, device_id=None, date_time_utc=None):
        """Get generic device data."""
        data = self._prepare_device_request_data(device_id, date_time_utc)
        return self._make_request(GENERIC_DEVICE_ENDPOINT, data)

    def get_cooling_unit_data(self, device_id=None, date_time_utc=None):
        """Get cooling unit data."""
        data = self._prepare_device_request_data(device_id, date_time_utc)
        return self._make_request(COOLING_UNIT_ENDPOINT, data)

    def get_heat_pump_data(self, device_id=None, date_time_utc=None):
        """Get heat pump data."""
        data = self._prepare_device_request_data(device_id, date_time_utc)
        return self._make_request(HEAT_PUMP_ENDPOINT, data)

    def get_raw_data(self, device_id=None, date_time_utc=None):
        """Get raw data."""
        data = self._prepare_device_request_data(device_id, date_time_utc)
        return self._make_request(RAW_DATA_ENDPOINT, data)

    def get_capabilities(self, device_id):
        """Get device capabilities."""
        data = {"DeviceId": device_id}
        return self._make_request(GET_CAPABILITIES_ENDPOINT, data)

    def set_property(self, device_id, property_name, value):
        """Set a device property."""
        data = {
            "DeviceId": device_id,
            "PropertyName": property_name,
            "Value": value
        }
        return self._make_request(SET_PROPERTY_ENDPOINT, data)

    def get_scenarios(self):
        """Get scenarios."""
        data = {}
        if self.organization_id:
            data["OrganizationId"] = self.organization_id
        return self._make_request(SCENARIOS_ENDPOINT, data)

    def get_user_access(self):
        """Get user access information."""
        data = {}
        if self.user_id:
            data["UserId"] = self.user_id
        return self._make_request(USER_ACCESS_ENDPOINT, data)

    def execute_scenario(self, scenario_id, duration_minutes=None):
        """Execute a scenario."""
        data = {"ScenarioId": scenario_id}
        if duration_minutes is not None:
            data["DurationMinutes"] = duration_minutes
        return self._make_request(EXECUTE_SCENARIO_ENDPOINT, data)

    def _prepare_device_request_data(self, device_id=None, date_time_utc=None):
        """Prepare request data for device endpoints."""
        data = {}
        
        if device_id is not None:
            data["DeviceId"] = device_id
            
        # Add datetime if specified
        if date_time_utc is not None:
            # Convert datetime to ISO format string if it's a datetime object
            if isinstance(date_time_utc, datetime):
                date_time_utc = date_time_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
            data["DateTimeUtc"] = date_time_utc
        
        return data