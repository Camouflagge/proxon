# Proxon FWT Modbus – Home Assistant Custom Integration

[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz/)

Custom Integration für **Proxon / Zimmermann Lüftungsheizungen** (FWT 2.0) und den **T300 Warmwasserspeicher** via Modbus TCP.

## Panel-Setup (getestet)

Diese Integration wurde mit folgender Panel-Konfiguration entwickelt und getestet:

- **Hauptpanel** (ZBP/Wohnzimmer)
- **Haupt-Nebenbedienpanel** (Kind Vorne)
- **Nebenpanel 1** (Diele)
- **Nebenpanel 3** (Kind Hinten)
- **Nebenpanel 4** (Schlafzimmer)

## Features

- **Config Flow** – Einrichtung komplett über die HA-UI (IP, Port, Slave ID, Scan-Intervall, T300 ja/nein)
- **30+ Sensoren** – Alle Temperaturen, Ventilator-RPMs, CO2, Feuchte, Leistung, Kompressor, Kühlfunktion, Filter, Betriebsstunden
- **Temperatursteuerung (Climate)** – Pro Raum Ist/Soll inkl. automatischer Offset-Berechnung, An/Aus-Schalter
- **Switches** – Heizelemente Global, Kühlung, T300 Heizstab/Warmwasser/PV-Vorrang/Legionellen
- **Number** – Lüfterstufe (1-4), Intensivlüftung (0-1440 min), Luftfeuchte Soll (0-100%), Mitteltemperatur pro Raum, T300 Soll & Heizstab Soll
- **Select** – Betriebsart (Aus/Sommer/Winter/Comfort), Zugriffsmodus
- **Device-Gruppierung** – Sauber unter "Proxon FWT" bzw. "Proxon T300"
- **Entity-Umbenennung** – Standardnamen können in HA jederzeit umbenannt werden

## Temperatursteuerung

Die Proxon arbeitet mit einem zentralen Soll-Wert (Wohnzimmer/ZBP) und einem Offset (-3 bis +3) für jedes Nebenpanel:

| Raum | Steuerung | Register | Bereich |
|------|-----------|----------|---------|
| Wohnzimmer (Hauptpanel) | Direkte Soll-Temp | 40071 | 10-30°C |
| Kind Vorne (Haupt-NB) | Offset | 40214 | -3 bis +3 |
| Diele (NB1) | Offset | 40215 | -3 bis +3 |
| Kind Hinten (NB3) | Offset | 40217 | -3 bis +3 |
| Schlafzimmer (NB4) | Offset | 40218 | -3 bis +3 |

Die Nebenpanels arbeiten mit **fester Basis 20°C**:

| Offset | Temperatur |
|--------|------------|
| -3 | 17°C |
| -2 | 18°C |
| -1 | 19°C |
| 0 | 20°C |
| +1 | 21°C |
| +2 | 22°C |
| +3 | 23°C |

In der Integration stellst du einfach die gewünschte Temperatur ein — der Offset wird automatisch berechnet.

## Schreibzugriff aktivieren (Zugriffsmodus)

Damit Home Assistant Werte auf die Proxon schreiben kann, muss der **Zugriffsmodus** auf **2** gesetzt werden. Der Wert `2` lässt sich aber nicht direkt anwählen — Proxon verlangt dafür eine Art „Bestätigungs-Trick":

1. Öffne das Dropdown **Zugriffsmodus** (Select-Entity)
2. Wähle mehrmals nacheinander **`55555`** aus
3. Sobald im Dropdown der Wert `55555` wirklich angezeigt/übernommen wird, kannst du auf **`2`** wechseln
4. Ab jetzt akzeptiert die Proxon Schreibbefehle aus HA

> **Hinweis:** Solange der Zugriffsmodus nicht auf `2` steht, werden alle Schreiboperationen (Temperatur, Lüfterstufe, Switches, …) von der Proxon ignoriert. Lesen funktioniert trotzdem.

## Hardware

- Proxon FWT 2.0 mit Modbus (X6 auf der Hauptplatine)
- RS485-zu-Ethernet Adapter (z.B. Waveshare) oder RS485-zu-USB

| Parameter | Wert |
|-----------|------|
| Baudrate | 19200 |
| Parity | Even |
| Stop Bits | 1 |
| Slave ID (FWT) | 41 |

> **Wichtig**: Damit HA Werte schreiben kann, muss der **Zugriffsmodus** auf **2** gesetzt sein – siehe Abschnitt [Schreibzugriff aktivieren](#schreibzugriff-aktivieren-zugriffsmodus).

## Installation (HACS)

1. HACS → Drei-Punkte-Menü → **Custom Repositories**
2. URL: `https://github.com/Camouflagge/proxon` / Kategorie: **Integration**
3. Installieren → HA neustarten → Integration hinzufügen

## Credits

Basierend auf der HA-Community: [Thread](https://community.home-assistant.io/t/add-proxon-heating-system-to-ha-via-modbus/585674), [Stroett/HA_config_Proxon](https://github.com/Stroett/HA_config_Proxon), [AgentP38](https://github.com/AgentP38/Proxxon-HomeAssistant)

## Lizenz
MIT
