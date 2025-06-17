"""Sensor platform for Loggamera integration."""

import logging
from datetime import datetime  # noqa: F401
from typing import Any, Dict, List, Optional  # noqa: F401

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfVolume,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (  # noqa: F401
    DOMAIN,
    SENSOR_ENERGY,
    SENSOR_HUMIDITY,
    SENSOR_POWER,
    SENSOR_TEMPERATURE,
    SENSOR_VALUE,
    SENSOR_WATER,
)

_LOGGER = logging.getLogger(__name__)

# Mapping of sensor name to device class and unit
SENSOR_MAP = {
    # PowerMeter standard values - THESE MUST BE PRESERVED
    "ConsumedTotalInkWh": {
        "device_class": SensorDeviceClass.ENERGY,
        "unit": UnitOfEnergy.KILO_WATT_HOUR,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "name": "Total Energy Consumption",
    },
    "PowerInkW": {
        "device_class": SensorDeviceClass.POWER,
        "unit": UnitOfPower.KILO_WATT,
        "state_class": SensorStateClass.MEASUREMENT,
        "name": "Current Energy Consumption",
    },
    "alarmActive": {
        "device_class": None,
        "unit": None,
        "state_class": None,
        "name": "Alarm Status",
        "icon": "mdi:alert-circle",
    },
    "alarmInClearText": {
        "device_class": None,
        "unit": None,
        "state_class": None,
        "name": "Alarm Context",
        "icon": "mdi:alert-box",
    },
    # RawData specific values - these are the most common ones
    "544352": {
        "device_class": SensorDeviceClass.ENERGY,
        "unit": UnitOfEnergy.KILO_WATT_HOUR,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "name": "Total Energy Consumed",
    },  # Energy imported
    "544353": {
        "device_class": SensorDeviceClass.ENERGY,
        "unit": UnitOfEnergy.KILO_WATT_HOUR,
        "state_class": SensorStateClass.MEASUREMENT,
        "name": "Total Energy Interval",
    },  # Energy imported interval
    "544399": {
        "device_class": SensorDeviceClass.POWER,
        "unit": UnitOfPower.WATT,
        "state_class": SensorStateClass.MEASUREMENT,
        "name": "Power",
    },  # Power
    # Common HeatPump RawData temperature sensors
    "541388": {
        "device_class": SensorDeviceClass.TEMPERATURE,
        "unit": UnitOfTemperature.CELSIUS,
        "state_class": SensorStateClass.MEASUREMENT,
        "name": "Hot Water Temperature",
    },  # Varmvattentemp
    "541125": {
        "device_class": SensorDeviceClass.TEMPERATURE,
        "unit": UnitOfTemperature.CELSIUS,
        "state_class": SensorStateClass.MEASUREMENT,
        "name": "Set Room Temperature",
    },  # Inställd rumstemperatur
    "541119": {
        "device_class": SensorDeviceClass.TEMPERATURE,
        "unit": UnitOfTemperature.CELSIUS,
        "state_class": SensorStateClass.MEASUREMENT,
        "name": "Outdoor Temperature",
    },  # Utetemperatur
    "541655": {
        "device_class": SensorDeviceClass.TEMPERATURE,
        "unit": UnitOfTemperature.CELSIUS,
        "state_class": SensorStateClass.MEASUREMENT,
        "name": "Hot Gas Temperature",
    },  # Hetgas (T6)
    "541104": {
        "device_class": SensorDeviceClass.TEMPERATURE,
        "unit": UnitOfTemperature.CELSIUS,
        "state_class": SensorStateClass.MEASUREMENT,
        "name": "Heat Carrier 1",
    },  # Värmebärare 1
    "541646": {
        "device_class": SensorDeviceClass.TEMPERATURE,
        "unit": UnitOfTemperature.CELSIUS,
        "state_class": SensorStateClass.MEASUREMENT,
        "name": "Heat Carrier Outgoing",
    },  # Värmebärare utgående (T8)
    "541647": {
        "device_class": SensorDeviceClass.TEMPERATURE,
        "unit": UnitOfTemperature.CELSIUS,
        "state_class": SensorStateClass.MEASUREMENT,
        "name": "Heat Carrier Incoming",
    },  # Värmebärare ingående (T9)
    "541651": {
        "device_class": SensorDeviceClass.TEMPERATURE,
        "unit": UnitOfTemperature.CELSIUS,
        "state_class": SensorStateClass.MEASUREMENT,
        "name": "Brine Incoming",
    },  # Köldbärare ingående (T10)
    "541648": {
        "device_class": SensorDeviceClass.TEMPERATURE,
        "unit": UnitOfTemperature.CELSIUS,
        "state_class": SensorStateClass.MEASUREMENT,
        "name": "Brine Outgoing",
    },  # Köldbärare utgående (T11)
    # HeatPump endpoint standard sensor names
    "heatCarrierInTempInDeg": {
        "device_class": SensorDeviceClass.TEMPERATURE,
        "unit": UnitOfTemperature.CELSIUS,
        "state_class": SensorStateClass.MEASUREMENT,
        "name": "Heat Carrier Inlet Temperature",
    },
    "heatCarrierOutTempInDeg": {
        "device_class": SensorDeviceClass.TEMPERATURE,
        "unit": UnitOfTemperature.CELSIUS,
        "state_class": SensorStateClass.MEASUREMENT,
        "name": "Heat Carrier Outlet Temperature",
    },
    "brineInTempInDeg": {
        "device_class": SensorDeviceClass.TEMPERATURE,
        "unit": UnitOfTemperature.CELSIUS,
        "state_class": SensorStateClass.MEASUREMENT,
        "name": "Brine Inlet Temperature",
    },
    "brineOutTempInDeg": {
        "device_class": SensorDeviceClass.TEMPERATURE,
        "unit": UnitOfTemperature.CELSIUS,
        "state_class": SensorStateClass.MEASUREMENT,
        "name": "Brine Outlet Temperature",
    },
    "reducedModeActive": {
        "device_class": None,
        "unit": None,
        "state_class": None,
        "name": "Reduced Mode",
        "icon": "mdi:power-sleep",
    },
    "pumpActivity": {
        "device_class": None,
        "unit": None,
        "state_class": None,
        "name": "Pump Activity",
        "icon": "mdi:pump",
    },
    "filterAlarmIsActive": {
        "device_class": None,
        "unit": None,
        "state_class": None,
        "name": "Filter Alarm",
        "icon": "mdi:air-filter",
    },
    "544463": {
        "device_class": SensorDeviceClass.ENERGY,
        "unit": UnitOfEnergy.KILO_WATT_HOUR,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "name": "Energy Phase 1",
    },  # Energy (Phase 1)
    "544464": {
        "device_class": SensorDeviceClass.ENERGY,
        "unit": UnitOfEnergy.KILO_WATT_HOUR,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "name": "Energy Phase 2",
    },  # Energy (Phase 2)
    "544465": {
        "device_class": SensorDeviceClass.ENERGY,
        "unit": UnitOfEnergy.KILO_WATT_HOUR,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "name": "Energy Phase 3",
    },  # Energy (Phase 3)
    "544391": {
        "device_class": SensorDeviceClass.CURRENT,
        "unit": UnitOfElectricCurrent.AMPERE,
        "state_class": SensorStateClass.MEASUREMENT,
        "name": "Current Phase 1",
    },  # Current (Phase 1)
    "544393": {
        "device_class": SensorDeviceClass.CURRENT,
        "unit": UnitOfElectricCurrent.AMPERE,
        "state_class": SensorStateClass.MEASUREMENT,
        "name": "Current Phase 2",
    },  # Current (Phase 2)
    "544394": {
        "device_class": SensorDeviceClass.CURRENT,
        "unit": UnitOfElectricCurrent.AMPERE,
        "state_class": SensorStateClass.MEASUREMENT,
        "name": "Current Phase 3",
    },  # Current (Phase 3)
    "544395": {
        "device_class": SensorDeviceClass.VOLTAGE,
        "unit": UnitOfElectricPotential.VOLT,
        "state_class": SensorStateClass.MEASUREMENT,
        "name": "Voltage Phase 1",
    },  # Voltage (Phase 1)
    "544396": {
        "device_class": SensorDeviceClass.VOLTAGE,
        "unit": UnitOfElectricPotential.VOLT,
        "state_class": SensorStateClass.MEASUREMENT,
        "name": "Voltage Phase 2",
    },  # Voltage (Phase 2)
    "544397": {
        "device_class": SensorDeviceClass.VOLTAGE,
        "unit": UnitOfElectricPotential.VOLT,
        "state_class": SensorStateClass.MEASUREMENT,
        "name": "Voltage Phase 3",
    },  # Voltage (Phase 3)
    "549990": {
        "device_class": SensorDeviceClass.ENERGY,
        "unit": UnitOfEnergy.KILO_WATT_HOUR,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "name": "Total Energy Generated",
    },  # Exported energy
    "550224": {
        "device_class": SensorDeviceClass.ENERGY,
        "unit": UnitOfEnergy.KILO_WATT_HOUR,
        "state_class": SensorStateClass.MEASUREMENT,
        "name": "Energy Generated Interval",
    },  # Exported energy interval
    "550205": {
        "device_class": SensorDeviceClass.POWER,
        "unit": UnitOfPower.WATT,
        "state_class": SensorStateClass.MEASUREMENT,
        "name": "Power Phase 1",
    },  # Power phase 1
    "550206": {
        "device_class": SensorDeviceClass.POWER,
        "unit": UnitOfPower.WATT,
        "state_class": SensorStateClass.MEASUREMENT,
        "name": "Power Phase 2",
    },  # Power phase 2
    "550207": {
        "device_class": SensorDeviceClass.POWER,
        "unit": UnitOfPower.WATT,
        "state_class": SensorStateClass.MEASUREMENT,
        "name": "Power Phase 3",
    },  # Power phase 3
}

# Temperature sensor mappings
TEMP_MAPPINGS = {
    "TemperatureInC": {
        "device_class": SensorDeviceClass.TEMPERATURE,
        "unit": UnitOfTemperature.CELSIUS,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "HumidityInRH": {
        "device_class": SensorDeviceClass.HUMIDITY,
        "unit": PERCENTAGE,
        "state_class": SensorStateClass.MEASUREMENT,
    },
}

# Water sensor mappings
WATER_MAPPINGS = {
    "ConsumedTotalInm3": {
        "device_class": SensorDeviceClass.WATER,
        "unit": UnitOfVolume.CUBIC_METERS,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "name": "Total Water Consumption",
    },
    "ConsumedTotalInM3": {  # Note: Capital M3 variant
        "device_class": SensorDeviceClass.WATER,
        "unit": UnitOfVolume.CUBIC_METERS,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "name": "Total Water Consumption",
    },
    "ConsumedSinceMidnightInLiters": {
        "device_class": SensorDeviceClass.WATER,
        "unit": UnitOfVolume.LITERS,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "name": "Water Used Since Midnight",
    },
}

# Combine all mappings
SENSOR_MAP.update(TEMP_MAPPINGS)
SENSOR_MAP.update(WATER_MAPPINGS)


async def async_setup_entry(  # noqa: C901
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
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

        _LOGGER.debug(
            f"Setting up sensors for device: {device_name} (ID: {device_id}, Type: {device_type})"  # noqa: E501
        )

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
            _LOGGER.debug(
                f"Device {device_name} data sources: {', '.join(data_sources)}"
            )

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
                    _LOGGER.debug(
                        f"Created sensor: {entity.name} with value: {value.get('Value')}"  # noqa: E501
                    )
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
                        _LOGGER.debug(
                            f"Created sensor: {entity.name} with value: {value.get('Value')}"  # noqa: E501
                        )
        else:
            _LOGGER.warning(f"No 'Values' data for device {device_name}")

    # Process RawData entities separately (disabled by default)
    _LOGGER.debug("Processing RawData entities...")
    for device in coordinator.data.get("devices", []):
        device_id = device["Id"]
        device_type = device["Class"]
        device_name = device.get("Title", f"{device_type} {device_id}")

        # Look for separately collected RawData
        raw_data_key = f"rawdata_{device_id}"
        raw_data = coordinator.data.get("device_data", {}).get(raw_data_key)

        if (
            raw_data
            and "Data" in raw_data
            and raw_data["Data"]
            and "Values" in raw_data["Data"]
        ):
            _LOGGER.debug(
                f"Processing {len(raw_data['Data']['Values'])} RawData values for {device_name}"
            )

            for value in raw_data["Data"]["Values"]:
                # Create unique ID to avoid conflicts with processed sensors
                unique_id = (
                    f"rawdata_{device_id}_{device_type.lower()}_"
                    f"{value.get('Name', 'unknown')}"
                )

                if unique_id not in processed_unique_ids:
                    # Create RawData sensor
                    entity = LoggameraSensor(
                        coordinator=coordinator,
                        api=api,
                        device_id=device_id,
                        device_type=device_type,
                        device_name=device_name,
                        value_data=value,
                        hass=hass,
                        is_raw_data=True,  # Flag to indicate this is RawData
                    )
                    entities.append(entity)
                    processed_unique_ids.add(unique_id)
                    _LOGGER.debug(
                        f"Created RawData sensor: {entity.name} (disabled by default)"
                    )

    if entities:
        async_add_entities(entities)
        _LOGGER.info(f"Added {len(entities)} Loggamera sensor entities")
    else:
        _LOGGER.warning("No Loggamera sensors added")


class LoggameraSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Loggamera sensor."""

    def __init__(
        self,
        coordinator,
        api,
        device_id,
        device_type,
        device_name,
        value_data,
        hass,
        is_raw_data=False,
    ):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.api = api
        self.device_id = device_id
        self.device_type = device_type
        self.device_name = device_name
        self.value_data = value_data
        self.hass = hass
        self.is_raw_data = is_raw_data
        self.sensor_name = value_data.get("Name", "unknown")

        # Initialize sensor attributes
        self._sensor_value = None
        self._sensor_unit = value_data.get("UnitPresentation", "")
        self._unit_type = value_data.get("UnitType", "")

        # Determine value type - handle null ValueType by inferring from UnitType
        value_type = value_data.get("ValueType")
        unit_type = value_data.get("UnitType", "")
        value = value_data.get("Value", "")

        # If ValueType is null (common in RawData responses), infer from UnitType
        if value_type is None:
            if unit_type in ["BooleanOnOff", "BooleanYesNo"]:
                self._is_boolean = True
                self._is_string = False
            elif unit_type == "Unitless" and str(value).replace(".", "").isdigit():
                # Unitless numeric values (like counters, indexes)
                self._is_boolean = False
                self._is_string = False
            elif unit_type in ["DegreesCelsius", "DegreesKelvin", "DegreesFahrenheit"]:
                # Temperature values are always numeric
                self._is_boolean = False
                self._is_string = False
            else:
                # Default to numeric for other measurement types
                self._is_boolean = False
                self._is_string = False
        else:
            # Use explicit ValueType when available
            self._is_boolean = value_type == "BOOLEAN"
            self._is_string = value_type == "STRING"

        # Get friendly name from SENSOR_MAP if available
        sensor_info = SENSOR_MAP.get(self.sensor_name, {})
        friendly_name = sensor_info.get("name")

        # If not found in hardcoded map, try dynamic detection for name
        if not friendly_name:
            dynamic_info = self._detect_sensor_attributes_dynamically()
            friendly_name = dynamic_info.get("name") if dynamic_info else None

        # Use friendly name if available, otherwise use API name
        display_name = (
            friendly_name
            if friendly_name
            else value_data.get("ClearTextName", value_data.get("Name", "Unknown"))
        )

        # Set entity naming based on whether this is RawData or standard device data
        if self.is_raw_data:
            # Use rawdata naming pattern: rawdata_{deviceid}_{devicetype}_{sensorname}
            device_type_lower = device_type.lower()
            self._attr_unique_id = (
                f"rawdata_{device_id}_{device_type_lower}_{self.sensor_name}"
            )
            # Also update the display name to indicate this is raw data
            self._attr_name = f"RawData {device_name} {display_name}"
            # Disable RawData entities by default
            self._attr_entity_registry_enabled_default = False
        else:
            # Use standard naming pattern for regular device sensors
            self._attr_unique_id = f"loggamera_{device_id}_{self.sensor_name}"
            self._attr_name = f"{device_name} {display_name}"

        # Ensure consistent device ID format
        try:
            if self.is_raw_data:
                device_type_lower = device_type.lower()
                self._attr_unique_id = (
                    f"rawdata_{int(device_id)}_{device_type_lower}_{self.sensor_name}"
                )
            else:
                self._attr_unique_id = f"loggamera_{int(device_id)}_{self.sensor_name}"
        except (ValueError, TypeError):
            pass

        # Determine device class, state class, and unit of measurement
        self._set_sensor_attributes()

        _LOGGER.debug(
            f"Initialized sensor: {self.name} with value: {value_data.get('Value')}"
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
            if not value and not self._is_boolean:
                return None

            # For boolean values, convert to boolean
            if self._is_boolean:
                # Handle various boolean representations
                value_lower = value.lower()
                if value_lower in ["true", "1", "on", "yes"]:
                    return True
                elif value_lower in ["false", "0", "off", "no", ""]:
                    return False
                else:
                    # Default to false for unknown boolean values
                    return False

            # For string values, return as is (but sanitized)
            if self._is_string:
                # Limit string length for safety
                return value[:255]

            # Try to convert to float for numeric values
            try:
                # Convert to float, handling comma as decimal separator (European format)  # noqa: E501
                value = value.replace(",", ".")
                return float(value)
            except (ValueError, TypeError):
                # Not a number, return as is (but sanitized)
                return value[:255]

        # If it's already a boolean, return it
        if isinstance(value, bool) and self._is_boolean:
            return value

        # Handle numeric boolean values (0/1)
        if self._is_boolean and isinstance(value, (int, float)):
            return bool(value)

        # If it's already a number, return it
        if (
            isinstance(value, (int, float))
            and not self._is_boolean
            and not self._is_string
        ):
            return float(value)

        # For any other type, convert to string and sanitize
        return str(value)[:255]

    def _detect_sensor_attributes_dynamically(self):
        """Dynamically detect sensor attributes for unknown sensors.

        Analyzes UnitType, UnitPresentation, ClearTextName, and sensor name
        to intelligently determine device_class, unit, and state_class.

        Returns:
            Dict with detected sensor attributes
        """
        detected = {}

        unit_type = self.value_data.get("UnitType", "").lower()
        unit_presentation = self.value_data.get("UnitPresentation", "").lower()
        clear_text_name = self.value_data.get("ClearTextName", "").lower()
        sensor_name = self.sensor_name.lower()

        # Temperature detection
        if (
            unit_type in ["degreescelsius", "celsius"]
            or "°c" in unit_presentation
            or "celsius" in unit_presentation
            or any(temp_word in clear_text_name for temp_word in ["temp", "temperatur"])
            or any(temp_word in sensor_name for temp_word in ["temp", "temperatur"])
        ):
            detected.update(
                {
                    "device_class": SensorDeviceClass.TEMPERATURE,
                    "unit": UnitOfTemperature.CELSIUS,
                    "state_class": SensorStateClass.MEASUREMENT,
                    "name": clear_text_name.title()
                    if clear_text_name
                    else sensor_name.title(),
                }
            )
            _LOGGER.debug(
                f"Dynamic detection: {sensor_name} → TEMPERATURE (UnitType: {unit_type})"
            )

        # Energy detection
        elif (
            unit_type in ["kwh", "kilowatthour"]
            or "kwh" in unit_presentation
            or any(
                energy_word in clear_text_name
                for energy_word in ["energy", "energi", "förbrukning"]
            )
            or any(
                energy_word in sensor_name
                for energy_word in ["energy", "consumed", "total"]
            )
        ):
            detected.update(
                {
                    "device_class": SensorDeviceClass.ENERGY,
                    "unit": UnitOfEnergy.KILO_WATT_HOUR,
                    "state_class": SensorStateClass.TOTAL_INCREASING,
                    "name": clear_text_name.title()
                    if clear_text_name
                    else sensor_name.title(),
                }
            )
            _LOGGER.debug(
                f"Dynamic detection: {sensor_name} → ENERGY (UnitType: {unit_type})"
            )

        # Power detection
        elif (
            unit_type in ["kw", "kilowatt", "w", "watt"]
            or "kw" in unit_presentation
            or "w" in unit_presentation
            or any(
                power_word in clear_text_name
                for power_word in ["power", "effekt", "watt"]
            )
            or any(power_word in sensor_name for power_word in ["power", "watt"])
        ):
            # Determine if kilowatt or watt based on presentation
            if "kw" in unit_presentation.lower() or "kilowatt" in unit_type:
                unit = UnitOfPower.KILO_WATT
            else:
                unit = UnitOfPower.WATT
            detected.update(
                {
                    "device_class": SensorDeviceClass.POWER,
                    "unit": unit,
                    "state_class": SensorStateClass.MEASUREMENT,
                    "name": clear_text_name.title()
                    if clear_text_name
                    else sensor_name.title(),
                }
            )
            _LOGGER.debug(
                f"Dynamic detection: {sensor_name} → POWER (UnitType: {unit_type})"
            )

        # Current detection
        elif (
            unit_type in ["ampere", "amp", "a"]
            or "a" in unit_presentation
            or "amp" in unit_presentation
        ):
            detected.update(
                {
                    "device_class": SensorDeviceClass.CURRENT,
                    "unit": UnitOfElectricCurrent.AMPERE,
                    "state_class": SensorStateClass.MEASUREMENT,
                    "name": clear_text_name.title()
                    if clear_text_name
                    else sensor_name.title(),
                }
            )
            _LOGGER.debug(
                f"Dynamic detection: {sensor_name} → CURRENT (UnitType: {unit_type})"
            )

        # Voltage detection
        elif (
            unit_type in ["volt", "v"]
            or "v" in unit_presentation
            or "volt" in unit_presentation
        ):
            detected.update(
                {
                    "device_class": SensorDeviceClass.VOLTAGE,
                    "unit": UnitOfElectricPotential.VOLT,
                    "state_class": SensorStateClass.MEASUREMENT,
                    "name": clear_text_name.title()
                    if clear_text_name
                    else sensor_name.title(),
                }
            )
            _LOGGER.debug(
                f"Dynamic detection: {sensor_name} → VOLTAGE (UnitType: {unit_type})"
            )

        # Water/Volume detection
        elif (
            unit_type in ["m3", "cubicmeter", "liter", "litre"]
            or "m³" in unit_presentation
            or "m3" in unit_presentation
            or "l" in unit_presentation
            or any(
                water_word in clear_text_name
                for water_word in ["water", "vatten", "volume"]
            )
            or any(water_word in sensor_name for water_word in ["water", "consumed"])
        ):
            if (
                "m3" in unit_presentation
                or "m³" in unit_presentation
                or "cubicmeter" in unit_type
            ):
                unit = UnitOfVolume.CUBIC_METERS
            else:
                unit = UnitOfVolume.LITERS
            detected.update(
                {
                    "device_class": SensorDeviceClass.WATER,
                    "unit": unit,
                    "state_class": SensorStateClass.TOTAL_INCREASING,
                    "name": clear_text_name.title()
                    if clear_text_name
                    else sensor_name.title(),
                }
            )
            _LOGGER.debug(
                f"Dynamic detection: {sensor_name} → WATER (UnitType: {unit_type})"
            )

        # Humidity detection
        elif (
            unit_type in ["percent", "percentage", "rh"]
            or "%" in unit_presentation
            or "rh" in unit_presentation
            or any(
                humidity_word in clear_text_name
                for humidity_word in ["humidity", "fuktighet"]
            )
            or any(humidity_word in sensor_name for humidity_word in ["humidity", "rh"])
        ):
            detected.update(
                {
                    "device_class": SensorDeviceClass.HUMIDITY,
                    "unit": PERCENTAGE,
                    "state_class": SensorStateClass.MEASUREMENT,
                    "name": clear_text_name.title()
                    if clear_text_name
                    else sensor_name.title(),
                }
            )
            _LOGGER.debug(
                f"Dynamic detection: {sensor_name} → HUMIDITY (UnitType: {unit_type})"
            )

        # Boolean detection
        elif (
            unit_type in ["boolean", "booleanonoff", "booleanyesno"]
            or any(
                bool_word in clear_text_name
                for bool_word in ["active", "on", "off", "alarm"]
            )
            or any(
                bool_word in sensor_name for bool_word in ["active", "alarm", "status"]
            )
        ):
            detected.update(
                {
                    "device_class": None,
                    "unit": None,
                    "state_class": None,
                    "name": clear_text_name.title()
                    if clear_text_name
                    else sensor_name.title(),
                }
            )
            _LOGGER.debug(
                f"Dynamic detection: {sensor_name} → BOOLEAN (UnitType: {unit_type})"
            )

        # Generic numeric fallback
        elif not self._is_boolean and not self._is_string:
            # Use the raw unit presentation if available
            unit = self._sensor_unit if self._sensor_unit else None
            detected.update(
                {
                    "device_class": None,
                    "unit": unit,
                    "state_class": SensorStateClass.MEASUREMENT,
                    "name": clear_text_name.title()
                    if clear_text_name
                    else sensor_name.title(),
                }
            )
            _LOGGER.info(
                f"Dynamic detection: {sensor_name} → GENERIC NUMERIC "
                f"(UnitType: {unit_type}, Unit: {unit})"
            )

        # Log when we couldn't detect anything useful
        if not detected:
            _LOGGER.warning(
                f"Dynamic detection failed for sensor {sensor_name} "
                f"(UnitType: {unit_type}, UnitPresentation: {unit_presentation})"
            )

        return detected

    def _set_sensor_attributes(self):
        """Set device class, state class, and unit of measurement based on sensor type."""  # noqa: E501
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

        # If not found in hardcoded map, try dynamic detection
        if not sensor_info:
            sensor_info = self._detect_sensor_attributes_dynamically()
            if sensor_info:
                _LOGGER.info(
                    f"Used dynamic detection for unknown sensor: {self.sensor_name}"
                )

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

        # Determine which data source to use based on sensor type
        if self.is_raw_data:
            # For RawData sensors, look in the rawdata_{device_id} key
            data_key = f"rawdata_{self.device_id}"
        else:
            # For standard sensors, use device_id directly
            data_key = self.device_id

        device_data = self.coordinator.data["device_data"].get(data_key)
        if not device_data:
            # Try string version of data_key as fallback
            device_data = self.coordinator.data["device_data"].get(str(data_key))

        if (
            not device_data
            or "Data" not in device_data
            or "Values" not in device_data["Data"]
        ):
            return None

        # Find our specific sensor value in the latest data
        sensor_name = self.sensor_name
        for value in device_data["Data"]["Values"]:
            if value.get("Name") == sensor_name:
                raw_value = value.get("Value", "")

                # Update icon if this is an alarm sensor
                if self._is_boolean and self.sensor_name == "alarmActive":
                    is_active = (
                        raw_value.lower() == "true"
                        if isinstance(raw_value, str)
                        else bool(raw_value)
                    )
                    self._attr_icon = (
                        "mdi:alert-circle" if is_active else "mdi:alert-circle-outline"
                    )

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

        # Determine which data source to use based on sensor type
        if self.is_raw_data:
            # For RawData sensors, look in the rawdata_{device_id} key
            data_key = f"rawdata_{self.device_id}"
        else:
            # For standard sensors, use device_id directly
            data_key = self.device_id

        # Check if our device data exists
        device_data = self.coordinator.data["device_data"].get(data_key)
        if not device_data:
            # Try string version of data_key as fallback
            device_data = self.coordinator.data["device_data"].get(str(data_key))
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
