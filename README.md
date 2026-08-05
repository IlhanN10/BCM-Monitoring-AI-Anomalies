<<<<<<< HEAD
# BCM-Monitoring-AI-Anomalies
Hobbyprojekt um die Grundlagen von IO Link/BCM Platform zu verstehen
=======
# BCM Monitoring & Anomalie-Grundlage

Ein leichtgewichtiges Python-Projekt zur kontinuierlichen Überwachung eines
Balluff BCM-Sensors an einem IO-Link-Master. Das Programm meldet sich am
Master an, liest die Prozessdaten des Sensors im Sekundentakt und gibt die
acht dekodierten Messwerte in der Konsole aus.

## Idee

Das Projekt bildet die technische Grundlage für ein Monitoring-System in der
Industrie. Zunächst werden valide Live-Daten zuverlässig abgefragt. Darauf
können später Funktionen wie Langzeitprotokollierung, Grenzwertüberwachung,
Port-Statuswarnungen und KI-gestützte Anomalieerkennung aufbauen.

Der Fokus der aktuellen Version liegt auf:

- einer wiederverwendbaren HTTP-Session zum IO-Link-Master,
- Anmeldung per Bearer-Token oder Session-Cookie,
- automatischer erneuter Anmeldung bei HTTP 401,
- strikter Prüfung der erwarteten Prozessdaten und
- einer einfachen Konsolenansicht für den Betrieb und die Fehlersuche.

## Projektstruktur

```text
.
├── config.py                    # Umgebungsbasierte Konfiguration und API-URLs
├── main.py                      # Konsolenprogramm mit Polling-Schleife
├── requirements.txt             # Python-Abhängigkeiten
├── monitoring/
│   └── bcm_reader.py            # Login, HTTP-Kommunikation und Float-Dekodierung
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

Die konkreten URLs werden in `config.py` aufgebaut. Das Projekt erwartet die
Balluff-Endpunkte für Login und IO-Link-Prozessdaten.

## Anwendung starten

Nach Aktivierung der virtuellen Umgebung und dem Setzen der Variablen:

```powershell
python main.py
```

Das Programm liest anschließend einmal pro Sekunde die Prozessdaten und gibt
acht Werte aus. Der siebte Wert wird derzeit als Temperatur formatiert.

Beenden mit `Strg + C`.

## Datenformat und Validierung

Der Reader erwartet im API-Feld `getData.ioLink.value` ein Byte-Array mit
genau 32 Byte. Diese werden als acht IEEE-754-Floats im Big-Endian-Format
dekodiert:

```text
32 Byte = 8 Werte × 4 Byte pro Float
```

Bei einer unvollständigen, zu langen oder ungültigen Antwort wird kein Wert
mit `0` aufgefüllt. Stattdessen erscheint eine eindeutige Fehlermeldung.
Damit können fehlerhafte Sensor- oder API-Daten nicht unbemerkt als plausible
Messwerte interpretiert werden.

## Tests ausführen

Die Tests benötigen keinen IO-Link-Master und verwenden keine echten
Zugangsdaten:

```powershell
python -m unittest discover -s tests -v
```

Getestet werden unter anderem die Float-Dekodierung, fehlerhafte Prozessdaten,
Bearer-Token-Login, fehlende Zugangsdaten und erneute Anmeldung nach HTTP 401.

## Aktueller Stand und nächste Ausbaustufen

Die Funktion `security/status_check.py` enthält bereits die Grundlogik zur
Bewertung von Port-Zuständen, ist aber noch nicht an die Polling-Schleife
angebunden. Sinnvolle nächste Erweiterungen sind:

- strukturierte Logs und ein gestaffelter Wiederholungsmechanismus bei
  Netzwerkfehlern,
- Speicherung von Zeitreihen für historische Auswertungen,
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
