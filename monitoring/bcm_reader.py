import struct
import time
import requests
from config import (
    BASE_URL,
    BCM_PASSWORD,
    BCM_PROCESS_DATA_PROFILE,
    BCM_URL,
    BCM_USERNAME,
    LOGIN_URL,
)


HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Referer": f"{BASE_URL}/",
    "User-Agent": "BCM-Monitoring/1.0"
}

BYTES_PER_FLOAT = 4
PROFILE_1_FLOAT_COUNT = 7
STATUS_BYTES_LENGTH = 4
EXPECTED_PROCESS_DATA_LENGTH = (PROFILE_1_FLOAT_COUNT * BYTES_PER_FLOAT) + STATUS_BYTES_LENGTH

PROFILE_1_FIELD_NAMES = (
    "v_rms_x",
    "v_rms_y",
    "v_rms_z",
    "v_peak_x",
    "v_peak_y",
    "v_peak_z",
    "contact_temperature",
)


def get_process_data_profile_assumption():
    """Describe the configured profile without claiming a runtime verification.

    The currently known BNI endpoints in this project provide port state and
    process data, but no documented field for the active BCM process-data
    profile. The deployment must therefore configure the BCM for Profile 1.
    """
    return {
        "name": BCM_PROCESS_DATA_PROFILE,
        "verified_via_api": False,
        "reason": "Kein Endpoint zum Auslesen des aktiven BCM-Profils im Projekt vorhanden.",
    }


def _as_process_data_bytes(raw_bytes):
    if not isinstance(raw_bytes, (bytes, bytearray, list, tuple)):
        raise BCMProcessDataError(
            "IO-Link-Prozessdaten müssen als Byte-Array geliefert werden."
        )

    try:
        payload = bytes(raw_bytes)
    except (TypeError, ValueError) as error:
        raise BCMProcessDataError(
            "IO-Link-Prozessdaten enthalten ungültige Byte-Werte."
        ) from error

    if len(payload) != EXPECTED_PROCESS_DATA_LENGTH:
        raise BCMProcessDataError(
            "Ungültige Länge der IO-Link-Prozessdaten: "
            f"{len(payload)} Byte erhalten, {EXPECTED_PROCESS_DATA_LENGTH} Byte erwartet."
        )

    return payload


def decode_status_bits(raw_status_bytes):
    """Return Status Bits Main as an unsigned 32-bit raw value.

    The bit positions are not available in the checked-in project
    documentation. Do not infer alarm meaning from this raw value yet.
    """
    if not isinstance(raw_status_bytes, (bytes, bytearray)) or len(raw_status_bytes) != STATUS_BYTES_LENGTH:
        raise BCMProcessDataError("Status Bits Main müssen genau 4 Byte enthalten.")
    return int.from_bytes(raw_status_bytes, byteorder="big", signed=False)


def decode_profile_1_measurement(raw_bytes):
    """Decode BCM Profile 1 (Vibration Velocity) process data.

    Bytes 1-28 contain seven big-endian Float32 values. Bytes 29-32 are
    Status Bits Main and deliberately are not interpreted as a Float32.
    """
    payload = _as_process_data_bytes(raw_bytes)
    float_values = [
        round(struct.unpack(">f", payload[offset:offset + BYTES_PER_FLOAT])[0], 4)
        for offset in range(0, PROFILE_1_FLOAT_COUNT * BYTES_PER_FLOAT, BYTES_PER_FLOAT)
    ]
    measurement = dict(zip(PROFILE_1_FIELD_NAMES, float_values, strict=True))
    measurement["status_raw"] = decode_status_bits(payload[-STATUS_BYTES_LENGTH:])
    return measurement


class BCMAuthenticationError(RuntimeError):
    """The IO-Link master could not be authenticated."""


class BCMProcessDataError(RuntimeError):
    """The IO-Link master returned invalid process data."""


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


def read_bcm_measurement():
    data = client.get_process_data()

    try:
        raw = data["getData"]["ioLink"]["value"]
    except (KeyError, TypeError) as error:
        raise BCMProcessDataError(
            "Ungültige API-Antwort: getData.ioLink.value fehlt."
        ) from error

    return decode_profile_1_measurement(raw)
