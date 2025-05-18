"""API client for Loggamera."""

import logging
import requests
import ssl
import sys
import platform
import json
import certifi
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
        # Force TLS version
        context.options |= (ssl.OP_NO_SSLv2 | ssl.OP_NO_SSLv3 | ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1)
        kwargs['ssl_context'] = context
        
        # Explicitly set the cert path using certifi
        kwargs.setdefault('cert_reqs', 'CERT_REQUIRED')
        kwargs.setdefault('ca_certs', certifi.where())
        
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
        
        # Use the TLS adapter we defined above
        adapter = TLSAdapter()
        self.session.mount('https://', adapter)
        
        # Explicitly set verify to use certifi's certificate bundle
        self.session.verify = certifi.where()
        
        # Log system information for diagnostics
        self._log_system_info()

    def _log_system_info(self):
        """Log system information for diagnostics."""
        _LOGGER.info(f"Python version: {sys.version}")
        _LOGGER.info(f"OpenSSL version: {ssl.OPENSSL_VERSION}")
        _LOGGER.info(f"System: {platform.system()} {platform.release()}")
        _LOGGER.info(f"Certifi location: {certifi.where()}")
        _LOGGER.info(f"API URL: {self.base_url}")

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
            
            # Using json.dumps directly to match the format in the examples
            payload = json.dumps(data)
            
            response = self.session.post(
                url,
                headers=self._headers(),
                data=payload,
                timeout=30,  # Add a timeout to prevent hanging requests
                verify=certifi.where()  # Explicitly use certifi for certificate verification
            )
            
            return self._handle_response(response)
        except requests.exceptions.SSLError as ssl_error:
            # Special handling for SSL errors with more detailed logging
            _LOGGER.error(f"SSL Error communicating with Loggamera API: {ssl_error}")
            
            # Try to determine more specific SSL error details
            error_str = str(ssl_error)
            if "CERTIFICATE_VERIFY_FAILED" in error_str:
                _LOGGER.error("Certificate verification failed. This could be due to a missing CA certificate.")
                _LOGGER.error(f"Certificate path used: {certifi.where()}")
                
                # Try to debug certificate issue
                try:
                    import subprocess
                    host = self.base_url.split('//')[1].split('/')[0]
                    _LOGGER.error(f"Attempting to get certificate info for {host}")
                    cmd = ["openssl", "s_client", "-connect", f"{host}:443", "-showcerts"]
                    result = subprocess.run(cmd, capture_output=True, text=True, input="")
                    if "BEGIN CERTIFICATE" in result.stdout:
                        _LOGGER.info("Server certificate retrieved successfully")
                        cert_lines = [line for line in result.stdout.split('\n') if "issuer=" in line or "subject=" in line]
                        for line in cert_lines:
                            _LOGGER.info(f"Cert info: {line.strip()}")
                except Exception as e:
                    _LOGGER.error(f"Failed to get certificate info: {e}")
                
            elif "WRONG_VERSION_NUMBER" in error_str:
                _LOGGER.error("Wrong TLS protocol version. The server might not support the TLS version being used.")
                
            raise LoggameraAPIError(f"SSL/TLS error: {ssl_error}")
        except requests.RequestException as error:
            _LOGGER.error(f"Error communicating with Loggamera API: {error}")
            raise LoggameraAPIError(f"Communication error: {error}")

    def _handle_response(self, response):
        """Handle the API response."""
        if response.status_code == 200:
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
        data = self._prepare_request_data(device_id, date_time_utc)
        return self._make_request(POWER_METER_ENDPOINT, data)

    def get_water_meter_data(self, device_id=None, date_time_utc=None):
        """Get water meter data."""
        data = self._prepare_request_data(device_id, date_time_utc)
        return self._make_request(WATER_METER_ENDPOINT, data)

    def get_room_sensor_data(self, device_id=None, date_time_utc=None):
        """Get room sensor data."""
        data = self._prepare_request_data(device_id, date_time_utc)
        return self._make_request(ROOM_SENSOR_ENDPOINT, data)

    def get_generic_device_data(self, device_id=None, date_time_utc=None):
        """Get generic device data."""
        data = self._prepare_request_data(device_id, date_time_utc)
        return self._make_request(GENERIC_DEVICE_ENDPOINT, data)

    def get_cooling_unit_data(self, device_id=None, date_time_utc=None):
        """Get cooling unit data."""
        data = self._prepare_request_data(device_id, date_time_utc)
        return self._make_request(COOLING_UNIT_ENDPOINT, data)

    def get_heat_pump_data(self, device_id=None, date_time_utc=None):
        """Get heat pump data."""
        data = self._prepare_request_data(device_id, date_time_utc)
        return self._make_request(HEAT_PUMP_ENDPOINT, data)

    def get_raw_data(self, device_id=None, date_time_utc=None):
        """Get raw data."""
        data = self._prepare_request_data(device_id, date_time_utc)
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

    def _prepare_request_data(self, device_id=None, date_time_utc=None):
        """Prepare request data with common parameters.
        
        Based on the example API calls, the parameter is DateTimeUtc, not StartTime/EndTime.
        """
        data = {}
        
        if device_id is not None:
            data["DeviceId"] = device_id
            
        # Add time filter if specified - following example format
        if date_time_utc is not None:
            # Format datetime to ISO format
            if isinstance(date_time_utc, datetime):
                date_time_utc = date_time_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
            data["DateTimeUtc"] = date_time_utc
        else:
            # Default to current time if not specified
            data["DateTimeUtc"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        
        return data