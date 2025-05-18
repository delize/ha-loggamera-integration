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
    import time
    from datetime import timedelta
    
    # Get configuration from config entry
    api_key = entry.data[CONF_API_KEY]
    organization_id = entry.data.get(CONF_ORGANIZATION_ID)
    
    # Get scan interval from config entry options or use default
    scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    
    # Initialize API client
    api = LoggameraAPI(api_key, organization_id)
    
    # Verify connectivity before proceeding
    try:
        # Test the connection to the API - use async_add_executor_job for blocking calls
        org_response = await hass.async_add_executor_job(api.get_organizations)
        
        if "Data" not in org_response or "Organizations" not in org_response["Data"]:
            raise ConfigEntryNotReady("Invalid organization response from API")
            
        # If we don't have an organization ID yet, get it from the response
        if not organization_id and org_response["Data"]["Organizations"]:
            organization_id = org_response["Data"]["Organizations"][0]["Id"]
            api.organization_id = organization_id
            
            # Update the config entry with the organization ID
            new_data = dict(entry.data)
            new_data[CONF_ORGANIZATION_ID] = organization_id
            hass.config_entries.async_update_entry(entry, data=new_data)
            
        # Verify we can access devices
        devices_response = await hass.async_add_executor_job(api.get_devices)
        if "Data" not in devices_response or "Devices" not in devices_response["Data"]:
            raise ConfigEntryNotReady("Invalid device response from API")
            
    except LoggameraAPIError as err:
        _LOGGER.error(f"Failed to connect to Loggamera API: {err}")
        raise ConfigEntryNotReady(f"Failed to connect to Loggamera API: {err}")
        
    # Create update coordinator
    async def _update_data():
        """Fetch data from API."""
        _LOGGER.debug("Starting data update cycle")
        start_time = time.time()
        
        try:
            # Get organizations - use async_add_executor_job for blocking API calls
            org_response = await hass.async_add_executor_job(api.get_organizations)
            if "Data" not in org_response or "Organizations" not in org_response["Data"]:
                raise UpdateFailed("Invalid organization response format")
                
            # Get devices
            devices_response = await hass.async_add_executor_job(api.get_devices)
            if "Data" not in devices_response or "Devices" not in devices_response["Data"]:
                raise UpdateFailed("Invalid device response format")
                
            devices = devices_response["Data"]["Devices"]
            
            # Get scenarios
            try:
                scenarios_response = await hass.async_add_executor_job(api.get_scenarios)
                scenarios = []
                if "Data" in scenarios_response and "Scenarios" in scenarios_response["Data"]:
                    scenarios = scenarios_response["Data"]["Scenarios"]
            except LoggameraAPIError:
                _LOGGER.warning("Failed to get scenarios")
                scenarios = []
                
            # Get data for each device
            device_data = {}
            for device in devices:
                device_id = device["Id"]
                device_type = device["Class"]
                
                try:
                    # Use async_add_executor_job for blocking API calls
                    data = await hass.async_add_executor_job(
                        api.get_device_data, device_id, device_type
                    )
                    if data:
                        device_data[device_id] = data
                except LoggameraAPIError:
                    _LOGGER.warning(f"Failed to get data for device {device_id}")
                    
            result = {
                "organizations": org_response["Data"]["Organizations"],
                "devices": devices,
                "scenarios": scenarios,
                "device_data": device_data,
            }
            
            _LOGGER.debug(f"Finished fetching loggamera data in {time.time() - start_time:.3f} seconds (success: True)")
            return result
            
        except Exception as err:
            _LOGGER.error(f"Error fetching loggamera data: {err}")
            _LOGGER.debug(f"Finished fetching loggamera data in {time.time() - start_time:.3f} seconds (success: False)")
            raise UpdateFailed(f"Error fetching loggamera data: {err}")
            
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=DOMAIN,
        update_method=_update_data,
        update_interval=timedelta(seconds=scan_interval),
    )
    
    # Fetch initial data
    await coordinator.async_refresh()
    
    # Store API and coordinator in hass.data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "api": api,
    }
    
    # Set up all platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # Register update listener for options
    entry.async_on_unload(entry.add_update_listener(async_update_options))
    
    _LOGGER.info(f"Loggamera integration set up with scan interval: {scan_interval} seconds (PowerMeter data typically updates every ~30 minutes)")
    return True

async def async_update_options(hass: HomeAssistant, entry: ConfigEntry):
    """Update options for Loggamera integration."""
    await hass.config_entries.async_reload(entry.entry_id)

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        if not hass.data[DOMAIN]:
            hass.data.pop(DOMAIN)
    return unload_ok