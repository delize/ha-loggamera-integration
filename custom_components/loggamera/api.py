"""API client for Loggamera."""

import logging
import requests
from datetime import datetime, timedelta

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
            response = requests.post(
                url,
                headers=self._headers(),
                json=data
            )
            return self._handle_response(response)
        except requests.RequestException as error:
            _LOGGER.error(f"Error communicating with Loggamera API: {error}")
            raise LoggameraAPIError(f"Communication error: {error}")

    def _handle_response(self, response):
        """Handle the API response."""
        if response.status_code == 200:
            # Some endpoints don't return a body, handle that case
            if not response.text:
                return {"success": True}
                
            data = response.json()
            
            # Check for API error
            if data.get("Error") is not None and data.get("Error") != "null" and data.get("Error") != "":
                error_message = f"API error: {data.get('Error')}"
                _LOGGER.error(error_message)
                raise LoggameraAPIError(error_message)
                
            return data
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

    def get_power_meter_data(self, device_id=None, start_time=None, end_time=None):
        """Get power meter data."""
        data = self._prepare_request_data(device_id, start_time, end_time)
        return self._make_request(POWER_METER_ENDPOINT, data)

    def get_water_meter_data(self, device_id=None, start_time=None, end_time=None):
        """Get water meter data."""
        data = self._prepare_request_data(device_id, start_time, end_time)
        return self._make_request(WATER_METER_ENDPOINT, data)

    def get_room_sensor_data(self, device_id=None, start_time=None, end_time=None):
        """Get room sensor data."""
        data = self._prepare_request_data(device_id, start_time, end_time)
        return self._make_request(ROOM_SENSOR_ENDPOINT, data)

    def get_generic_device_data(self, device_id=None, start_time=None, end_time=None):
        """Get generic device data."""
        data = self._prepare_request_data(device_id, start_time, end_time)
        return self._make_request(GENERIC_DEVICE_ENDPOINT, data)

    def get_cooling_unit_data(self, device_id=None, start_time=None, end_time=None):
        """Get cooling unit data."""
        data = self._prepare_request_data(device_id, start_time, end_time)
        return self._make_request(COOLING_UNIT_ENDPOINT, data)

    def get_heat_pump_data(self, device_id=None, start_time=None, end_time=None):
        """Get heat pump data."""
        data = self._prepare_request_data(device_id, start_time, end_time)
        return self._make_request(HEAT_PUMP_ENDPOINT, data)

    def get_raw_data(self, device_id=None, start_time=None, end_time=None):
        """Get raw data."""
        data = self._prepare_request_data(device_id, start_time, end_time)
        return self._make_request(RAW_DATA_ENDPOINT, data)

    def get_capabilities(self, device_id):
        """Get device capabilities."""
        data = {"DeviceId": device_id}
        return self._make_request(GET_CAPABILITIES_ENDPOINT, data)

    def set_property(self, device_id, property_name, property_value):
        """Set a device property."""
        data = {
            "DeviceId": device_id,
            "PropertyName": property_name,
            "PropertyValue": property_value
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

    def _prepare_request_data(self, device_id=None, start_time=None, end_time=None):
        """Prepare request data with common parameters."""
        data = {}
        
        if device_id is not None:
            data["DeviceId"] = device_id
            
        # Add time filter if specified
        if start_time is not None:
            # Format datetime to ISO format
            if isinstance(start_time, datetime):
                start_time = start_time.isoformat()
            data["StartTime"] = start_time
            
        if end_time is not None:
            # Format datetime to ISO format
            if isinstance(end_time, datetime):
                end_time = end_time.isoformat()
            data["EndTime"] = end_time
        
        return data