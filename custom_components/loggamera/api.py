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
        """Make a request to the Loggamera API."""
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
                raise LoggameraAPIError(f"HTTP error {response.status_code}: {response.text}")
            
            try:
                result = response.json()
            except ValueError:
                _LOGGER.error(f"Invalid JSON response: {response.text}")
                raise LoggameraAPIError(f"Invalid JSON response: {response.text}")
            
            # Check for API errors
            if "Error" in result and result["Error"] is not None:
                if isinstance(result["Error"], dict) and "Message" in result["Error"]:
                    error_message = result["Error"]["Message"]
                    if error_message == "invalid endpoint":
                        _LOGGER.debug(f"Endpoint {endpoint} is not valid for this device")
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
        """Get device data from appropriate endpoints.
        
        For PowerMeter devices, this will attempt to fetch both PowerMeter and RawData data
        and combine them for the most complete picture.
        """
        # Input validation
        try:
            device_id = int(device_id)  # Ensure device_id is an integer
        except (ValueError, TypeError):
            _LOGGER.error(f"Invalid device ID: {device_id}")
            raise LoggameraAPIError(f"Invalid device ID: {device_id}")
            
        if not device_type or not isinstance(device_type, str):
            _LOGGER.error(f"Invalid device type: {device_type}")
            raise LoggameraAPIError(f"Invalid device type: {device_type}")
        
        # For PowerMeter devices, try to fetch both PowerMeter and RawData data
        if device_type == "PowerMeter":
            combined_data = {"Data": {"Values": []}, "Error": None}
            raw_data_used = False
            power_meter_used = False
            
            # Try PowerMeter endpoint FIRST to ensure we have the standard sensors
            try:
                # Try simple format first (without DateTimeUtc)
                power_meter_data = self._make_request(API_ENDPOINT_POWER_METER, {
                    "ApiKey": self.api_key,
                    "DeviceId": device_id
                })
                
                # Check if we got valid data
                if "Data" in power_meter_data and power_meter_data["Data"] is not None and "Values" in power_meter_data["Data"] and power_meter_data["Data"]["Values"]:
                    # Add all PowerMeter values first to ensure they have priority
                    combined_data["Data"]["Values"] = power_meter_data["Data"]["Values"]
                    
                    if "LogDateTimeUtc" in power_meter_data["Data"]:
                        combined_data["Data"]["LogDateTimeUtc"] = power_meter_data["Data"]["LogDateTimeUtc"]
                    
                    _LOGGER.debug(f"Got {len(power_meter_data['Data']['Values'])} values from PowerMeter endpoint")
                    power_meter_used = True
                else:
                    # If simple format didn't work, try with DateTimeUtc
                    _LOGGER.debug("PowerMeter endpoint without DateTimeUtc returned no values, trying with DateTimeUtc")
                    current_time = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
                    power_meter_data = self._make_request(API_ENDPOINT_POWER_METER, {
                        "ApiKey": self.api_key,
                        "DeviceId": device_id,
                        "DateTimeUtc": current_time
                    })
                    
                    if "Data" in power_meter_data and power_meter_data["Data"] is not None and "Values" in power_meter_data["Data"] and power_meter_data["Data"]["Values"]:
                        # Add all PowerMeter values
                        combined_data["Data"]["Values"] = power_meter_data["Data"]["Values"]
                        
                        if "LogDateTimeUtc" in power_meter_data["Data"]:
                            combined_data["Data"]["LogDateTimeUtc"] = power_meter_data["Data"]["LogDateTimeUtc"]
                        
                        _LOGGER.debug(f"Got {len(power_meter_data['Data']['Values'])} values from PowerMeter endpoint with DateTimeUtc")
                        power_meter_used = True
                    else:
                        _LOGGER.debug("PowerMeter endpoint returned no values with either format")
            except LoggameraAPIError as e:
                _LOGGER.debug(f"Error getting PowerMeter data: {e}")
            
            # Then try RawData to add additional detailed metrics
            try:
                # Use simple format for RawData
                raw_data = self._make_request(API_ENDPOINT_RAW_DATA, {
                    "ApiKey": self.api_key,
                    "DeviceId": device_id
                })
                if "Data" in raw_data and raw_data["Data"] is not None and "Values" in raw_data["Data"]:
                    # If we didn't get a timestamp from PowerMeter, use the one from RawData
                    if "LogDateTimeUtc" not in combined_data["Data"] and "LogDateTimeUtc" in raw_data["Data"]:
                        combined_data["Data"]["LogDateTimeUtc"] = raw_data["Data"]["LogDateTimeUtc"]
                    
                    # Create synthetic PowerMeter values if none were found
                    if not power_meter_used:
                        # Find energy and power values in RawData to create equivalent PowerMeter values
                        for value in raw_data["Data"]["Values"]:
                            if value.get("Name") == "544352":  # Energy imported
                                # Create ConsumedTotalInkWh equivalent
                                synthetic_value = {
                                    "Name": "ConsumedTotalInkWh",
                                    "ClearTextName": "Total förbrukning",
                                    "ValueType": "DECIMAL",
                                    "Value": value.get("Value", "0"),
                                    "UnitType": "KwH",
                                    "UnitPresentation": "kWh",
                                    "_synthetic": True  # Mark as synthetic for debugging
                                }
                                combined_data["Data"]["Values"].append(synthetic_value)
                                _LOGGER.debug(f"Created synthetic ConsumedTotalInkWh from RawData")
                            
                            if value.get("Name") == "544399":  # Power
                                # Convert from W to kW for PowerInkW
                                try:
                                    power_w = float(value.get("Value", "0"))
                                    power_kw = power_w / 1000.0
                                    
                                    # Create PowerInkW equivalent
                                    synthetic_value = {
                                        "Name": "PowerInkW",
                                        "ClearTextName": "Effekt",
                                        "ValueType": "DECIMAL",
                                        "Value": str(power_kw),
                                        "UnitType": "KW",
                                        "UnitPresentation": "kW",
                                        "_synthetic": True  # Mark as synthetic for debugging
                                    }
                                    combined_data["Data"]["Values"].append(synthetic_value)
                                    _LOGGER.debug(f"Created synthetic PowerInkW from RawData")
                                except (ValueError, TypeError):
                                    _LOGGER.debug(f"Could not convert RawData power value to kW")
                    
                    # Add values from RawData that aren't already in the combined data
                    existing_names = [v.get("Name") for v in combined_data["Data"]["Values"]]
                    existing_cleartext = [v.get("ClearTextName") for v in combined_data["Data"]["Values"] if v.get("ClearTextName")]
                    
                    for value in raw_data["Data"]["Values"]:
                        # Skip if the Name already exists
                        if value.get("Name") in existing_names:
                            continue
                        
                        # Also skip if there's a clear text name match to avoid duplicates
                        clear_name = value.get("ClearTextName")
                        if clear_name and clear_name in existing_cleartext:
                            continue
                        
                        # Add this unique value
                        combined_data["Data"]["Values"].append(value)
                        existing_names.append(value.get("Name"))
                        if clear_name:
                            existing_cleartext.append(clear_name)
                    
                    _LOGGER.debug(f"Added additional values from RawData endpoint")
                    raw_data_used = True
                else:
                    _LOGGER.debug("No valid data from RawData endpoint")
            except LoggameraAPIError as e:
                _LOGGER.debug(f"Error getting RawData: {e}")
            
            # Record which endpoints were used
            if raw_data_used:
                combined_data["_raw_data_used"] = True
            if power_meter_used:
                combined_data["_power_meter_used"] = True
                
            # Check if we got any data
            if not combined_data["Data"]["Values"]:
                # If we got no data from either endpoint, try the other standard endpoints
                _LOGGER.warning(f"No data from PowerMeter or RawData endpoints, trying GenericDevice")
                try:
                    generic_data = self._make_request(API_ENDPOINT_GENERIC_DEVICE, {"DeviceId": device_id})
                    if "Data" in generic_data and generic_data["Data"] is not None and "Values" in generic_data["Data"]:
                        combined_data = generic_data
                        combined_data["_generic_device_used"] = True
                        return combined_data
                except LoggameraAPIError as e:
                    _LOGGER.debug(f"Error getting GenericDevice data: {e}")
                    
                _LOGGER.error(f"Failed to get any data for PowerMeter device {device_id}")
                raise LoggameraAPIError(f"No data found for PowerMeter device {device_id}")
            
            return combined_data
        
        # For other device types, try their specific endpoint
        endpoints_to_try = []
        
        if device_type == "RoomSensor":
            endpoints_to_try.append(API_ENDPOINT_ROOM_SENSOR)
        elif device_type == "WaterMeter":
            endpoints_to_try.append(API_ENDPOINT_WATER_METER)
        elif device_type == "CoolingUnit":
            endpoints_to_try.append(API_ENDPOINT_COOLING_UNIT)
        elif device_type == "HeatPump":
            endpoints_to_try.append(API_ENDPOINT_HEAT_PUMP)
        
        # Add RawData and GenericDevice as fallbacks for all device types
        endpoints_to_try.append(API_ENDPOINT_RAW_DATA)
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
                if "Error" in response and response["Error"] and isinstance(response["Error"], dict) and "Message" in response["Error"] and response["Error"]["Message"] == "invalid endpoint":
                    continue
                
                # Check if we got valid data
                if "Data" in response and "Values" in response["Data"] and response["Data"]["Values"]:
                    # Add the endpoint info to the response for debugging/tracking
                    response["_endpoint_used"] = endpoint
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