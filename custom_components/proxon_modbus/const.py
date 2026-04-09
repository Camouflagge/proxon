"""Constants for the Proxon FWT Modbus integration."""

DOMAIN = "proxon_modbus"
DEFAULT_NAME = "Proxon FWT"
DEFAULT_PORT = 502
DEFAULT_SLAVE = 41
DEFAULT_T300_SLAVE = 41  # T300 Register sind bei den meisten über FWT Slave 41 erreichbar
DEFAULT_SCAN_INTERVAL = 30

CONF_SLAVE = "slave"
CONF_T300_ENABLED = "t300_enabled"
CONF_T300_SLAVE = "t300_slave"

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
REG_MITTETEMPERATUR_NB1 = 191   # 40192 (int16, scale 0.1)
REG_OFFSET_KIND_VORNE = 213     # 40214 (int16, scale 1 → -3..+3)
REG_OFFSET_DIELE = 214          # 40215
REG_OFFSET_KIND_HINTEN = 216    # 40217
REG_OFFSET_SCHLAFEN = 217       # 40218
REG_MITTETEMPERATUR_HNB = 233   # 40234
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

# ──── Raum-Definitionen ────
ROOM_DEFINITIONS = [
    {
        "key": "wohnzimmer", "name": "Wohnzimmer", "panel_type": "ZBP",
        "temp_reg": REG_TEMP_WOHNZIMMER, "temp_input": "input", "temp_scale": 0.01, "temp_dtype": "int16",
        "offset_reg": None, "soll_reg": REG_SOLL_TEMP_WOHNZIMMER, "soll_scale": 1,
        "soll_min": 15, "soll_max": 25,
        "heiz_reg": REG_HEIZELEMENT_WOHNZIMMER,
    },
    {
        "key": "kind_vorne", "name": "Kind Vorne", "panel_type": "Haupt NB",
        "temp_reg": REG_TEMP_KIND_VORNE, "temp_input": "input", "temp_scale": 0.1, "temp_dtype": "int16",
        "offset_reg": REG_OFFSET_KIND_VORNE,
        "soll_reg": None, "soll_scale": None, "soll_min": None, "soll_max": None,
        "heiz_reg": REG_HEIZELEMENT_KIND_VORNE,
    },
    {
        "key": "diele", "name": "Diele", "panel_type": "NB1",
        "temp_reg": REG_TEMP_DIELE, "temp_input": "input", "temp_scale": 0.1, "temp_dtype": "int16",
        "offset_reg": REG_OFFSET_DIELE,
        "soll_reg": None, "soll_scale": None, "soll_min": None, "soll_max": None,
        "heiz_reg": REG_HEIZELEMENT_DIELE,
    },
    {
        "key": "kind_hinten", "name": "Kind Hinten", "panel_type": "NB3",
        "temp_reg": REG_TEMP_KIND_HINTEN, "temp_input": "input", "temp_scale": 0.1, "temp_dtype": "int16",
        "offset_reg": REG_OFFSET_KIND_HINTEN,
        "soll_reg": None, "soll_scale": None, "soll_min": None, "soll_max": None,
        "heiz_reg": REG_HEIZELEMENT_KIND_HINTEN,
    },
    {
        "key": "schlafzimmer", "name": "Schlafzimmer", "panel_type": "NB4",
        "temp_reg": REG_TEMP_SCHLAFEN, "temp_input": "input", "temp_scale": 0.1, "temp_dtype": "int16",
        "offset_reg": REG_OFFSET_SCHLAFEN,
        "soll_reg": None, "soll_scale": None, "soll_min": None, "soll_max": None,
        "heiz_reg": REG_HEIZELEMENT_SCHLAFEN,
    },
]

# ──── System-Sensoren ────
SENSOR_DEFINITIONS = [
    {"register": REG_VENTILATOR_ZULUFT, "name": "Ventilator Zuluft", "uid": "vent_zuluft", "unit": "rpm", "dc": None, "sc": "measurement", "inp": "input", "dt": "uint16", "scale": 1, "icon": "mdi:fan"},
    {"register": REG_VENTILATOR_ABLUFT, "name": "Ventilator Abluft", "uid": "vent_abluft", "unit": "rpm", "dc": None, "sc": "measurement", "inp": "input", "dt": "uint16", "scale": 1, "icon": "mdi:fan"},
    {"register": REG_FEUCHTE, "name": "Luftfeuchte", "uid": "feuchte", "unit": "%", "dc": "humidity", "sc": "measurement", "inp": "input", "dt": "uint16", "scale": 1, "icon": "mdi:water-percent"},
    {"register": REG_CO2_SENSOR, "name": "CO2", "uid": "co2", "unit": "ppm", "dc": "carbon_dioxide", "sc": "measurement", "inp": "input", "dt": "uint16", "scale": 1, "icon": "mdi:molecule-co2"},
    {"register": REG_LEISTUNG_AKTUELL, "name": "Leistungsaufnahme", "uid": "leistung", "unit": "W", "dc": "power", "sc": "measurement", "inp": "input", "dt": "uint16", "scale": 1, "icon": "mdi:flash"},
    {"register": REG_TEMP_ZULUFT, "name": "Temperatur Zuluft", "uid": "t_zuluft", "unit": "°C", "dc": "temperature", "sc": "measurement", "inp": "input", "dt": "int16", "scale": 0.01, "icon": "mdi:thermometer"},
    {"register": REG_TEMP_ABLUFT, "name": "Temperatur Abluft", "uid": "t_abluft", "unit": "°C", "dc": "temperature", "sc": "measurement", "inp": "input", "dt": "int16", "scale": 0.01, "icon": "mdi:thermometer"},
    {"register": REG_TEMP_FORTLUFT, "name": "Temperatur Fortluft", "uid": "t_fortluft", "unit": "°C", "dc": "temperature", "sc": "measurement", "inp": "input", "dt": "int16", "scale": 0.01, "icon": "mdi:thermometer"},
    {"register": REG_TEMP_FRISCHLUFT, "name": "Temperatur Frischluft", "uid": "t_frischluft", "unit": "°C", "dc": "temperature", "sc": "measurement", "inp": "input", "dt": "int16", "scale": 0.01, "icon": "mdi:thermometer-low"},
    {"register": REG_TEMP_VERDAMPFER, "name": "Temperatur Verdampfer", "uid": "t_verdampfer", "unit": "°C", "dc": "temperature", "sc": "measurement", "inp": "input", "dt": "uint16", "scale": 0.1, "icon": "mdi:thermometer"},
    {"register": REG_TEMP_KONDENSATOR, "name": "Temperatur Kondensator", "uid": "t_kondensator", "unit": "°C", "dc": "temperature", "sc": "measurement", "inp": "input", "dt": "uint16", "scale": 0.1, "icon": "mdi:thermometer"},
    {"register": REG_TEMP_KOMPRESSOR, "name": "Temperatur Kompressor", "uid": "t_kompressor", "unit": "°C", "dc": "temperature", "sc": "measurement", "inp": "input", "dt": "uint16", "scale": 0.1, "icon": "mdi:thermometer-high"},
    {"register": REG_KOMPRESSOR_DZ, "name": "Kompressor Drehzahl", "uid": "komp_dz", "unit": "rpm", "dc": None, "sc": "measurement", "inp": "input", "dt": "uint16", "scale": 1, "icon": "mdi:engine"},
    {"register": REG_KUEHLFUNKTION_KOMP, "name": "Kühlfunktion Kompressor", "uid": "kf_komp", "unit": "°C", "dc": "temperature", "sc": "measurement", "inp": "holding", "dt": "uint16", "scale": 1, "icon": "mdi:snowflake-thermometer"},
    {"register": REG_KUEHLFUNKTION_KOND, "name": "Kühlfunktion Kondensator", "uid": "kf_kond", "unit": "°C", "dc": "temperature", "sc": "measurement", "inp": "holding", "dt": "uint16", "scale": 1, "icon": "mdi:snowflake-thermometer"},
    {"register": REG_KUEHLFUNKTION_LEIST, "name": "Kühlfunktion Leistung", "uid": "kf_leist", "unit": "%", "dc": None, "sc": "measurement", "inp": "holding", "dt": "uint16", "scale": 1, "icon": "mdi:snowflake"},
    {"register": REG_BETRIEBSART, "name": "Betriebsart", "uid": "betriebsart", "unit": None, "dc": None, "sc": None, "inp": "holding", "dt": "uint16", "scale": 1, "icon": "mdi:cog"},
    {"register": REG_LUEFTERSTUFE, "name": "Lüfterstufe", "uid": "luefterstufe", "unit": None, "dc": None, "sc": None, "inp": "holding", "dt": "uint16", "scale": 1, "icon": "mdi:fan-speed-3"},
    {"register": REG_INTENSIVLUEFTUNG_REST, "name": "Intensivlüftung Restzeit", "uid": "intensiv_rest", "unit": "min", "dc": "duration", "sc": None, "inp": "holding", "dt": "uint16", "scale": 1, "icon": "mdi:timer-outline"},
    {"register": REG_LUFTFEUCHTE_HOLDING, "name": "Luftfeuchte (Holding)", "uid": "feuchte_h", "unit": "%", "dc": "humidity", "sc": "measurement", "inp": "holding", "dt": "uint16", "scale": 1, "icon": "mdi:water-percent"},
    {"register": REG_FILTER_NUTZZEIT, "name": "Filter Nutzzeit", "uid": "filter_nutz", "unit": "h", "dc": "duration", "sc": "total_increasing", "inp": "holding", "dt": "uint16", "scale": 1, "icon": "mdi:air-filter"},
    {"register": REG_FILTER_STANDZEIT, "name": "Filter Standzeit", "uid": "filter_stand", "unit": "h", "dc": "duration", "sc": None, "inp": "holding", "dt": "uint16", "scale": 1, "icon": "mdi:air-filter"},
    {"register": REG_BETRIEBSSTUNDEN_FWT, "name": "Betriebsstunden", "uid": "betriebsstd", "unit": "h", "dc": "duration", "sc": "total_increasing", "inp": "holding", "dt": "uint16", "scale": 1, "icon": "mdi:clock-outline"},
    {"register": REG_MITTETEMPERATUR_NB1, "name": "Mittetemperatur NB1", "uid": "mitte_nb1", "unit": "°C", "dc": "temperature", "sc": "measurement", "inp": "holding", "dt": "int16", "scale": 0.1, "icon": "mdi:thermometer"},
    {"register": REG_ZUGRIFF, "name": "Modbus Zugriffsmodus", "uid": "zugriff", "unit": None, "dc": None, "sc": None, "inp": "holding", "dt": "uint16", "scale": 1, "icon": "mdi:lock-open-variant"},
    {"register": REG_SOLL_TEMP_WOHNZIMMER, "name": "Soll-Temperatur Wohnzimmer", "uid": "soll_wz", "unit": "°C", "dc": "temperature", "sc": None, "inp": "holding", "dt": "uint16", "scale": 1, "icon": "mdi:thermometer-check"},
]

T300_SENSOR_DEFINITIONS = [
    {"register": REG_TEMP_T300_INPUT, "name": "T300 Wassertemperatur", "uid": "t300_temp", "unit": "°C", "dc": "temperature", "sc": "measurement", "inp": "input", "dt": "uint16", "scale": 0.1, "offset": -100, "icon": "mdi:water-thermometer"},
    {"register": REG_T300_SOLL_TEMP, "name": "T300 Soll-Temperatur", "uid": "t300_soll", "unit": "°C", "dc": "temperature", "sc": None, "inp": "holding", "dt": "int16", "scale": 1, "offset": 0, "icon": "mdi:thermometer-water"},
    {"register": REG_T300_HEIZSTAB_SOLL, "name": "T300 Heizstab Soll", "uid": "t300_hs_soll", "unit": "°C", "dc": "temperature", "sc": None, "inp": "holding", "dt": "int16", "scale": 1, "offset": 0, "icon": "mdi:thermometer-alert"},
    {"register": REG_T300_ZUSTAND, "name": "T300 Zustand", "uid": "t300_zustand", "unit": None, "dc": None, "sc": None, "inp": "holding", "dt": "uint16", "scale": 1, "offset": 0, "icon": "mdi:water-boiler"},
]

SWITCH_DEFINITIONS = [
    {"register": REG_HEIZELEMENT_GLOBAL, "name": "Heizelemente Global", "uid": "heiz_global", "icon": "mdi:radiator"},
    {"register": REG_KUEHLUNG_GLOBAL, "name": "Kühlung", "uid": "kuehlung", "icon": "mdi:snowflake"},
    {"register": REG_PV_VORRANG, "name": "PV-Vorrang", "uid": "pv_vorrang", "icon": "mdi:solar-power"},
]

T300_SWITCH_DEFINITIONS = [
    {"register": REG_T300_HEIZELEMENT, "name": "T300 Heizstab", "uid": "t300_heizstab", "icon": "mdi:water-boiler"},
    {"register": REG_T300_PV_VORRANG, "name": "T300 PV-Vorrang", "uid": "t300_pv", "icon": "mdi:solar-power-variant"},
    {"register": REG_T300_LEGIONELLEN, "name": "T300 Legionellenfunktion", "uid": "t300_legio", "icon": "mdi:bacteria"},
]

BETRIEBSART_MAP = {0: "Aus", 1: "Eco", 2: "Komfort", 3: "Intensiv"}
BETRIEBSART_REVERSE_MAP = {v: k for k, v in BETRIEBSART_MAP.items()}
