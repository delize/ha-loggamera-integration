"""Config flow for Loggamera integration."""
import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback

from .api import LoggameraAPI, LoggameraAPIError
from .const import (
    DOMAIN,
    CONF_API_KEY,
    CONF_SCAN_INTERVAL,
    CONF_ORGANIZATION_ID,
    DEFAULT_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


class LoggameraConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Loggamera."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            api_key = user_input[CONF_API_KEY]
            
            try:
                # Create API client
                api = LoggameraAPI(api_key)
                
                # Test connection by getting organizations
                org_data = await self.hass.async_add_executor_job(api.get_organizations)
                
                # Get first organization ID if available
                organization_id = None
                if "Data" in org_data and "Organizations" in org_data["Data"]:
                    orgs = org_data["Data"]["Organizations"]
                    if orgs:
                        organization_id = orgs[0]["Id"]
                        _LOGGER.info("Found organization ID")
                
                # Save the data and create entry
                entry_data = {CONF_API_KEY: api_key}
                if organization_id:
                    entry_data[CONF_ORGANIZATION_ID] = organization_id
                
                return self.async_create_entry(
                    title="Loggamera",
                    data=entry_data,
                )
                
            except LoggameraAPIError as err:
                _LOGGER.error(f"Failed to connect to Loggamera API: {err}")
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_API_KEY): str,
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return LoggameraOptionsFlow(config_entry)


class LoggameraOptionsFlow(config_entries.OptionsFlow):
    """Handle Loggamera options."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = {
            vol.Optional(
                CONF_SCAN_INTERVAL,
                default=self.config_entry.options.get(
                    CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                ),
            ): vol.All(vol.Coerce(int), vol.Range(min=300, max=3600)),
        }

        return self.async_show_form(
            step_id="init", 
            data_schema=vol.Schema(options),
            description_placeholders={
                "update_frequency": "The PowerMeter endpoint updates approximately every 30 minutes. A scan interval of 20 minutes (1200 seconds) is recommended to balance timely updates with API efficiency."
            },
        )