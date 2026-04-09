"""Config flow for Proxon FWT Modbus."""
from __future__ import annotations
import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL
from .const import *

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_HOST): str,
    vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
    vol.Required(CONF_SLAVE, default=DEFAULT_SLAVE): int,
    vol.Required(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(int, vol.Range(min=5, max=300)),
    vol.Optional(CONF_T300_ENABLED, default=True): bool,
    vol.Optional(CONF_T300_SLAVE, default=DEFAULT_T300_SLAVE): int,
})

class ProxonModbusConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            await self.async_set_unique_id(f"proxon_{user_input[CONF_HOST]}")
            self._abort_if_unique_id_configured()
            try:
                from pymodbus.client import AsyncModbusTcpClient
                client = AsyncModbusTcpClient(host=user_input[CONF_HOST], port=user_input[CONF_PORT], timeout=5)
                connected = await client.connect()
                if connected:
                    result = await client.read_holding_registers(address=16, count=1, slave=user_input[CONF_SLAVE])
                    client.close()
                    if result.isError():
                        errors["base"] = "cannot_connect"
                    else:
                        return self.async_create_entry(title=f"Proxon FWT ({user_input[CONF_HOST]})", data=user_input)
                else:
                    errors["base"] = "cannot_connect"
            except Exception:
                errors["base"] = "unknown"
        return self.async_show_form(step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors)
