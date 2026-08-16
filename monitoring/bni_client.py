"""Single HTTP client for the BNI XG5 IO-Link master."""

import time

import requests

from config import (
    BASE_URL,
    BCM_PASSWORD,
    BCM_URL,
    BCM_USERNAME,
    LOGIN_URL,
    PORTS_URL,
    REQUEST_TIMEOUT_SECONDS,
)
from monitoring.bcm_reader import BCMProcessDataError, decode_profile_1_measurement


HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Referer": f"{BASE_URL}/",
    "User-Agent": "BCM-Monitoring/1.0",
}

PORT_STATUS_DETAILS = {
    "OPERATE": ("OK", "Gerät läuft normal."),
    "DEVICE_ONLINE": ("OK", "Gerät läuft normal."),
    "COMMUNICATION_LOST": ("WARNUNG", "Port erwartet Kommunikation, aber kein Gerät antwortet."),
    "DEACTIVATED": ("INFO", "Port ist deaktiviert oder nicht aktiv genutzt."),
}


class BNIAuthenticationError(RuntimeError):
    """The IO-Link master could not be authenticated."""


class BNIResponseError(RuntimeError):
    """The IO-Link master returned an unexpected API response."""


class BNINetworkError(RuntimeError):
    """The IO-Link master could not be reached."""


def evaluate_port_status(ports):
    """Normalize raw BNI port states for display without changing the master."""
    results = []
    for port in ports:
        try:
            status = port["statusInfo"]
            port_number = port["portNumber"]
            alias = port["deviceAlias"]
        except (KeyError, TypeError) as error:
            raise BNIResponseError("Ungültiger Eintrag in der BNI-Portübersicht.") from error

        level, message = PORT_STATUS_DETAILS.get(status, ("UNKNOWN", "Unbekannter Portstatus."))
        results.append({
            "port": port_number,
            "alias": alias,
            "status": status,
            "level": level,
            "message": message,
        })
    return results


class BNIClient:
    """Session-based access to BNI login, BCM process data and port states."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.authenticated = False
        self.login_diagnostics = {}
        self.next_login_attempt = 0.0

    @staticmethod
    def _get_bearer_token(response):
        try:
            payload = response.json()
        except ValueError:
            payload = {}

        token = (
            payload.get("bearer")
            or payload.get("Bearer")
            or payload.get("token")
            or payload.get("accessToken")
        )
        authorization = response.headers.get("Authorization", "")
        if not token and authorization.lower().startswith("bearer "):
            token = authorization[7:]
        return token, payload

    def login(self):
        if not BCM_USERNAME or not BCM_PASSWORD:
            raise BNIAuthenticationError(
                "BCM_USERNAME und BCM_PASSWORD müssen als Umgebungsvariablen gesetzt sein."
            )

        remaining_wait = self.next_login_attempt - time.monotonic()
        if remaining_wait > 0:
            raise BNIAuthenticationError(
                f"Login wird nach einem vorherigen Fehler erst in {remaining_wait:.0f} Sekunden erneut versucht."
            )

        response = self.session.post(
            LOGIN_URL,
            json={"username": BCM_USERNAME, "password": BCM_PASSWORD},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        if not response.ok:
            self.next_login_attempt = time.monotonic() + 30
            try:
                error_data = response.json()
                error_message = error_data.get("message") or error_data.get("code")
            except ValueError:
                error_message = "keine JSON-Fehlerbeschreibung"
            raise BNIAuthenticationError(
                f"Balluff-Login fehlgeschlagen (HTTP {response.status_code}): {error_message}"
            )

        bearer_token, payload = self._get_bearer_token(response)
        self.login_diagnostics = {
            "http_status": response.status_code,
            "response_fields": sorted(payload) if isinstance(payload, dict) else [],
            "cookie_names": sorted(cookie.name for cookie in self.session.cookies),
        }
        if bearer_token:
            self.session.headers["Authorization"] = f"Bearer {bearer_token.strip()}"
        elif "JSESSIONID" not in self.session.cookies:
            fields = ", ".join(sorted(payload)) if isinstance(payload, dict) else "keine JSON-Felder"
            raise BNIAuthenticationError(
                "Login erfolgreich, aber weder Bearer-Token noch JSESSIONID erhalten. "
                f"Antwortfelder: {fields}"
            )

        self.authenticated = True
        self.next_login_attempt = 0.0

    def get_process_data(self):
        if not self.authenticated:
            self.login()

        response = self.session.get(BCM_URL, timeout=REQUEST_TIMEOUT_SECONDS)
        if response.status_code == 401:
            self.authenticated = False
            self.session.headers.pop("Authorization", None)
            self.login()
            response = self.session.get(BCM_URL, timeout=REQUEST_TIMEOUT_SECONDS)

        if response.status_code == 401:
            raise BNIAuthenticationError(
                "Der Master akzeptiert die Anmeldung für Prozessdaten nicht. "
                f"Login-Diagnose: {self.login_diagnostics}"
            )
        response.raise_for_status()
        return response.json()

    def read_bcm_measurement(self):
        data = self.get_process_data()
        try:
            raw = data["getData"]["ioLink"]["value"]
        except (KeyError, TypeError) as error:
            raise BCMProcessDataError(
                "Ungültige API-Antwort: getData.ioLink.value fehlt."
            ) from error
        return decode_profile_1_measurement(raw)

    def get_port_statuses(self):
        try:
            response = self.session.get(PORTS_URL, timeout=REQUEST_TIMEOUT_SECONDS)
            response.raise_for_status()
        except requests.RequestException as error:
            raise BNINetworkError("BNI-Portübersicht ist nicht erreichbar.") from error
        try:
            ports = response.json()
        except ValueError as error:
            raise BNIResponseError("BNI-Portübersicht ist kein gültiges JSON.") from error
        if not isinstance(ports, list):
            raise BNIResponseError("BNI-Portübersicht muss eine Liste sein.")
        return evaluate_port_status(ports)
