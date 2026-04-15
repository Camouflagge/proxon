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
    CONF_TYPE, TYPE_TCP, TYPE_SERIAL,
    CONF_DEVICE, CONF_BAUDRATE, CONF_BYTESIZE, CONF_METHOD, CONF_PARITY, CONF_STOPBITS,
    DEFAULT_DEVICE, DEFAULT_BAUDRATE, DEFAULT_BYTESIZE, DEFAULT_METHOD,
    DEFAULT_PARITY, DEFAULT_STOPBITS,
)
from .hub import ProxonModbusHub

_LOGGER = logging.getLogger(__name__)
PLATFORMS_LIST = [
    Platform.SENSOR, Platform.SWITCH, Platform.CLIMATE,
    Platform.NUMBER, Platform.SELECT,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Proxon FWT from a config entry."""
    conn_type = entry.data.get(CONF_TYPE, TYPE_TCP)
    hub = ProxonModbusHub(
        hass=hass,
        conn_type=conn_type,
        slave=entry.data.get(CONF_SLAVE, DEFAULT_SLAVE),
        t300_enabled=entry.data.get(CONF_T300_ENABLED, False),
        t300_slave=entry.data.get(CONF_T300_SLAVE, DEFAULT_T300_SLAVE),
        scan_interval=entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        # TCP
        host=entry.data.get(CONF_HOST),
        port=entry.data.get(CONF_PORT, DEFAULT_PORT),
        # Serial
        device=entry.data.get(CONF_DEVICE, DEFAULT_DEVICE),
        baudrate=entry.data.get(CONF_BAUDRATE, DEFAULT_BAUDRATE),
        bytesize=entry.data.get(CONF_BYTESIZE, DEFAULT_BYTESIZE),
        method=entry.data.get(CONF_METHOD, DEFAULT_METHOD),
        parity=entry.data.get(CONF_PARITY, DEFAULT_PARITY),
        stopbits=entry.data.get(CONF_STOPBITS, DEFAULT_STOPBITS),
    )

    # Restore previously-discovered rooms from the config entry cache so
    # the platforms see the correct list on first refresh. If the entry
    # has no cached rooms yet (fresh install), the hub.rooms property
    # falls back to the ALWAYS_ACTIVE_SLOTS defaults until
    # async_discover_rooms succeeds below.
    cached_rooms = entry.data.get("rooms") or []
    if cached_rooms:
        hub.set_discovered_rooms(cached_rooms)

    try:
        if not await hub.async_connect():
            raise ConfigEntryNotReady(
                f"Cannot connect to Proxon Modbus ({hub._describe()})"
            )
    except Exception as err:
        raise ConfigEntryNotReady(
            f"Error connecting to Proxon: {err}"
        ) from err

    # Run discovery once per setup. This reads the name blocks from the
    # device and updates hub._discovered_rooms. If it fails for any reason
    # we fall back to whatever was cached in the entry (or, failing that,
    # the ALWAYS_ACTIVE_SLOTS defaults) – setup continues either way.
    try:
        discovered = await hub.async_discover_rooms()
    except Exception as err:  # noqa: BLE001
        _LOGGER.warning(
            "Proxon: panel discovery failed (%s) – continuing with cached/default rooms",
            err,
        )
        discovered = []

    if discovered and discovered != cached_rooms:
        _LOGGER.info(
            "Proxon: persisting %d discovered panels to config entry",
            len(discovered),
        )
        hass.config_entries.async_update_entry(
            entry, data={**entry.data, "rooms": discovered},
        )

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
