"""Support for Loggamera binary sensors."""
import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Loggamera binary sensors based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    # Wait for coordinator to do its first update
    await coordinator.async_config_entry_first_refresh()
    
    entities = []
    
    for device_id, device in coordinator.devices.items():
        device_class = device.get("Class")
        device_title = device.get("Title", f"Device {device_id}")
        
        if device_id in coordinator.device_data:
            device_data = coordinator.device_data[device_id]
            
            if device_data.get("Data") and device_data["Data"].get("Values"):
                values = device_data["Data"]["Values"]
                
                # Look for binary values
                for value in values:
                    if value["Name"] == "alarmActive" and value["ValueType"] == "BOOLEAN":
                        entities.append(
                            LoggameraBinarySensor(
                                coordinator,
                                device_id,
                                device_class,
                                device_title,
                                "alarmActive",
                                "Alarm Active",
                                BinarySensorDeviceClass.PROBLEM,
                            )
                        )
                    elif value["Name"] == "reducedModeActive" and value["ValueType"] == "BOOLEAN":
                        entities.append(
                            LoggameraBinarySensor(
                                coordinator,
                                device_id,
                                device_class,
                                device_title,
                                "reducedModeActive",
                                "Reduced Mode Active",
                                None,
                            )
                        )
                    elif value["Name"] == "filterAlarmIsActive" and value["ValueType"] == "BOOLEAN":
                        entities.append(
                            LoggameraBinarySensor(
                                coordinator,
                                device_id,
                                device_class,
                                device_title,
                                "filterAlarmIsActive",
                                "Filter Alarm Active",
                                BinarySensorDeviceClass.PROBLEM,
                            )
                        )
    
    async_add_entities(entities)

class LoggameraBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of a Loggamera binary sensor."""

    def __init__(
        self,
        coordinator,
        device_id,
        device_class,
        device_title,
        value_name,
        value_clear_name,
        sensor_device_class,
    ):
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._device_class = device_class
        self._device_title = device_title
        self._value_name = value_name
        self._value_clear_name = value_clear_name
        
        # Set entity properties
        self._attr_name = f"{device_title} {value_clear_name}"
        self._attr_unique_id = f"loggamera_{device_id}_{value_name}"
        self._attr_device_class = sensor_device_class
        
        # Set icon
        if sensor_device_class == BinarySensorDeviceClass.PROBLEM:
            self._attr_icon = "mdi:alert"
        elif "reduced" in value_name.lower():
            self._attr_icon = "mdi:power-sleep"
        else:
            self._attr_icon = "mdi:toggle-switch"

    @property
    def device_info(self):
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, str(self._device_id))},
            "name": self._device_title,
            "manufacturer": "Loggamera",
            "model": self._device_class,
        }

    @property
    def available(self):
        """Return if entity is available."""
        if (
            not self.coordinator.data
            or "device_data" not in self.coordinator.data
            or self._device_id not in self.coordinator.data["device_data"]
        ):
            return False
            
        return True

    @property
    def is_on(self):
        """Return true if the binary sensor is on."""
        if not self.available:
            return None
            
        device_data = self.coordinator.data["device_data"][self._device_id]
        
        if (
            device_data
            and device_data.get("Data")
            and device_data["Data"].get("Values")
        ):
            values = device_data["Data"]["Values"]
            for value in values:
                if value["Name"] == self._value_name:
                    # Convert to boolean
                    return value["Value"].lower() == "true"
                    
        return None