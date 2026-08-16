import struct
from config import BCM_PROCESS_DATA_PROFILE

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


class BCMProcessDataError(RuntimeError):
    """The IO-Link master returned invalid process data."""
