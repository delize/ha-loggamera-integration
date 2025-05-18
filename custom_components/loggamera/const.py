"""Constants for the Loggamera integration."""

DOMAIN = "loggamera"
BASE_API_URL = "https://platform.loggamera.se/api/v2"

# API Endpoints
ORGANIZATIONS_ENDPOINT = "Organizations"
DEVICES_ENDPOINT = "Devices"
POWER_METER_ENDPOINT = "PowerMeter"
ROOM_SENSOR_ENDPOINT = "RoomSensor"
GENERIC_DEVICE_ENDPOINT = "GenericDevice"
WATER_METER_ENDPOINT = "WaterMeter"
COOLING_UNIT_ENDPOINT = "CoolingUnit"
HEAT_PUMP_ENDPOINT = "HeatPump"
RAW_DATA_ENDPOINT = "RawData"
GET_CAPABILITIES_ENDPOINT = "GetCapabilities"
SET_PROPERTY_ENDPOINT = "SetProperty"
SCENARIOS_ENDPOINT = "Scenarios"
USER_ACCESS_ENDPOINT = "UserAccess"
EXECUTE_SCENARIO_ENDPOINT = "ExecuteScenarioAsync"

# Configuration
CONF_API_KEY = "api_key"
CONF_SCAN_INTERVAL = "scan_interval"
DEFAULT_SCAN_INTERVAL = 60  # seconds

# Entity categories
CATEGORY_POWER = "power"
CATEGORY_WATER = "water"
CATEGORY_ROOM = "room"
CATEGORY_CLIMATE = "climate"