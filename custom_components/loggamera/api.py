"""API client for Loggamera."""

import logging
import requests
from datetime import datetime, timedelta

_LOGGER = logging.getLogger(__name__)

class LoggameraAPIError(Exception):
    """Exception for Loggamera API errors."""
    pass

class LoggameraAPI:
    """API client for Loggamera."""
    
    def __init__(self, api_key):
        """Initialize the API client."""
        self.api_key = api_key
        self.base_url = "https://api.loggamera.com/Api/v2"

    def _headers(self):
        """Return the headers for API requests."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def _make_request(self, endpoint, data=None):
        """Make a POST request to the Loggamera API."""
        url = f"{self.base_url}/{endpoint}"
        
        try:
            response = requests.post(
                url,
                headers=self._headers(),
                json=data or {}
            )
            return self._handle_response(response)
        except requests.RequestException as error:
            _LOGGER.error(f"Error communicating with Loggamera API: {error}")
            raise LoggameraAPIError(f"Communication error: {error}")

    def _handle_response(self, response):
        """Handle the API response."""
        if response.status_code == 200:
            return response.json()
        else:
            error_message = f"API error {response.status_code}: {response.text}"
            _LOGGER.error(error_message)
            raise LoggameraAPIError(error_message)

    def get_organizations(self):
        """Get organization data."""
        return self._make_request("Organizations")

    def get_devices(self):
        """Get device data."""
        return self._make_request("Devices")

    def get_power_meter_data(self, device_id=None, start_time=None, end_time=None):
        """Get power meter data."""
        data = self._prepare_time_filter(device_id, start_time, end_time)
        return self._make_request("PowerMeter", data)

    def get_water_meter_data(self, device_id=None, start_time=None, end_time=None):
        """Get water meter data."""
        data = self._prepare_time_filter(device_id, start_time, end_time)
        return self._make_request("WaterMeter", data)

    def get_room_sensor_data(self, device_id=None, start_time=None, end_time=None):
        """Get room sensor data."""
        data = self._prepare_time_filter(device_id, start_time, end_time)
        return self._make_request("RoomSensor", data)

    def get_generic_device_data(self, device_id=None, start_time=None, end_time=None):
        """Get generic device data."""
        data = self._prepare_time_filter(device_id, start_time, end_time)
        return self._make_request("GenericDevice", data)

    def get_cooling_unit_data(self, device_id=None, start_time=None, end_time=None):
        """Get cooling unit data."""
        data = self._prepare_time_filter(device_id, start_time, end_time)
        return self._make_request("CoolingUnit", data)

    def get_heat_pump_data(self, device_id=None, start_time=None, end_time=None):
        """Get heat pump data."""
        data = self._prepare_time_filter(device_id, start_time, end_time)
        return self._make_request("HeatPump", data)

    def get_raw_data(self, device_id=None, start_time=None, end_time=None):
        """Get raw data."""
        data = self._prepare_time_filter(device_id, start_time, end_time)
        return self._make_request("RawData", data)

    def get_capabilities(self, device_id=None):
        """Get device capabilities."""
        data = {} if device_id is None else {"deviceId": device_id}
        return self._make_request("GetCapabilities", data)

    def set_property(self, device_id, property_name, property_value):
        """Set a device property."""
        data = {
            "deviceId": device_id,
            "propertyName": property_name,
            "propertyValue": property_value
        }
        return self._make_request("SetProperty", data)

    def get_scenarios(self):
        """Get scenarios."""
        return self._make_request("Scenarios")

    def get_user_access(self):
        """Get user access information."""
        return self._make_request("UserAccess")

    def execute_scenario(self, scenario_id):
        """Execute a scenario."""
        data = {"scenarioId": scenario_id}
        return self._make_request("ExecuteScenarioAsync", data)

    def _prepare_time_filter(self, device_id=None, start_time=None, end_time=None):
        """Prepare time filter for data requests."""
        data = {}
        
        if device_id is not None:
            data["deviceId"] = device_id
            
        # Default to last 24 hours if no time range is specified
        if start_time is None:
            start_time = datetime.now() - timedelta(days=1)
        if end_time is None:
            end_time = datetime.now()
            
        # Format datetime objects to ISO format strings
        if isinstance(start_time, datetime):
            start_time = start_time.isoformat()
        if isinstance(end_time, datetime):
            end_time = end_time.isoformat()
            
        data["startTime"] = start_time
        data["endTime"] = end_time
        
        return data