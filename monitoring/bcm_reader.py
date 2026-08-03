import struct
import requests
from config import BCM_URL, TOKEN, SESSION_ID


HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Authorization": f"Bearer {TOKEN}",
    "Referer": "http://192.168.1.1/",
    "User-Agent": "Mozilla/5.0"
}

COOKIES = {
    "JSESSIONID": SESSION_ID
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


def read_bcm_values():
    response = requests.get(
        BCM_URL,
        headers=HEADERS,
        cookies=COOKIES,
        timeout=3
    )

    data = response.json()

    if "getData" not in data:
        raise Exception(f"Keine getData Antwort: {data}")

    if "ioLink" not in data["getData"]:
        raise Exception(f"Keine IO-Link Daten: {data}")

    raw = data["getData"]["ioLink"]["value"]

    return decode_float_values(raw)