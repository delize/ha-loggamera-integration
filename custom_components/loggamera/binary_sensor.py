"""Support for Loggamera binary sensors."""
import logging
from typing import Any, Dict, List, Optional, Callable

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .api import LoggameraAPI, LoggameraAPIError
from .const import DOMAIN, ATTR_DEVICE_TYPE

_LOGGER = logging.getLogger(__name__)

ALARM_DEVICE_CLASSES = {
    "PowerMeter": BinarySensorDeviceClass.PROBLEM,
    "RoomSensor": BinarySensorDeviceClass.PROBLEM,
    "WaterMeter": BinarySensorDeviceClass.PROBLEM,
    "CoolingUnit": BinarySensorDeviceClass.PROBLEM,
    "HeatPump": BinarySensorDeviceClass.PROBLEM,
}

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Loggamera binary sensors based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    api = hass.data[DOMAIN][entry.entry_id]["api"]
    
    try:
        # Try to force a refresh to get latest data
        await coordinator.async_refresh()
    except Exception as err:
        _LOGGER.error(f"Error refreshing coordinator: {err}")
        # Continue with available data or none
    
    binary_sensors = []
    
    # Get devices from coordinator data
    if not coordinator.data or "devices" not in coordinator.data:
        _LOGGER.error("No devices found in coordinator data")
        return
    
    devices = coordinator.data.get("devices", [])
    
    for device in devices:
        device_id = device["Id"]
        device_type = device["Class"]
        device_name = device["Title"] or f"{device_type}-{device_id}"
        
        try:
            # Get device-specific data to create binary sensors
            # This will be performed in a background thread
            device_data_response = await hass.async_add_executor_job(
                api.get_device_data, device_id, device_type
            )
            
            if not device_data_response or "Data" not in device_data_response or "Values" not in device_data_response["Data"]:
                _LOGGER.warning(f"Failed to get any data for device {device_name}")
                continue
            
            # Process the available values
            values = device_data_response["Data"]["Values"]
            
            # Look for alarm-related values
            alarm_active = next((v for v in values if v["Name"] == "alarmActive"), None)
            alarm_text = next((v for v in values if v["Name"] == "alarmInClearText"), None)
            
            # Add alarm binary sensor if alarm data is available
            if alarm_active:
                binary_sensors.append(
                    LoggameraAlarmBinarySensor(
                        coordinator,
                        device_id,
                        device_type,
                        device_name,
                        alarm_active,
                        alarm_text,
                    )
                )
        
        except LoggameraAPIError as err:
            _LOGGER.error(f"Failed to get data for device {device_name}: {err}")
            continue
    
    if binary_sensors:
        _LOGGER.info(f"Adding {len(binary_sensors)} Loggamera binary sensors")
        async_add_entities(binary_sensors)


class LoggameraAlarmBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of a Loggamera alarm binary sensor."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        device_id: int,
        device_type: str,
        device_name: str,
        alarm_active_value: Dict[str, Any],
        alarm_text_value: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        
        self._device_id = device_id
        self._device_type = device_type
        self._device_name = device_name
        self._alarm_text = alarm_text_value.get("Value", "") if alarm_text_value else ""
        
        # Generate a unique ID for the sensor
        self._attr_unique_id = f"{DOMAIN}_{device_id}_alarm"
        
        # Set name
        self._attr_name = f"{device_name} Alarm"
        
        # Set state
        self._attr_is_on = alarm_active_value["Value"].lower() in ["true", "1", "yes", "on"]
        
        # Set device class
        self._attr_device_class = ALARM_DEVICE_CLASSES.get(device_type, BinarySensorDeviceClass.PROBLEM)
        
        # Set device info
        self._attr_device_info = {
            "identifiers": {(DOMAIN, str(device_id))},
            "name": device_name,
            "manufacturer": "Loggamera",
            "model": device_type,
        }
        
        # Set extra attributes
        self._attr_extra_state_attributes = {
            ATTR_DEVICE_TYPE: device_type,
            "alarm_text": self._alarm_text,
        }

    async def async_update(self) -> None:
        """Update the binary sensor."""
        await self.coordinator.async_request_refresh()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        # Get API client from hass.data
        api = None
        for entry_id, entry_data in self.hass.data[DOMAIN].items():
            if "api" in entry_data:
                api = entry_data["api"]
                break
        
        if not api:
            return
        
        # Get latest device data
        try:
            device_data = api.get_device_data(self._device_id, self._device_type)
            
            if "Data" in device_data and "Values" in device_data["Data"]:
                values = device_data["Data"]["Values"]
                
                # Find alarm values
                alarm_active = next((v for v in values if v["Name"] == "alarmActive"), None)
                alarm_text = next((v for v in values if v["Name"] == "alarmInClearText"), None)
                
                # Update state if alarm active found
                if alarm_active and "Value" in alarm_active:
                    self._attr_is_on = alarm_active["Value"].lower() in ["true", "1", "yes", "on"]
                
                # Update alarm text if found
                if alarm_text and "Value" in alarm_text:
                    self._alarm_text = alarm_text["Value"]
                    self._attr_extra_state_attributes["alarm_text"] = self._alarm_text
        except LoggameraAPIError as err:
            _LOGGER.error(f"Error updating binary sensor: {err}")
        
        self.async_write_ha_state()