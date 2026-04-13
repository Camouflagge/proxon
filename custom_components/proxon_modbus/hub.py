"""Modbus coordinator for Proxon FWT."""
from __future__ import annotations
import asyncio, logging, re, struct
from datetime import timedelta
from typing import Any

from pymodbus.client import AsyncModbusTcpClient, AsyncModbusSerialClient
from pymodbus.exceptions import ModbusException

# ── Framer auflösen (pymodbus 3.6+ und ältere Versionen) ──
_FRAMER_RTU = None
_FRAMER_SOURCE = "none"
try:
    # pymodbus >= 3.6
    from pymodbus.framer import FramerType  # type: ignore
    _FRAMER_RTU = FramerType.RTU
    _FRAMER_SOURCE = "FramerType.RTU"
except (ImportError, AttributeError):
    try:
        from pymodbus.framer.rtu_framer import ModbusRtuFramer  # type: ignore
        _FRAMER_RTU = ModbusRtuFramer
        _FRAMER_SOURCE = "ModbusRtuFramer"
    except ImportError:
        pass

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .const import *

_LOGGER = logging.getLogger(__name__)

# Delay between modbus reads to avoid bus collisions (ms)
READ_DELAY = 0.05  # 50ms between reads


# ── Bus-Rauschen unterdrücken (Issue #4, @Oponn4) ──────────────────────
# Auf RS485-Bussen empfängt pymodbus regelmäßig PDU-Frames von anderen
# Geräten, die keiner offenen Anfrage entsprechen. pymodbus loggt diese
# als ERROR ("received pdu without a corresponding request, IGNORING")
# und als WARNING ("Repeating"). Die Frames werden korrekt verworfen,
# erzeugen aber massiven Log-Spam (bis zu ~170 Einträge in 12h).
# Dieser Filter stuft sie auf DEBUG herunter.
class _PymodbusBusNoiseFilter(logging.Filter):
    """Demote pymodbus bus-noise errors to DEBUG level."""

    _PATTERNS = (
        "received pdu without a corresponding request",
        "Repeating",
    )

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: A003
        if record.levelno >= logging.WARNING:
            msg = record.getMessage()
            for pattern in self._PATTERNS:
                if pattern in msg:
                    record.levelno = logging.DEBUG
                    record.levelname = "DEBUG"
                    break
        return True  # always pass through – never suppress, just re-level


# Apply the filter exactly once at import time. If the integration is
# reloaded, the module is re-imported but the logger keeps existing
# filters, so we guard against duplicates.
_pymodbus_logger = logging.getLogger("pymodbus")
if not any(isinstance(f, _PymodbusBusNoiseFilter) for f in _pymodbus_logger.filters):
    _pymodbus_logger.addFilter(_PymodbusBusNoiseFilter())


class ProxonModbusHub:
    def __init__(
        self,
        hass,
        conn_type: str,
        slave: int,
        t300_enabled: bool,
        t300_slave: int,
        scan_interval: int,
        # TCP
        host: str | None = None,
        port: int | None = None,
        # Serial
        device: str | None = None,
        baudrate: int | None = None,
        bytesize: int | None = None,
        method: str | None = None,
        parity: str | None = None,
        stopbits: int | None = None,
    ):
        self.hass = hass
        self.conn_type = conn_type
        # TCP
        self.host = host
        self.port = port
        # Serial
        self.device = device
        self.baudrate = baudrate
        self.bytesize = bytesize
        self.method = method
        self.parity = parity
        self.stopbits = stopbits
        # Shared
        self.slave = slave
        self.t300_enabled = t300_enabled
        self.t300_slave = t300_slave
        self.scan_interval = scan_interval
        self._client = None
        self._lock = asyncio.Lock()
        self.data: dict[str, Any] = {}
        # Room discovery state. `_discovered_rooms` is a list of
        # {"slot": int, "name": str} dicts, populated by async_discover_rooms
        # during config/setup and cached in entry.data["rooms"]. The `rooms`
        # property turns this into the full room-definition dicts that the
        # platforms iterate over.
        self._discovered_rooms: list[dict] = []
        self.coordinator = DataUpdateCoordinator(
            hass, _LOGGER, name=f"{DOMAIN}_coordinator",
            update_method=self.async_update_data,
            update_interval=timedelta(seconds=scan_interval),
        )

    def _describe(self) -> str:
        """Human-readable connection description for logs."""
        if self.conn_type == TYPE_SERIAL:
            return f"serial {self.device} @ {self.baudrate} {self.bytesize}{self.parity}{self.stopbits} ({self.method})"
        if self.conn_type == TYPE_RTUOVERTCP:
            return f"rtuovertcp {self.host}:{self.port}"
        return f"tcp {self.host}:{self.port}"

    def _build_client(self):
        """Create a pymodbus client matching the configured connection type."""
        if self.conn_type == TYPE_SERIAL:
            return AsyncModbusSerialClient(
                port=self.device,
                baudrate=self.baudrate,
                bytesize=self.bytesize,
                parity=self.parity,
                stopbits=self.stopbits,
                timeout=10,
            )
        if self.conn_type == TYPE_RTUOVERTCP:
            # Raw RTU frames tunneled over a TCP socket (e.g. Waveshare/USR
            # serial server in "transparent" mode – no protocol conversion).
            if _FRAMER_RTU is None:
                raise RuntimeError(
                    "pymodbus has no RTU framer available – cannot use rtuovertcp"
                )
            try:
                return AsyncModbusTcpClient(
                    host=self.host, port=self.port, framer=_FRAMER_RTU, timeout=10,
                )
            except TypeError:
                # Very old pymodbus: framer kwarg missing – fall back to positional
                return AsyncModbusTcpClient(
                    self.host, self.port, _FRAMER_RTU, timeout=10,
                )
        # default: real Modbus-TCP (MBAP)
        return AsyncModbusTcpClient(host=self.host, port=self.port, timeout=10)

    async def async_connect(self) -> bool:
        try:
            self._client = self._build_client()
            _LOGGER.info(
                "Proxon: opening connection mode=%s target=%s slave=%s framer=%s",
                self.conn_type, self._describe(), self.slave, _FRAMER_SOURCE,
            )
            connected = await self._client.connect()
            if not connected:
                _LOGGER.error("Failed to connect to Proxon (%s)", self._describe())
                return False
            _LOGGER.info("Connected to Proxon (%s, slave %s)", self._describe(), self.slave)
            return True
        except Exception as err:
            _LOGGER.error("Error connecting to Proxon (%s): %s", self._describe(), err)
            return False

    async def async_test_connection(self) -> tuple[bool, str | None]:
        """Try to connect and read one register to validate the config.

        Used by the config flow. Always closes the probe client afterwards.
        Returns (ok, error_message).
        """
        client = None
        try:
            client = self._build_client()
            connected = await client.connect()
            if not connected:
                return False, f"connect failed ({self._describe()})"
            # Probe: read one holding register (Betriebsart) – tolerant to
            # devices that only expose some of the ranges.
            try:
                r = await client.read_holding_registers(
                    REG_BETRIEBSART, count=1, device_id=self.slave,
                )
            except TypeError:
                # Older pymodbus uses `slave=` kwarg
                r = await client.read_holding_registers(
                    REG_BETRIEBSART, count=1, slave=self.slave,
                )
            if r is None or r.isError():
                return False, f"read probe failed: {r}"
            return True, None
        except Exception as err:  # noqa: BLE001
            return False, f"{type(err).__name__}: {err}"
        finally:
            if client is not None:
                try:
                    client.close()
                except Exception:  # noqa: BLE001
                    pass

    async def async_close(self):
        if self._client:
            self._client.close()

    # ──────────────────────────── Room discovery ────────────────────────────
    def set_discovered_rooms(self, rooms: list[dict]) -> None:
        """Load a previously-discovered room list (from config entry cache).

        `rooms` is the list returned by `async_discover_rooms`: each entry
        must contain at least `slot` (int) and `name` (str). Invalid entries
        are silently dropped so that schema changes in old entries don't
        prevent startup.
        """
        clean: list[dict] = []
        for r in rooms or []:
            try:
                slot = int(r["slot"])
                name = str(r["name"])
            except (KeyError, TypeError, ValueError):
                continue
            if 0 <= slot < PANEL_SLOT_COUNT and name:
                clean.append({"slot": slot, "name": name})
        self._discovered_rooms = clean

    @property
    def rooms(self) -> list[dict]:
        """Return the active rooms as full room-definition dicts.

        Built dynamically from `_discovered_rooms` via `build_room_def`.
        If discovery has never run (empty list), a minimal fallback set
        containing the always-active slots (ZBP + HNBE) is returned so
        the integration still exposes the most important entities.
        """
        if not self._discovered_rooms:
            return [
                build_room_def(slot, FALLBACK_SLOT_NAMES[slot])
                for slot in ALWAYS_ACTIVE_SLOTS
            ]
        return [build_room_def(r["slot"], r["name"]) for r in self._discovered_rooms]

    async def async_discover_rooms(self) -> list[dict]:
        """Read panel names from the device and return the active slots.

        Reads up to `PANEL_SLOT_COUNT` name blocks starting at
        `NAME_REG_BASE` (each block = `NAME_REG_COUNT` holding registers,
        2 Latin-1 bytes per register). Slots are considered "active" when
        the decoded name is non-empty and does NOT match the default
        pattern `^Raum\\s*\\d+$` (e.g. "Raum 1", "Raum 12").

        Slots in `ALWAYS_ACTIVE_SLOTS` (ZBP and HNBE) are force-included
        even if the read fails or returns a default name; a fallback name
        from `FALLBACK_SLOT_NAMES` is used in that case.

        Discovery uses the hub's primary client under its lock, so the
        coordinator update loop cannot interleave with it. The result is
        a sorted list of {"slot": int, "name": str} dicts.

        Credit: the register layout (4x0621 + slot*10) was reverse-
        engineered by @Oponn4 in https://github.com/Camouflagge/proxon/pull/3
        and independently verified by the user against a real FWT 2.0.
        """
        default_re = re.compile(DEFAULT_NAME_REGEX, re.IGNORECASE)
        found: dict[int, str] = {}

        async with self._lock:
            await self._ensure_connected()
            if not self._client or not self._client.connected:
                _LOGGER.warning(
                    "Proxon: cannot discover panels – no connection (%s)",
                    self._describe(),
                )
            else:
                for slot in range(PANEL_SLOT_COUNT):
                    addr = NAME_REG_BASE + slot * NAME_REG_STRIDE
                    try:
                        r = await self._client.read_holding_registers(
                            addr, count=NAME_REG_COUNT, device_id=self.slave,
                        )
                    except Exception as err:  # noqa: BLE001
                        _LOGGER.debug(
                            "Proxon: name read slot %d (reg %d) raised %s",
                            slot, addr, err,
                        )
                        await asyncio.sleep(READ_DELAY)
                        continue
                    if r is None or r.isError() or len(r.registers) < NAME_REG_COUNT:
                        _LOGGER.debug(
                            "Proxon: name read slot %d (reg %d) failed: %s",
                            slot, addr, r,
                        )
                        await asyncio.sleep(READ_DELAY)
                        continue
                    # Decode 2 Latin-1 bytes per register, cut at first NUL.
                    chars: list[str] = []
                    for reg_val in r.registers:
                        hi = (reg_val >> 8) & 0xFF
                        lo = reg_val & 0xFF
                        chars.append(chr(hi) if hi else "\x00")
                        chars.append(chr(lo) if lo else "\x00")
                    name = "".join(chars).split("\x00", 1)[0].strip()
                    if not name:
                        _LOGGER.debug("Proxon: slot %d empty", slot)
                        await asyncio.sleep(READ_DELAY)
                        continue
                    if default_re.match(name):
                        _LOGGER.debug(
                            "Proxon: slot %d has default name %r – skipping",
                            slot, name,
                        )
                        await asyncio.sleep(READ_DELAY)
                        continue
                    _LOGGER.info(
                        "Proxon: discovered slot %d (%s) = %r",
                        slot, slot_panel_type(slot), name,
                    )
                    found[slot] = name
                    await asyncio.sleep(READ_DELAY)

        # Always-active slots get a fallback name if discovery missed them.
        for slot in ALWAYS_ACTIVE_SLOTS:
            if slot not in found:
                fallback = FALLBACK_SLOT_NAMES.get(slot, slot_panel_type(slot))
                _LOGGER.info(
                    "Proxon: slot %d (%s) not discovered – using fallback %r",
                    slot, slot_panel_type(slot), fallback,
                )
                found[slot] = fallback

        result = [{"slot": slot, "name": name} for slot, name in sorted(found.items())]
        self._discovered_rooms = result
        return result

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

            # Room temperatures, offsets, heizelemente – iteriert über die
            # dynamisch entdeckten Räume (hub.rooms), nicht über eine
            # statische Liste. So kommen neu hinzugekommene Panels nach
            # einem Reload automatisch dazu, ohne const.py-Änderung.
            for room in self.rooms:
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
