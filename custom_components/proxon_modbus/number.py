"""Number platform for Proxon FWT Modbus."""
from __future__ import annotations
from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import *
from .hub import ProxonModbusHub

async def async_setup_entry(hass, entry, async_add_entities):
    hub = hass.data[DOMAIN][entry.entry_id]
    ents = [
        ProxonNumber(hub.coordinator, hub, entry, REG_LUEFTERSTUFE, "luefterstufe", "Lüfterstufe", "proxon_luefterstufe_nr", 1, 4, 1, "mdi:fan-speed-3", None, 1, "Proxon FWT", "FWT 2.0"),
        ProxonNumber(hub.coordinator, hub, entry, REG_INTENSIVLUEFTUNG_REST, "intensiv_rest", "Intensivlüftung", "proxon_intensiv_nr", 0, 1440, 1, "mdi:fan-plus", "min", 1, "Proxon FWT", "FWT 2.0", mode=NumberMode.BOX),
        ProxonNumber(hub.coordinator, hub, entry, REG_LUFTFEUCHTE_HOLDING, "feuchte_h", "Luftfeuchte Soll", "proxon_feuchte_h_nr", 0, 100, 1, "mdi:water-percent", "%", 1, "Proxon FWT", "FWT 2.0"),
    ]
    # Mitteltemperatur als Number-Entities (echte Mitteltemp. aus Reg. 232+slot)
    for room in hub.rooms:
        if room.get("mitte_reg") is not None:
            ents.append(ProxonNumber(
                hub.coordinator, hub, entry,
                room["mitte_reg"], f"mitte_{room['key']}",
                f"Mitteltemperatur {room['name']}", f"proxon_mitte_{room['key']}_nr",
                0, 50, 1, "mdi:thermometer-lines", "°C",
                room.get("mitte_scale", 1),
                "Proxon FWT", "FWT 2.0",
                mode=NumberMode.BOX,
            ))
    # Ist-Offset als Number-Entities (Kalibrierung der Ist-Temperatur-Anzeige)
    for room in hub.rooms:
        if room.get("ist_offset_reg") is not None:
            ents.append(ProxonNumber(
                hub.coordinator, hub, entry,
                room["ist_offset_reg"], f"ist_offset_{room['key']}",
                f"Ist-Offset {room['name']}", f"proxon_ist_offset_{room['key']}_nr",
                -10, 10, 0.1, "mdi:thermometer-chevron-up", "°C",
                room.get("ist_offset_scale", 0.1),
                "Proxon FWT", "FWT 2.0",
                mode=NumberMode.BOX,
            ))
    if entry.data.get(CONF_T300_ENABLED, False):
        ents.append(ProxonNumber(hub.coordinator, hub, entry, REG_T300_SOLL_TEMP, "t300_soll", "T300 Soll-Temperatur", "proxon_t300_soll_nr", 20, 55, 1, "mdi:thermometer-water", "°C", 0.1, "Proxon T300", "T300", hub.t300_slave))
        ents.append(ProxonNumber(hub.coordinator, hub, entry, REG_T300_HEIZSTAB_SOLL, "t300_hs_soll", "T300 Heizstab Soll", "proxon_t300_hs_nr", 20, 70, 1, "mdi:thermometer-alert", "°C", 0.1, "Proxon T300", "T300", hub.t300_slave))
    async_add_entities(ents)

class ProxonNumber(CoordinatorEntity, NumberEntity):
    _attr_has_entity_name = True
    def __init__(self, coord, hub, entry, reg, data_key, name, uid, mn, mx, step, icon, unit, scale, dev_name, dev_model, slave_override=None, mode=NumberMode.SLIDER):
        super().__init__(coord)
        self._hub, self._reg, self._data_key, self._scale, self._slave, self._entry = hub, reg, data_key, scale, slave_override, entry
        self._attr_name, self._attr_unique_id = name, uid
        self._attr_native_min_value, self._attr_native_max_value, self._attr_native_step = mn, mx, step
        self._attr_icon, self._attr_native_unit_of_measurement = icon, unit
        self._attr_mode = mode
        self._dev_name, self._dev_model = dev_name, dev_model
    @property
    def device_info(self):
        return DeviceInfo(identifiers={(DOMAIN, f"{self._entry.entry_id}_{self._dev_name}")}, name=self._dev_name, manufacturer="Zimmermann / Proxon", model=self._dev_model)
    @property
    def native_value(self):
        return self.coordinator.data.get(self._data_key) if self.coordinator.data else None
    async def async_set_native_value(self, value):
        rv = round(value / self._scale) if self._scale != 1 else int(value)
        if await self._hub.async_write_register(self._reg, rv, self._slave or self._hub.slave):
            self.coordinator.data[self._data_key] = int(value) if self._scale == 1 else value
            self.async_write_ha_state()
            await self.coordinator.async_request_refresh()
