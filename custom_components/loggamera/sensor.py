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
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
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

# Mapping of sensor name to device class and unit
SENSOR_MAP = {
    # PowerMeter standard values - THESE MUST BE PRESERVED
    "ConsumedTotalInkWh": {"device_class": SensorDeviceClass.ENERGY, "unit": UnitOfEnergy.KILO_WATT_HOUR, "state_class": SensorStateClass.TOTAL_INCREASING, "name": "Total förbrukning"},
    "PowerInkW": {"device_class": SensorDeviceClass.POWER, "unit": UnitOfPower.KILO_WATT, "state_class": SensorStateClass.MEASUREMENT, "name": "Effekt"},
    "alarmActive": {"device_class": None, "unit": None, "state_class": None, "name": "Larm aktivt", "icon": "mdi:alert-circle"},
    "alarmInClearText": {"device_class": None, "unit": None, "state_class": None, "name": "Larmtext", "icon": "mdi:alert-box"},
    
    # RawData specific values - these are the most common ones
    "544352": {"device_class": SensorDeviceClass.ENERGY, "unit": UnitOfEnergy.KILO_WATT_HOUR, "state_class": SensorStateClass.TOTAL_INCREASING, "name": "Energy Imported"},  # Energy imported
    "544353": {"device_class": SensorDeviceClass.ENERGY, "unit": UnitOfEnergy.KILO_WATT_HOUR, "state_class": SensorStateClass.MEASUREMENT, "name": "Energy Imported Interval"},  # Energy imported interval
    "544399": {"device_class": SensorDeviceClass.POWER, "unit": UnitOfPower.WATT, "state_class": SensorStateClass.MEASUREMENT, "name": "Power"},  # Power
    "544463": {"device_class": SensorDeviceClass.ENERGY, "unit": UnitOfEnergy.KILO_WATT_HOUR, "state_class": SensorStateClass.TOTAL_INCREASING, "name": "Energy Phase 1"},  # Energy (Phase 1)
    "544464": {"device_class": SensorDeviceClass.ENERGY, "unit": UnitOfEnergy.KILO_WATT_HOUR, "state_class": SensorStateClass.TOTAL_INCREASING, "name": "Energy Phase 2"},  # Energy (Phase 2)
    "544465": {"device_class": SensorDeviceClass.ENERGY, "unit": UnitOfEnergy.KILO_WATT_HOUR, "state_class": SensorStateClass.TOTAL_INCREASING, "name": "Energy Phase 3"},  # Energy (Phase 3)
    "544391": {"device_class": SensorDeviceClass.CURRENT, "unit": UnitOfElectricCurrent.AMPERE, "state_class": SensorStateClass.MEASUREMENT, "name": "Current Phase 1"},  # Current (Phase 1)
    "544393": {"device_class": SensorDeviceClass.CURRENT, "unit": UnitOfElectricCurrent.AMPERE, "state_class": SensorStateClass.MEASUREMENT, "name": "Current Phase 2"},  # Current (Phase 2)
    "544394": {"device_class": SensorDeviceClass.CURRENT, "unit": UnitOfElectricCurrent.AMPERE, "state_class": SensorStateClass.MEASUREMENT, "name": "Current Phase 3"},  # Current (Phase 3)
    "544395": {"device_class": SensorDeviceClass.VOLTAGE, "unit": UnitOfElectricPotential.VOLT, "state_class": SensorStateClass.MEASUREMENT, "name": "Voltage Phase 1"},  # Voltage (Phase 1)
    "544396": {"device_class": SensorDeviceClass.VOLTAGE, "unit": UnitOfElectricPotential.VOLT, "state_class": SensorStateClass.MEASUREMENT, "name": "Voltage Phase 2"},  # Voltage (Phase 2)
    "544397": {"device_class": SensorDeviceClass.VOLTAGE, "unit": UnitOfElectricPotential.VOLT, "state_class": SensorStateClass.MEASUREMENT, "name": "Voltage Phase 3"},  # Voltage (Phase 3)
    "549990": {"device_class": SensorDeviceClass.ENERGY, "unit": UnitOfEnergy.KILO_WATT_HOUR, "state_class": SensorStateClass.TOTAL_INCREASING, "name": "Energy Exported"},  # Exported energy
    "550224": {"device_class": SensorDeviceClass.ENERGY, "unit": UnitOfEnergy.KILO_WATT_HOUR, "state_class": SensorStateClass.MEASUREMENT, "name": "Energy Exported Interval"},  # Exported energy interval
    "550205": {"device_class": SensorDeviceClass.POWER, "unit": UnitOfPower.WATT, "state_class": SensorStateClass.MEASUREMENT, "name": "Power Phase 1"},  # Power phase 1
    "550206": {"device_class": SensorDeviceClass.POWER, "unit": UnitOfPower.WATT, "state_class": SensorStateClass.MEASUREMENT, "name": "Power Phase 2"},  # Power phase 2
    "550207": {"device_class": SensorDeviceClass.POWER, "unit": UnitOfPower.WATT, "state_class": SensorStateClass.MEASUREMENT, "name": "Power Phase 3"},  # Power phase 3
}

# Temperature sensor mappings
TEMP_MAPPINGS = {
    "TemperatureInC": {"device_class": SensorDeviceClass.TEMPERATURE, "unit": UnitOfTemperature.CELSIUS, "state_class": SensorStateClass.MEASUREMENT},
    "HumidityInRH": {"device_class": SensorDeviceClass.HUMIDITY, "unit": PERCENTAGE, "state_class": SensorStateClass.MEASUREMENT},
}

# Water sensor mappings
WATER_MAPPINGS = {
    "ConsumedTotalInm3": {"device_class": SensorDeviceClass.WATER, "unit": UnitOfVolume.CUBIC_METERS, "state_class": SensorStateClass.TOTAL_INCREASING},
}

# Combine all mappings
SENSOR_MAP.update(TEMP_MAPPINGS)
SENSOR_MAP.update(WATER_MAPPINGS)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    """Set up Loggamera sensors based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    api = hass.data[DOMAIN][entry.entry_id]["api"]
    
    entities = []
    processed_unique_ids = set()  # Track which sensors we've already created
    
    if not coordinator.data or "devices" not in coordinator.data:
        _LOGGER.error("No devices data in coordinator")
        return
    
    for device in coordinator.data.get("devices", []):
        device_id = device["Id"]
        device_type = device["Class"]
        device_name = device.get("Title", f"{device_type} {device_id}")
        
        _LOGGER.debug(f"Setting up sensors for device: {device_name} (ID: {device_id}, Type: {device_type})")
        
        # Get device data from coordinator
        device_data = coordinator.data.get("device_data", {}).get(str(device_id))
        if not device_data:
            # Try with integer key as fallback
            device_data = coordinator.data.get("device_data", {}).get(device_id)
            
        if not device_data:
            _LOGGER.warning(f"No device data found for {device_name}")
            continue
        
        if "Data" not in device_data or device_data["Data"] is None:
            _LOGGER.warning(f"No 'Data' in device data for {device_name}")
            continue
            
        # Log data sources used
        data_sources = []
        if device_data.get("_raw_data_used"):
            data_sources.append("RawData")
        if device_data.get("_power_meter_used"):
            data_sources.append("PowerMeter")
        if device_data.get("_endpoint_used"):
            data_sources.append(device_data["_endpoint_used"])
        if device_data.get("_generic_device_used"):
            data_sources.append("GenericDevice")
            
        if data_sources:
            _LOGGER.debug(f"Device {device_name} data sources: {', '.join(data_sources)}")
        
        if "Values" in device_data["Data"]:
            values = device_data["Data"]["Values"]
            if not values:
                _LOGGER.warning(f"Device {device_name} has no sensor values")
                continue
            
            # Create sensor entities for each value
            for value in values:
                # Skip empty or unlabeled values
                if not value.get("ClearTextName") and not value.get("Name"):
                    continue
                    
                # Get value name and type
                value_name = value.get("Name", "")
                value_type = value.get("ValueType", "DECIMAL")
                is_boolean = value_type == "BOOLEAN"
                is_string = value_type == "STRING"
                
                # For non-numeric values, check if we should include them
                if not is_boolean and not is_string:
                    # Skip empty values
                    if value.get("Value", "") == "":
                        continue
                
                # Generate a unique ID for this sensor
                unique_id = f"loggamera_{device_id}_{value_name}"
                
                # Skip if we've already processed this unique ID
                if unique_id in processed_unique_ids:
                    continue
                processed_unique_ids.add(unique_id)
                
                # For PowerMeter devices, include all values including non-numeric
                if device_type == "PowerMeter":
                    # Include all PowerMeter values
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
                    # For other device types, only include numeric values
                    try:
                        # Try to convert to float for numeric check
                        float(value.get("Value", "0"))
                        is_numeric = True
                    except (ValueError, TypeError):
                        is_numeric = False
                    
                    if is_numeric:
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
        self.device_name = device_name
        self.value_data = value_data
        self.hass = hass
        self._value_name = value_data.get("Name", "unknown")
        self._value_type = value_data.get("ValueType", "DECIMAL")
        self._is_boolean = self._value_type == "BOOLEAN"
        self._is_string = self._value_type == "STRING"
        
        # Get display name from mapping if available
        self._value_display_name = value_data.get("ClearTextName", self._value_name)
        if self._value_name in SENSOR_MAP:
            map_name = SENSOR_MAP[self._value_name].get("name")
            if map_name:
                self._value_display_name = map_name
        
        # Set unique ID and name
        self._attr_unique_id = f"loggamera_{device_id}_{self._value_name}"
        self._attr_name = f"{device_name} {self._value_display_name}"
        
        # Get icon from mapping if available
        if self._value_name in SENSOR_MAP and "icon" in SENSOR_MAP[self._value_name]:
            self._attr_icon = SENSOR_MAP[self._value_name]["icon"]
            
        # Set special icons for alarm states
        if self._value_name == "alarmActive" and self._is_boolean:
            current_value = value_data.get("Value", "false")
            is_active = current_value.lower() == "true" if isinstance(current_value, str) else bool(current_value)
            self._attr_icon = "mdi:alert-circle" if is_active else "mdi:alert-circle-outline"
    
    @property
    def native_value(self):
        """Return the state of the sensor."""
        if not self.coordinator.data or "device_data" not in self.coordinator.data:
            return None
        
        # Try to get device data using device_id
        device_data = self.coordinator.data.get("device_data", {}).get(self.device_id)
        if not device_data:
            # Try with string device_id
            device_data = self.coordinator.data.get("device_data", {}).get(str(self.device_id))
        
        if not device_data or "Data" not in device_data or "Values" not in device_data["Data"]:
            return None
        
        # Find our sensor value in device data
        for value in device_data["Data"]["Values"]:
            if value.get("Name") == self._value_name:
                raw_value = value.get("Value", "")
                
                # Update icon if this is an alarm sensor
                if self._value_name == "alarmActive" and self._is_boolean:
                    is_active = raw_value.lower() == "true" if isinstance(raw_value, str) else bool(raw_value)
                    self._attr_icon = "mdi:alert-circle" if is_active else "mdi:alert-circle-outline"
                
                # Parse the value based on its type
                return self._parse_value(raw_value)
        
        return None