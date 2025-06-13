"""Button platform for Loggamera integration."""

import logging
from typing import Any, Dict, List, Optional

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import LoggameraAPIError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    """Set up Loggamera buttons based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    api = hass.data[DOMAIN][entry.entry_id]["api"]

    entities = []

    # Get scenarios from coordinator
    scenarios = coordinator.data.get("scenarios", [])

    if not scenarios:
        _LOGGER.debug("No scenarios found in coordinator data")
        return

    # Create button for each scenario
    for scenario in scenarios:
        scenario_id = scenario.get("Id")
        if not scenario_id:
            continue

        entities.append(
            LoggameraScenarioButton(
                coordinator=coordinator,
                api=api,
                scenario_id=scenario_id,
                scenario_name=scenario.get("Name", f"Scenario {scenario_id}"),
            )
        )

    if entities:
        async_add_entities(entities)
        _LOGGER.info(f"Added {len(entities)} Loggamera scenario buttons")


class LoggameraScenarioButton(CoordinatorEntity, ButtonEntity):
    """Representation of a Loggamera scenario button."""

    def __init__(self, coordinator, api, scenario_id, scenario_name):
        """Initialize the button."""
        super().__init__(coordinator)
        self.api = api
        self.scenario_id = scenario_id
        self.scenario_name = scenario_name

        # Entity attributes
        self._attr_unique_id = f"loggamera_scenario_{scenario_id}"
        self._attr_name = f"Execute {scenario_name}"

        # Device info - create a virtual device for scenarios
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"scenarios_{api.organization_id}")},
            name="Loggamera Scenarios",
            manufacturer="Loggamera",
            model="Scenarios",
        )

        _LOGGER.debug(f"Created scenario button: {self.name}")

    async def async_press(self) -> None:
        """Execute the scenario when the button is pressed."""
        try:
            _LOGGER.info(
                f"Executing scenario: {self.scenario_name} (ID: {self.scenario_id})"
            )
            await self.hass.async_add_executor_job(
                self.api.execute_scenario, self.scenario_id
            )
        except LoggameraAPIError as err:
            _LOGGER.error(f"Failed to execute scenario {self.scenario_id}: {err}")
