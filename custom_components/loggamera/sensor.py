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
    "alarmActive": {"device_class": None, "unit": None, "state_class": None, "name": "Larm aktivt"},
    "alarmInClearText": {"device_class": None, "unit": None, "state_class": None, "name": "Larmtext"},
    
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
                    
                # Skip empty values
                if value.get("Value", "") == "":
                    continue
                
                # Generate a unique ID for this sensor
                unique_id = f"loggamera_{device_id}_{value.get('Name')}"
                
                # Skip if we've already processed this unique ID
                if unique_id in processed_unique_ids:
                    continue
                processed_unique_ids.add(unique_id)
                
                # Check if this is a numeric value
                try:
                    # Try to convert to float for numeric check
                    float(value.get("Value", "0"))
                    is_numeric = True
                except (ValueError, TypeError):
                    is_numeric = False
                
                # For PowerMeter endpoints, include all values including non-numeric
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
        
        # Get sensor name and type
        self.sensor_name = value_data.get("Name", "")
        self.sensor_clear_name = value_data.get("ClearTextName", self.sensor_name)
        
        if not self.sensor_clear_name:
            self.sensor_clear_name = self.sensor_name
            
        # Construct unique ID
        self._attr_unique_id = f"loggamera_{device_id}_{self.sensor_name}"
        
        # Device name will be the parent device
        self._attr_name = f"{device_name} {self.sensor_clear_name}"
        
        # Determine native value and unit
        self._native_value = self._parse_value(value_data.get("Value"))
        
        # Set device class, unit, and state class based on sensor type
        self._set_sensor_attributes()
        
        # Device info
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, str(device_id))},
            name=device_name,
            manufacturer="Loggamera",
            model=device_type,
        )
        
        _LOGGER.debug(
            f"Created sensor: {self.name} with value: {self._native_value}, "
            f"device_class: {self._attr_device_class}, unit: {self._attr_native_unit_of_measurement}, "
            f"state_class: {self._attr_state_class}"
        )

    def _parse_value(self, value):
        """Parse value to the correct type with proper sanitization."""
        if value is None:
            return None
            
        # Handle string values
        if isinstance(value, str):
            # Remove any leading/trailing whitespace
            value = value.strip()
            
            # Check for empty strings
            if not value:
                return None
                
            # Try to convert to float for numeric values
            try:
                # Convert to float, handling comma as decimal separator (European format)
                value = value.replace(',', '.')
                return float(value)
            except (ValueError, TypeError):
                # Not a number, return as is (but sanitized)
                # Limit string length for safety
                return value[:255]
        
        # If it's already a number, return it
        if isinstance(value, (int, float)):
            return float(value)
            
        # For any other type, convert to string and sanitize
        return str(value)[:255]

    def _set_sensor_attributes(self):
        """Set device class, unit, and state class based on sensor type."""
        # Check if we have a direct mapping for this sensor
        if self.sensor_name in SENSOR_MAP:
            sensor_info = SENSOR_MAP[self.sensor_name]
            self._attr_device_class = sensor_info.get("device_class")
            self._attr_native_unit_of_measurement = sensor_info.get("unit")
            self._attr_state_class = sensor_info.get("state_class")
            
            # Override name if provided in mapping
            if "name" in sensor_info:
                self._attr_name = f"{self.device_name} {sensor_info['name']}"
        else:
            # Try to determine from the unit type
            unit_type = self.value_data.get("UnitType", "").lower()
            unit_presentation = self.value_data.get("UnitPresentation", "")
            
            if unit_type == "kwh":
                self._attr_device_class = SensorDeviceClass.ENERGY
                self._attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
                self._attr_state_class = SensorStateClass.TOTAL_INCREASING
            elif unit_type == "kw":
                self._attr_device_class = SensorDeviceClass.POWER
                self._attr_native_unit_of_measurement = UnitOfPower.KILO_WATT
                self._attr_state_class = SensorStateClass.MEASUREMENT
            elif unit_type == "watt":
                self._attr_device_class = SensorDeviceClass.POWER
                self._attr_native_unit_of_measurement = UnitOfPower.WATT
                self._attr_state_class = SensorStateClass.MEASUREMENT
            elif unit_type == "ampere":
                self._attr_device_class = SensorDeviceClass.CURRENT
                self._attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE
                self._attr_state_class = SensorStateClass.MEASUREMENT
            elif unit_type == "volt":
                self._attr_device_class = SensorDeviceClass.VOLTAGE
                self._attr_native_unit_of_measurement = UnitOfElectricPotential.VOLT
                self._attr_state_class = SensorStateClass.MEASUREMENT
            else:
                # Default to measurement for unknown types
                self._attr_device_class = None
                self._attr_native_unit_of_measurement = unit_presentation
                self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        """Return the state of the sensor."""
        try:
            # Get latest data for this device
            device_data = self.coordinator.data.get("device_data", {}).get(str(self.device_id))
            
            if not device_data or "Data" not in device_data or not device_data["Data"]:
                return self._native_value
                
            # Find the matching value in the latest data
            if "Values" in device_data["Data"]:
                for value in device_data["Data"]["Values"]:
                    if value.get("Name") == self.sensor_name:
                        return self._parse_value(value.get("Value"))
            
            # If we got here, the value wasn't found in the latest data
            return self._native_value
            
        except Exception as err:
            _LOGGER.error(f"Error getting native value for {self.name}: {err}")
            return self._native_value