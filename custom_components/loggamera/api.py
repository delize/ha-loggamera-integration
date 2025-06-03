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
            {"Content-Type": "application/json"}
        )
        # Note: We don't add X-Api-Key header by default anymore, since some endpoints need it in the body
        
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
            
        # Only add organization ID for certain endpoints that need it
        if endpoint not in ["Organizations", "PowerMeter"] and self.organization_id and "OrganizationId" not in data:
            data["OrganizationId"] = self.organization_id
            
        url = f"{self.base_url}/{endpoint}"
        
        _LOGGER.debug(f"Making request to {url} with data: {data}")
        
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
                
                # If Data is null, this is a critical error
                if "Data" in json_response and json_response["Data"] is None:
                    raise LoggameraAPIError(f"API error: {error_msg}")
                
                # Some errors may still return partial data, so we'll continue with a warning
                _LOGGER.warning(f"API warning: {error_msg}, but data was returned")
                
            return json_response
            
        except requests.exceptions.RequestException as err:
            _LOGGER.error(f"Request error: {err}")
            raise LoggameraAPIError(f"Request error: {err}")
            
        except json.JSONDecodeError as err:
            _LOGGER.error(f"JSON decode error: {err}")
            raise LoggameraAPIError(f"JSON decode error: {err}")

    def get_organizations(self) -> Dict[str, Any]:
        """Get organizations."""
        # Based on our API explorer testing, the Organizations endpoint requires the ApiKey in the body
        return self._make_request("Organizations", {"ApiKey": self.api_key})

    def get_devices(self) -> Dict[str, Any]:
        """Get devices."""
        # Build data with API key and organization ID if available
        data = {"ApiKey": self.api_key}
        if self.organization_id:
            data["OrganizationId"] = self.organization_id
        
        return self._make_request("Devices", data)

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