"""Switch platform for Proxon FWT Modbus."""
from __future__ import annotations
from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import *
from .hub import ProxonModbusHub

async def async_setup_entry(hass, entry, async_add_entities):
    hub = hass.data[DOMAIN][entry.entry_id]
    ents = []
    for sw in SWITCH_DEFINITIONS:
        ents.append(ProxonSwitch(hub.coordinator, hub, entry, sw["register"], sw["uid"], sw["name"], f"proxon_{sw['uid']}", sw.get("icon"), "Proxon FWT", "FWT 2.0"))
    for room in hub.rooms:
        ents.append(ProxonSwitch(hub.coordinator, hub, entry, room["heiz_reg"], f"heiz_{room['key']}", f"Heizelement {room['name']}", f"proxon_heiz_{room['key']}", "mdi:radiator", "Proxon FWT", "FWT 2.0"))
    if entry.data.get(CONF_T300_ENABLED, False):
        for sw in T300_SWITCH_DEFINITIONS:
            ents.append(ProxonSwitch(hub.coordinator, hub, entry, sw["register"], sw["uid"], sw["name"], f"proxon_{sw['uid']}", sw.get("icon"), "Proxon T300", "T300", hub.t300_slave))
    async_add_entities(ents)

class ProxonSwitch(CoordinatorEntity, SwitchEntity):
    _attr_has_entity_name = True
    def __init__(self, coord, hub, entry, register, data_key, name, uid, icon, dev_name, dev_model, slave_override=None):
        super().__init__(coord)
        self._hub, self._register, self._data_key, self._entry = hub, register, data_key, entry
        self._attr_name, self._attr_unique_id, self._attr_icon = name, uid, icon
        self._dev_name, self._dev_model, self._slave = dev_name, dev_model, slave_override
    @property
    def device_info(self):
        return DeviceInfo(identifiers={(DOMAIN, f"{self._entry.entry_id}_{self._dev_name}")}, name=self._dev_name, manufacturer="Zimmermann / Proxon", model=self._dev_model)
    @property
    def is_on(self):
        return self.coordinator.data.get(self._data_key) if self.coordinator.data else None
    async def async_turn_on(self, **kw):
        if await self._hub.async_write_register(self._register, 1, self._slave or self._hub.slave):
            self.coordinator.data[self._data_key] = True
            self.async_write_ha_state()
            await self.coordinator.async_request_refresh()
    async def async_turn_off(self, **kw):
        if await self._hub.async_write_register(self._register, 0, self._slave or self._hub.slave):
            self.coordinator.data[self._data_key] = False
            self.async_write_ha_state()
            await self.coordinator.async_request_refresh()
