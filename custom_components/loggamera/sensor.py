import os
from dotenv import load_dotenv
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers import aiohttp_client
import logging
from datetime import timedelta

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(minutes=5)

# Load environment variables from .env file (for testing purposes)
load_dotenv()

class LoggameraSensor(Entity):
    def __init__(self, coordinator: DataUpdateCoordinator, sensor_name: str):
        self.coordinator = coordinator
        self._sensor_name = sensor_name
        self._state = None

    @property
    def name(self):
        return self._sensor_name

    @property
    def state(self):
        return self._state

    async def async_update(self):
        await self.coordinator.async_request_refresh()
        self._state = self.coordinator.data.get(self._sensor_name)

class LoggameraDataUpdateCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, api_url, api_key=None, device_id=None, update_interval=None):
        super().__init__(hass, _LOGGER, name="Loggamera Data", update_interval=update_interval)
        self.api_url = api_url  # "https://platform.loggamera.se/api/v2/PowerMeter"
        self.api_key = api_key or os.getenv("LOGGAMERA_API_KEY")
        self.device_id = device_id or os.getenv("LOGGAMERA_DEVICE_ID")

    async def _async_update_data(self):
        session = aiohttp_client.async_get_clientsession(self.hass)
        headers = {"Content-Type": "application/json"}
        payload = {
            "ApiKey": self.api_key,
            "DeviceId": int(self.device_id) if self.device_id else None,
            # "DateTimeUtc": "2025-04-05T16:33:00Z"  # Include for a specific snapshot; omit for freshest data.
        }
        async with session.post(self.api_url, headers=headers, json=payload) as response:
            if response.status != 200:
                _LOGGER.error("Error fetching data from Loggamera PowerMeter: %s", response.status)
                return {}
            data = await response.json()
            if data.get("Error"):
                _LOGGER.error("Error in API response: %s", data["Error"])
                return {}
            values = data.get("Data", {}).get("Values", [])
            # Convert list of sensor values into a dictionary keyed by sensor Name.
            return {item["Name"]: item["Value"] for item in values}