# Proxon FWT Modbus – Home Assistant Custom Integration

[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz/)

Custom Integration für **Proxon / Zimmermann Lüftungsheizungen** (FWT 2.0 / P2 V2.0) und den **T300 Warmwasserspeicher** — wahlweise via **Modbus TCP** (echtes Gateway), **Modbus RTU-over-TCP** (Waveshare/USR Serial-Server im Transparent-Modus) oder **Modbus Seriell / RTU** (USB-RS485-Adapter direkt am HA-Host).

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

## Hardware & Verbindungsarten

Die Integration unterstützt **drei Verbindungstypen**, die bei der Einrichtung über ein Dropdown ausgewählt werden:

### 1. Modbus TCP (echtes Gateway)
Empfohlen, wenn du ein echtes Modbus-TCP-Gateway (Protokollwandler) vor der Proxon hast. Nur zwei Eingaben:
- IP-Adresse
- Port (Standard: 502)

### 2. Modbus RTU-over-TCP (Waveshare / USR im Transparent-Modus)
Empfohlen, wenn du einen **RS485-zu-Ethernet Serial-Server** (z.B. **Waveshare**, USR-TCP232, Elfin EW11, …) im **Transparent-/Pass-Through-Modus** betreibst. Diese Adapter reichen die RTU-Frames einfach 1:1 über eine TCP-Verbindung durch — sie machen also **keine echte Protokollumwandlung**. Eingaben:
- IP-Adresse des Serial-Servers
- Port (z.B. 502, 8899, 26 … je nach Adapter)

> **Hinweis**: Wenn du nicht sicher bist, ob dein Gateway „echtes" Modbus-TCP spricht oder nur RTU transparent weiterleitet: Probiere zuerst **TCP**. Wenn das Timeouts/Paritätsfehler liefert, wechsel auf **RTU-over-TCP**. Waveshare-Adapter in der Standardkonfiguration sind meistens RTU-over-TCP.

### 3. Modbus Seriell / RTU (USB / RS485)
Empfohlen, wenn du einen **RS485-zu-USB-Adapter** direkt am HA-Host (z.B. Raspberry Pi, Proxmox VM mit USB-Passthrough) angeschlossen hast. Der Device-Pfad wird direkt eingegeben (z.B. `/dev/ttyUSB0`), alle Parameter sind Dropdowns:
- **Gerät/Port** (z.B. `/dev/ttyUSB0`, `/dev/serial/by-id/...`)
- **Baudrate** (1200–115200)
- **Datenbits** (5–8)
- **Methode** (RTU / ASCII)
- **Parität** (Even / None / Odd)
- **Stopbits** (1 / 2)

### Proxon-Standardparameter (RTU)

| Parameter | Wert |
|-----------|------|
| Baudrate | 19200 |
| Datenbits | 8 |
| Parität | Even (E) |
| Stopbits | 1 |
| Methode | RTU |
| Slave ID (FWT) | 41 |

Anschluss am Proxon: **X6 auf der Hauptplatine**.

> **Neu konfigurieren**: Über das 3-Punkte-Menü → „Neu konfigurieren" auf der Integration kannst du jederzeit zwischen TCP, RTU-over-TCP und Seriell wechseln, oder Parameter anpassen — ohne die Integration zu löschen. Entity-IDs, Historie und Automatisierungen bleiben erhalten.

> **Wichtig**: Damit HA Werte schreiben kann, muss der **Zugriffsmodus** auf **2** gesetzt sein – siehe Abschnitt [Schreibzugriff aktivieren](#schreibzugriff-aktivieren-zugriffsmodus).

## Installation (HACS)

1. HACS → Drei-Punkte-Menü → **Custom Repositories**
2. URL: `https://github.com/Camouflagge/proxon` / Kategorie: **Integration**
3. Installieren → HA neustarten → Integration hinzufügen

## Credits

Basierend auf der HA-Community: [Thread](https://community.home-assistant.io/t/add-proxon-heating-system-to-ha-via-modbus/585674), [Stroett/HA_config_Proxon](https://github.com/Stroett/HA_config_Proxon), [AgentP38](https://github.com/AgentP38/Proxxon-HomeAssistant)

## Lizenz
MIT
