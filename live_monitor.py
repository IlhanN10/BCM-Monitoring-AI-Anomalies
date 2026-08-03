import requests
import struct
import json
import time

URL = "http://192.168.1.1/iolink/v1/devices/master1port2/processdata/value?format=byteArray"

TOKEN = "jd469lfjls7xu7g"
SESSION_ID = "8ygzr2t149vzgdh"
 
headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/json"
}

cookies = {
    "JSESSIONID": SESSION_ID
}


def decode_float_values(raw_bytes):
    values = []

    for i in range(0, len(raw_bytes), 4):
        chunk = raw_bytes[i:i + 4]

        if len(chunk) == 4:
            value = struct.unpack(">f", bytes(chunk))[0]
            values.append(value)

    return values


def check_warnings(values):
    if len(values) < 6:
        return

    if values[3] > 10:
        print("⚠️ Starker Ausschlag bei Wert 4 erkannt!")

    if values[4] > 10:
        print("⚠️ Hohe Vibration bei Wert 5 erkannt!")

    if values[5] > 10:
        print("⚠️ Starker Stoß bei Wert 6 erkannt!")


while True:
    response = requests.get(
        URL,
        headers=headers,
        cookies=cookies
    )

    print("Status:", response.status_code)

    try:
        data = response.json()
    except Exception:
        print("Keine JSON-Antwort:")
        print(response.text)
        break

    if response.status_code == 401:
        print("Unauthorized. Token oder JSESSIONID falsch/abgelaufen.")
        print(json.dumps(data, indent=4))
        break

    if "getData" not in data:
        print("Unerwartete Antwort:")
        print(json.dumps(data, indent=4))
        break

    raw = data["getData"]["ioLink"]["value"]
    values = decode_float_values(raw)

    print("\n--- BCM Live Daten ---")

    for index, value in enumerate(values, start=1):
        print(f"Wert {index}: {value:.4f}")

    check_warnings(values)

    time.sleep(1)