import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
import logging

from .helpers import fetch_organizations, fetch_devices

_LOGGER = logging.getLogger(__name__)

DOMAIN = "loggamera"

# Schemas for the forms:
STEP_USER_DATA_SCHEMA = vol.Schema({
    vol.Required("api_key"): str,
})

def organizations_schema(org_list):
    """Build a schema for organization selection based on API data."""
    options = {org["Id"]: org["Name"] for org in org_list}
    return vol.Schema({
        vol.Required("organization_id"): vol.In(options)
    })

def devices_schema(device_list):
    """Build a schema for device selection based on API data."""
    options = {device["Id"]: f'{device.get("Title") or device["Id"]} ({device["Class"]})' for device in device_list}
    return vol.Schema({
        vol.Required("device_id"): vol.In(options)
    })

class LoggameraConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle user step for entering API key."""
        if user_input is not None:
            self.api_key = user_input["api_key"]
            try:
                organizations = await fetch_organizations(self.hass, self.api_key)
                if not organizations:
                    return self.async_abort(reason="no_organizations_found")
                self.organizations = organizations
                return await self.async_step_org_select()
            except Exception as e:
                _LOGGER.error("Error validating API Key: %s", e)
                return self.async_abort(reason="invalid_api_key")
                
        return self.async_show_form(step_id="user", data_schema=STEP_USER_DATA_SCHEMA)

    async def async_step_org_select(self, user_input=None):
        """Select organization after API key is validated."""
        if user_input is not None:
            self.selected_org = user_input["organization_id"]
            devices = await fetch_devices(self.hass, self.api_key, self.selected_org)
            if not devices:
                return self.async_abort(reason="no_devices_found")
            self.devices = devices
            return await self.async_step_device_select()
            
        return self.async_show_form(
            step_id="org_select",
            data_schema=organizations_schema(self.organizations)
        )

    async def async_step_device_select(self, user_input=None):
        """Select device after organization is chosen."""
        if user_input is not None:
            return self.async_create_entry(
                title="Loggamera",
                data={
                    "api_key": self.api_key,
                    "organization_id": self.selected_org,
                    "device_id": user_input["device_id"],
                }
            )
        return self.async_show_form(
            step_id="device_select",
            data_schema=devices_schema(self.devices)
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return LoggameraOptionsFlow(config_entry)

class LoggameraOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry
        
    async def async_step_init(self, user_input=None):
        # Your options logic here if you need to change configuration.
        return self.async_show_form(step_id="init")