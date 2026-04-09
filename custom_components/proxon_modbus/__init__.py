"""The Proxon FWT Modbus integration."""
from __future__ import annotations
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from .const import (
    DOMAIN, DEFAULT_PORT, DEFAULT_SLAVE, DEFAULT_T300_SLAVE,
    DEFAULT_SCAN_INTERVAL, CONF_SLAVE, CONF_T300_ENABLED, CONF_T300_SLAVE,
)
from .hub import ProxonModbusHub

_LOGGER = logging.getLogger(__name__)
PLATFORMS_LIST = [
    Platform.SENSOR, Platform.SWITCH, Platform.CLIMATE,
    Platform.NUMBER, Platform.SELECT,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Proxon FWT from a config entry."""
    hub = ProxonModbusHub(
        hass=hass,
        host=entry.data[CONF_HOST],
        port=entry.data.get(CONF_PORT, DEFAULT_PORT),
        slave=entry.data.get(CONF_SLAVE, DEFAULT_SLAVE),
        t300_enabled=entry.data.get(CONF_T300_ENABLED, False),
        t300_slave=entry.data.get(CONF_T300_SLAVE, DEFAULT_T300_SLAVE),
        scan_interval=entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
    )

    try:
        if not await hub.async_connect():
            raise ConfigEntryNotReady(
                f"Cannot connect to Proxon Modbus at "
                f"{entry.data[CONF_HOST]}:{entry.data.get(CONF_PORT, DEFAULT_PORT)}"
            )
    except Exception as err:
        raise ConfigEntryNotReady(
            f"Error connecting to Proxon: {err}"
        ) from err

    try:
        await hub.coordinator.async_config_entry_first_refresh()
    except Exception as err:
        await hub.async_close()
        raise ConfigEntryNotReady(
            f"Error fetching initial data from Proxon: {err}"
        ) from err

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = hub
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS_LIST)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS_LIST)
    if ok:
        hub = hass.data[DOMAIN].pop(entry.entry_id)
        await hub.async_close()
    return ok


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)
