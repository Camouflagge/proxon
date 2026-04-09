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
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Check if already configured
            await self.async_set_unique_id(f"proxon_{user_input[CONF_HOST]}")
            self._abort_if_unique_id_configured()

            # Test connection
            can_connect = await self._test_connection(
                user_input[CONF_HOST],
                user_input[CONF_PORT],
                user_input[CONF_SLAVE],
            )

            if can_connect:
                return self.async_create_entry(
                    title=f"Proxon FWT ({user_input[CONF_HOST]})",
                    data=user_input,
                )
            else:
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def _test_connection(self, host: str, port: int, slave: int) -> bool:
        """Test the Modbus TCP connection."""
        try:
            from pymodbus.client import AsyncModbusTcpClient

            client = AsyncModbusTcpClient(host=host, port=port, timeout=5)
            connected = await client.connect()

            if not connected:
                _LOGGER.error(
                    "Proxon: Could not connect to %s:%s", host, port
                )
                return False

            try:
                # Try to read Betriebsart register (16) as connection test
                result = await client.read_holding_registers(
                    address=16, count=1, slave=slave
                )
                if result.isError():
                    _LOGGER.error(
                        "Proxon: Connected but register read failed: %s", result
                    )
                    return False

                _LOGGER.info(
                    "Proxon: Connection test OK. Betriebsart = %s",
                    result.registers[0],
                )
                return True

            finally:
                client.close()

        except Exception as err:
            _LOGGER.error("Proxon: Connection test failed: %s", err)
            return False
