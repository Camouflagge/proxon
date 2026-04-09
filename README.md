# Proxon FWT Modbus – Home Assistant Custom Integration

[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz/)

Custom Integration für **Proxon / Zimmermann Lüftungsheizungen** (FWT 2.0) und den **T300 Warmwasserspeicher** via Modbus TCP.

## Features

- **Config Flow** – Einrichtung komplett über die HA-UI (IP, Port, Slave ID, Scan-Intervall, T300 ja/nein)
- **30+ Sensoren** – Alle Temperaturen, Ventilator-RPMs, CO2, Feuchte, Leistung, Kompressor, Kühlfunktion, Filter, Betriebsstunden
- **Temperatursteuerung (Climate)** – Pro Raum Ist/Soll inkl. automatischer Offset-Berechnung
- **Switches** – Heizelemente pro Zone, Kühlung, PV-Vorrang, T300 Heizstab/Legionellen
- **Number** – Lüfterstufe (Slider 1-4), T300 Soll-Temperatur
- **Select** – Betriebsart (Aus/Eco/Komfort/Intensiv)
- **Device-Gruppierung** – Sauber unter "Proxon FWT" bzw. "Proxon T300"
- **Entity-Umbenennung** – Standardnamen können in HA jederzeit umbenannt werden

## Temperatursteuerung

Die Proxon arbeitet mit einem zentralen Soll-Wert (Wohnzimmer/ZBP) und Offset-Werten (-3 bis +3) für jeden Nebenraum:

| Raum | Steuerung | Register | Bereich |
|------|-----------|----------|---------|
| Wohnzimmer | Direkte Soll-Temp | 40071 | 15-25°C |
| Nebenräume | Offset zum Wohnzimmer | 40214-40218 | -3 bis +3 (→ 17-23°C bei Basis 20°C) |

In der Integration stellst du einfach die gewünschte Temperatur ein — der Offset wird automatisch berechnet.

## Hardware

- Proxon FWT 2.0 mit Modbus (X6 auf der Hauptplatine)
- RS485-zu-Ethernet Adapter (z.B. Waveshare) oder RS485-zu-USB

| Parameter | Wert |
|-----------|------|
| Baudrate | 19200 |
| Parity | Even |
| Stop Bits | 1 |
| Slave ID (FWT) | 41 |

> **Wichtig**: "Modbus schreiben" muss vom Proxon-Support auf Modus **2** gesetzt werden!

## Installation (HACS)

1. HACS → Drei-Punkte-Menü → **Custom Repositories**
2. URL: `https://github.com/Camouflagge/proxon` / Kategorie: **Integration**
3. Installieren → HA neustarten → Integration hinzufügen

## Credits

Basierend auf der HA-Community: [Thread](https://community.home-assistant.io/t/add-proxon-heating-system-to-ha-via-modbus/585674), [Stroett/HA_config_Proxon](https://github.com/Stroett/HA_config_Proxon), [AgentP38](https://github.com/AgentP38/Proxxon-HomeAssistant)

## Lizenz
MIT
