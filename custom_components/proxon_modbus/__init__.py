"""The Proxon FWT Modbus integration."""
from __future__ import annotations
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import entity_registry as er
from .const import (
    DOMAIN, DEFAULT_PORT, DEFAULT_SLAVE, DEFAULT_T300_SLAVE,
    DEFAULT_SCAN_INTERVAL, CONF_SLAVE, CONF_T300_ENABLED, CONF_T300_SLAVE,
    CONF_TYPE, TYPE_TCP, TYPE_SERIAL,
    CONF_DEVICE, CONF_BAUDRATE, CONF_BYTESIZE, CONF_METHOD, CONF_PARITY, CONF_STOPBITS,
    DEFAULT_DEVICE, DEFAULT_BAUDRATE, DEFAULT_BYTESIZE, DEFAULT_METHOD,
    DEFAULT_PARITY, DEFAULT_STOPBITS,
    LEGACY_KEY_TO_SLOT_KEY,
)
from .hub import ProxonModbusHub

_LOGGER = logging.getLogger(__name__)
PLATFORMS_LIST = [
    Platform.SENSOR, Platform.SWITCH, Platform.CLIMATE,
    Platform.NUMBER, Platform.SELECT,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Proxon FWT from a config entry."""
    # Migrate v1.8.x entities (wohnzimmer/kind_vorne/…) to v1.9.x slot keys
    # (zbp/hnbe/nb1/…) BEFORE platforms are set up, so their async_setup_entry
    # finds the already-renamed entities in the registry.
    await _async_migrate_entity_unique_ids(hass, entry)

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
    # has no cached rooms yet (fresh install or upgrade from v1.8.x), the
    # hub.rooms property falls back to the ALWAYS_ACTIVE_SLOTS defaults
    # until async_discover_rooms succeeds below.
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

    # Only persist the new discovery result if it is at least as complete as
    # the cached list. A partial result (fewer rooms than before) means some
    # reads failed – in that case we keep the cache so no room is silently
    # lost. A WARNING is logged so the user knows the result was discarded.
    if discovered and discovered != cached_rooms:
        if len(discovered) < len(cached_rooms):
            _LOGGER.warning(
                "Proxon: discovery returned %d panel(s) but cache has %d – "
                "keeping cached rooms to avoid data loss (partial read?)",
                len(discovered), len(cached_rooms),
            )
        else:
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


async def _async_migrate_entity_unique_ids(
    hass: HomeAssistant, entry: ConfigEntry,
) -> None:
    """Rename legacy v1.8.x unique_ids to the new stable slot keys.

    In v1.8.x the per-room entities were keyed by user-facing names like
    `wohnzimmer`, `kind_vorne`, `diele`, `kind_hinten`, `schlafzimmer`. In
    v1.9.x they are keyed by the slot-derived stable IDs `zbp`, `hnbe`,
    `nb1`, `nb3`, `nb4`. Without migration, HA would delete the old
    entities (breaking history and automations) and create new ones.

    For each affected unique_id prefix, this walks the entity registry
    and rewrites the unique_id in place. The user-facing entity_id is
    *not* touched, so existing dashboard/automation references keep
    working. The platforms used by the affected rooms are:

        sensor:  temp_*, offset_*, mitte_*, proxon_filter_*
        switch:  proxon_heiz_*
        climate: proxon_climate_*
        number:  proxon_mitte_*_nr
    """
    registry = er.async_get(hass)
    # Collect the mapping once so we can iterate registry entries in a
    # single pass. Each tuple is (old_unique_id, new_unique_id).
    renames: list[tuple[str, str]] = []
    for old_key, new_key in LEGACY_KEY_TO_SLOT_KEY.items():
        renames.extend([
            (f"proxon_temp_{old_key}",    f"proxon_temp_{new_key}"),
            (f"proxon_offset_{old_key}",  f"proxon_offset_{new_key}"),
            (f"proxon_mitte_{old_key}",   f"proxon_mitte_{new_key}"),
            (f"proxon_heiz_{old_key}",    f"proxon_heiz_{new_key}"),
            (f"proxon_climate_{old_key}", f"proxon_climate_{new_key}"),
            (f"proxon_mitte_{old_key}_nr", f"proxon_mitte_{new_key}_nr"),
        ])
    rename_map = dict(renames)
    migrated = 0
    for ent in list(registry.entities.values()):
        if ent.config_entry_id != entry.entry_id:
            continue
        new_uid = rename_map.get(ent.unique_id)
        if not new_uid or new_uid == ent.unique_id:
            continue
        # If the target unique_id already exists (e.g. the user ran both
        # old and new versions), skip to avoid collisions – the registry
        # would raise otherwise.
        existing = registry.async_get_entity_id(ent.domain, DOMAIN, new_uid)
        if existing and existing != ent.entity_id:
            _LOGGER.warning(
                "Proxon: cannot migrate %s → %s, target already exists (%s)",
                ent.unique_id, new_uid, existing,
            )
            continue
        _LOGGER.info(
            "Proxon: migrating entity unique_id %s → %s (%s)",
            ent.unique_id, new_uid, ent.entity_id,
        )
        registry.async_update_entity(ent.entity_id, new_unique_id=new_uid)
        migrated += 1
    if migrated:
        _LOGGER.info("Proxon: migrated %d entity unique_ids to slot-based keys", migrated)


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
