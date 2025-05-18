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
from homeassistant.util import dt as dt_util
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

# Map Loggamera sensor names to device classes
DEVICE_CLASS_MAP = {
    "PowerInkW": SensorDeviceClass.POWER,
    "ConsumedTotalInkWh": SensorDeviceClass.ENERGY,
    "ExportedTotalInkWh": SensorDeviceClass.ENERGY,
    "Temperature": SensorDeviceClass.TEMPERATURE,
    "Humidity": SensorDeviceClass.HUMIDITY,
    "WaterVolume": SensorDeviceClass.WATER,
    "WaterLevel": SensorDeviceClass.WATER,
    "CO2": SensorDeviceClass.CO2,
}

# Map Loggamera units to HA units
UNIT_MAP = {
    "kW": UnitOfPower.KILO_WATT,
    "kWh": UnitOfEnergy.KILO_WATT_HOUR,
    "Wh": UnitOfEnergy.WATT_HOUR,
    "°C": UnitOfTemperature.CELSIUS,
    "C": UnitOfTemperature.CELSIUS,
    "%": PERCENTAGE,
    "m³": UnitOfVolume.CUBIC_METERS,
    "liters": UnitOfVolume.LITERS,
    "ppm": "ppm",
}

# Map sensor types to state classes
STATE_CLASS_MAP = {
    "PowerInkW": SensorStateClass.MEASUREMENT,
    "ConsumedTotalInkWh": SensorStateClass.TOTAL_INCREASING,
    "ExportedTotalInkWh": SensorStateClass.TOTAL_INCREASING,
    "Temperature": SensorStateClass.MEASUREMENT,
    "Humidity": SensorStateClass.MEASUREMENT,
    "WaterVolume": SensorStateClass.TOTAL_INCREASING,
}

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    """Set up Loggamera sensors based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    api = hass.data[DOMAIN][entry.entry_id]["api"]
    
    entities = []
    
    # Process devices from coordinator data
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
            _LOGGER.warning(f"No device data found for {device_name}")
            continue
        
        if "Data" not in device_data:
            _LOGGER.warning(f"No 'Data' in device data for {device_name}")
            continue
            
        # Special handling for PowerMeter devices - check for PowerReadings
        if device_type == "PowerMeter" and "PowerReadings" in device_data["Data"]:
            readings = device_data["Data"]["PowerReadings"]
            if readings:
                latest_reading = readings[-1]
                _LOGGER.debug(f"Latest PowerReading for {device_name}: {latest_reading}")
                
                # Create power sensor
                if "PowerInkW" in latest_reading:
                    entities.append(
                        LoggameraSensor(
                            coordinator=coordinator,
                            api=api,
                            device_id=device_id,
                            device_type=device_type,
                            device_name=device_name,
                            value_data={
                                "Name": "PowerInkW",
                                "ClearTextName": "Current Power",
                                "Value": latest_reading["PowerInkW"],
                                "ValueType": "NUMBER",
                                "UnitType": "POWER",
                                "UnitPresentation": "kW"
                            },
                            hass=hass,
                        )
                    )
                
                # Create energy consumption sensor
                if "ConsumedTotalInkWh" in latest_reading:
                    entities.append(
                        LoggameraSensor(
                            coordinator=coordinator,
                            api=api,
                            device_id=device_id,
                            device_type=device_type,
                            device_name=device_name,
                            value_data={
                                "Name": "ConsumedTotalInkWh",
                                "ClearTextName": "Energy Consumption",
                                "Value": latest_reading["ConsumedTotalInkWh"],
                                "ValueType": "NUMBER",
                                "UnitType": "ENERGY",
                                "UnitPresentation": "kWh"
                            },
                            hass=hass,
                        )
                    )
                
                # Create energy export sensor
                if "ExportedTotalInkWh" in latest_reading:
                    entities.append(
                        LoggameraSensor(
                            coordinator=coordinator,
                            api=api,
                            device_id=device_id,
                            device_type=device_type,
                            device_name=device_name,
                            value_data={
                                "Name": "ExportedTotalInkWh",
                                "ClearTextName": "Energy Export",
                                "Value": latest_reading["ExportedTotalInkWh"],
                                "ValueType": "NUMBER",
                                "UnitType": "ENERGY",
                                "UnitPresentation": "kWh"
                            },
                            hass=hass,
                        )
                    )
        
        # Standard handling for devices with Values
        if "Values" in device_data["Data"]:
            values = device_data["Data"]["Values"]
            if not values:
                _LOGGER.warning(f"Device {device_name} has no sensor values in Values array")
                continue
            
            # Create sensor entities for each value that is not a boolean
            for value in values:
                if value.get("ValueType") != "BOOLEAN":
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
        self._last_value = value_data.get("Value", None)
        
        # Entity attributes
        self._attr_unique_id = f"loggamera_{device_id}_{self._value_name}"
        self._attr_name = f"{device_name} {self._clear_name}"
        
        # Set device class based on value name or type
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
                      f"unit: {self._attr_native_unit_of_measurement}")
    
    def _get_device_class(self):
        """Determine sensor device class based on value name and unit."""
        # Try to get device class from the map
        if self._value_name in DEVICE_CLASS_MAP:
            return DEVICE_CLASS_MAP[self._value_name]
        
        # Try to determine from unit type
        if self._unit_type:
            unit_type_lower = self._unit_type.lower()
            if "power" in unit_type_lower:
                return SensorDeviceClass.POWER
            elif "energy" in unit_type_lower:
                return SensorDeviceClass.ENERGY
            elif "temp" in unit_type_lower:
                return SensorDeviceClass.TEMPERATURE
            elif "humid" in unit_type_lower:
                return SensorDeviceClass.HUMIDITY
            elif "water" in unit_type_lower:
                return SensorDeviceClass.WATER
        
        # Try to determine from clear name
        clear_name_lower = self._clear_name.lower()
        
        if "temperatur" in clear_name_lower:
            return SensorDeviceClass.TEMPERATURE
        elif "fukt" in clear_name_lower or "humidity" in clear_name_lower:
            return SensorDeviceClass.HUMIDITY
        elif "effekt" in clear_name_lower or "power" in clear_name_lower:
            return SensorDeviceClass.POWER
        elif "energi" in clear_name_lower or "energy" in clear_name_lower or "förbrukning" in clear_name_lower:
            return SensorDeviceClass.ENERGY
        elif "vatten" in clear_name_lower or "water" in clear_name_lower:
            return SensorDeviceClass.WATER
        
        # Fallback based on unit
        if self._unit in ["°C", "C"]:
            return SensorDeviceClass.TEMPERATURE
        elif self._unit == "%":
            return SensorDeviceClass.HUMIDITY
        elif self._unit == "kW":
            return SensorDeviceClass.POWER
        elif self._unit == "kWh":
            return SensorDeviceClass.ENERGY
        elif self._unit in ["m³", "liters"]:
            return SensorDeviceClass.WATER
        
        # Default, return None (no device class)
        return None
    
    @property
    def native_value(self):
        """Return the state of the sensor."""
        # Special handling for PowerMeter devices with PowerReadings
        if self.device_type == "PowerMeter":
            device_data = self.coordinator.data.get("device_data", {}).get(str(self.device_id))
            
            if device_data and "Data" in device_data:
                # Check for PowerReadings
                if "PowerReadings" in device_data["Data"] and device_data["Data"]["PowerReadings"]:
                    readings = device_data["Data"]["PowerReadings"]
                    latest_reading = readings[-1]
                    
                    # Return the appropriate value based on this sensor's name
                    if self._value_name == "PowerInkW" and "PowerInkW" in latest_reading:
                        self._last_value = latest_reading["PowerInkW"]
                        return self._last_value
                    elif self._value_name == "ConsumedTotalInkWh" and "ConsumedTotalInkWh" in latest_reading:
                        self._last_value = latest_reading["ConsumedTotalInkWh"]
                        return self._last_value
                    elif self._value_name == "ExportedTotalInkWh" and "ExportedTotalInkWh" in latest_reading:
                        self._last_value = latest_reading["ExportedTotalInkWh"]
                        return self._last_value
        
        # Standard handling for Values
        try:
            device_data = self.coordinator.data.get("device_data", {}).get(str(self.device_id))
            if device_data and "Data" in device_data and "Values" in device_data["Data"]:
                for value in device_data["Data"]["Values"]:
                    if value.get("Name") == self._value_name:
                        self._last_value = value.get("Value")
                        return self._last_value
            
            # Fall back to the last known value
            return self._last_value
        except Exception as err:
            _LOGGER.error(f"Error getting value for {self.name}: {err}")
            return self._last_value
    
    @property
    def extra_state_attributes(self) -> Optional[Dict[str, Any]]:
        """Return additional state attributes."""
        attrs = {
            "loggamera_name": self._value_name,
            "loggamera_type": self._value_type,
        }
        
        # Add timestamp if available
        device_data = self.coordinator.data.get("device_data", {}).get(str(self.device_id))
        if device_data and "Data" in device_data and "LogDateTimeUtc" in device_data["Data"]:
            attrs["last_update"] = device_data["Data"]["LogDateTimeUtc"]
            
        return attrs