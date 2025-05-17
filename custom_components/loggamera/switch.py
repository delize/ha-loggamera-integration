"""Support for Loggamera switches."""
import asyncio
import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import LoggameraAPIError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Loggamera switches based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    # Get scenarios
    try:
        scenarios_response = await hass.async_add_executor_job(
            coordinator.api.get_scenarios
        )
        
        if scenarios_response.get("Data") and scenarios_response["Data"].get("Scenarios"):
            scenarios = scenarios_response["Data"]["Scenarios"]
            entities = []
            
            for scenario in scenarios:
                entities.append(
                    LoggameraScenarioSwitch(
                        coordinator,
                        scenario["Id"],
                        scenario["Name"],
                    )
                )
                
            async_add_entities(entities)
    except LoggameraAPIError as error:
        _LOGGER.error(f"Failed to get scenarios: {error}")

class LoggameraScenarioSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of a Loggamera scenario switch."""

    def __init__(
        self,
        coordinator,
        scenario_id,
        scenario_name,
    ):
        """Initialize the switch."""
        super().__init__(coordinator)
        self._scenario_id = scenario_id
        self._scenario_name = scenario_name
        
        # Set entity properties
        self._attr_name = f"Scenario {scenario_name}"
        self._attr_unique_id = f"loggamera_scenario_{scenario_id}"
        self._attr_icon = "mdi:script-text-outline"
        self._is_on = False

    @property
    def device_info(self):
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, f"scenarios")},
            "name": "Loggamera Scenarios",
            "manufacturer": "Loggamera",
            "model": "Scenarios",
        }

    @property
    def is_on(self):
        """Return true if the switch is on."""
        return self._is_on

    async def async_turn_on(self, **kwargs):
        """Turn on the switch."""
        try:
            await self.hass.async_add_executor_job(
                self.coordinator.api.execute_scenario, self._scenario_id
            )
            self._is_on = True
            self.async_write_ha_state()
            
            # Reset after 5 seconds (scenarios are momentary)
            async def reset_switch_state():
                await asyncio.sleep(5)
                self._is_on = False
                self.async_write_ha_state()
                
            self.hass.async_create_task(reset_switch_state())
        except LoggameraAPIError as error:
            _LOGGER.error(f"Failed to execute scenario {self._scenario_name}: {error}")

    async def async_turn_off(self, **kwargs):
        """Turn off the switch."""
        # Scenarios can't be turned off, they're just triggered
        self._is_on = False
        self.async_write_ha_state()