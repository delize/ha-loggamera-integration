"""Support for Loggamera switches."""
import logging
from typing import Any, Dict, List, Optional, Callable

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .api import LoggameraAPI, LoggameraAPIError
from .const import DOMAIN, ATTR_DEVICE_TYPE, ATTR_DURATION_MINUTES

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Loggamera switches based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    api = hass.data[DOMAIN][entry.entry_id]["api"]
    
    try:
        # Try to force a refresh to get latest data
        await coordinator.async_refresh()
    except Exception as err:
        _LOGGER.error(f"Error refreshing coordinator: {err}")
        # Continue with available data or none
    
    switches = []
    
    # Get scenarios from coordinator data
    if not coordinator.data or "scenarios" not in coordinator.data:
        _LOGGER.info("No scenarios found in coordinator data")
        return
    
    scenarios = coordinator.data.get("scenarios", [])
    
    if not scenarios:
        _LOGGER.info("No scenarios available")
        return
    
    # Create a switch for each scenario
    for scenario in scenarios:
        switches.append(
            LoggameraScenarioSwitch(
                coordinator,
                api,
                scenario,
            )
        )
    
    if switches:
        _LOGGER.info(f"Adding {len(switches)} Loggamera scenario switches")
        async_add_entities(switches)


class LoggameraScenarioSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of a Loggamera scenario switch."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        api: LoggameraAPI,
        scenario: Dict[str, Any],
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        
        self._api = api
        self._scenario_id = scenario["Id"]
        self._scenario_name = scenario["Name"]
        self._is_on = False  # Scenarios don't have a persistent state
        
        # Generate a unique ID for the switch
        self._attr_unique_id = f"{DOMAIN}_scenario_{self._scenario_id}"
        
        # Set name
        self._attr_name = f"Scenario: {self._scenario_name}"
        
        # Set device info - use organization as the "device"
        org_id = self._api.organization_id
        self._attr_device_info = {
            "identifiers": {(DOMAIN, f"org_{org_id}")},
            "name": f"Loggamera Organization {org_id}",
            "manufacturer": "Loggamera",
            "model": "Organization",
        }
        
        # Set extra attributes
        self._attr_extra_state_attributes = {
            "scenario_id": self._scenario_id,
            "scenario_name": self._scenario_name,
        }

    @property
    def is_on(self) -> bool:
        """Return true if the switch is on."""
        return self._is_on

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on by executing the scenario."""
        duration_minutes = kwargs.get(ATTR_DURATION_MINUTES)
        
        try:
            await self.hass.async_add_executor_job(
                self._api.execute_scenario, self._scenario_id, duration_minutes
            )
            self._is_on = True
            self.async_write_ha_state()
            
            # Set state back to off after a short delay
            def set_state_to_off():
                self._is_on = False
                self.async_write_ha_state()
            
            self.hass.helpers.event.async_call_later(2, lambda _: set_state_to_off())
            
        except LoggameraAPIError as err:
            _LOGGER.error(f"Failed to execute scenario: {err}")

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off - not supported for scenarios."""
        # Scenarios can't be turned off directly
        self._is_on = False
        self.async_write_ha_state()