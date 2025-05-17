from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from .const import DOMAIN, CONF_API_KEY

class LoggameraConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self):
        super().__init__()
        self.api_key = None

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            self.api_key = user_input[CONF_API_KEY]
            return self.async_create_entry(title="Loggamera", data={"api_key": self.api_key})

        return self.async_show_form(step_id="user", data_schema=self._get_schema())

    def _get_schema(self):
        from homeassistant.helpers import config_entry_flow
        from homeassistant.helpers import schema

        return schema.Schema({
            schema.string(CONF_API_KEY): schema.string("API Key"),
        })