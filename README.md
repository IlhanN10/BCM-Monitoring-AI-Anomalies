<<<<<<< HEAD
# BCM-Monitoring-AI-Anomalies
Hobbyprojekt um die Grundlagen von IO Link/BCM Platform zu verstehen
=======
# BCM Monitoring & Anomalie-Grundlage

Ein leichtgewichtiges Python-Projekt zur kontinuierlichen Überwachung eines
Balluff BCM0003 an einem BNI XG5 IO-Link-Master. Das Programm meldet sich am
Master an, liest 32 Byte Prozessdaten im Sekundentakt und zeigt die fachlich
benannten Messwerte des BCM Process Data Profile 1 an.

## Idee

Das Projekt bildet die technische Grundlage für ein Monitoring-System in der
Industrie. Zunächst werden valide Live-Daten zuverlässig abgefragt. Darauf
können später Funktionen wie Langzeitprotokollierung, Grenzwertüberwachung,
Port-Statuswarnungen und KI-gestützte Anomalieerkennung aufbauen.

Der Fokus der aktuellen Version liegt auf:

- einer wiederverwendbaren HTTP-Session zum IO-Link-Master,
- Anmeldung per Bearer-Token oder Session-Cookie,
- automatischer erneuter Anmeldung bei HTTP 401,
- strikter Prüfung der erwarteten Prozessdaten,
- semantischer Dekodierung von Vibrationsgeschwindigkeiten und
- einer einfachen Konsolenansicht für den Betrieb und die Fehlersuche.

## Projektstruktur

```text
.
├── config.py                    # Umgebungsbasierte Konfiguration und API-URLs
├── main.py                      # Konsolenprogramm mit Polling-Schleife
├── dashboard.py                 # Web-Dashboard für Messwerte und Port-Zustände
├── requirements.txt             # Python-Abhängigkeiten
├── monitoring/
│   ├── bcm_reader.py            # Login, HTTP-Kommunikation und Float-Dekodierung
│   └── data_logger.py           # Speicherung der Messwerte in SQLite
├── security/
│   └── status_check.py          # Vorbereitung zur Auswertung von Port-Zuständen
└── tests/
    └── test_bcm_reader.py       # Automatisierte Unit-Tests
```

## Voraussetzungen

- Python 3.10 oder neuer
- Netzwerkzugriff auf den Balluff IO-Link-Master
- Benutzerkonto mit Berechtigung zum Lesen der Prozessdaten

## Installation

Im Projektordner eine virtuelle Umgebung anlegen und die Abhängigkeiten
installieren:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Falls PowerShell die Aktivierung blockiert, kann für die aktuelle Sitzung
folgender Befehl verwendet werden:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

## Konfiguration

Die Zugangsdaten werden nicht im Quellcode gespeichert. Vor dem Start müssen
sie als Umgebungsvariablen gesetzt werden.

```powershell
$env:BCM_USERNAME = "dein-benutzername"
$env:BCM_PASSWORD = "dein-passwort"
```

Optional können Master-IP und der Gerätealias überschrieben werden:

```powershell
$env:BCM_MASTER_IP = "192.168.1.1"
$env:BCM_PORT_ALIAS = "master1port1"
```

| Variable | Standardwert | Bedeutung |
| --- | --- | --- |
| `BCM_USERNAME` | keiner | Benutzername für den Master; erforderlich |
| `BCM_PASSWORD` | keiner | Passwort für den Master; erforderlich |
| `BCM_MASTER_IP` | `192.168.1.1` | IP-Adresse oder Hostname des IO-Link-Masters |
| `BCM_PORT_ALIAS` | `master1port1` | Gerätealias des angeschlossenen BCM-Sensors |
| `BCM_DATABASE_PATH` | `data/bcm_monitoring.sqlite3` | Speicherort der lokalen SQLite-Datenbank |
| `BCM_PROCESS_DATA_PROFILE` | `profile_1_vibration_velocity` | Erwartetes BCM-Prozessdatenprofil |

Die konkreten URLs werden in `config.py` aufgebaut. Das Projekt erwartet die
Balluff-Endpunkte für Login und IO-Link-Prozessdaten.

### Process Data Profile

Das Projekt dekodiert **BCM Process Data Profile 1 – Vibration Velocity**:

| Byte | Feld | Einheit |
| --- | --- | --- |
| 1–4 | v-RMS X | mm/s |
| 5–8 | v-RMS Y | mm/s |
| 9–12 | v-RMS Z | mm/s |
| 13–16 | v-Peak X | mm/s |
| 17–20 | v-Peak Y | mm/s |
| 21–24 | v-Peak Z | mm/s |
| 25–28 | Kontakttemperatur | °C |
| 29–32 | Status Bits Main | Raw-UInt32 |

Die im Projekt verwendeten BNI-Endpunkte stellen keine zuverlässig auslesbare
Angabe zum aktiven BCM-Profil bereit. Profile 1 ist deshalb eine explizite
Annahme (`BCM_PROCESS_DATA_PROFILE=profile_1_vibration_velocity`) und muss mit
der Sensorparametrierung übereinstimmen. Die Bitbelegung von `Status Bits Main`
ist im Projekt nicht dokumentiert; die Software speichert und zeigt deshalb
nur den unverfälschten Raw-Wert, ohne Alarmbits zu erraten.

## Anwendung starten

Nach Aktivierung der virtuellen Umgebung und dem Setzen der Variablen:

```powershell
python main.py
```

Das Programm liest anschließend einmal pro Sekunde die Prozessdaten und gibt
RMS- und Peak-Vibrationsgeschwindigkeiten je Achse, die Kontakttemperatur und
den unveränderten Status-Raw-Wert aus.
Jede erfolgreiche Messung wird zusätzlich mit einem UTC-Zeitstempel in der
SQLite-Datenbank gespeichert. Der Standardpfad `data/` ist von Git
ausgeschlossen.

Beenden mit `Strg + C`.

## Datenformat und Validierung

Der Reader erwartet im API-Feld `getData.ioLink.value` ein Byte-Array mit
genau 32 Byte. Diese werden als acht IEEE-754-Floats im Big-Endian-Format
dekodiert:

```text
28 Byte = 7 Float32-Werte × 4 Byte, danach 4 Byte Status Bits Main
```

Bei einer unvollständigen, zu langen oder ungültigen Antwort wird kein Wert
mit `0` aufgefüllt. Die letzten vier Byte werden nie als Float interpretiert.
Stattdessen erscheint eine eindeutige Fehlermeldung. Damit können fehlerhafte
Sensor- oder API-Daten nicht unbemerkt als plausible Messwerte interpretiert
werden.

## Tests ausführen

Die Tests benötigen keinen IO-Link-Master und verwenden keine echten
Zugangsdaten:

```powershell
python -m unittest discover -s tests -v
```

Getestet werden unter anderem die Float-Dekodierung, fehlerhafte Prozessdaten,
Bearer-Token-Login, fehlende Zugangsdaten und erneute Anmeldung nach HTTP 401.

## Dashboard starten

Das Dashboard liest die bereits gespeicherten Messdaten aus SQLite und die
aktuelle Portübersicht des BNI-Masters. Der Datensammler muss deshalb in einem
separaten Terminal laufen:

```powershell
python main.py
```

In einem zweiten Terminal die virtuelle Umgebung aktivieren und starten:

```powershell
.\.venv\Scripts\Activate.ps1
streamlit run dashboard.py
```

Anschließend zeigt Streamlit die lokale Browser-Adresse an, normalerweise
`http://localhost:8501`. Das Dashboard enthält aktuelle Kennzahlen,
Messverläufe, Zeitpunkt der letzten Speicherung und die BNI-Portzustände. Das
Aktualisierungsintervall lässt sich in der Seitenleiste einstellen.

## Aktueller Stand und nächste Ausbaustufen

Die Funktion `security/status_check.py` bewertet die vom BNI-Master gelieferten
Port-Zustände; `DEVICE_ONLINE` und `OPERATE` gelten dabei als OK. Die Abfrage
ist noch nicht an die Polling-Schleife angebunden. Sinnvolle nächste
Erweiterungen sind:

- strukturierte Logs und ein gestaffelter Wiederholungsmechanismus bei
  Netzwerkfehlern,
- Integration der Port-Zustandsüberwachung,
- Grenzwerte und Alarmierung sowie
- Anomalieerkennung auf Basis der gesammelten Messdaten.

## Sicherheit

Zugangsdaten gehören ausschließlich in Umgebungsvariablen oder einen sicheren
Secret-Store und dürfen nicht eingecheckt werden. Der Master wird aktuell per
`http://` angesprochen. In produktiven Netzen sollte geprüft werden, ob HTTPS
verfügbar ist, und der Zugriff auf ein isoliertes, vertrauenswürdiges
Industrienetz beschränkt werden.
>>>>>>> master
