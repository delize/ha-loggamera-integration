"""Sensor platform for Loggamera integration."""
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.const import (
    UnitOfTemperature,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfVolume,
    PERCENTAGE,
)

from .const import (
    DOMAIN,
    SENSOR_ENERGY,
    SENSOR_POWER,
    SENSOR_TEMPERATURE,
    SENSOR_HUMIDITY,
    SENSOR_WATER,
    SENSOR_VALUE,
)

_LOGGER = logging.getLogger(__name__)

# Mapping of value names to state classes
STATE_CLASS_MAP = {
    "ConsumedTotalInkWh": SensorStateClass.TOTAL_INCREASING,
    "ExportedTotalInkWh": SensorStateClass.TOTAL_INCREASING,
    "PowerInkW": SensorStateClass.MEASUREMENT,
    "TemperatureInC": SensorStateClass.MEASUREMENT,
    "HumidityInRH": SensorStateClass.MEASUREMENT,
    "ConsumedTotalInm3": SensorStateClass.TOTAL_INCREASING
}

# Mapping of unit types to HA units
UNIT_MAP = {
    "°C": UnitOfTemperature.CELSIUS,
    "kWh": UnitOfEnergy.KILO_WATT_HOUR,
    "kW": UnitOfPower.KILO_WATT,
    "m³": UnitOfVolume.CUBIC_METERS,
    "%": PERCENTAGE
}

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    """Set up Loggamera sensors based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    api = hass.data[DOMAIN][entry.entry_id]["api"]
    
    # Ensure we have the latest data
    await coordinator.async_refresh()
    
    entities = []
    
    if not coordinator.data or "devices" not in coordinator.data:
        _LOGGER.warning("No devices data in coordinator")
        return
    
    for device in coordinator.data.get("devices", []):
        device_id = device["Id"]
        device_type = device["Class"]
        device_name = device.get("Title", f"{device_type} {device_id}")
        
        _LOGGER.debug(f"Setting up sensors for device: {device_name} (ID: {device_id}, Type: {device_type})")
        
        # Get device data from coordinator
        device_data = coordinator.data.get("device_data", {}).get(str(device_id))
        
        if not device_data:
            _LOGGER.warning(f"No device data for {device_name}")
            continue
        
        if "Data" not in device_data or device_data["Data"] is None:
            _LOGGER.warning(f"No 'Data' in device data for {device_name}")
            continue
        
        # Standard handling for devices with Values
        if "Values" in device_data["Data"]:
            values = device_data["Data"]["Values"]
            if not values:
                _LOGGER.warning(f"No values data for device {device_name}")
                continue
            
            for value in values:
                # Skip boolean and string values
                if value.get("ValueType") in ["BOOLEAN", "STRING"]:
                    continue
                
                entity = LoggameraSensor(
                    coordinator=coordinator,
                    api=api,
                    device_id=device_id,
                    device_type=device_type,
                    device_name=device_name,
                    value_data=value,
                    hass=hass,
                )
                entities.append(entity)
                _LOGGER.debug(f"Created sensor: {entity.name} with value: {value.get('Value')}")
        else:
            _LOGGER.warning(f"No 'Values' data for device {device_name}")
    
    if entities:
        async_add_entities(entities)
        _LOGGER.info(f"Added {len(entities)} Loggamera sensor entities")
    else:
        _LOGGER.warning("No Loggamera sensors added")


class LoggameraSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Loggamera sensor."""

    def __init__(self, coordinator, api, device_id, device_type, device_name, value_data, hass):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.api = api
        self.device_id = device_id
        self.device_type = device_type
        self._device_name = device_name
        self._hass = hass
        self._value_data = value_data
        
        # Value data
        self._value_name = value_data.get("Name", "Unknown")
        self._clear_name = value_data.get("ClearTextName", self._value_name)
        self._value_type = value_data.get("ValueType", "Unknown")
        self._unit_type = value_data.get("UnitType", "")
        self._unit = value_data.get("UnitPresentation", "")
        
        # Handle value conversion for numeric types
        if self._value_type in ["DECIMAL", "NUMBER"]:
            try:
                self._last_value = float(value_data.get("Value", 0))
            except (ValueError, TypeError):
                self._last_value = value_data.get("Value")
        else:
            self._last_value = value_data.get("Value")
        
        # Entity attributes
        self._attr_unique_id = f"loggamera_{device_id}_{self._value_name}"
        self._attr_name = f"{device_name} {self._clear_name}"
        
        # Set device class based on value name
        self._attr_device_class = self._get_device_class()
        
        # Set state class based on value name
        self._attr_state_class = STATE_CLASS_MAP.get(self._value_name)
        
        # Set unit of measurement
        self._attr_native_unit_of_measurement = UNIT_MAP.get(self._unit, self._unit)
        
        # Device info
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, str(device_id))},
            name=device_name,
            manufacturer="Loggamera",
            model=device_type,
        )
        
        _LOGGER.debug(f"Created sensor: {self.name} ({self._value_name}), "
                      f"device_class: {self._attr_device_class}, "
                      f"state_class: {self._attr_state_class}, "
                      f"unit: {self._attr_native_unit_of_measurement}, "
                      f"initial value: {self._last_value}")

    def _get_device_class(self):
        """Get the correct device class based on the value name and type."""
        value_name = self._value_name.lower()
        
        if "temperature" in value_name or self._value_name == "TemperatureInC":
            return SensorDeviceClass.TEMPERATURE
            
        elif "humidity" in value_name or self._value_name == "HumidityInRH":
            return SensorDeviceClass.HUMIDITY
            
        elif "consumed" in value_name and "kwh" in value_name or self._value_name == "ConsumedTotalInkWh":
            return SensorDeviceClass.ENERGY
            
        elif "exported" in value_name and "kwh" in value_name or self._value_name == "ExportedTotalInkWh":
            return SensorDeviceClass.ENERGY
            
        elif "power" in value_name or self._value_name == "PowerInkW":
            return SensorDeviceClass.POWER
            
        elif "water" in value_name or "m3" in value_name or self._value_name == "ConsumedTotalInm3":
            return SensorDeviceClass.WATER
            
        return None

    @property
    def native_value(self):
        """Return the state of the sensor."""
        try:
            # Find the device data in coordinator
            device_data = self.coordinator.data.get("device_data", {}).get(str(self.device_id))
            if not device_data or "Data" not in device_data or device_data["Data"] is None:
                return self._last_value
            
            # Check for Values
            if "Values" in device_data["Data"]:
                for value in device_data["Data"]["Values"]:
                    if value.get("Name") == self._value_name:
                        # Convert string values to proper types for decimal/number values
                        if value.get("ValueType") == "DECIMAL" or value.get("ValueType") == "NUMBER":
                            try:
                                self._last_value = float(value.get("Value"))
                            except (ValueError, TypeError):
                                # If conversion fails, keep as is
                                self._last_value = value.get("Value")
                        else:
                            self._last_value = value.get("Value")
                        return self._last_value
            
            return self._last_value
        except Exception as err:
            _LOGGER.error(f"Error getting value for {self.name}: {err}")
            return self._last_value