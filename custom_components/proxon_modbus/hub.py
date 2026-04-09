"""Modbus coordinator for Proxon FWT."""
from __future__ import annotations
import asyncio, logging, struct
from datetime import timedelta
from typing import Any
from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .const import *

_LOGGER = logging.getLogger(__name__)

class ProxonModbusHub:
    def __init__(self, hass, host, port, slave, t300_enabled, t300_slave, scan_interval):
        self.hass = hass
        self.host = host
        self.port = port
        self.slave = slave
        self.t300_enabled = t300_enabled
        self.t300_slave = t300_slave
        self.scan_interval = scan_interval
        self._client = None
        self._lock = asyncio.Lock()
        self.data = {}
        self.coordinator = DataUpdateCoordinator(
            hass, _LOGGER, name=f"{DOMAIN}_coordinator",
            update_method=self.async_update_data,
            update_interval=timedelta(seconds=scan_interval),
        )

    async def async_connect(self):
        try:
            self._client = AsyncModbusTcpClient(host=self.host, port=self.port, timeout=10)
            connected = await self._client.connect()
            if not connected:
                _LOGGER.error("Failed to connect to Proxon at %s:%s", self.host, self.port)
                return False
            _LOGGER.info("Connected to Proxon at %s:%s", self.host, self.port)
            return True
        except Exception as err:
            _LOGGER.error("Error connecting: %s", err)
            return False

    async def async_close(self):
        if self._client: self._client.close()

    async def _read_reg(self, address, slave, input_type="input", count=1):
        async with self._lock:
            try:
                if not self._client or not self._client.connected:
                    await self.async_connect()
                if input_type == "input":
                    r = await self._client.read_input_registers(address=address, count=count, slave=slave)
                else:
                    r = await self._client.read_holding_registers(address=address, count=count, slave=slave)
                if r.isError(): return None
                return r.registers
            except Exception:
                return None

    async def async_write_register(self, address, value, slave=None):
        if slave is None: slave = self.slave
        async with self._lock:
            try:
                if not self._client or not self._client.connected:
                    await self.async_connect()
                if value < 0:
                    value = struct.unpack("H", struct.pack("h", value))[0]
                r = await self._client.write_register(address=address, value=int(value), slave=slave)
                return not r.isError()
            except Exception as err:
                _LOGGER.error("Write error reg %d: %s", address, err)
                return False

    def _decode(self, raw, dt, scale, offset=0):
        if dt == "int16" and raw > 32767: raw -= 65536
        val = raw * scale + offset
        if scale in (0.01, 0.1): val = round(val, 2 if scale == 0.01 else 1)
        return val

    async def async_update_data(self):
        data = {}
        try:
            # System sensors
            for s in SENSOR_DEFINITIONS:
                regs = await self._read_reg(s["register"], self.slave, s["inp"])
                if regs:
                    data[s["uid"]] = self._decode(regs[0], s["dt"], s["scale"])
                    if s["uid"] == "betriebsart":
                        data["betriebsart_text"] = BETRIEBSART_MAP.get(int(regs[0]), f"? ({regs[0]})")

            # Room temperatures
            for room in ROOM_DEFINITIONS:
                regs = await self._read_reg(room["temp_reg"], self.slave, room["temp_input"])
                if regs:
                    data[f"temp_{room['key']}"] = self._decode(regs[0], room["temp_dtype"], room["temp_scale"])
                # Offsets
                if room["offset_reg"] is not None:
                    regs = await self._read_reg(room["offset_reg"], self.slave, "holding")
                    if regs:
                        data[f"offset_{room['key']}"] = self._decode(regs[0], "int16", 1)
                # Heizelemente
                regs = await self._read_reg(room["heiz_reg"], self.slave, "holding")
                if regs:
                    data[f"heiz_{room['key']}"] = bool(regs[0])

            # Global switches
            for sw in SWITCH_DEFINITIONS:
                regs = await self._read_reg(sw["register"], self.slave, "holding")
                if regs: data[sw["uid"]] = bool(regs[0])

            # T300
            if self.t300_enabled:
                for t in T300_SENSOR_DEFINITIONS:
                    regs = await self._read_reg(t["register"], self.t300_slave, t["inp"])
                    if regs:
                        data[t["uid"]] = self._decode(regs[0], t["dt"], t["scale"], t.get("offset", 0))
                for sw in T300_SWITCH_DEFINITIONS:
                    regs = await self._read_reg(sw["register"], self.t300_slave, "holding")
                    if regs: data[sw["uid"]] = bool(regs[0])
        except Exception as err:
            raise UpdateFailed(f"Error: {err}") from err
        self.data = data
        return data
