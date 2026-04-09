"""Config flow for Proxon FWT Modbus."""
from __future__ import annotations
import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL
from .const import (
    DOMAIN, DEFAULT_PORT, DEFAULT_SLAVE, DEFAULT_T300_SLAVE,
    DEFAULT_SCAN_INTERVAL, CONF_SLAVE, CONF_T300_ENABLED, CONF_T300_SLAVE,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_HOST): str,
    vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
    vol.Required(CONF_SLAVE, default=DEFAULT_SLAVE): int,
    vol.Required(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
        int, vol.Range(min=5, max=300)
    ),
    vol.Optional(CONF_T300_ENABLED, default=True): bool,
    vol.Optional(CONF_T300_SLAVE, default=DEFAULT_T300_SLAVE): int,
})


class ProxonModbusConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Proxon FWT Modbus."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step.
        
        No connection test here — the actual connection is tested
        during async_setup_entry in __init__.py. If it fails there,
        HA will show the integration as "setup_retry" with the error.
        This is the standard pattern for most HA integrations.
        """
        if user_input is not None:
            await self.async_set_unique_id(f"proxon_{user_input[CONF_HOST]}")
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=f"Proxon FWT ({user_input[CONF_HOST]})",
                data=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
        )
