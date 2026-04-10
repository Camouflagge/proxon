"""Config flow for Proxon FWT Modbus (TCP + Serial/RTU)."""
from __future__ import annotations
import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL
from homeassistant.helpers.selector import (
    SelectSelector, SelectSelectorConfig, SelectSelectorMode,
)

from .const import (
    DOMAIN, DEFAULT_PORT, DEFAULT_SLAVE, DEFAULT_T300_SLAVE,
    DEFAULT_SCAN_INTERVAL, CONF_SLAVE, CONF_T300_ENABLED, CONF_T300_SLAVE,
    CONF_TYPE, TYPE_TCP, TYPE_RTUOVERTCP, TYPE_SERIAL, CONNECTION_TYPES,
    CONF_DEVICE, CONF_BAUDRATE, CONF_BYTESIZE, CONF_METHOD, CONF_PARITY, CONF_STOPBITS,
    DEFAULT_DEVICE, DEFAULT_BAUDRATE, DEFAULT_BYTESIZE, DEFAULT_METHOD,
    DEFAULT_PARITY, DEFAULT_STOPBITS,
    BAUDRATE_OPTIONS, BYTESIZE_OPTIONS, METHOD_OPTIONS, PARITY_OPTIONS, STOPBITS_OPTIONS,
)

_LOGGER = logging.getLogger(__name__)


def _type_selector() -> SelectSelector:
    return SelectSelector(
        SelectSelectorConfig(
            options=CONNECTION_TYPES,
            mode=SelectSelectorMode.DROPDOWN,
            translation_key="connection_type",
        )
    )


def _str_select(options: list[str], translation_key: str) -> SelectSelector:
    return SelectSelector(
        SelectSelectorConfig(
            options=options,
            mode=SelectSelectorMode.DROPDOWN,
            translation_key=translation_key,
        )
    )


def _int_select(options: list[int]) -> SelectSelector:
    return SelectSelector(
        SelectSelectorConfig(
            options=[str(o) for o in options],
            mode=SelectSelectorMode.DROPDOWN,
        )
    )


def _common_fields(d: dict) -> dict:
    """Common fields that are always present (slave, scan_interval, T300)."""
    return {
        vol.Required(CONF_SLAVE, default=d.get(CONF_SLAVE, DEFAULT_SLAVE)): int,
        vol.Required(
            CONF_SCAN_INTERVAL,
            default=d.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        ): vol.All(int, vol.Range(min=1, max=60)),
        vol.Optional(CONF_T300_ENABLED, default=d.get(CONF_T300_ENABLED, True)): bool,
        vol.Optional(
            CONF_T300_SLAVE, default=d.get(CONF_T300_SLAVE, DEFAULT_T300_SLAVE)
        ): int,
    }


def _tcp_schema(d: dict | None = None) -> vol.Schema:
    d = d or {}
    return vol.Schema({
        vol.Required(CONF_HOST, default=d.get(CONF_HOST, vol.UNDEFINED)): str,
        vol.Required(CONF_PORT, default=d.get(CONF_PORT, DEFAULT_PORT)): int,
        **_common_fields(d),
    })


def _serial_schema(d: dict | None = None) -> vol.Schema:
    d = d or {}
    return vol.Schema({
        vol.Required(CONF_DEVICE, default=d.get(CONF_DEVICE, DEFAULT_DEVICE)): str,
        vol.Required(
            CONF_BAUDRATE, default=str(d.get(CONF_BAUDRATE, DEFAULT_BAUDRATE)),
        ): _int_select(BAUDRATE_OPTIONS),
        vol.Required(
            CONF_BYTESIZE, default=str(d.get(CONF_BYTESIZE, DEFAULT_BYTESIZE)),
        ): _int_select(BYTESIZE_OPTIONS),
        vol.Required(
            CONF_METHOD, default=d.get(CONF_METHOD, DEFAULT_METHOD),
        ): _str_select(METHOD_OPTIONS, "method"),
        vol.Required(
            CONF_PARITY, default=d.get(CONF_PARITY, DEFAULT_PARITY),
        ): _str_select(PARITY_OPTIONS, "parity"),
        vol.Required(
            CONF_STOPBITS, default=str(d.get(CONF_STOPBITS, DEFAULT_STOPBITS)),
        ): _int_select(STOPBITS_OPTIONS),
        **_common_fields(d),
    })


def _normalize_serial(user_input: dict) -> dict:
    """Convert string dropdown values back to int where needed."""
    out = dict(user_input)
    for k in (CONF_BAUDRATE, CONF_BYTESIZE, CONF_STOPBITS):
        if k in out:
            try:
                out[k] = int(out[k])
            except (TypeError, ValueError):
                pass
    return out


def _unique_id_for(data: dict) -> str:
    t = data.get(CONF_TYPE)
    if t == TYPE_SERIAL:
        return f"proxon_serial_{data.get(CONF_DEVICE, '')}"
    if t == TYPE_RTUOVERTCP:
        return f"proxon_rtuovertcp_{data.get(CONF_HOST, '')}"
    return f"proxon_tcp_{data.get(CONF_HOST, '')}"


def _title_for(data: dict) -> str:
    t = data.get(CONF_TYPE)
    if t == TYPE_SERIAL:
        return f"Proxon FWT ({data.get(CONF_DEVICE, 'serial')})"
    if t == TYPE_RTUOVERTCP:
        return f"Proxon FWT RTU-over-TCP ({data.get(CONF_HOST, 'tcp')})"
    return f"Proxon FWT ({data.get(CONF_HOST, 'tcp')})"


class ProxonModbusConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Proxon FWT Modbus."""

    VERSION = 1

    def __init__(self) -> None:
        self._conn_type: str | None = None

    # ─────────── Initial Setup ───────────

    async def async_step_user(self, user_input=None):
        """First step: choose connection type."""
        if user_input is not None:
            self._conn_type = user_input[CONF_TYPE]
            if self._conn_type == TYPE_SERIAL:
                return await self.async_step_serial()
            if self._conn_type == TYPE_RTUOVERTCP:
                return await self.async_step_rtuovertcp()
            return await self.async_step_tcp()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_TYPE, default=TYPE_TCP): _type_selector(),
            }),
        )

    async def async_step_tcp(self, user_input=None):
        if user_input is not None:
            data = {CONF_TYPE: TYPE_TCP, **user_input}
            await self.async_set_unique_id(_unique_id_for(data))
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=_title_for(data), data=data)

        return self.async_show_form(step_id="tcp", data_schema=_tcp_schema())

    async def async_step_rtuovertcp(self, user_input=None):
        if user_input is not None:
            data = {CONF_TYPE: TYPE_RTUOVERTCP, **user_input}
            await self.async_set_unique_id(_unique_id_for(data))
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=_title_for(data), data=data)

        return self.async_show_form(step_id="rtuovertcp", data_schema=_tcp_schema())

    async def async_step_serial(self, user_input=None):
        if user_input is not None:
            data = {CONF_TYPE: TYPE_SERIAL, **_normalize_serial(user_input)}
            await self.async_set_unique_id(_unique_id_for(data))
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=_title_for(data), data=data)

        return self.async_show_form(step_id="serial", data_schema=_serial_schema())

    # ─────────── Reconfigure ───────────

    async def async_step_reconfigure(self, user_input=None):
        """Entry point for reconfiguration — pick type, prefilled."""
        entry = self._get_reconfigure_entry()
        current_type = entry.data.get(CONF_TYPE, TYPE_TCP)

        if user_input is not None:
            self._conn_type = user_input[CONF_TYPE]
            if self._conn_type == TYPE_SERIAL:
                return await self.async_step_reconfigure_serial()
            if self._conn_type == TYPE_RTUOVERTCP:
                return await self.async_step_reconfigure_rtuovertcp()
            return await self.async_step_reconfigure_tcp()

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema({
                vol.Required(CONF_TYPE, default=current_type): _type_selector(),
            }),
        )

    async def async_step_reconfigure_tcp(self, user_input=None):
        entry = self._get_reconfigure_entry()
        if user_input is not None:
            data = {CONF_TYPE: TYPE_TCP, **user_input}
            await self.async_set_unique_id(_unique_id_for(data))
            self._abort_if_unique_id_mismatch(reason="already_configured")
            return self.async_update_reload_and_abort(
                entry, data=data, title=_title_for(data),
            )

        # Prefill: use existing data if same type, otherwise defaults.
        # rtuovertcp uses the same fields, so we can also prefill from there.
        defaults = (
            dict(entry.data)
            if entry.data.get(CONF_TYPE) in (TYPE_TCP, TYPE_RTUOVERTCP)
            else {}
        )
        return self.async_show_form(
            step_id="reconfigure_tcp", data_schema=_tcp_schema(defaults),
        )

    async def async_step_reconfigure_rtuovertcp(self, user_input=None):
        entry = self._get_reconfigure_entry()
        if user_input is not None:
            data = {CONF_TYPE: TYPE_RTUOVERTCP, **user_input}
            await self.async_set_unique_id(_unique_id_for(data))
            self._abort_if_unique_id_mismatch(reason="already_configured")
            return self.async_update_reload_and_abort(
                entry, data=data, title=_title_for(data),
            )

        defaults = (
            dict(entry.data)
            if entry.data.get(CONF_TYPE) in (TYPE_RTUOVERTCP, TYPE_TCP)
            else {}
        )
        return self.async_show_form(
            step_id="reconfigure_rtuovertcp", data_schema=_tcp_schema(defaults),
        )

    async def async_step_reconfigure_serial(self, user_input=None):
        entry = self._get_reconfigure_entry()
        if user_input is not None:
            data = {CONF_TYPE: TYPE_SERIAL, **_normalize_serial(user_input)}
            await self.async_set_unique_id(_unique_id_for(data))
            self._abort_if_unique_id_mismatch(reason="already_configured")
            return self.async_update_reload_and_abort(
                entry, data=data, title=_title_for(data),
            )

        defaults = dict(entry.data) if entry.data.get(CONF_TYPE) == TYPE_SERIAL else {}
        return self.async_show_form(
            step_id="reconfigure_serial", data_schema=_serial_schema(defaults),
        )
