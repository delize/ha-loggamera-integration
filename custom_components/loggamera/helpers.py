import json
from homeassistant.helpers import aiohttp_client
import logging

_LOGGER = logging.getLogger(__name__)

async def fetch_organizations(hass, api_key):
    """Fetch list of organizations using the API key."""
    session = aiohttp_client.async_get_clientsession(hass)
    url = "https://platform.loggamera.se/api/v2/Organizations"
    headers = {"Content-Type": "application/json"}
    payload = {"ApiKey": api_key}
    async with session.post(url, headers=headers, json=payload) as response:
        if response.status != 200:
            _LOGGER.error("Error fetching organizations: %s", response.status)
            return []
        data = await response.json()
        return data.get("Data", {}).get("Organizations", [])

async def fetch_devices(hass, api_key, organization_id):
    """Fetch list of devices for a given organization."""
    session = aiohttp_client.async_get_clientsession(hass)
    url = "https://platform.loggamera.se/api/v2/Devices"
    headers = {"Content-Type": "application/json"}
    payload = {"ApiKey": api_key, "OrganizationId": organization_id}
    async with session.post(url, headers=headers, json=payload) as response:
        if response.status != 200:
            _LOGGER.error("Error fetching devices: %s", response.status)
            return []
        data = await response.json()
        return data.get("Data", {}).get("Devices", [])