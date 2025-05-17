"""The Loggamera integration."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import LoggameraAPI, LoggameraAPIError
from .const import DOMAIN, CONF_API_KEY, DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Loggamera from a config entry."""
    api = LoggameraAPI(entry.data[CONF_API_KEY])

    async def async_update_data():
        """Fetch data from API."""
        try:
            # Get devices first
            devices = await hass.async_add_executor_job(api.get_devices)
            
            # Create a data structure with all needed information
            data = {"devices": devices}
            
            # For each device, get relevant data based on its type
            for device in devices:
                device_id = device.get("deviceId")
                if not device_id:
                    continue
                
                # Get capabilities for this device
                capabilities = await hass.async_add_executor_job(
                    api.get_capabilities, device_id
                )
                data[f"capabilities_{device_id}"] = capabilities
                
                # Based on device capabilities, fetch appropriate data
                # This is simplified and should be expanded based on actual API response structure
                if "power" in str(capabilities).lower():
                    data[f"power_{device_id}"] = await hass.async_add_executor_job(
                        api.get_power_meter_data, device_id
                    )
                
                if "water" in str(capabilities).lower():
                    data[f"water_{device_id}"] = await hass.async_add_executor_job(
                        api.get_water_meter_data, device_id
                    )
                
                if "temperature" in str(capabilities).lower() or "humidity" in str(capabilities).lower():
                    data[f"room_{device_id}"] = await hass.async_add_executor_job(
                        api.get_room_sensor_data, device_id
                    )
                
            return data
        except LoggameraAPIError as err:
            raise UpdateFailed(f"Error communicating with API: {err}")

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=DOMAIN,
        update_method=async_update_data,
        update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
    )

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "api": api,
    }

    # Register services
    async def execute_scenario(call: ServiceCall) -> None:
        """Handle execute scenario service."""
        scenario_id = call.data.get("scenario_id")
        try:
            await hass.async_add_executor_job(api.execute_scenario, scenario_id)
            _LOGGER.info(f"Successfully executed scenario {scenario_id}")
        except LoggameraAPIError as err:
            _LOGGER.error(f"Failed to execute scenario {scenario_id}: {err}")

    async def set_property(call: ServiceCall) -> None:
        """Handle set property service."""
        device_id = call.data.get("device_id")
        property_name = call.data.get("property_name")
        property_value = call.data.get("property_value")
        try:
            await hass.async_add_executor_job(
                api.set_property, device_id, property_name, property_value
            )
            _LOGGER.info(f"Successfully set property {property_name} to {property_value} for device {device_id}")
        except LoggameraAPIError as err:
            _LOGGER.error(f"Failed to set property {property_name} for device {device_id}: {err}")

    hass.services.async_register(DOMAIN, "execute_scenario", execute_scenario)
    hass.services.async_register(DOMAIN, "set_property", set_property)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok