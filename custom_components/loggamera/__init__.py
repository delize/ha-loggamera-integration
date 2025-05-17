"""The Loggamera integration."""
import asyncio
import logging
from datetime import timedelta

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
import homeassistant.helpers.config_validation as cv

from .api import LoggameraAPI, LoggameraAPIError
from .const import (
    DOMAIN,
    CONF_API_KEY,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

# List of platforms to support
PLATFORMS = ["sensor", "binary_sensor", "switch"]

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Loggamera component."""
    hass.data.setdefault(DOMAIN, {})
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Loggamera from a config entry."""
    api_key = entry.data[CONF_API_KEY]
    scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

    # Create API client
    api = LoggameraAPI(api_key)

    # Set up coordinator for data updates
    coordinator = LoggameraDataUpdateCoordinator(
        hass, api=api, scan_interval=scan_interval
    )

    # Fetch initial data
    await coordinator.async_refresh()

    # Store coordinator in hass data
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Register services
    register_services(hass)

    # Forward setup to each platform
    for platform in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, platform)
        )

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    # Unload platforms
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
            ]
        )
    )

    # Remove coordinator
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok

def register_services(hass):
    """Register Loggamera services."""
    
    async def handle_execute_scenario(call: ServiceCall) -> None:
        """Handle the execute_scenario service call."""
        scenario_id = call.data.get("scenario_id")
        duration_minutes = call.data.get("duration_minutes")
        entry_id = call.data.get("entry_id")
        
        # If no specific entry_id is provided, use the first one
        if not entry_id and hass.data[DOMAIN]:
            entry_id = list(hass.data[DOMAIN].keys())[0]
            
        if not entry_id or entry_id not in hass.data[DOMAIN]:
            _LOGGER.error("No valid entry_id found for Loggamera integration")
            return
            
        coordinator = hass.data[DOMAIN][entry_id]
        
        try:
            await hass.async_add_executor_job(
                coordinator.api.execute_scenario,
                scenario_id,
                duration_minutes,
            )
        except LoggameraAPIError as error:
            _LOGGER.error(f"Failed to execute scenario: {error}")
    
    hass.services.async_register(
        DOMAIN, "execute_scenario", handle_execute_scenario
    )

class LoggameraDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(self, hass, api, scan_interval):
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )
        self.api = api
        self.devices = {}
        self.device_data = {}
        self.organizations = {}

    async def _async_update_data(self):
        """Update data."""
        try:
            # Get organizations
            organizations_response = await self.hass.async_add_executor_job(
                self.api.get_organizations
            )
            if organizations_response.get("Data") and organizations_response["Data"].get("Organizations"):
                self.organizations = {
                    org["Id"]: org for org in organizations_response["Data"]["Organizations"]
                }
                
            # Get devices
            devices_response = await self.hass.async_add_executor_job(
                self.api.get_devices
            )
            if devices_response.get("Data") and devices_response["Data"].get("Devices"):
                self.devices = {
                    device["Id"]: device for device in devices_response["Data"]["Devices"]
                }
                
            # Update data for each device
            for device_id, device in self.devices.items():
                device_class = device.get("Class")
                device_data = None
                
                if device_class == "PowerMeter":
                    device_data = await self.hass.async_add_executor_job(
                        self.api.get_power_meter_data, device_id
                    )
                elif device_class == "WaterMeter":
                    device_data = await self.hass.async_add_executor_job(
                        self.api.get_water_meter_data, device_id
                    )
                elif device_class == "RoomSensor":
                    device_data = await self.hass.async_add_executor_job(
                        self.api.get_room_sensor_data, device_id
                    )
                elif device_class == "GenericDevice":
                    device_data = await self.hass.async_add_executor_job(
                        self.api.get_generic_device_data, device_id
                    )
                elif device_class == "CoolingUnit":
                    device_data = await self.hass.async_add_executor_job(
                        self.api.get_cooling_unit_data, device_id
                    )
                elif device_class == "HeatPump":
                    device_data = await self.hass.async_add_executor_job(
                        self.api.get_heat_pump_data, device_id
                    )
                
                if device_data:
                    self.device_data[device_id] = device_data
                
            return {
                "devices": self.devices,
                "device_data": self.device_data,
                "organizations": self.organizations,
            }
            
        except LoggameraAPIError as error:
            _LOGGER.error(f"Error communicating with Loggamera API: {error}")
            raise UpdateFailed(f"Error communicating with API: {error}")