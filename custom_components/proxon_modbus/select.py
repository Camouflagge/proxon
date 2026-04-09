"""Select platform for Proxon FWT Modbus."""
from __future__ import annotations
from homeassistant.components.select import SelectEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import *

async def async_setup_entry(hass, entry, async_add_entities):
    hub = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        ProxonBetriebsartSelect(hub.coordinator, hub, entry),
        ProxonZugriffSelect(hub.coordinator, hub, entry),
    ])

class ProxonBetriebsartSelect(CoordinatorEntity, SelectEntity):
    _attr_has_entity_name = True
    _attr_name = "Betriebsart"
    _attr_icon = "mdi:cog-outline"
    _attr_options = list(BETRIEBSART_MAP.values())
    def __init__(self, coord, hub, entry):
        super().__init__(coord)
        self._hub, self._entry = hub, entry
        self._attr_unique_id = "proxon_betriebsart_select"
    @property
    def device_info(self):
        return DeviceInfo(identifiers={(DOMAIN, f"{self._entry.entry_id}_Proxon FWT")}, name="Proxon FWT", manufacturer="Zimmermann / Proxon", model="FWT 2.0")
    @property
    def current_option(self):
        return self.coordinator.data.get("betriebsart_text") if self.coordinator.data else None
    async def async_select_option(self, option):
        val = BETRIEBSART_REVERSE_MAP.get(option)
        if val is not None and await self._hub.async_write_register(REG_BETRIEBSART, val):
            self.coordinator.data["betriebsart"] = val
            self.coordinator.data["betriebsart_text"] = option
            self.async_write_ha_state()
            await self.coordinator.async_request_refresh()

class ProxonZugriffSelect(CoordinatorEntity, SelectEntity):
    _attr_has_entity_name = True
    _attr_name = "Zugriffsmodus"
    _attr_icon = "mdi:lock-open-variant"
    _attr_options = list(ZUGRIFF_MAP.values())
    def __init__(self, coord, hub, entry):
        super().__init__(coord)
        self._hub, self._entry = hub, entry
        self._attr_unique_id = "proxon_zugriff_select"
    @property
    def device_info(self):
        return DeviceInfo(identifiers={(DOMAIN, f"{self._entry.entry_id}_Proxon FWT")}, name="Proxon FWT", manufacturer="Zimmermann / Proxon", model="FWT 2.0")
    @property
    def current_option(self):
        val = self.coordinator.data.get("zugriff") if self.coordinator.data else None
        return ZUGRIFF_MAP.get(val)
    async def async_select_option(self, option):
        val = ZUGRIFF_REVERSE_MAP.get(option)
        if val is not None and await self._hub.async_write_register(REG_ZUGRIFF, val):
            self.coordinator.data["zugriff"] = val
            self.async_write_ha_state()
            await self.coordinator.async_request_refresh()
