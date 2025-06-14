"""The Loggamera integration."""

import logging
import time
from datetime import timedelta
from typing import Any, Dict

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import LoggameraAPI, LoggameraAPIError
from .const import (
    CONF_API_KEY,
    CONF_ORGANIZATION_ID,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    PLATFORMS,
)

_LOGGER = logging.getLogger(__name__)

# Since this integration only supports config entries and has no YAML configuration,
# we use the config_entry_only_config_schema helper
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Loggamera integration."""
    # Create domain data if not exists
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Loggamera from a config entry."""
    try:
        # Get config entry data
        api_key = entry.data[CONF_API_KEY]
        organization_id = entry.data.get(CONF_ORGANIZATION_ID)

        # Get scan interval from options or data, or use default
        scan_interval = entry.options.get(
            CONF_SCAN_INTERVAL,
            entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        )

        _LOGGER.debug(
            f"Setting up integration with scan interval: {scan_interval} seconds"
        )

        # Create API client
        api = LoggameraAPI(api_key=api_key, organization_id=organization_id)

        # Test API connection
        try:
            # Test connection by getting organizations
            await hass.async_add_executor_job(api.get_organizations)
        except LoggameraAPIError as err:
            _LOGGER.error(f"Failed to connect to Loggamera API: {err}")
            raise ConfigEntryNotReady(f"Failed to connect to Loggamera API: {err}")

        # Create update coordinator
        coordinator = LoggameraDataUpdateCoordinator(
            hass,
            api=api,
            name=f"Loggamera {organization_id}" if organization_id else "Loggamera",
            update_interval=timedelta(seconds=scan_interval),
        )

        # Initial data fetch
        await coordinator.async_config_entry_first_refresh()

        if not coordinator.last_update_success:
            raise ConfigEntryNotReady(
                f"Failed to fetch initial data: {coordinator.last_exception}"
            )

        # Store the coordinator and API client
        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][entry.entry_id] = {
            "coordinator": coordinator,
            "api": api,
        }

        # Set up platforms
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

        # Add update listener
        entry.async_on_unload(entry.add_update_listener(async_reload_entry))

        return True
    except Exception as err:
        _LOGGER.exception(f"Unexpected error during setup: {err}")
        raise ConfigEntryNotReady(f"Unexpected error during setup: {err}")


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug(f"Unloading Loggamera integration for {entry.title}")

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    _LOGGER.debug(f"Reloading Loggamera integration for {entry.title}")
    await hass.config_entries.async_reload(entry.entry_id)


class LoggameraDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Loggamera data."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: LoggameraAPI,
        name: str,
        update_interval: timedelta,
    ):
        """Initialize data update coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=name,
            update_interval=update_interval,
        )
        self.api = api
        self.data = {
            "devices": [],
            "device_data": {},
            "scenarios": [],
        }

        _LOGGER.debug(
            "Created Loggamera data coordinator with update interval: %s",
            update_interval,
        )

    async def _async_update_data(self) -> Dict[str, Any]:  # noqa: C901
        """Fetch data from API."""
        try:
            _LOGGER.debug("Starting data update cycle")
            start_time = time.time()

            # Start with existing data - we'll update it
            updated_data = self.data.copy()

            # Fetch organizations first if needed (typically not necessary)
            if not self.api.organization_id:
                _LOGGER.debug("No organization ID set, fetching organizations")
                org_response = await self.hass.async_add_executor_job(
                    self.api.get_organizations
                )

                if (
                    "Data" in org_response
                    and "Organizations" in org_response["Data"]
                    and org_response["Data"]["Organizations"]
                ):
                    self.api.organization_id = org_response["Data"]["Organizations"][0][
                        "Id"
                    ]
                    _LOGGER.info(f"Set organization ID to {self.api.organization_id}")

            # Fetch devices if we don't have them yet
            if not updated_data["devices"]:
                devices_response = await self.hass.async_add_executor_job(
                    self.api.get_devices
                )
                if "Data" in devices_response and "Devices" in devices_response["Data"]:
                    updated_data["devices"] = devices_response["Data"]["Devices"]
                    _LOGGER.info(f"Found {len(updated_data['devices'])} devices")

            # Fetch scenarios if available (for button platform if needed in future)
            try:
                scenarios_response = await self.hass.async_add_executor_job(
                    self.api.get_scenarios
                )
                if (
                    "Data" in scenarios_response
                    and "Scenarios" in scenarios_response["Data"]
                ):
                    updated_data["scenarios"] = scenarios_response["Data"]["Scenarios"]
                    _LOGGER.debug(f"Found {len(updated_data['scenarios'])} scenarios")
            except LoggameraAPIError:
                # Don't fail the whole update if scenarios aren't available
                pass

            # Fetch device data for each device - this will now fetch both
            # RawData and PowerMeter data for PowerMeter devices as implemented
            # in the API client
            for device in updated_data["devices"]:
                device_id = device["Id"]
                device_type = device["Class"]
                try:
                    # Fetch device data - our updated get_device_data method handles combining data sources  # noqa: E501
                    device_data = await self.hass.async_add_executor_job(
                        self.api.get_device_data, device_id, device_type
                    )

                    # Store the device data
                    updated_data["device_data"][str(device_id)] = device_data

                    # Log which data sources were used
                    sources = []
                    if device_data.get("_raw_data_used"):
                        sources.append("RawData")
                    if device_data.get("_power_meter_used"):
                        sources.append("PowerMeter")
                    if device_data.get("_endpoint_used"):
                        sources.append(device_data["_endpoint_used"])

                    if sources:
                        _LOGGER.debug(
                            f"Device {device_id} data fetched from: {', '.join(sources)}"  # noqa: E501
                        )
                except Exception as err:
                    _LOGGER.warning(f"Failed to get data for device {device_id}: {err}")

            # Calculate time taken for the update
            elapsed = time.time() - start_time
            _LOGGER.debug(
                f"Finished fetching loggamera data in {elapsed:.3f} seconds (success: {True})"  # noqa: E501
            )

            return updated_data
        except LoggameraAPIError as err:
            _LOGGER.error(f"Error fetching data: {err}")
            raise UpdateFailed(f"Error fetching data: {err}")
        except Exception as err:
            _LOGGER.exception(f"Unexpected error during update: {err}")
            raise UpdateFailed(f"Unexpected error: {err}")
