"""Constants for the Proxon FWT Modbus integration."""

DOMAIN = "proxon_modbus"
DEFAULT_NAME = "Proxon FWT"
DEFAULT_PORT = 502
DEFAULT_SLAVE = 41
DEFAULT_T300_SLAVE = 41  # T300 Register sind bei den meisten über FWT Slave 41 erreichbar
DEFAULT_SCAN_INTERVAL = 10

# Verbindungstypen
CONF_TYPE = "type"
TYPE_TCP = "tcp"
TYPE_RTUOVERTCP = "rtuovertcp"
TYPE_SERIAL = "serial"
CONNECTION_TYPES = [TYPE_TCP, TYPE_RTUOVERTCP, TYPE_SERIAL]

# Gemeinsam
CONF_SLAVE = "slave"
CONF_T300_ENABLED = "t300_enabled"
CONF_T300_SLAVE = "t300_slave"

# Serielle Parameter
CONF_DEVICE = "device"
CONF_BAUDRATE = "baudrate"
CONF_BYTESIZE = "bytesize"
CONF_METHOD = "method"
CONF_PARITY = "parity"
CONF_STOPBITS = "stopbits"

DEFAULT_DEVICE = "/dev/ttyUSB0"
DEFAULT_BAUDRATE = 19200
DEFAULT_BYTESIZE = 8
DEFAULT_METHOD = "rtu"   # rtu oder ascii
DEFAULT_PARITY = "E"     # E, N, O
DEFAULT_STOPBITS = 1     # 1 oder 2

BAUDRATE_OPTIONS = [1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200]
BYTESIZE_OPTIONS = [5, 6, 7, 8]
METHOD_OPTIONS = ["rtu", "ascii"]
PARITY_OPTIONS = ["E", "N", "O"]  # Even, None, Odd
STOPBITS_OPTIONS = [1, 2]

PLATFORMS = ["sensor", "switch", "climate", "number", "select"]

# ──── Register (0-basiert, pymodbus) ────
# ioBroker 3xxxx → Input Reg (addr - 30001), 4xxxx → Holding Reg (addr - 40001)

# === Input Register ===
REG_VENTILATOR_ZULUFT = 0       # 30001
REG_VENTILATOR_ABLUFT = 1       # 30002
REG_CO2_SENSOR = 21             # 30022
REG_FEUCHTE = 22                # 30023
REG_LEISTUNG_AKTUELL = 25       # 30026
REG_TEMP_WOHNZIMMER = 41        # 30042 (scale 0.01, int16)
REG_TEMP_VERDAMPFER = 176       # 30177 (scale 0.1, uint16)
REG_TEMP_KONDENSATOR = 179      # 30180 (scale 0.1)
REG_TEMP_KOMPRESSOR = 180       # 30181 (scale 0.1)
REG_KOMPRESSOR_DZ = 190         # 30191
REG_TEMP_ZULUFT = 195           # 30196 (scale 0.01, int16)
REG_TEMP_ABLUFT = 196           # 30197
REG_TEMP_FORTLUFT = 197         # 30198
REG_TEMP_FRISCHLUFT = 198       # 30199
REG_TEMP_KIND_VORNE = 590       # 30591 (scale 0.1)
REG_TEMP_DIELE = 593            # 30594
REG_TEMP_KIND_HINTEN = 599      # 30600
REG_TEMP_SCHLAFEN = 602         # 30603
REG_TEMP_T300_INPUT = 814       # 30815

# === Holding Register ===
REG_BETRIEBSART = 16            # 40017
REG_LUEFTERSTUFE = 22           # 40023
REG_KUEHLFUNKTION_KOMP = 34     # 40035
REG_KUEHLFUNKTION_KOND = 45     # 40046
REG_KUEHLFUNKTION_LEIST = 52    # 40053
REG_KUEHLUNG_GLOBAL = 62        # 40063
REG_PV_VORRANG = 63             # 40064
REG_SOLL_TEMP_WOHNZIMMER = 70   # 40071 (scale 1, raw °C)
REG_LUFTFEUCHTE_HOLDING = 118   # 40119
REG_INTENSIVLUEFTUNG_REST = 133 # 40134
REG_HEIZELEMENT_WOHNZIMMER = 187# 40188
REG_MITTETEMPERATUR_KIND_VORNE = 190  # 40191
REG_MITTETEMPERATUR_DIELE = 191      # 40192 (int16, scale 0.1)
REG_MITTETEMPERATUR_KIND_HINTEN = 193 # 40194
REG_MITTETEMPERATUR_SCHLAFZIMMER = 194 # 40195
REG_OFFSET_KIND_VORNE = 213     # 40214 (int16, scale 1 → -3..+3)
REG_OFFSET_DIELE = 214          # 40215
REG_OFFSET_KIND_HINTEN = 216    # 40217
REG_OFFSET_SCHLAFEN = 217       # 40218
REG_HEIZELEMENT_KIND_VORNE = 253# 40254
REG_HEIZELEMENT_DIELE = 254     # 40255
REG_HEIZELEMENT_KIND_HINTEN = 256# 40257
REG_HEIZELEMENT_SCHLAFEN = 257  # 40258
REG_HEIZELEMENT_GLOBAL = 325    # 40326
REG_ZUGRIFF = 438               # 40439
REG_HBDE_MITTETEMPERATUR = 458  # 40459
REG_BETRIEBSSTUNDEN_FWT = 467   # 40468
REG_FILTER_STANDZEIT = 468      # 40469
REG_FILTER_NUTZZEIT = 469       # 40470

# === T300 (Holding, Slave 41 bei Tobias) ===
REG_T300_SOLL_TEMP = 2000       # 42001
REG_T300_HEIZELEMENT = 2001     # 42002
REG_T300_ZUSTAND = 2002         # 42003
REG_T300_HEIZSTAB_SOLL = 2003   # 42004
REG_T300_PV_VORRANG = 2010      # 42011
REG_T300_LEGIONELLEN = 2025     # 42026

# ──── Panel Auto-Discovery ────
# Namens-Register: ab 4x0621 (pymodbus offset 620), 10 Register pro Slot,
# 2 Latin-1 Bytes pro Register. Recherche/Entdeckung der Adressen: @Oponn4
# (siehe https://github.com/Camouflagge/proxon/pull/3). Vom Nutzer verifiziert
# gegen eine FWT 2.0 mit realem Setup (slot 0..11 getestet).
NAME_REG_BASE = 620              # pymodbus offset (= Modicon 40621)
NAME_REG_STRIDE = 10             # Register-Abstand zwischen zwei Slots
NAME_REG_COUNT = 10              # Register pro Slot (→ 20 Latin-1 Zeichen max)
PANEL_SLOT_COUNT = 12            # wir lesen bis zu 12 Slots: ZBP + HNBE + NB1..NB10

# Slot-Layout:
#   0       = ZBP  (Zentralbedienpanel / Hauptpanel, Wohnzimmer)
#   1       = HNBE (Haupt-Nebenpanel)
#   2..11   = NB1..NB10 (Nebenpanels)
SLOT_ZBP = 0
SLOT_HNBE = 1
SLOT_FIRST_NBE = 2

# Regex-Pattern für Default-Namen (Slot wird als unbenutzt gewertet, Entität
# wird NICHT angelegt). Matcht z.B. "Raum 1", "Raum 12", "raum42", "RAUM  3".
DEFAULT_NAME_REGEX = r"^Raum\s*\d+$"

# Slots, die IMMER angelegt werden – auch wenn die Namens-Lesung fehlschlägt.
# ZBP (Wohnzimmer) und HNBE sind auf praktisch jeder FWT 2.0 vorhanden.
ALWAYS_ACTIVE_SLOTS = (SLOT_ZBP, SLOT_HNBE)

# Fallback-Namen, wenn Discovery fehlschlägt oder einen Default-Namen liefert.
FALLBACK_SLOT_NAMES = {
    SLOT_ZBP: "Wohnzimmer",
    SLOT_HNBE: "Haupt-Nebenpanel",
}


def slot_key(slot: int) -> str:
    """Stable key/unique-id component for a slot.

    These keys become part of every entity's unique_id. They MUST never
    change, even if the user renames the panel in the device, otherwise
    entity history and automations would break.

        slot 0  → "zbp"      (Hauptpanel)
        slot 1  → "hnbe"     (Haupt-Nebenpanel)
        slot 2  → "nb1"
        slot 11 → "nb10"
    """
    if slot == SLOT_ZBP:
        return "zbp"
    if slot == SLOT_HNBE:
        return "hnbe"
    return f"nb{slot - SLOT_FIRST_NBE + 1}"


def slot_panel_type(slot: int) -> str:
    """Human-readable panel type label (attribute value, not unique_id)."""
    if slot == SLOT_ZBP:
        return "ZBP"
    if slot == SLOT_HNBE:
        return "HNBE"
    return f"NB{slot - SLOT_FIRST_NBE + 1}"


def slot_name_reg(slot: int) -> int:
    """Start register (pymodbus offset) of the 10-register name block."""
    return NAME_REG_BASE + slot * NAME_REG_STRIDE


def build_room_def(slot: int, name: str) -> dict:
    """Construct a room-definition dict for a given slot.

    Register addresses are derived algebraically from the slot index.
    Formulas verified via Symcon/Proxon official module AND live Modbus
    reads against a real FWT 2.0. See also PR #5 (@Oponn4).

        slot ≥ 1 (HNBE and NBx):
            temp_reg           = 587 + slot * 3  (input, int16, scale 0.1)
            mitte_reg          = 232 + slot      (holding, uint16, scale 1, °C)
            offset_reg         = 212 + slot      (holding, int16, scale 1, -3..+3)
            heiz_reg           = 252 + slot      (holding, uint16, 0/1)
            ist_offset_reg     = 189 + slot      (holding, int16, scale 0.1)
            taste_sperren_reg  = 272 + slot      (holding, uint16, 0/1)

    Middle temperature (mitte_reg): The base temperature used by the
    heating system. Target = Mitte + Offset. Default is 20°C.
    Confirmed at registers 4x0234–4x0240 (Symcon: 233+X, our: 232+slot).

    Ist-Offset (ist_offset_reg): Calibration correction for the displayed
    current temperature on the panel. E.g. -2.4 means the panel subtracts
    2.4°C from the raw sensor reading. Located at 4x0191–4x0196
    (previously incorrectly labelled as "Mitteltemperatur").

    Slot 0 (ZBP = Wohnzimmer / Hauptpanel) is special: it has a direct
    target-temperature register (40071) and no mitte/offset scheme.
    """
    key = slot_key(slot)
    panel_type = slot_panel_type(slot)

    if slot == SLOT_ZBP:
        return {
            "slot": slot,
            "key": key,
            "name": name,
            "panel_type": panel_type,
            "temp_reg": REG_TEMP_WOHNZIMMER,
            "temp_input": "input",
            "temp_scale": 0.01,
            "temp_dtype": "int16",
            "offset_reg": None,
            "soll_reg": REG_SOLL_TEMP_WOHNZIMMER,
            "soll_scale": 0.01,
            "soll_min": 10,
            "soll_max": 30,
            "heiz_reg": REG_HEIZELEMENT_WOHNZIMMER,
            "mitte_reg": None,              # ZBP hat direkte Soll-Temp, kein Mitte+Offset
            "mitte_scale": None,
            "mitte_dtype": None,
            "ist_offset_reg": REG_HBDE_MITTETEMPERATUR,  # 458 = ZBP Ist-Kalibrierung
            "ist_offset_scale": 0.1,
            "taste_sperren_reg": None,      # ZBP hat keine Tastensperre
        }

    # HNBE (slot 1) and NBx (slot ≥ 2) share the same formula-derived layout.
    return {
        "slot": slot,
        "key": key,
        "name": name,
        "panel_type": panel_type,
        "temp_reg": 587 + slot * 3,
        "temp_input": "input",
        "temp_scale": 0.1,
        "temp_dtype": "int16",
        "offset_reg": 212 + slot,
        "soll_reg": None,
        "soll_scale": None,
        "soll_min": None,
        "soll_max": None,
        "heiz_reg": 252 + slot,
        "mitte_reg": 232 + slot,            # echte Mitteltemperatur (Symcon: 233+X)
        "mitte_scale": 1,                   # scale 1, uint16, Werte ~20°C
        "mitte_dtype": "uint16",
        "ist_offset_reg": 189 + slot,       # Ist-Kalibrierung (scale 0.1, int16)
        "ist_offset_scale": 0.1,
        "taste_sperren_reg": 272 + slot,    # Tastensperre (holding, 0/1)
    }


# Mapping alte unique_id-Keys → neue slot_key() Werte.
# Wird von __init__.py async_migrate_entry genutzt, um Entitäten aus v1.8.x
# auf die neuen stabilen Slot-IDs zu migrieren, ohne dass der Nutzer seine
# Automationen, Dashboards und Historien verliert.
LEGACY_KEY_TO_SLOT_KEY = {
    "wohnzimmer":   "zbp",    # slot 0
    "kind_vorne":   "hnbe",   # slot 1 (Haupt NB)
    "diele":        "nb1",    # slot 2
    "kind_hinten":  "nb3",    # slot 4 (Register 599 → slot 4 per Formel)
    "schlafzimmer": "nb4",    # slot 5 (Register 602 → slot 5 per Formel)
}

# ──── System-Sensoren ────
SENSOR_DEFINITIONS = [
    {"register": REG_VENTILATOR_ZULUFT, "name": "Ventilator Zuluft", "uid": "vent_zuluft", "unit": "rpm", "dc": None, "sc": "measurement", "inp": "input", "dt": "uint16", "scale": 1, "icon": "mdi:fan"},
    {"register": REG_VENTILATOR_ABLUFT, "name": "Ventilator Abluft", "uid": "vent_abluft", "unit": "rpm", "dc": None, "sc": "measurement", "inp": "input", "dt": "uint16", "scale": 1, "icon": "mdi:fan"},
    {"register": REG_FEUCHTE, "name": "Luftfeuchte", "uid": "feuchte", "unit": "%", "dc": "humidity", "sc": "measurement", "inp": "input", "dt": "uint16", "scale": 1, "icon": "mdi:water-percent"},
    {"register": REG_CO2_SENSOR, "name": "CO2", "uid": "co2", "unit": "ppm", "dc": "carbon_dioxide", "sc": "measurement", "inp": "input", "dt": "uint16", "scale": 1, "icon": "mdi:molecule-co2"},
    {"register": REG_LEISTUNG_AKTUELL, "name": "Leistungsaufnahme", "uid": "leistung", "unit": "W", "dc": "power", "sc": "measurement", "inp": "input", "dt": "uint16", "scale": 0.1, "icon": "mdi:flash"},
    {"register": REG_TEMP_ZULUFT, "name": "Temperatur Zuluft", "uid": "t_zuluft", "unit": "°C", "dc": "temperature", "sc": "measurement", "inp": "input", "dt": "int16", "scale": 0.01, "icon": "mdi:thermometer"},
    {"register": REG_TEMP_ABLUFT, "name": "Temperatur Abluft", "uid": "t_abluft", "unit": "°C", "dc": "temperature", "sc": "measurement", "inp": "input", "dt": "int16", "scale": 0.01, "icon": "mdi:thermometer"},
    {"register": REG_TEMP_FORTLUFT, "name": "Temperatur Fortluft", "uid": "t_fortluft", "unit": "°C", "dc": "temperature", "sc": "measurement", "inp": "input", "dt": "int16", "scale": 0.01, "icon": "mdi:thermometer"},
    {"register": REG_TEMP_FRISCHLUFT, "name": "Temperatur Frischluft", "uid": "t_frischluft", "unit": "°C", "dc": "temperature", "sc": "measurement", "inp": "input", "dt": "int16", "scale": 0.01, "icon": "mdi:thermometer-low"},
    {"register": REG_TEMP_VERDAMPFER, "name": "Temperatur Verdampfer", "uid": "t_verdampfer", "unit": "°C", "dc": "temperature", "sc": "measurement", "inp": "input", "dt": "uint16", "scale": 0.01, "icon": "mdi:thermometer"},
    {"register": REG_TEMP_KONDENSATOR, "name": "Temperatur Kondensator", "uid": "t_kondensator", "unit": "°C", "dc": "temperature", "sc": "measurement", "inp": "input", "dt": "uint16", "scale": 0.01, "icon": "mdi:thermometer"},
    {"register": REG_TEMP_KOMPRESSOR, "name": "Temperatur Kompressor", "uid": "t_kompressor", "unit": "°C", "dc": "temperature", "sc": "measurement", "inp": "input", "dt": "uint16", "scale": 0.01, "icon": "mdi:thermometer-high"},
    {"register": REG_KOMPRESSOR_DZ, "name": "Kompressor Drehzahl", "uid": "komp_dz", "unit": "rpm", "dc": None, "sc": "measurement", "inp": "input", "dt": "uint16", "scale": 1, "icon": "mdi:engine"},
    {"register": REG_KUEHLFUNKTION_KOMP, "name": "Kühlfunktion Kompressor", "uid": "kf_komp", "unit": "°C", "dc": "temperature", "sc": "measurement", "inp": "holding", "dt": "uint16", "scale": 0.01, "icon": "mdi:snowflake-thermometer"},
    {"register": REG_KUEHLFUNKTION_KOND, "name": "Kühlfunktion Kondensator", "uid": "kf_kond", "unit": "°C", "dc": "temperature", "sc": "measurement", "inp": "holding", "dt": "uint16", "scale": 0.01, "icon": "mdi:snowflake-thermometer"},
    {"register": REG_KUEHLFUNKTION_LEIST, "name": "Kühlfunktion Leistung", "uid": "kf_leist", "unit": "%", "dc": None, "sc": "measurement", "inp": "holding", "dt": "uint16", "scale": 0.01, "icon": "mdi:snowflake"},
    {"register": REG_BETRIEBSART, "name": "Betriebsart", "uid": "betriebsart", "unit": None, "dc": None, "sc": None, "inp": "holding", "dt": "uint16", "scale": 1, "icon": "mdi:cog"},
    {"register": REG_LUEFTERSTUFE, "name": "Lüfterstufe", "uid": "luefterstufe", "unit": None, "dc": None, "sc": None, "inp": "holding", "dt": "uint16", "scale": 1, "icon": "mdi:fan-speed-3"},
    {"register": REG_INTENSIVLUEFTUNG_REST, "name": "Intensivlüftung Restzeit", "uid": "intensiv_rest", "unit": "min", "dc": "duration", "sc": None, "inp": "holding", "dt": "uint16", "scale": 1, "icon": "mdi:timer-outline"},
    {"register": REG_FILTER_NUTZZEIT, "name": "Filter Nutzzeit", "uid": "filter_nutz", "unit": "h", "dc": "duration", "sc": "total_increasing", "inp": "holding", "dt": "uint16", "scale": 1, "icon": "mdi:air-filter"},
    {"register": REG_BETRIEBSSTUNDEN_FWT, "name": "Betriebsstunden", "uid": "betriebsstd", "unit": "h", "dc": "duration", "sc": "total_increasing", "inp": "holding", "dt": "uint16", "scale": 1, "icon": "mdi:clock-outline"},
    {"register": REG_SOLL_TEMP_WOHNZIMMER, "name": "Soll-Temperatur Wohnzimmer", "uid": "soll_wz", "unit": "°C", "dc": "temperature", "sc": None, "inp": "holding", "dt": "uint16", "scale": 0.01, "icon": "mdi:thermometer-check"},
]

T300_SENSOR_DEFINITIONS = [
    {"register": REG_TEMP_T300_INPUT, "name": "T300 Wassertemperatur", "uid": "t300_temp", "unit": "°C", "dc": "temperature", "sc": "measurement", "inp": "input", "dt": "uint16", "scale": 0.1, "offset": -100, "icon": "mdi:water-thermometer"},
    {"register": REG_T300_SOLL_TEMP, "name": "T300 Soll-Temperatur", "uid": "t300_soll", "unit": "°C", "dc": "temperature", "sc": None, "inp": "holding", "dt": "int16", "scale": 0.1, "offset": 0, "icon": "mdi:thermometer-water"},
    {"register": REG_T300_HEIZSTAB_SOLL, "name": "T300 Heizstab Soll", "uid": "t300_hs_soll", "unit": "°C", "dc": "temperature", "sc": None, "inp": "holding", "dt": "int16", "scale": 0.1, "offset": 0, "icon": "mdi:thermometer-alert"},
]

SWITCH_DEFINITIONS = [
    {"register": REG_KUEHLUNG_GLOBAL, "name": "Kühlung", "uid": "kuehlung", "icon": "mdi:snowflake"},
]

T300_SWITCH_DEFINITIONS = [
    {"register": REG_T300_HEIZELEMENT, "name": "T300 Heizstab", "uid": "t300_heizstab", "icon": "mdi:water-boiler"},
    {"register": REG_T300_ZUSTAND, "name": "T300 Warmwasser", "uid": "t300_warmwasser", "icon": "mdi:water-boiler-alert"},
    {"register": REG_T300_PV_VORRANG, "name": "T300 PV-Vorrang", "uid": "t300_pv", "icon": "mdi:solar-power-variant"},
    {"register": REG_T300_LEGIONELLEN, "name": "T300 Legionellenfunktion", "uid": "t300_legio", "icon": "mdi:bacteria"},
]

BETRIEBSART_MAP = {0: "Aus", 1: "Sommer", 2: "Winter", 3: "Comfort"}
BETRIEBSART_REVERSE_MAP = {v: k for k, v in BETRIEBSART_MAP.items()}

ZUGRIFF_MAP = {0: "0", 1: "1", 2: "2", 55555: "55555"}
ZUGRIFF_REVERSE_MAP = {v: k for k, v in ZUGRIFF_MAP.items()}
