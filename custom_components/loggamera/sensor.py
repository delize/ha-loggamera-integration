"""Sensor platform for Loggamera integration."""
from __future__ import annotations

import logging
from typing import Any, Callable, Optional

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfPower,
    UnitOfEnergy,
    UnitOfVolume,
    UnitOfTemperature,
    PERCENTAGE,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DOMAIN, CATEGORY_POWER, CATEGORY_WATER, CATEGORY_ROOM, CATEGORY_CLIMATE

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Loggamera sensor based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    
    entities = []

    # Add sensors based on available devices and their capabilities
    if coordinator.data:
        devices = coordinator.data.get("devices", [])
        
        for device in devices:
            device_id = device.get("deviceId")
            device_name = device.get("name", f"Device {device_id}")
            
            if not device_id:
                continue
                
            capabilities_key = f"capabilities_{device_id}"
            capabilities = coordinator.data.get(capabilities_key, {})
            
            # Add power sensors if available
            power_key = f"power_{device_id}"
            if power_key in coordinator.data:
                # You would need to adapt these based on the actual data structure from the API
                entities.append(LoggameraPowerSensor(coordinator, device_id, device_name, "power", "Current Power", UnitOfPower.WATT, SensorDeviceClass.POWER))
                entities.append(LoggameraPowerSensor(coordinator, device_id, device_name, "energy", "Energy Consumption", UnitOfEnergy.KILO_WATT_HOUR, SensorDeviceClass.ENERGY))
            
            # Add water sensors if available
            water_key = f"water_{device_id}"
            if water_key in coordinator.data:
                entities.append(LoggameraWaterSensor(coordinator, device_id, device_name, "water", "Water Consumption", UnitOfVolume.LITERS, SensorDeviceClass.WATER))
            
            # Add room sensors if available
            room_key = f"room_{device_id}"
            if room_key in coordinator.data:
                entities.append(LoggameraRoomSensor(coordinator, device_id, device_name, "temperature", "Temperature", UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE))
                entities.append(LoggameraRoomSensor(coordinator, device_id, device_name, "humidity", "Humidity", PERCENTAGE, SensorDeviceClass.HUMIDITY))
    
    async_add_entities(entities)


class LoggameraBaseSensor(CoordinatorEntity, SensorEntity):
    """Base class for Loggamera sensors."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        device_id: str,
        device_name: str,
        sensor_type: str,
        name: str,
        unit: str,
        device_class: str,
        state_class: str = SensorStateClass.MEASUREMENT,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._device_name = device_name
        self._sensor_type = sensor_type
        self._attr_name = f"{device_name} {name}"
        self._attr_unique_id = f"{device_id}_{sensor_type}"
        self._attr_device_class = device_class
        self._attr_native_unit_of_measurement = unit
        self._attr_state_class = state_class
        self._attr_should_poll = False
        
        # Device info
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=device_name,
            manufacturer="Loggamera",
        )
    
    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        # This method should be implemented by subclasses
        return None


class LoggameraPowerSensor(LoggameraBaseSensor):
    """Representation of a Loggamera power sensor."""
    
    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None
            
        power_data = self.coordinator.data.get(f"power_{self._device_id}")
        if not power_data:
            return None
            
        # Extract the value based on the sensor type and the API response structure
        # This is a placeholder and should be adapted to match the actual API response
        if self._sensor_type == "power":
            return power_data.get("currentPower")
        elif self._sensor_type == "energy":
            return power_data.get("totalEnergy")
        
        return None


class LoggameraWaterSensor(LoggameraBaseSensor):
    """Representation of a Loggamera water sensor."""
    
    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None
            
        water_data = self.coordinator.data.get(f"water_{self._device_id}")
        if not water_data:
            return None
            
        # Extract the value based on the API response structure
        # This is a placeholder and should be adapted to match the actual API response
        return water_data.get("totalConsumption")


class LoggameraRoomSensor(LoggameraBaseSensor):
    """Representation of a Loggamera room sensor."""
    
    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None
            
        room_data = self.coordinator.data.get(f"room_{self._device_id}")
        if not room_data:
            return None
            
        # Extract the value based on the sensor type and the API response structure
        # This is a placeholder and should be adapted to match the actual API response
        if self._sensor_type == "temperature":
            return room_data.get("temperature")
        elif self._sensor_type == "humidity":
            return room_data.get("humidity")
        
        return None