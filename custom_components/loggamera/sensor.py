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
    
    # Try to force a refresh to get fresh data
    await coordinator.async_refresh()
    
    entities = []
    
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
        
        if "Data" not in device_data or device_data["Data"] is None:
            _LOGGER.warning(f"No 'Data' in device data for {device_name}")
            continue
        
        # Standard handling for devices with Values
        if "Values" in device_data["Data"]:
            values = device_data["Data"]["Values"]
            if not values:
                _LOGGER.warning(f"Device {device_name} has no sensor values in Values array")
                continue
            
            # Create sensor entities for each value that is not a boolean
            for value in values:
                if value.get("ValueType") != "BOOLEAN" and value.get("ValueType") != "STRING":
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
        
        # Track last update time
        self._last_update_time = None
        self._stale_data_reported = False
        
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
                      f"unit: {self._attr_native_unit_of_measurement}, "
                      f"initial value: {self._last_value}")
    
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
            
            # Track data update timestamp for PowerMeter
            if self.device_type == "PowerMeter" and "LogDateTimeUtc" in device_data["Data"]:
                try:
                    timestamp = datetime.fromisoformat(device_data["Data"]["LogDateTimeUtc"].replace('Z', '+00:00'))
                    if hasattr(self, '_last_update_time') and self._last_update_time != timestamp:
                        self._last_update_time = timestamp
                        if hasattr(self, '_stale_data_reported'):
                            self._stale_data_reported = False  # Reset stale data flag on new data
                except (ValueError, AttributeError):
                    pass
            
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