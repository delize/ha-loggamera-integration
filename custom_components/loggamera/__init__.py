"""The Loggamera integration."""
import logging
import asyncio
from datetime import timedelta

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.const import Platform

from .api import LoggameraAPI, LoggameraAPIError
from .const import (
    DOMAIN,
    CONF_API_KEY,
    CONF_ORGANIZATION_ID,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    PLATFORMS,
)

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Loggamera component."""
    hass.data[DOMAIN] = {}
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Loggamera from a config entry."""
    # Get configuration from config entry
    api_key = entry.data[CONF_API_KEY]
    organization_id = entry.data.get(CONF_ORGANIZATION_ID)
    
    # Get scan interval from config entry options or use default
    scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    
    # Initialize API client
    api = LoggameraAPI(api_key, organization_id)
    
    # Verify connectivity before proceeding
    try:
        # Test the connection to the API
        org_response = await hass.async_add_executor_job(api.get_organizations)
        
        if "Data" not in org_response or "Organizations" not in org_response["Data"]:
            _LOGGER.error("Failed to fetch organizations - invalid response format")
            raise ConfigEntryNotReady("Invalid response from Loggamera API")
        
        # If no organization ID is set, try to use the first one
        if not organization_id and org_response["Data"]["Organizations"]:
            organization_id = org_response["Data"]["Organizations"][0]["Id"]
            api.organization_id = organization_id
            _LOGGER.info("Using first available organization")
            
        # Test device access
        try:
            devices_response = await hass.async_add_executor_job(api.get_devices)
            if "Data" not in devices_response or "Devices" not in devices_response["Data"]:
                _LOGGER.error("Failed to fetch devices - invalid response format")
                raise ConfigEntryNotReady("Invalid device response from Loggamera API")
        except LoggameraAPIError as err:
            _LOGGER.error(f"Error accessing devices: {err}")
            raise ConfigEntryNotReady(f"Failed to access Loggamera devices: {err}")
            
    except LoggameraAPIError as err:
        _LOGGER.error(f"Failed to connect to Loggamera API: {err}")
        raise ConfigEntryNotReady(f"Failed to connect to Loggamera API: {err}")
    
    # Create update coordinator
    coordinator = LoggameraDataUpdateCoordinator(
        hass,
        _LOGGER,
        api=api,
        name="loggamera",
        update_interval=timedelta(seconds=scan_interval),
    )
    
    # Initial update - this will raise ConfigEntryNotReady if it fails
    await coordinator.async_config_entry_first_update()
    
    # Store API client and coordinator in hass.data
    hass.data[DOMAIN][entry.entry_id] = {
        "api": api,
        "coordinator": coordinator,
    }
    
    # Log the scan interval for debugging
    _LOGGER.info(
        f"Loggamera integration set up with scan interval: {scan_interval} seconds "
        f"(PowerMeter data typically updates every ~30 minutes)"
    )
    
    # Set up all supported platforms - properly awaited
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # Register update listener for config entry changes
    entry.async_on_unload(entry.add_update_listener(async_update_options))
    
    return True

async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update options for the Loggamera integration."""
    await hass.config_entries.async_reload(entry.entry_id)

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    # Clean up if unload was successful
    if unload_ok:
        del hass.data[DOMAIN][entry.entry_id]
        
        # Remove the entire domain if it's empty
        if not hass.data[DOMAIN]:
            del hass.data[DOMAIN]
    
    return unload_ok

class LoggameraDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(
        self,
        hass: HomeAssistant,
        logger: logging.Logger,
        api: LoggameraAPI,
        name: str,
        update_interval: timedelta,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            logger,
            name=name,
            update_interval=update_interval,
        )
        self.api = api
        self._update_timestamps = {}
        self._data_age_warnings = {}

    async def _async_update_data(self):
        """Fetch data from API."""
        try:
            # Get devices
            devices_response = await self.hass.async_add_executor_job(
                self.api.get_devices
            )
            
            if "Data" not in devices_response or "Devices" not in devices_response["Data"]:
                raise UpdateFailed("Failed to fetch devices from API")
            
            devices = devices_response["Data"]["Devices"]
            
            if not devices:
                self.logger.warning("No devices found in API response")
            
            # Get scenarios
            scenarios_response = await self.hass.async_add_executor_job(
                self.api.get_scenarios
            )
            
            scenarios = []
            if "Data" in scenarios_response and "Scenarios" in scenarios_response["Data"]:
                scenarios = scenarios_response["Data"]["Scenarios"]
            
            # Check device data timestamps to warn about stale data
            for device in devices:
                device_id = device["Id"]
                device_type = device["Class"]
                device_name = device.get("Title", f"{device_type}-{device_id}")
                
                # Get device data to check timestamp
                try:
                    device_data = await self.hass.async_add_executor_job(
                        self.api.get_device_data, device_id, device_type
                    )
                    
                    # Check for LogDateTimeUtc timestamp
                    if "Data" in device_data and "LogDateTimeUtc" in device_data["Data"]:
                        timestamp = device_data["Data"]["LogDateTimeUtc"]
                        
                        # Generate a unique key for this device
                        device_key = f"{device_type}_{device_id}"
                        
                        # Check if we have seen this device before
                        if device_key in self._update_timestamps:
                            last_timestamp = self._update_timestamps[device_key]
                            
                            # If timestamp has changed, log it
                            if last_timestamp != timestamp:
                                self.logger.info(
                                    f"Device {device_name} data updated: {last_timestamp} -> {timestamp}"
                                )
                                self._update_timestamps[device_key] = timestamp
                                
                                # Reset the warning flag since we have fresh data
                                if device_key in self._data_age_warnings:
                                    del self._data_age_warnings[device_key]
                            else:
                                # If the data hasn't changed, check how many updates we've gone without changes
                                if device_key not in self._data_age_warnings:
                                    self._data_age_warnings[device_key] = 1
                                else:
                                    self._data_age_warnings[device_key] += 1
                                
                                # Warn if we've gone 3 or more updates without changes
                                if self._data_age_warnings[device_key] >= 3:
                                    self.logger.warning(
                                        f"Device {device_name} data hasn't updated in {self._data_age_warnings[device_key]} checks. "
                                        f"Last update was at {timestamp}. "
                                        f"This is normal for PowerMeter devices which update ~every 30 minutes."
                                    )
                                    # Only warn every 3rd check to avoid log spam
                                    self._data_age_warnings[device_key] = 0
                        else:
                            # First time seeing this device
                            self._update_timestamps[device_key] = timestamp
                            self.logger.info(f"Device {device_name} initial data timestamp: {timestamp}")
                    
                except LoggameraAPIError as err:
                    self.logger.error(f"Failed to get data for device {device_name}: {err}")
            
            # Return all data
            return {
                "devices": devices,
                "scenarios": scenarios,
            }
            
        except LoggameraAPIError as err:
            raise UpdateFailed(f"Error communicating with API: {err}")
        except Exception as err:
            raise UpdateFailed(f"Unexpected error: {err}")