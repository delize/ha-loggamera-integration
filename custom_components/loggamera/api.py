"""API client for Loggamera."""
import logging
import requests
import certifi
import json
import sys
import platform
import ssl
from datetime import datetime

from homeassistant.const import CONTENT_TYPE_JSON

from .const import (
    API_URL,
    API_ENDPOINT_ORGANIZATIONS,
    API_ENDPOINT_DEVICES,
    API_ENDPOINT_POWER_METER,
    API_ENDPOINT_ROOM_SENSOR,
    API_ENDPOINT_GENERIC_DEVICE,
    API_ENDPOINT_WATER_METER,
    API_ENDPOINT_COOLING_UNIT,
    API_ENDPOINT_HEAT_PUMP,
    API_ENDPOINT_RAW_DATA,
    API_ENDPOINT_CAPABILITIES,
    API_ENDPOINT_SCENARIOS,
    API_ENDPOINT_EXECUTE_SCENARIO,
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

    def __init__(self, api_key, organization_id=None):
        """Initialize API client."""
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
        _LOGGER.info(f"OpenSSL version: {getattr(ssl, 'OPENSSL_VERSION', 'Unknown')}" 
                     if platform.python_implementation() == 'CPython' else "OpenSSL info not available")
        _LOGGER.info(f"System: {platform.system()} {platform.release()}")
        _LOGGER.info(f"Certifi location: {certifi.where()}")
        _LOGGER.info(f"API URL: {API_URL}")
        
        # For debugging - enable this if needed
        # from http.client import HTTPConnection
        # HTTPConnection.debuglevel = 1

    def _make_request(self, endpoint, data=None):
        """Make a request to the API."""
        # Check if we already know this endpoint is invalid
        if endpoint in self._endpoint_cache and self._endpoint_cache[endpoint] is False:
            _LOGGER.debug(f"Skipping known invalid endpoint: {endpoint}")
            return {"Data": {}, "Error": {"Message": "invalid endpoint"}}
            
        url = f"{API_URL}/{endpoint}"
        
        if data is None:
            data = {}
        
        # Add API key to all requests
        data["ApiKey"] = self.api_key
        
        # Add organization ID if available and not already in data
        if self.organization_id and "OrganizationId" not in data:
            # Only add for endpoints that accept OrganizationId
            if endpoint in [API_ENDPOINT_DEVICES, API_ENDPOINT_SCENARIOS]:
                data["OrganizationId"] = self.organization_id
        
        try:
            # Log the request but mask the API key
            log_data = data.copy()
            if "ApiKey" in log_data:
                log_data["ApiKey"] = "***API_KEY***"
            _LOGGER.debug(f"Making request to {url}")
            
            response = self.session.post(
                url,
                headers={"Content-Type": CONTENT_TYPE_JSON},
                data=json.dumps(data),
                timeout=30
            )
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    
                    # Check if we got a straightforward error message
                    if isinstance(result, dict) and "Message" in result:
                        message = result["Message"]
                        if message == "access denied":
                            _LOGGER.error(f"API error: {result}")
                            raise LoggameraAPIError(f"API error: {result}")
                        elif message == "invalid endpoint":
                            _LOGGER.warning(f"API endpoint not available: {endpoint}")
                            # Cache that this endpoint is invalid
                            self._endpoint_cache[endpoint] = False
                            return {"Data": {}, "Error": result}
                    
                    # Mark the endpoint as valid in our cache
                    self._endpoint_cache[endpoint] = True
                    
                    # Check if there's an error in the error field
                    if "Error" in result and result["Error"] is not None and result["Error"] != "null" and result["Error"] != "":
                        error_message = result["Error"]
                        _LOGGER.error(f"API error: {error_message}")
                        raise LoggameraAPIError(f"API error: {error_message}")
                    
                    # Check if this is a data endpoint that might have a timestamp
                    if endpoint in [API_ENDPOINT_POWER_METER, API_ENDPOINT_RAW_DATA, API_ENDPOINT_GENERIC_DEVICE]:
                        device_id = data.get("DeviceId")
                        if device_id and "Data" in result and "LogDateTimeUtc" in result["Data"]:
                            new_timestamp = result["Data"]["LogDateTimeUtc"]
                            
                            # Generate a key for this device+endpoint combination
                            cache_key = f"{endpoint}_{device_id}"
                            
                            # Check if we have a previous timestamp for this device
                            if cache_key in self._last_data_timestamp:
                                old_timestamp = self._last_data_timestamp[cache_key]
                                
                                # If the timestamp has changed, log it
                                if old_timestamp != new_timestamp:
                                    _LOGGER.info(f"Data updated for {endpoint} device {device_id}: {old_timestamp} -> {new_timestamp}")
                                    self._last_data_timestamp[cache_key] = new_timestamp
                            else:
                                # First time seeing this device
                                self._last_data_timestamp[cache_key] = new_timestamp
                                _LOGGER.info(f"Initial data for {endpoint} device {device_id}: {new_timestamp}")
                    
                    return result
                except ValueError as e:
                    _LOGGER.error(f"Invalid JSON response: {response.text}")
                    raise LoggameraAPIError(f"Invalid JSON response: {e}")
            else:
                _LOGGER.error(f"HTTP error {response.status_code}: {response.text}")
                raise LoggameraAPIError(f"HTTP error {response.status_code}: {response.text}")
        except requests.exceptions.RequestException as e:
            _LOGGER.error(f"Request error: {e}")
            raise LoggameraAPIError(f"Request error: {e}")

    def get_organizations(self):
        """Get organizations."""
        return self._make_request(API_ENDPOINT_ORGANIZATIONS)

    def get_devices(self):
        """Get devices."""
        if not self.organization_id:
            _LOGGER.error("Organization ID is required for get_devices")
            raise LoggameraAPIError("Organization ID is required for get_devices")
            
        return self._make_request(API_ENDPOINT_DEVICES, {"OrganizationId": self.organization_id})

    def get_device_data(self, device_id, device_type):
        """Get device data - tries multiple endpoints based on availability.
        
        Note: For PowerMeter devices, data typically updates approximately every 30 minutes
        in the Loggamera backend. More frequent polling will not yield new data until
        the backend itself updates.
        """
        # Create a list of endpoints to try in order of preference
        endpoints_to_try = []
        
        # First, add the device-specific endpoint
        if device_type == "PowerMeter":
            endpoints_to_try.append(API_ENDPOINT_POWER_METER)
        elif device_type == "RoomSensor":
            endpoints_to_try.append(API_ENDPOINT_ROOM_SENSOR)
        elif device_type == "WaterMeter":
            endpoints_to_try.append(API_ENDPOINT_WATER_METER)
        elif device_type == "CoolingUnit":
            endpoints_to_try.append(API_ENDPOINT_COOLING_UNIT)
        elif device_type == "HeatPump":
            endpoints_to_try.append(API_ENDPOINT_HEAT_PUMP)
        
        # Add RawData as second preference - it often has more detailed info
        endpoints_to_try.append(API_ENDPOINT_RAW_DATA)
        
        # Add GenericDevice as final fallback
        endpoints_to_try.append(API_ENDPOINT_GENERIC_DEVICE)
        
        # Try endpoints in order
        last_error = None
        for endpoint in endpoints_to_try:
            try:
                # Skip if we know this endpoint is invalid
                if endpoint in self._endpoint_cache and self._endpoint_cache[endpoint] is False:
                    continue
                
                response = self._make_request(endpoint, {"DeviceId": device_id})
                
                # Check if this endpoint is invalid
                if "Error" in response and response["Error"] and "Message" in response["Error"] and response["Error"]["Message"] == "invalid endpoint":
                    continue
                
                # Check if we got valid data
                if "Data" in response and "Values" in response["Data"] and response["Data"]["Values"]:
                    return response
            except LoggameraAPIError as e:
                _LOGGER.debug(f"Error with endpoint {endpoint}: {e}")
                last_error = e
                continue
        
        # If we get here, all endpoints failed
        if last_error:
            raise last_error
        else:
            raise LoggameraAPIError(f"All endpoints failed for device {device_id}")

    def get_raw_data(self, device_id):
        """Get raw device data."""
        return self._make_request(API_ENDPOINT_RAW_DATA, {
            "DeviceId": device_id,
        })

    def get_capabilities(self, device_id):
        """Get device capabilities."""
        try:
            return self._make_request(API_ENDPOINT_CAPABILITIES, {"DeviceId": device_id})
        except LoggameraAPIError as e:
            # Don't raise error if endpoint is not available
            if "invalid endpoint" in str(e):
                _LOGGER.warning(f"Capabilities endpoint not available for device {device_id}")
                return {"Data": {"ReadCapabilities": [], "WriteCapabilities": []}, "Error": None}
            else:
                raise

    def get_scenarios(self):
        """Get scenarios."""
        if not self.organization_id:
            _LOGGER.error("Organization ID is required for get_scenarios")
            return {"Data": {"Scenarios": []}, "Error": None}
            
        try:
            return self._make_request(API_ENDPOINT_SCENARIOS, {"OrganizationId": self.organization_id})
        except LoggameraAPIError as e:
            # Don't raise error if endpoint is not available
            if "invalid endpoint" in str(e):
                _LOGGER.warning(f"Scenarios endpoint not available for organization {self.organization_id}")
                return {"Data": {"Scenarios": []}, "Error": None}
            else:
                raise
                
    def execute_scenario(self, scenario_id, duration_minutes=None):
        """Execute a scenario."""
        data = {"ScenarioId": scenario_id}
        
        if duration_minutes is not None:
            data["DurationMinutes"] = duration_minutes
            
        return self._make_request(API_ENDPOINT_EXECUTE_SCENARIO, data)