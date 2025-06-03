"""Loggamera API client."""
import logging
import json
import platform
import sys
import ssl
import certifi
from datetime import datetime
from typing import Dict, Any, Optional

import requests

_LOGGER = logging.getLogger(__name__)

class LoggameraAPIError(Exception):
    """Exception to indicate a general API error."""
    pass

class LoggameraAPI:
    """Loggamera API client."""

    def __init__(
        self, api_key: str, organization_id: Optional[str] = None, base_url: str = "https://platform.loggamera.se/api/v2"
    ):
        """Initialize the API client."""
        self.api_key = api_key
        self.organization_id = organization_id
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update(
            {"Content-Type": "application/json", "X-Api-Key": api_key}
        )
        
        # Log environment information for debugging
        _LOGGER.info(f"Python version: {sys.version}")
        _LOGGER.info(f"OpenSSL version: {ssl.OPENSSL_VERSION}")
        _LOGGER.info(f"System: {platform.system()} {platform.release()}")
        _LOGGER.info(f"Certifi location: {certifi.where()}")
        _LOGGER.info(f"API URL: {base_url}")
        
        # Keep track of device data update timestamps
        self.device_timestamps = {}
        self.last_device_data = {}

    def _make_request(self, endpoint: str, data: Dict = None) -> Dict[str, Any]:
        """Make a request to the API."""
        if not data:
            data = {}
            
        # Add organization ID if available and not already in data
        if self.organization_id and "OrganizationId" not in data:
            data["OrganizationId"] = self.organization_id
            
        url = f"{self.base_url}/{endpoint}"
        
        _LOGGER.debug(f"Making request to {url}")
        
        try:
            response = self.session.post(
                url,
                json=data,
                timeout=30
            )
            
            # Check for HTTP errors
            response.raise_for_status()
            
            # Parse response
            json_response = response.json()
            
            # Check for API errors
            if "Error" in json_response and json_response["Error"]:
                error_msg = json_response["Error"].get("Message", "Unknown API error")
                _LOGGER.error(f"API error: {error_msg}")
                raise LoggameraAPIError(f"API error: {error_msg}")
                
            return json_response
            
        except requests.exceptions.RequestException as err:
            _LOGGER.error(f"Request error: {err}")
            raise LoggameraAPIError(f"Request error: {err}")
            
        except json.JSONDecodeError as err:
            _LOGGER.error(f"JSON decode error: {err}")
            raise LoggameraAPIError(f"JSON decode error: {err}")

    def get_organizations(self) -> Dict[str, Any]:
        """Get organizations."""
        return self._make_request("Organizations")

    def get_devices(self) -> Dict[str, Any]:
        """Get devices."""
        return self._make_request("Devices")

    def get_scenarios(self) -> Dict[str, Any]:
        """Get scenarios."""
        return self._make_request("Scenarios")

    def execute_scenario(self, scenario_id: str) -> Dict[str, Any]:
        """Execute a scenario."""
        return self._make_request("ExecuteScenario", {"ScenarioId": scenario_id})

    def get_device_data(self, device_id: str, device_type: str) -> Dict[str, Any]:
        """Get device data based on device type."""
        endpoint = self._get_endpoint_for_device_type(device_type)
        
        try:
            # Special handling for PowerMeter endpoint based on the working example
            if endpoint == "PowerMeter":
                # Use the current time in the required format
                current_time = datetime.utcnow()
                timestamp = current_time.strftime("%Y-%m-%dT%H:%M:%SZ")
                
                # Using the format that works with the API (confirmed with API explorer)
                data = {
                    "ApiKey": self.api_key,  # API key is required in body for this endpoint
                    "DeviceId": int(device_id),  # Must be an integer
                    "DateTimeUtc": timestamp  # This is the required format
                }
                
                _LOGGER.debug(f"PowerMeter request with data: {data}")
                response = self._make_request(endpoint, data)
            else:
                # Default request format for other endpoints
                response = self._make_request(endpoint, {"DeviceId": device_id})
            
            # Debug the response structure 
            if endpoint == "PowerMeter":
                _LOGGER.debug(f"PowerMeter response keys: {list(response.keys())}")
                if "Data" in response:
                    if response["Data"] is None:
                        _LOGGER.error("PowerMeter response Data is None")
                    else:
                        _LOGGER.debug(f"PowerMeter Data keys: {list(response['Data'].keys())}")
                        if "Values" in response["Data"]:
                            _LOGGER.debug(f"Found {len(response['Data']['Values'])} values in response")
                            for val in response["Data"]["Values"]:
                                _LOGGER.debug(f"Value: {val['Name']} = {val['Value']} {val.get('UnitPresentation', '')}")
            
            # Store timestamp for PowerMeter devices
            if endpoint == "PowerMeter" and "Data" in response and response["Data"] is not None:
                if "LogDateTimeUtc" in response["Data"]:
                    timestamp = response["Data"]["LogDateTimeUtc"]
                    
                    if device_id not in self.device_timestamps or self.device_timestamps[device_id] != timestamp:
                        # Log when data actually updates
                        if device_id in self.device_timestamps:
                            _LOGGER.debug(f"PowerMeter device {device_id} data updated: {timestamp} (previous: {self.device_timestamps[device_id]})")
                        else:
                            _LOGGER.info(f"Initial data for PowerMeter device {device_id}: {timestamp}")
                            
                        self.device_timestamps[device_id] = timestamp
            
            # Store the device data for later use
            self.last_device_data[device_id] = response
            
            return response
            
        except LoggameraAPIError as error:
            # If we get an error, try falling back to the RawData endpoint
            error_str = str(error)
            
            if "invalid endpoint" in error_str.lower() or "invalid power meter" in error_str.lower() or "malformed request" in error_str.lower():
                # Try RawData instead
                _LOGGER.debug(f"Falling back to RawData endpoint for device {device_id}")
                return self._make_request("RawData", {"DeviceId": device_id})
            else:
                # Re-raise other errors
                raise

    def _get_endpoint_for_device_type(self, device_type: str) -> str:
        """Map device type to API endpoint."""
        # Map known device types to endpoints
        type_to_endpoint = {
            "PowerMeter": "PowerMeter",
            "RoomSensor": "RoomSensor",
            "WaterMeter": "WaterMeter",
            "CoolingUnit": "CoolingUnit",
            "HeatPump": "HeatPump",
            "GenericDevice": "GenericDevice",
        }
        
        # Return the appropriate endpoint or fallback to RawData
        return type_to_endpoint.get(device_type, "RawData")