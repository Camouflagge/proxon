"""Climate platform for Proxon FWT Modbus.

Proxon Temperatursteuerung:
- Wohnzimmer (ZBP): Hat eine direkte Soll-Temperatur (Register 70/40071)
  → Bereich 10-30°C, direkt schreibbar (scale 0.01)
- Nebenpanels (NB): Haben einen Offset von -3 bis +3 (Register 213+, scale 1)
  und eine konfigurierbare Mitteltemperatur (Register 233+, scale 1, 0–50°C)
  → Regeltemperatur = Mitteltemperatur + Offsettemperatur
  → Beim Setzen: offset = round(gewünschte_temp - mitteltemperatur)
  (Proxon PTC Software-Beschreibung, ParaID 305–324 / 330–349)
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
    for room in hub.rooms:
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

        if room["soll_reg"] is not None:
            self._attr_min_temp = room["soll_min"]
            self._attr_max_temp = room["soll_max"]
        # NBE: min/max werden dynamisch als Properties berechnet (Mitteltemp ± 3)

    @property
    def device_info(self):
        return DeviceInfo(
            identifiers={(DOMAIN, f"{self._entry.entry_id}_Proxon FWT")},
            name="Proxon FWT", manufacturer="Zimmermann / Proxon", model="FWT 2.0"
        )

    def _mittel(self):
        """Mitteltemperatur des Raums aus den Coordinator-Daten."""
        if not self.coordinator.data:
            return NBE_MITTEL_DEFAULT
        return self.coordinator.data.get(f"mitte_{self._room['key']}", NBE_MITTEL_DEFAULT)

    @property
    def min_temp(self):
        if self._room["soll_reg"] is not None:
            return self._room["soll_min"]
        return self._mittel() + NBE_OFFSET_MIN

    @property
    def max_temp(self):
        if self._room["soll_reg"] is not None:
            return self._room["soll_max"]
        return self._mittel() + NBE_OFFSET_MAX

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
            # Nebenpanel: Regeltemperatur = Mitteltemperatur + Offset
            offset = self.coordinator.data.get(f"offset_{r['key']}", 0)
            if offset is not None:
                return self._mittel() + offset
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
            # Nebenpanel: Offset = Temperatur - Mitteltemperatur
            new_offset = round(temp - self._mittel())
            new_offset = max(NBE_OFFSET_MIN, min(NBE_OFFSET_MAX, new_offset))
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
