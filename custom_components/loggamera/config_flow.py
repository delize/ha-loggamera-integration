"""Config flow for Loggamera integration."""
import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorOption,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
)

from .api import LoggameraAPI, LoggameraAPIError
from .const import (
    DOMAIN,
    CONF_API_KEY,
    CONF_ORGANIZATION_ID,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


async def validate_api_key(hass: HomeAssistant, api_key: str) -> dict:
    """Validate the API key by trying to fetch organizations."""
    api = LoggameraAPI(api_key)
    
    try:
        org_response = await hass.async_add_executor_job(api.get_organizations)
        
        if "Data" not in org_response or "Organizations" not in org_response["Data"]:
            raise InvalidAuth("Failed to fetch organizations")
        
        organizations = org_response["Data"]["Organizations"]
        if not organizations:
            _LOGGER.warning("No organizations available for this API key")
        
        return {"organizations": organizations}
        
    except LoggameraAPIError as err:
        _LOGGER.error(f"Error validating API key: {err}")
        if "access denied" in str(err).lower():
            raise InvalidAuth("Invalid API key")
        raise CannotConnect(f"Failed to connect to Loggamera API: {err}")


class LoggameraConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Loggamera."""

    VERSION = 1

    def __init__(self):
        """Initialize."""
        self.api_key = None
        self.organizations = None
        self.selected_organization_id = None

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            try:
                api_key = user_input[CONF_API_KEY]
                
                info = await validate_api_key(self.hass, api_key)
                self.api_key = api_key
                self.organizations = info.get("organizations", [])
                
                # If only one organization, use it automatically
                if len(self.organizations) == 1:
                    self.selected_organization_id = self.organizations[0]["Id"]
                    return self.async_create_entry(
                        title="Loggamera",
                        data={
                            CONF_API_KEY: self.api_key,
                            CONF_ORGANIZATION_ID: self.selected_organization_id,
                        },
                    )
                
                # If multiple organizations, move to organization selection step
                elif len(self.organizations) > 1:
                    return await self.async_step_organization()
                else:
                    # No organizations but API key works - proceed anyway
                    return self.async_create_entry(
                        title="Loggamera",
                        data={
                            CONF_API_KEY: self.api_key,
                        },
                    )
                
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_API_KEY): str,
                }
            ),
            errors=errors,
        )

    async def async_step_organization(self, user_input=None) -> FlowResult:
        """Handle organization selection."""
        errors = {}

        if user_input is not None:
            try:
                self.selected_organization_id = user_input[CONF_ORGANIZATION_ID]
                
                return self.async_create_entry(
                    title="Loggamera",
                    data={
                        CONF_API_KEY: self.api_key,
                        CONF_ORGANIZATION_ID: self.selected_organization_id,
                    },
                )
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        options = []
        for org in self.organizations:
            options.append(
                SelectSelectorOption(
                    value=str(org["Id"]),
                    label=f"{org['Name']} (ID: {org['Id']})",
                )
            )

        return self.async_show_form(
            step_id="organization",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ORGANIZATION_ID): SelectSelector(
                        SelectSelectorConfig(options=options)
                    ),
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

        # Creating scan interval options with guidance about PowerMeter update frequency
        scan_interval_options = {
            vol.Optional(
                CONF_SCAN_INTERVAL,
                default=self.config_entry.options.get(
                    CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                ),
            ): NumberSelector(
                NumberSelectorConfig(
                    min=300,  # 5 minutes minimum
                    max=3600,  # 1 hour maximum
                    step=60,   # 1 minute increments
                    mode=NumberSelectorMode.BOX,
                    unit_of_measurement="seconds"
                )
            ),
        }

        return self.async_show_form(
            step_id="init", 
            data_schema=vol.Schema(scan_interval_options),
            description_placeholders={
                "update_frequency": "The PowerMeter endpoint updates approximately every 30 minutes. A scan interval of 20 minutes (1200 seconds) is recommended to balance timely updates with API efficiency."
            },
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""