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
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util
from homeassistant.const import (
    UnitOfTemperature,
    UnitOfEnergy,
    UnitOfPower,
    PERCENTAGE,
    UnitOfVolume,
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

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up Loggamera sensors based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    api = hass.data[DOMAIN][entry.entry_id]["api"]
    
    # Wait for a successful update before proceeding
    await coordinator.async_config_entry_first_update()
    
    entities = []
    
    # Process devices from coordinator data
    if "devices" not in coordinator.data:
        _LOGGER.error("No devices data in coordinator")
        return
    
    for device in coordinator.data["devices"]:
        device_id = device["Id"]
        device_type = device["Class"]
        device_name = device.get("Title", f"{device_type} {device_id}")
        
        _LOGGER.debug(f"Setting up sensors for device: {device_name} (ID: {device_id}, Type: {device_type})")
        
        # Get device data
        try:
            device_data = await hass.async_add_executor_job(
                api.get_device_data, device_id, device_type
            )
            
            if "Data" not in device_data or "Values" not in device_data["Data"]:
                _LOGGER.warning(f"No values data for device {device_name}")
                continue
            
            # Check if device has any sensors
            values = device_data["Data"]["Values"]
            if not values:
                _LOGGER.warning(f"Device {device_name} has no sensor values")
                continue
            
            # Check data timestamp for PowerMeter devices
            if device_type == "PowerMeter" and "LogDateTimeUtc" in device_data["Data"]:
                timestamp_str = device_data["Data"]["LogDateTimeUtc"]
                try:
                    # Parse the timestamp to check data age
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    now = dt_util.utcnow()
                    age = now - timestamp
                    
                    # If data is more than 2 hours old, log a warning
                    if age.total_seconds() > 7200:
                        _LOGGER.warning(
                            f"PowerMeter device {device_name} data is {age.total_seconds()/3600:.1f} hours old "
                            f"(timestamp: {timestamp_str}). This may indicate an issue with the device."
                        )
                    else:
                        _LOGGER.debug(f"PowerMeter device {device_name} data timestamp: {timestamp_str}")
                except (ValueError, AttributeError):
                    _LOGGER.warning(f"Could not parse timestamp: {timestamp_str}")
            
            # Create sensor entities for each value
            for value in values:
                entity = LoggameraSensor(
                    coordinator=coordinator,
                    api=api,
                    device_id=device_id,
                    device_type=device_type,
                    device_name=device_name,
                    value_data=value,
                )
                entities.append(entity)
            
            _LOGGER.debug(f"Added {len(values)} sensors for device {device_name}")
            
        except Exception as err:
            _LOGGER.error(f"Error setting up sensors for device {device_name}: {err}")
    
    if entities:
        async_add_entities(entities)
        _LOGGER.info(f"Added {len(entities)} Loggamera sensor entities")
    else:
        _LOGGER.warning("No Loggamera sensors added")

class LoggameraSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Loggamera sensor."""

    def __init__(self, coordinator, api, device_id, device_type, device_name, value_data):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.api = api
        self.device_id = device_id
        self.device_type = device_type
        self._device_name = device_name
        
        # Value data
        self._value_name = value_data.get("Name", "Unknown")
        self._clear_name = value_data.get("ClearTextName", self._value_name)
        self._value_type = value_data.get("ValueType", "Unknown")
        self._unit_type = value_data.get("UnitType", "")
        self._unit = value_data.get("UnitPresentation", "")
        
        # Last value and timestamp for tracking updates
        self._last_value = None
        self._last_update_time = None
        self._stale_data_reported = False
        
        # Entity attributes
        self._attr_unique_id = f"loggamera_{device_id}_{self._value_name}"
        self._attr_name = f"{device_name} {self._clear_name}"
        
        # Set device class based on value name or type
        self._attr_device_class = self._get_device_class()
        
        # Set state class
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
    
    def _get_device_class(self):
        """Determine sensor device class based on value name and unit."""
        # Try to get device class from the map
        if self._value_name in DEVICE_CLASS_MAP:
            return DEVICE_CLASS_MAP[self._value_name]
        
        # Try to determine from clear name for common sensors
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
    def available(self) -> bool:
        """Return if entity is available."""
        if self.coordinator.last_update_success:
            # For PowerMeter devices, check if data is stale
            if self.device_type == "PowerMeter" and self._last_update_time:
                now = dt_util.utcnow()
                # If no update in over 2 hours, mark as unavailable and log warning once
                if (now - self._last_update_time).total_seconds() > 7200 and not self._stale_data_reported:
                    _LOGGER.warning(
                        f"PowerMeter device {self._device_name} data may be stale - last update: {self._last_update_time.isoformat()}"
                    )
                    self._stale_data_reported = True
                    return False
            return True
        return False
    
    @property
    def native_value(self):
        """Return the state of the sensor."""
        try:
            # Find the current device in updated data
            for device in self.coordinator.data.get("devices", []):
                if device["Id"] == self.device_id:
                    # Get device data
                    device_data = None
                    for device_id, data in self.coordinator.data.get("device_data", {}).items():
                        if int(device_id) == self.device_id:
                            device_data = data
                            break
                    
                    if not device_data or "Data" not in device_data or "Values" not in device_data["Data"]:
                        return self._last_value
                    
                    # Track data update timestamp for PowerMeter
                    if self.device_type == "PowerMeter" and "LogDateTimeUtc" in device_data["Data"]:
                        try:
                            timestamp = datetime.fromisoformat(device_data["Data"]["LogDateTimeUtc"].replace('Z', '+00:00'))
                            if self._last_update_time != timestamp:
                                self._last_update_time = timestamp
                                self._stale_data_reported = False  # Reset stale data flag on new data
                        except (ValueError, AttributeError):
                            pass
                    
                    # Find the value
                    for value in device_data["Data"]["Values"]:
                        if value.get("Name") == self._value_name:
                            self._last_value = value.get("Value")
                            return self._last_value
            
            return self._last_value
        except Exception as err:
            _LOGGER.error(f"Error getting value for {self.name}: {err}")
            return self._last_value
    
    @property
    def extra_state_attributes(self) -> Optional[Dict[str, Any]]:
        """Return additional state attributes."""
        attributes = {
            "loggamera_name": self._value_name,
            "loggamera_type": self._value_type,
        }
        
        # For PowerMeter devices, include timestamp of last data update
        if self.device_type == "PowerMeter" and self._last_update_time:
            attributes["last_data_update"] = self._last_update_time.isoformat()
        
        return attributes