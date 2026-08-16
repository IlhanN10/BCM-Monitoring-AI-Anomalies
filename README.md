# BCM Monitoring & Anomalie-Grundlage

Dieses Lern- und Portfolio-Projekt bildet ein lokales Condition-Monitoring-System
für einen Balluff BCM0003 an einem BNI XG5 IO-Link-Master. Ein Python-Collector
liest die Prozessdaten über die BNI REST API, dekodiert sie als BCM Process Data
Profile 1, speichert valide Messungen in SQLite und stellt sie in einem
Streamlit-Dashboard dar. Die gesammelten Daten sind eine Grundlage für spätere
Vibrationsanalyse und Anomalieerkennung.

Es ist kein produktionsreifes industrielles Monitoring-System.

## Quickstart

```bash
git clone https://github.com/IlhanN10/BCM-Monitoring-AI-Anomalies.git
cd BCM-Monitoring-AI-Anomalies
```

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt

$env:BCM_USERNAME = "dein-master-benutzer"
$env:BCM_PASSWORD = "dein-master-passwort"
python main.py
```

Falls die Aktivierung blockiert wird, gilt nur für das aktuelle Terminal:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

In einem zweiten, ebenfalls aktivierten Terminal:

```powershell
streamlit run dashboard.py
```

### Raspberry Pi / Linux

Falls das Paket für virtuelle Umgebungen fehlt:

```bash
sudo apt update
sudo apt install python3-venv -y
```

Dann das Projekt einrichten und starten:

```bash
git clone https://github.com/IlhanN10/BCM-Monitoring-AI-Anomalies.git
cd BCM-Monitoring-AI-Anomalies
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt

export BCM_USERNAME="dein-master-benutzer"
export BCM_PASSWORD="dein-master-passwort"
python3 main.py
```

In einem zweiten Terminal:

```bash
cd BCM-Monitoring-AI-Anomalies
source .venv/bin/activate
streamlit run dashboard.py
```

Streamlit gibt die lokale Browser-Adresse beim Start aus; üblich ist
`http://localhost:8501`.

## Hardware / Systemaufbau

- Balluff BCM0003 Condition-Monitoring-Sensor
- BNI XG5 IO-Link-Master
- Raspberry Pi oder Entwicklungsrechner im selben lokalen Netzwerk

```text
BCM Sensor
    │ IO-Link
    ▼
BNI XG5 IO-Link Master
    │ Ethernet / REST API
    ▼
Raspberry Pi / Entwicklungsrechner
    ├── Python-Datensammler
    ├── SQLite
    └── Streamlit-Dashboard
```

## Architektur

```text
BCM → IO-Link → BNI REST API → bni_client.py → bcm_reader.py
                                              ↓
                                        data_logger.py → SQLite → dashboard.py
```

- `monitoring/bni_client.py` bündelt Anmeldung, HTTP-Timeouts, Prozessdaten-
  und Portstatus-Abfragen.
- `monitoring/bcm_reader.py` dekodiert ausschließlich die 32 Byte BCM-
  Prozessdaten.
- `monitoring/data_logger.py` speichert semantisch benannte Messungen in
  SQLite.
- `main.py` führt den Collector im Sekundentakt aus.
- `dashboard.py` liest SQLite und die BNI-Portzustände lesend aus.

## Messwerte und Prozessdatenprofil

Das Projekt erwartet **BCM Process Data Profile 1 – Vibration Velocity**.

| Messwert | Einheit | Byte |
| --- | --- | --- |
| v-RMS X | mm/s | 1–4 |
| v-RMS Y | mm/s | 5–8 |
| v-RMS Z | mm/s | 9–12 |
| v-Peak X | mm/s | 13–16 |
| v-Peak Y | mm/s | 17–20 |
| v-Peak Z | mm/s | 21–24 |
| Kontakttemperatur | °C | 25–28 |
| Status Bits Main | Raw UInt32 | 29–32 |

Die ersten 28 Byte werden als sieben Big-Endian-`Float32` dekodiert. Die
letzten vier Byte sind Statusbits und werden bewusst nur als unveränderter
unsigned 32-Bit-Raw-Wert `status_raw` gespeichert. Ihre Bitbelegung ist im
Projekt nicht dokumentiert; Alarmzustände werden daher nicht geraten.

Die bekannten BNI-Endpunkte im Projekt liefern keine verlässliche Angabe zum
aktiven BCM-Profil. Profile 1 ist eine konfigurierte Annahme und muss zur
Sensorparametrierung passen.

## Konfiguration

Die Konfiguration erfolgt über Umgebungsvariablen. [.env.example](.env.example)
enthält eine sichere Vorlage, wird aber vom aktuellen Python-Code **nicht
automatisch geladen**. Setze die Variablen daher im Terminal oder über die
Umgebung deines Dienstes.

| Variable | Standardwert | Zweck |
| --- | --- | --- |
| `BCM_USERNAME` | keiner | Benutzername des BNI-Masters; für Prozessdaten erforderlich |
| `BCM_PASSWORD` | keiner | Passwort des BNI-Masters; für Prozessdaten erforderlich |
| `BCM_MASTER_IP` | `192.168.1.1` | IP-Adresse/Hostname des BNI-Masters |
| `BCM_PORT_ALIAS` | `master1port1` | Alias des BCM-Geräts am Master |
| `BCM_DATABASE_PATH` | `data/bcm_monitoring.sqlite3` | SQLite-Datei für Messungen |
| `BCM_PROCESS_DATA_PROFILE` | `profile_1_vibration_velocity` | erwartetes Prozessdatenprofil |
| `BNI_REQUEST_TIMEOUT_SECONDS` | `3` | HTTP-Timeout für BNI-Anfragen |

Beispiel für weitere optionale Werte in PowerShell:

```powershell
$env:BCM_MASTER_IP = "192.168.1.1"
$env:BCM_PORT_ALIAS = "master1port1"
$env:BCM_DATABASE_PATH = "data/bcm_monitoring.sqlite3"
```

Unter Linux/Raspberry Pi:

```bash
export BCM_MASTER_IP="192.168.1.1"
export BCM_PORT_ALIAS="master1port1"
export BCM_DATABASE_PATH="data/bcm_monitoring.sqlite3"
```

Der Code verwendet diese BNI-REST-Endpunkte:

```text
POST /api/balluff/v1/users/login
GET  /iolink/v1/devices/{BCM_PORT_ALIAS}/processdata/value?format=byteArray
GET  /iolink/v1/masters/1/ports
```

## Netzwerk prüfen

Der BNI-Master und der Raspberry Pi/PC müssen sich im passenden Netzwerk
befinden. Mit der Standardkonfiguration kann die Erreichbarkeit geprüft werden:

```bash
ping 192.168.1.1
```

Die BNI-Portübersicht ist im Dashboard sichtbar. Ein angeschlossener BCM am
Standardalias `master1port1` sollte den Status `DEVICE_ONLINE` oder `OPERATE`
als OK anzeigen.

## Collector und Dashboard starten

Der Collector und das Dashboard laufen parallel.

### Terminal 1: Datenerfassung

`main.py` liest kontinuierlich Prozessdaten, verwirft ungültige Antworten und
speichert jede gültige Messung mit UTC-Zeitstempel in SQLite.

```powershell
python main.py
```

```bash
python3 main.py
```

Beenden mit `Strg+C`.

### Terminal 2: Dashboard

```powershell
.\.venv\Scripts\Activate.ps1
streamlit run dashboard.py
```

```bash
source .venv/bin/activate
streamlit run dashboard.py
```

Das Dashboard zeigt aktuelle v-RMS- und v-Peak-Werte, Kontakttemperatur,
Zeitverläufe, den Raw-Statuswert sowie BNI-Portzustände. Das
Aktualisierungsintervall wird in der Seitenleiste gewählt.

## Datenhaltung

Der Collector legt bei Bedarf den Datenbankordner an und schreibt in die
SQLite-Tabelle `bcm_profile1_measurements`. Standardpfad ist
`data/bcm_monitoring.sqlite3`. Datenbanken und der gesamte `data/`-Ordner sind
absichtlich von Git ausgeschlossen.

## Tests

Python **3.10 oder neuer** ist erforderlich; der aktuelle Code verwendet unter
anderem `zip(..., strict=True)`. Die Entwicklungsumgebung wurde mit Python
3.14.2 geprüft.

```powershell
python -m unittest discover -s tests -v
```

```bash
python3 -m unittest discover -s tests -v
```

Die Tests benötigen keinen BNI-Master und keine Zugangsdaten. Sie prüfen
Decoder, BNI-Client-Logik und SQLite-Speicherung.

## Projektstruktur

```text
BCM-Monitoring-AI-Anomalies/
├── .env.example
├── .gitignore
├── README.md
├── config.py
├── dashboard.py
├── main.py
├── requirements.txt
├── monitoring/
│   ├── __init__.py
│   ├── bcm_reader.py
│   ├── bni_client.py
│   └── data_logger.py
└── tests/
    ├── test_bcm_reader.py
    ├── test_bni_client.py
    └── test_data_logger.py
```

`data/` entsteht zur Laufzeit und ist deshalb nicht versioniert.

## Aktueller Funktionsumfang

- [x] BNI-Login per Bearer-Token oder Session-Cookie
- [x] BCM-Prozessdaten über die BNI REST API lesen
- [x] Profile-1-Daten semantisch dekodieren
- [x] v-RMS und v-Peak für X/Y/Z anzeigen und speichern
- [x] Kontakttemperatur speichern und anzeigen
- [x] Status Bits Main als `status_raw` speichern
- [x] SQLite-Datenspeicherung
- [x] Streamlit-Dashboard mit Zeitverläufen
- [x] BNI-Portstatus im Dashboard
- [ ] aktives Prozessdatenprofil über API verifizieren
- [ ] Statusbitbelegung interpretieren
- [ ] Grenzwertüberwachung und Alarmierung
- [ ] Anomalieerkennung
- [ ] reproduzierbarer Vibrations-Versuchsstand

## Roadmap

```text
Sensor → Datenerfassung → SQLite → Feature Engineering
       → Anomalieerkennung → Bewertung/Alarm → Dashboard
```

Vorgesehene nächste Schritte:

1. Prozessdatenprofil zuverlässig verifizieren.
2. Reproduzierbaren Vibrations-Versuchsstand aufbauen.
3. Normalzustand und verschiedene Anomaliezustände aufzeichnen.
4. Datensatz und geeignete Merkmale analysieren.
5. Baseline und Grenzwerte entwickeln.
6. Danach ML-basierte Anomalieerkennung untersuchen.
7. Ergebnisse und Alarme im Dashboard darstellen.

## Sicherheit

- Keine Passwörter, Bearer-Tokens oder Session-IDs ins Repository committen.
- Zugangsdaten ausschließlich über Umgebungsvariablen oder einen geeigneten
  Secret-Store bereitstellen.
- `.env` und Datenbanken sind über `.gitignore` ausgeschlossen.
- Der Master wird aktuell über lokales `http://` angesprochen. Das ist nicht
  automatisch für Produktionsnetze geeignet; Netzwerksegmentierung und, falls
  unterstützt, HTTPS sollten geprüft werden.
