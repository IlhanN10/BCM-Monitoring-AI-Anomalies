import struct
import time
import requests
from config import BASE_URL, BCM_PASSWORD, BCM_URL, BCM_USERNAME, LOGIN_URL


HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Referer": f"{BASE_URL}/",
    "User-Agent": "BCM-Monitoring/1.0"
}


def decode_float_values(raw_bytes):
    values = []

    for i in range(0, len(raw_bytes), 4):
        chunk = raw_bytes[i:i + 4]

        if len(chunk) == 4:
            value = struct.unpack(">f", bytes(chunk))[0]
            values.append(round(value, 4))

    while len(values) < 8:
        values.append(0)

    return values


class BCMAuthenticationError(RuntimeError):
    """The IO-Link master could not be authenticated."""


class BCMClient:
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
            raise BCMAuthenticationError(
                "BCM_USERNAME und BCM_PASSWORD müssen als Umgebungsvariablen gesetzt sein."
            )

        remaining_wait = self.next_login_attempt - time.monotonic()
        if remaining_wait > 0:
            raise BCMAuthenticationError(
                f"Login wird nach einem vorherigen Fehler erst in {remaining_wait:.0f} Sekunden erneut versucht."
            )

        response = self.session.post(
            LOGIN_URL,
            json={"username": BCM_USERNAME, "password": BCM_PASSWORD},
            timeout=3
        )
        if not response.ok:
            self.next_login_attempt = time.monotonic() + 30
            try:
                error_data = response.json()
                error_message = error_data.get("message") or error_data.get("code")
            except ValueError:
                error_message = "keine JSON-Fehlerbeschreibung"

            raise BCMAuthenticationError(
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
            raise BCMAuthenticationError(
                "Login erfolgreich, aber weder Bearer-Token noch JSESSIONID erhalten. "
                f"Antwortfelder: {fields}"
            )

        self.authenticated = True
        self.next_login_attempt = 0.0

    def get_process_data(self):
        if not self.authenticated:
            self.login()

        response = self.session.get(BCM_URL, timeout=3)

        if response.status_code == 401:
            self.authenticated = False
            self.session.headers.pop("Authorization", None)
            self.login()
            response = self.session.get(BCM_URL, timeout=3)

        if response.status_code == 401:
            raise BCMAuthenticationError(
                "Der Master akzeptiert die Anmeldung für Prozessdaten nicht. "
                "Prüfe Benutzerrechte und Zugangsdaten des Master-Benutzers. "
                f"Login-Diagnose: {self.login_diagnostics}"
            )

        response.raise_for_status()
        return response.json()


client = BCMClient()


def read_bcm_values():
    data = client.get_process_data()

    if "getData" not in data:
        raise Exception(f"Keine getData Antwort: {data}")

    if "ioLink" not in data["getData"]:
        raise Exception(f"Keine IO-Link Daten: {data}")

    raw = data["getData"]["ioLink"]["value"]

    return decode_float_values(raw)
