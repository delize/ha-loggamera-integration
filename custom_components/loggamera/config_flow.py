"""Config flow for Loggamera integration."""
import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.const import CONF_NAME

from .api import LoggameraAPI, LoggameraAPIError
from .const import DOMAIN, CONF_API_KEY, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

class LoggameraConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Loggamera."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            api_key = user_input[CONF_API_KEY]

            try:
                # Test API connection
                api = LoggameraAPI(api_key)
                await self.hass.async_add_executor_job(api.get_organizations)

                # If no error is raised, the connection is successful
                return self.async_create_entry(
                    title="Loggamera",
                    data={
                        CONF_API_KEY: api_key,
                    },
                )
            except LoggameraAPIError as error:
                _LOGGER.error(f"Failed to connect to Loggamera API: {error}")
                errors["base"] = "cannot_connect"

        # Show form
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
        return LoggameraOptionsFlowHandler(config_entry)

class LoggameraOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle Loggamera options."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        default=self.config_entry.options.get(
                            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                        ),
                    ): int,
                }
            ),
        )