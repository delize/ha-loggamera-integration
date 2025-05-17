"""Support for Loggamera sensors."""
import logging
from typing import Any, Dict, List, Optional

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfVolume,
    PERCENTAGE,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
)

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Loggamera sensors based on a config entry."""
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
                
                # Create entities for each value
                for value in values:
                    # Skip alarm values for sensors (they'll be used for binary sensors)
                    if value["Name"] in ["alarmActive", "alarmInClearText"]:
                        continue
                        
                    entities.append(
                        LoggameraSensor(
                            coordinator,
                            device_id,
                            device_class,
                            device_title,
                            value["Name"],
                            value["ClearTextName"],
                            value["ValueType"],
                            value["UnitType"],
                            value["UnitPresentation"],
                        )
                    )
    
    async_add_entities(entities)

class LoggameraSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Loggamera sensor."""

    def __init__(
        self,
        coordinator,
        device_id,
        device_class,
        device_title,
        value_name,
        value_clear_name,
        value_type,
        unit_type,
        unit_presentation,
    ):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._device_class = device_class
        self._device_title = device_title
        self._value_name = value_name
        self._value_clear_name = value_clear_name
        self._value_type = value_type
        self._unit_type = unit_type
        self._unit_presentation = unit_presentation
        
        # Set entity properties
        self._attr_name = f"{device_title} {value_clear_name}"
        self._attr_unique_id = f"loggamera_{device_id}_{value_name}"
        
        # Set appropriate icon
        self._set_icon()
        
        # Set device class and state class
        self._set_device_class()
        self._set_state_class()
        
        # Set unit of measurement
        self._set_unit_of_measurement()

    def _set_icon(self):
        """Set the icon based on the value type."""
        if self._value_name == "Temperature":
            self._attr_icon = "mdi:thermometer"
        elif "Temperature" in self._value_name:
            self._attr_icon = "mdi:thermometer"
        elif self._value_name == "Humidity":
            self._attr_icon = "mdi:water-percent"
        elif "Consumed" in self._value_name and "kWh" in self._value_name:
            self._attr_icon = "mdi:flash"
        elif "Power" in self._value_name:
            self._attr_icon = "mdi:lightning-bolt"
        elif "Water" in self._value_name or "M3" in self._value_name:
            self._attr_icon = "mdi:water"
        else:
            self._attr_icon = "mdi:gauge"

    def _set_device_class(self):
        """Set the sensor device class based on the value type."""
        if self._unit_type == "DegreesCelsius":
            self._attr_device_class = SensorDeviceClass.TEMPERATURE
        elif self._unit_type == "KwH":
            self._attr_device_class = SensorDeviceClass.ENERGY
        elif self._unit_type == "KW":
            self._attr_device_class = SensorDeviceClass.POWER
        elif self._unit_type == "CubicMeters":
            self._attr_device_class = SensorDeviceClass.WATER
        else:
            self._attr_device_class = None

    def _set_state_class(self):
        """Set the state class based on the value type."""
        if "Total" in self._value_name:
            self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        elif self._device_class in [
            SensorDeviceClass.TEMPERATURE,
            SensorDeviceClass.POWER,
        ]:
            self._attr_state_class = SensorStateClass.MEASUREMENT
        else:
            self._attr_state_class = None

    def _set_unit_of_measurement(self):
        """Set the unit of measurement based on the unit type."""
        if self._unit_type == "DegreesCelsius":
            self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        elif self._unit_type == "KwH":
            self._attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
        elif self._unit_type == "KW":
            self._attr_native_unit_of_measurement = UnitOfPower.KILO_WATT
        elif self._unit_type == "CubicMeters":
            self._attr_native_unit_of_measurement = UnitOfVolume.CUBIC_METERS
        else:
            self._attr_native_unit_of_measurement = self._unit_presentation

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
    def native_value(self):
        """Return the state of the sensor."""
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
                    # Convert value based on type
                    if self._value_type == "DECIMAL" or self._device_class in [
                        SensorDeviceClass.TEMPERATURE,
                        SensorDeviceClass.ENERGY,
                        SensorDeviceClass.POWER,
                        SensorDeviceClass.WATER,
                    ]:
                        try:
                            return float(value["Value"])
                        except (ValueError, TypeError):
                            return None
                    else:
                        return value["Value"]
                        
        return None