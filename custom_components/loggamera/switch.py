"""Support for Loggamera switches."""

import asyncio
import logging
from typing import Any, Dict, Optional

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import LoggameraAPIError
from .const import ATTR_DEVICE_TYPE, ATTR_DURATION_MINUTES, DOMAIN  # noqa: F401

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Loggamera switches based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    api = hass.data[DOMAIN][entry.entry_id]["api"]

    # Check if we have scenarios data
    if (
        not coordinator.data
        or "scenarios" not in coordinator.data
        or not coordinator.data["scenarios"]
    ):
        _LOGGER.info("No scenarios available")
        return

    # Create switch for each scenario
    switches = []
    for scenario in coordinator.data["scenarios"]:
        switch = LoggameraScenarioSwitch(coordinator, api, scenario, hass)
        switches.append(switch)

    if switches:
        async_add_entities(switches)
        _LOGGER.info(f"Adding {len(switches)} Loggamera scenario switches")


class LoggameraScenarioSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of a Loggamera scenario switch."""

    def __init__(self, coordinator, api, scenario, hass):
        """Initialize the switch."""
        super().__init__(coordinator)
        self._api = api
        self._scenario = scenario
        self._scenario_id = scenario["Id"]
        self._name = f"Scenario {scenario['Name']}"
        self._unique_id = f"scenario_{self._scenario_id}"
        self._is_on = False
        self._hass = hass

    @property
    def unique_id(self) -> str:
        """Return a unique ID for this entity."""
        return self._unique_id

    @property
    def name(self) -> str:
        """Return the name of the switch."""
        return self._name

    @property
    def is_on(self) -> bool:
        """Return true if the switch is on."""
        return self._is_on

    @property
    def available(self) -> bool:
        """Return if the switch is available."""
        return self.coordinator.last_update_success

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, f"scenario_{self._scenario_id}")},
            name=f"Scenario {self._scenario['Name']}",
            manufacturer="Loggamera",
            model="Scenario",
        )

    async def async_turn_on(self, **kwargs):
        """Turn on the switch."""
        try:
            # Use async_add_executor_job for the blocking API call
            result = await self._hass.async_add_executor_job(
                self._api.execute_scenario, self._scenario_id
            )

            if result and "Data" in result:
                self._is_on = True
                self.async_write_ha_state()

                # Auto turn off after a short delay
                async def async_turn_off_later():
                    """Turn off the switch after a delay."""
                    await asyncio.sleep(2)
                    self._is_on = False
                    self.async_write_ha_state()

                # Schedule turn off
                asyncio.create_task(async_turn_off_later())

        except LoggameraAPIError as err:
            _LOGGER.error(f"Failed to execute scenario: {err}")

    async def async_turn_off(self, **kwargs):
        """Turn off the switch."""
        # Scenarios don't actually have an off state,
        # they just run momentarily and then stop
        self._is_on = False
        self.async_write_ha_state()

    @property
    def extra_state_attributes(self) -> Optional[Dict[str, Any]]:
        """Return extra state attributes."""
        attrs = {}

        if self._scenario:
            attrs["scenario_id"] = self._scenario_id
            if "Description" in self._scenario:
                attrs["description"] = self._scenario["Description"]
            if "DurationMinutes" in self._scenario:
                attrs[ATTR_DURATION_MINUTES] = self._scenario["DurationMinutes"]

        return attrs
