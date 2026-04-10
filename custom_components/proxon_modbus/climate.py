"""Climate platform for Proxon FWT Modbus.

Proxon Temperatursteuerung:
- Wohnzimmer (ZBP): Hat eine direkte Soll-Temperatur (Register 70/40071)
  → Bereich 10-30°C, direkt schreibbar (scale 0.01)
- Nebenpanels (NB): Haben einen Offset von -3 bis +3 (Register 213-218)
  → Soll = 20 + Offset (feste Basis 20°C)
  → -3=17°C, -2=18°C, -1=19°C, 0=20°C, +1=21°C, +2=22°C, +3=23°C
  → Beim Setzen: offset = gewünschte_temp - 20
"""
from __future__ import annotations
import logging
from typing import Any
from homeassistant.components.climate import (
    ClimateEntity, ClimateEntityFeature, HVACAction, HVACMode,
)
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import *
from .hub import ProxonModbusHub

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    hub = hass.data[DOMAIN][entry.entry_id]
    ents = []
    for room in ROOM_DEFINITIONS:
        ents.append(ProxonClimate(hub.coordinator, hub, entry, room))
    async_add_entities(ents)

class ProxonClimate(CoordinatorEntity, ClimateEntity):
    _attr_has_entity_name = True
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_hvac_modes = [HVACMode.HEAT, HVACMode.OFF]
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.TURN_ON
        | ClimateEntityFeature.TURN_OFF
    )
    _attr_target_temperature_step = 1.0

    def __init__(self, coord, hub, entry, room):
        super().__init__(coord)
        self._hub = hub
        self._entry = entry
        self._room = room
        self._attr_name = f"Heizung {room['name']}"
        self._attr_unique_id = f"proxon_climate_{room['key']}"
        self._attr_icon = "mdi:thermostat"

        # Wohnzimmer: direkte Soll-Temp (10-30)
        # Nebenpanels: feste Basis 20°C ± 3 → 17-23°C
        if room["soll_reg"] is not None:
            self._attr_min_temp = room["soll_min"]
            self._attr_max_temp = room["soll_max"]
        else:
            self._attr_min_temp = 17
            self._attr_max_temp = 23

    @property
    def device_info(self):
        return DeviceInfo(
            identifiers={(DOMAIN, f"{self._entry.entry_id}_Proxon FWT")},
            name="Proxon FWT", manufacturer="Zimmermann / Proxon", model="FWT 2.0"
        )

    @property
    def current_temperature(self):
        if not self.coordinator.data: return None
        return self.coordinator.data.get(f"temp_{self._room['key']}")

    @property
    def target_temperature(self):
        if not self.coordinator.data: return None
        r = self._room
        if r["soll_reg"] is not None:
            # Wohnzimmer: direkte Soll-Temperatur
            return self.coordinator.data.get("soll_wz")
        else:
            # Nebenpanel: Soll = 20 + Offset (feste Basis)
            offset = self.coordinator.data.get(f"offset_{r['key']}", 0)
            if offset is not None:
                return 20 + offset
        return None

    @property
    def hvac_mode(self):
        # Prüfe ob Heizelement aktiv ist
        if self.coordinator.data:
            heiz = self.coordinator.data.get(f"heiz_{self._room['key']}")
            if heiz is False:
                return HVACMode.OFF
        return HVACMode.HEAT

    @property
    def hvac_action(self):
        cur = self.current_temperature
        tgt = self.target_temperature
        if cur is not None and tgt is not None:
            return HVACAction.HEATING if cur < tgt - 0.3 else HVACAction.IDLE
        return None

    async def async_set_temperature(self, **kwargs):
        temp = kwargs.get(ATTR_TEMPERATURE)
        if temp is None: return
        r = self._room

        if r["soll_reg"] is not None:
            # Wohnzimmer: Direkt die Soll-Temperatur schreiben
            reg_val = int(temp / r["soll_scale"]) if r["soll_scale"] != 1 else int(temp)
            ok = await self._hub.async_write_register(r["soll_reg"], reg_val)
            if ok:
                _LOGGER.info("Set %s Soll to %.1f°C (raw: %d)", r["name"], temp, reg_val)
                await self.coordinator.async_request_refresh()
        else:
            # Nebenpanel: Offset = Temperatur - 20 (feste Basis)
            new_offset = int(temp - 20)
            # Clamp to -3..+3
            new_offset = max(-3, min(3, new_offset))
            ok = await self._hub.async_write_register(r["offset_reg"], new_offset)
            if ok:
                _LOGGER.info("Set %s offset to %d (target: %.1f°C)", r["name"], new_offset, temp)
                await self.coordinator.async_request_refresh()

    async def async_set_hvac_mode(self, hvac_mode):
        r = self._room
        if hvac_mode == HVACMode.OFF:
            await self._hub.async_write_register(r["heiz_reg"], 0)
        elif hvac_mode == HVACMode.HEAT:
            await self._hub.async_write_register(r["heiz_reg"], 1)
        await self.coordinator.async_request_refresh()

    async def async_turn_on(self):
        await self.async_set_hvac_mode(HVACMode.HEAT)

    async def async_turn_off(self):
        await self.async_set_hvac_mode(HVACMode.OFF)
