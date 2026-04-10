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

# Delay between modbus reads to avoid bus collisions (ms)
READ_DELAY = 0.05  # 50ms between reads


class ProxonModbusHub:
    def __init__(self, hass, host, port, slave, t300_enabled, t300_slave, scan_interval):
        self.hass = hass
        self.host = host
        self.port = port
        self.slave = slave
        self.t300_enabled = t300_enabled
        self.t300_slave = t300_slave
        self.scan_interval = scan_interval
        self._client: AsyncModbusTcpClient | None = None
        self._lock = asyncio.Lock()
        self.data: dict[str, Any] = {}
        self.coordinator = DataUpdateCoordinator(
            hass, _LOGGER, name=f"{DOMAIN}_coordinator",
            update_method=self.async_update_data,
            update_interval=timedelta(seconds=scan_interval),
        )

    async def async_connect(self) -> bool:
        try:
            self._client = AsyncModbusTcpClient(
                host=self.host, port=self.port, timeout=10,
            )
            connected = await self._client.connect()
            if not connected:
                _LOGGER.error("Failed to connect to Proxon at %s:%s", self.host, self.port)
                return False
            _LOGGER.info("Connected to Proxon at %s:%s (slave %s)", self.host, self.port, self.slave)
            return True
        except Exception as err:
            _LOGGER.error("Error connecting: %s", err)
            return False

    async def async_close(self):
        if self._client:
            self._client.close()

    async def _ensure_connected(self):
        """Ensure the client is connected."""
        if not self._client or not self._client.connected:
            await self.async_connect()

    async def _read_reg(self, address: int, slave: int, input_type: str = "input", count: int = 1) -> list[int] | None:
        """Read register(s) with delay between reads."""
        async with self._lock:
            try:
                await self._ensure_connected()
                if input_type == "input":
                    r = await self._client.read_input_registers(address, count=count, device_id=slave)
                else:
                    r = await self._client.read_holding_registers(address, count=count, device_id=slave)
                if r.isError():
                    _LOGGER.debug("Read error reg %d slave %d: %s", address, slave, r)
                    return None
                await asyncio.sleep(READ_DELAY)
                return r.registers
            except Exception as err:
                _LOGGER.debug("Exception reading reg %d: %s", address, err)
                return None

    async def async_write_register(self, address: int, value: int, slave: int | None = None) -> bool:
        """Write a single holding register."""
        if slave is None:
            slave = self.slave
        async with self._lock:
            try:
                await self._ensure_connected()
                # Handle negative values for int16
                if value < 0:
                    value = struct.unpack("H", struct.pack("h", value))[0]
                r = await self._client.write_register(address, int(value), device_id=slave)
                if r.isError():
                    _LOGGER.error("Write error reg %d: %s", address, r)
                    return False
                await asyncio.sleep(READ_DELAY)
                return True
            except Exception as err:
                _LOGGER.error("Write exception reg %d: %s", address, err)
                return False

    def _decode(self, raw: int, dt: str, scale: float, offset: float = 0) -> float | int:
        """Decode a raw Modbus register value."""
        if dt == "int16" and raw > 32767:
            raw -= 65536
        val = raw * scale + offset
        if scale == 0.01:
            val = round(val, 2)
        elif scale == 0.1:
            val = round(val, 1)
        return val

    async def async_update_data(self) -> dict[str, Any]:
        """Fetch data from the Modbus device."""
        data: dict[str, Any] = {}
        try:
            # System sensors
            for s in SENSOR_DEFINITIONS:
                regs = await self._read_reg(s["register"], self.slave, s["inp"])
                if regs is not None:
                    data[s["uid"]] = self._decode(regs[0], s["dt"], s["scale"])
                    if s["uid"] == "betriebsart":
                        data["betriebsart_text"] = BETRIEBSART_MAP.get(
                            int(regs[0]), f"? ({regs[0]})"
                        )

            # Room temperatures, offsets, heizelemente
            for room in ROOM_DEFINITIONS:
                # Ist-Temperatur
                regs = await self._read_reg(room["temp_reg"], self.slave, room["temp_input"])
                if regs is not None:
                    data[f"temp_{room['key']}"] = self._decode(
                        regs[0], room["temp_dtype"], room["temp_scale"]
                    )
                # Offset
                if room["offset_reg"] is not None:
                    regs = await self._read_reg(room["offset_reg"], self.slave, "holding")
                    if regs is not None:
                        data[f"offset_{room['key']}"] = self._decode(regs[0], "int16", 1)
                # Mitteltemperatur
                if room.get("mitte_reg") is not None:
                    regs = await self._read_reg(room["mitte_reg"], self.slave, "holding")
                    if regs is not None:
                        data[f"mitte_{room['key']}"] = self._decode(
                            regs[0], room.get("mitte_dtype", "int16"),
                            room.get("mitte_scale", 0.1)
                        )
                # Heizelement
                regs = await self._read_reg(room["heiz_reg"], self.slave, "holding")
                if regs is not None:
                    data[f"heiz_{room['key']}"] = bool(regs[0])

            # Zugriffsmodus (für Select-Entity)
            regs = await self._read_reg(REG_ZUGRIFF, self.slave, "holding")
            if regs is not None:
                data["zugriff"] = int(regs[0])

            # Luftfeuchte Holding (für Number-Entity)
            regs = await self._read_reg(REG_LUFTFEUCHTE_HOLDING, self.slave, "holding")
            if regs is not None:
                data["feuchte_h"] = int(regs[0])

            # Global switches
            for sw in SWITCH_DEFINITIONS:
                regs = await self._read_reg(sw["register"], self.slave, "holding")
                if regs is not None:
                    data[sw["uid"]] = bool(regs[0])

            # T300
            if self.t300_enabled:
                for t in T300_SENSOR_DEFINITIONS:
                    regs = await self._read_reg(t["register"], self.t300_slave, t["inp"])
                    if regs is not None:
                        data[t["uid"]] = self._decode(
                            regs[0], t["dt"], t["scale"], t.get("offset", 0)
                        )
                for sw in T300_SWITCH_DEFINITIONS:
                    regs = await self._read_reg(sw["register"], self.t300_slave, "holding")
                    if regs is not None:
                        data[sw["uid"]] = bool(regs[0])

        except Exception as err:
            raise UpdateFailed(f"Error: {err}") from err

        self.data = data
        return data
