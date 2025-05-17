# This file initializes the Loggamera integration package. It typically contains setup functions and may define the integration's domain.

DOMAIN = "loggamera"

async def async_setup(hass, config):
    """Set up the Loggamera integration."""
    hass.data[DOMAIN] = {}
    return True

async def async_setup_entry(hass, entry):
    """Set up a config entry for Loggamera."""
    hass.data[DOMAIN][entry.entry_id] = entry.data
    return True

async def async_unload_entry(hass, entry):
    """Unload a config entry."""
    hass.data[DOMAIN].pop(entry.entry_id)
    return True