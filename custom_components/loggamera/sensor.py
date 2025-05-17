from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
import logging
import requests
from .const import DOMAIN, API_URL, POWER_SENSOR, WATER_SENSOR

_LOGGER = logging.getLogger(__name__)

class LoggameraSensor(Entity):
    def __init__(self, coordinator: DataUpdateCoordinator, sensor_type: str):
        self.coordinator = coordinator
        self.sensor_type = sensor_type
        self._attr_name = f"{DOMAIN} {sensor_type}"
        self._attr_unique_id = f"{DOMAIN}_{sensor_type}"

    @property
    def state(self):
        return self.coordinator.data.get(self.sensor_type)

    @property
    def device_class(self):
        if self.sensor_type == POWER_SENSOR:
            return "power"
        elif self.sensor_type == WATER_SENSOR:
            return "water"
        return None

class LoggameraDataUpdateCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, api_key):
        self.api_key = api_key
        super().__init__(hass, _LOGGER, name=DOMAIN)

    async def _async_update_data(self):
        headers = {"Authorization": f"Bearer {self.api_key}"}
        response = requests.get(API_URL, headers=headers)
        response.raise_for_status()
        return response.json()