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
    
    # Define the update method
    async def async_update_data():
        """Fetch data from Loggamera API."""
        try:
            # Get devices
            devices_response = await hass.async_add_executor_job(api.get_devices)
            if "Data" not in devices_response or "Devices" not in devices_response["Data"]:
                raise UpdateFailed("Invalid device response format")
            
            devices = devices_response["Data"]["Devices"]
            
            # Get scenarios
            scenarios = []
            try:
                scenarios_response = await hass.async_add_executor_job(api.get_scenarios)
                if "Data" in scenarios_response and "Scenarios" in scenarios_response["Data"]:
                    scenarios = scenarios_response["Data"]["Scenarios"]
            except LoggameraAPIError as err:
                _LOGGER.warning(f"Failed to get scenarios: {err}")
            
            # Get device data
            device_data = {}
            for device in devices:
                device_id = device["Id"]
                device_type = device["Class"]
                
                try:
                    data = await hass.async_add_executor_job(
                        api.get_device_data, device_id, device_type
                    )
                    if data:
                        device_data[device_id] = data
                except LoggameraAPIError as err:
                    _LOGGER.warning(f"Failed to get data for device {device_id}: {err}")
            
            return {
                "devices": devices,
                "scenarios": scenarios,
                "device_data": device_data,
            }
        except Exception as err:
            _LOGGER.error(f"Error fetching data: {err}")
            raise UpdateFailed(f"Error fetching data: {err}")
    
    # Create update coordinator
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=DOMAIN,
        update_method=async_update_data,
        update_interval=timedelta(seconds=scan_interval),
    )
    
    # Fetch initial data
    await coordinator.async_refresh()
    
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
    
    return unload_ok