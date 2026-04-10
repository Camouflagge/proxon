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


def _build_schema(defaults: dict | None = None) -> vol.Schema:
    """Build the config/reconfigure schema, optionally pre-filled with defaults."""
    d = defaults or {}
    return vol.Schema({
        vol.Required(CONF_HOST, default=d.get(CONF_HOST, vol.UNDEFINED)): str,
        vol.Required(CONF_PORT, default=d.get(CONF_PORT, DEFAULT_PORT)): int,
        vol.Required(CONF_SLAVE, default=d.get(CONF_SLAVE, DEFAULT_SLAVE)): int,
        vol.Required(
            CONF_SCAN_INTERVAL,
            default=d.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        ): vol.All(int, vol.Range(min=1, max=60)),
        vol.Optional(CONF_T300_ENABLED, default=d.get(CONF_T300_ENABLED, True)): bool,
        vol.Optional(
            CONF_T300_SLAVE, default=d.get(CONF_T300_SLAVE, DEFAULT_T300_SLAVE)
        ): int,
    })


class ProxonModbusConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Proxon FWT Modbus."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Initial setup step."""
        if user_input is not None:
            await self.async_set_unique_id(f"proxon_{user_input[CONF_HOST]}")
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=f"Proxon FWT ({user_input[CONF_HOST]})",
                data=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=_build_schema(),
        )

    async def async_step_reconfigure(self, user_input=None):
        """Handle reconfiguration of an existing entry."""
        entry = self._get_reconfigure_entry()

        if user_input is not None:
            # Update unique_id if host changed
            new_uid = f"proxon_{user_input[CONF_HOST]}"
            await self.async_set_unique_id(new_uid)
            self._abort_if_unique_id_mismatch(reason="already_configured")

            return self.async_update_reload_and_abort(
                entry,
                data_updates=user_input,
                title=f"Proxon FWT ({user_input[CONF_HOST]})",
            )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=_build_schema(dict(entry.data)),
        )
