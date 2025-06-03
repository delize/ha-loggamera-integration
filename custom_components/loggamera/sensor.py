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
                    # Skip empty values (but allow boolean false values)
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
        self.sensor_name = value_data.get("Name", "unknown")
        
        # Initialize sensor attributes
        self._sensor_value = None
        self._sensor_unit = value_data.get("UnitPresentation", "")
        self._unit_type = value_data.get("UnitType", "")
        self._is_boolean = value_data.get("ValueType") == "BOOLEAN"
        self._is_string = value_data.get("ValueType") == "STRING"
        
        # Set entity description
        self._attr_name = f"{device_name} {value_data.get('ClearTextName', value_data.get('Name', 'Unknown'))}"
        self._attr_unique_id = f"loggamera_{device_id}_{self.sensor_name}"
        
        # For device with device ID in string format, ensure we have a consistent format
        try:
            self._attr_unique_id = f"loggamera_{int(device_id)}_{self.sensor_name}"
        except (ValueError, TypeError):
            pass
        
        # Determine device class, state class, and unit of measurement
        self._set_sensor_attributes()
        
        _LOGGER.debug(f"Initialized sensor: {self.name} with value: {value_data.get('Value')}")
        
    def _parse_value(self, value):
        """Parse value to the correct type with proper sanitization."""
        if value is None:
            return None
            
        # Handle string values
        if isinstance(value, str):
            # Remove any leading/trailing whitespace
            value = value.strip()
            
            # Check for empty strings
            if not value and not self._is_boolean:
                return None
                
            # For boolean values, convert to boolean
            if self._is_boolean:
                return value.lower() == "true"
                
            # For string values, return as is (but sanitized)
            if self._is_string:
                # Limit string length for safety
                return value[:255]
                
            # Try to convert to float for numeric values
            try:
                # Convert to float, handling comma as decimal separator (European format)
                value = value.replace(',', '.')
                return float(value)
            except (ValueError, TypeError):
                # Not a number, return as is (but sanitized)
                return value[:255]
        
        # If it's already a boolean, return it
        if isinstance(value, bool) and self._is_boolean:
            return value
            
        # If it's already a number, return it
        if isinstance(value, (int, float)) and not self._is_boolean and not self._is_string:
            return float(value)
            
        # For any other type, convert to string and sanitize
        return str(value)[:255]
        
    def _set_sensor_attributes(self):
        """Set device class, state class, and unit of measurement based on sensor type."""
        # Set icon for boolean alarm sensors
        if self._is_boolean and self.sensor_name == "alarmActive":
            if self.value_data.get("Value", "").lower() == "true":
                self._attr_icon = "mdi:alert-circle"
            else:
                self._attr_icon = "mdi:alert-circle-outline"
        
        # Set icon for string alarm text
        if self._is_string and self.sensor_name == "alarmInClearText":
            self._attr_icon = "mdi:alert-box"
        
        # For boolean and string values, no need for device class or units
        if self._is_boolean or self._is_string:
            self._attr_device_class = None
            self._attr_state_class = None
            self._attr_native_unit_of_measurement = None
            return
        
        # For numeric values, try to determine device class and units
        sensor_info = SENSOR_MAP.get(self.sensor_name, {})
        
        # Set device class if available in mapping
        self._attr_device_class = sensor_info.get("device_class")
        
        # Set state class if available
        self._attr_state_class = sensor_info.get("state_class")
        
        # Set unit of measurement
        if "unit" in sensor_info:
            self._attr_native_unit_of_measurement = sensor_info["unit"]
        else:
            self._attr_native_unit_of_measurement = self._sensor_unit

    @property
    def native_value(self):
        """Return the state of the sensor."""
        # Get the latest data from the coordinator
        if not self.coordinator.data or "device_data" not in self.coordinator.data:
            return None
        
        device_data = self.coordinator.data["device_data"].get(self.device_id)
        if not device_data:
            # Try string version of device_id as fallback
            device_data = self.coordinator.data["device_data"].get(str(self.device_id))
            
        if not device_data or "Data" not in device_data or "Values" not in device_data["Data"]:
            return None
        
        # Find our specific sensor value in the latest data
        sensor_name = self.sensor_name
        for value in device_data["Data"]["Values"]:
            if value.get("Name") == sensor_name:
                raw_value = value.get("Value", "")
                
                # Update icon if this is an alarm sensor
                if self._is_boolean and self.sensor_name == "alarmActive":
                    is_active = raw_value.lower() == "true" if isinstance(raw_value, str) else bool(raw_value)
                    self._attr_icon = "mdi:alert-circle" if is_active else "mdi:alert-circle-outline"
                
                # Use the _parse_value method to handle different value types
                return self._parse_value(raw_value)
                    
        # If we didn't find our sensor, return None
        return None
        
    @property
    def device_info(self):
        """Return device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, str(self.device_id))},
            name=self.device_name,
            manufacturer="Loggamera",
            model=self.device_type,
        )

    @property
    def available(self):
        """Return if entity is available."""
        # Check if coordinator has data
        if not self.coordinator.data or "device_data" not in self.coordinator.data:
            return False
            
        # Check if our device data exists
        device_data = self.coordinator.data["device_data"].get(self.device_id)
        if not device_data:
            # Try string version of device_id as fallback
            device_data = self.coordinator.data["device_data"].get(str(self.device_id))
            if not device_data:
                return False
                
        # Check if we have values
        if "Data" not in device_data or "Values" not in device_data["Data"]:
            return False
            
        # Check if our specific value exists
        sensor_name = self.sensor_name
        for value in device_data["Data"]["Values"]:
            if value.get("Name") == sensor_name:
                return True
                
        return False