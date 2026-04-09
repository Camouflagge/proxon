"""Sensor platform for Proxon FWT Modbus."""
from __future__ import annotations
import logging
from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import *
from .hub import ProxonModbusHub

_LOGGER = logging.getLogger(__name__)
DC = {"temperature": SensorDeviceClass.TEMPERATURE, "power": SensorDeviceClass.POWER,
      "carbon_dioxide": SensorDeviceClass.CO2, "duration": SensorDeviceClass.DURATION,
      "humidity": SensorDeviceClass.HUMIDITY}
SC = {"measurement": SensorStateClass.MEASUREMENT, "total_increasing": SensorStateClass.TOTAL_INCREASING}

async def async_setup_entry(hass, entry, async_add_entities):
    hub = hass.data[DOMAIN][entry.entry_id]
    ents = []
    # System sensors
    for s in SENSOR_DEFINITIONS:
        ents.append(ProxonSensor(hub.coordinator, hub, entry, s["uid"], s["name"], f"proxon_{s['uid']}", s["unit"], s.get("dc"), s.get("sc"), s.get("icon"), "Proxon FWT", "FWT 2.0"))
    # Betriebsart text
    ents.append(ProxonSensor(hub.coordinator, hub, entry, "betriebsart_text", "Betriebsart Text", "proxon_betriebsart_text", None, None, None, "mdi:cog-outline", "Proxon FWT", "FWT 2.0"))
    # Room temperatures + offsets
    for room in ROOM_DEFINITIONS:
        ents.append(ProxonSensor(hub.coordinator, hub, entry, f"temp_{room['key']}", f"Temperatur {room['name']}", f"proxon_temp_{room['key']}", "°C", "temperature", "measurement", "mdi:home-thermometer", "Proxon FWT", "FWT 2.0"))
        if room["offset_reg"] is not None:
            ents.append(ProxonSensor(hub.coordinator, hub, entry, f"offset_{room['key']}", f"Offset {room['name']}", f"proxon_offset_{room['key']}", "°C", "temperature", None, "mdi:thermometer-plus", "Proxon FWT", "FWT 2.0"))
    # Filter days
    ents.append(ProxonFilterDays(hub.coordinator, hub, entry, "filter_nutz", "Filter Laufzeit (Tage)", "proxon_filter_laufzeit_d", "laufzeit"))
    ents.append(ProxonFilterDays(hub.coordinator, hub, entry, "filter_nutz", "Filter Restzeit (Tage)", "proxon_filter_restzeit_d", "restzeit"))
    # T300
    if entry.data.get(CONF_T300_ENABLED, False):
        for t in T300_SENSOR_DEFINITIONS:
            ents.append(ProxonSensor(hub.coordinator, hub, entry, t["uid"], t["name"], f"proxon_{t['uid']}", t["unit"], t.get("dc"), t.get("sc"), t.get("icon"), "Proxon T300", "T300"))
    async_add_entities(ents)

class ProxonSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True
    def __init__(self, coord, hub, entry, data_key, name, uid, unit, dc, sc, icon, dev_name, dev_model):
        super().__init__(coord)
        self._hub, self._data_key, self._entry = hub, data_key, entry
        self._attr_name, self._attr_unique_id = name, uid
        self._attr_native_unit_of_measurement, self._attr_icon = unit, icon
        self._dev_name, self._dev_model = dev_name, dev_model
        if dc and dc in DC: self._attr_device_class = DC[dc]
        if sc and sc in SC: self._attr_state_class = SC[sc]
    @property
    def device_info(self):
        return DeviceInfo(identifiers={(DOMAIN, f"{self._entry.entry_id}_{self._dev_name}")}, name=self._dev_name, manufacturer="Zimmermann / Proxon", model=self._dev_model)
    @property
    def native_value(self):
        return self.coordinator.data.get(self._data_key) if self.coordinator.data else None

class ProxonFilterDays(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = "d"
    _attr_icon = "mdi:air-filter"
    def __init__(self, coord, hub, entry, key, name, uid, mode):
        super().__init__(coord)
        self._hub, self._key, self._mode, self._entry = hub, key, mode, entry
        self._attr_name, self._attr_unique_id = name, uid
    @property
    def device_info(self):
        return DeviceInfo(identifiers={(DOMAIN, f"{self._entry.entry_id}_Proxon FWT")}, name="Proxon FWT", manufacturer="Zimmermann / Proxon", model="FWT 2.0")
    @property
    def native_value(self):
        if not self.coordinator.data: return None
        raw = self.coordinator.data.get(self._key)
        if raw is None: return None
        days = round((raw * 2) / 24)
        return days if self._mode == "laufzeit" else max(0, 180 - days)
