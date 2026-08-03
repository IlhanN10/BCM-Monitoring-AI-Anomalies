from flask import Flask, render_template, jsonify, request
import requests
import struct
import time
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)

BASE_URL = "http://192.168.1.1"
BCM_PORT_ALIAS = "master1port2"

TOKEN = "bj2m8jtesbi6kf5"
SESSION_ID = "y7fwmzquurrcza5"

headers = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Authorization": f"Bearer {TOKEN}",
    "Referer": f"{BASE_URL}/",
    "User-Agent": "Mozilla/5.0"
}

cookies = {
    "JSESSIONID": SESSION_ID
}

scoreboard = []


def decode_values(raw_bytes):
    values = []

    for i in range(0, len(raw_bytes), 4):
        chunk = raw_bytes[i:i + 4]

        if len(chunk) == 4:
            value = struct.unpack(">f", bytes(chunk))[0]
            values.append(round(value, 4))

    while len(values) < 8:
        values.append(0)

    return values


def read_process_data():
    url = f"{BASE_URL}/iolink/v1/devices/{BCM_PORT_ALIAS}/processdata/value?format=byteArray"

    print("BENUTZTE URL:", url)

    response = requests.get(
        url,
        headers=headers,
        cookies=cookies,
        timeout=3,
        allow_redirects=False,
        verify=False
    )

    print("STATUS:", response.status_code)
    print("TEXT:", response.text)

    data = response.json()

    if "getData" in data and "ioLink" in data["getData"]:
        raw = data["getData"]["ioLink"].get("value", [])

        if raw:
            return decode_values(raw)

    return [0, 0, 0, 0, 0, 0, 0, 0]


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/live")
def live_data():
    values = read_process_data()

    return jsonify({
        "timestamp": time.strftime("%H:%M:%S"),
        "port": BCM_PORT_ALIAS,
        "values": values,
        "temperature": values[6],
        "mainValue": values[5]
    })


@app.route("/api/save_score", methods=["POST"])
def save_score():
    data = request.json

    group_name = data.get("groupName", "Unbekannte Gruppe")
    max_value = data.get("maxValue", 0)

    scoreboard.append({
        "group": group_name,
        "maxValue": round(float(max_value), 2),
        "time": time.strftime("%H:%M:%S")
    })

    scoreboard.sort(key=lambda x: x["maxValue"], reverse=True)

    return jsonify({
        "status": "saved",
        "scoreboard": scoreboard
    })


@app.route("/api/scoreboard")
def get_scoreboard():
    return jsonify(scoreboard)


@app.route("/api/reset_scores", methods=["POST"])
def reset_scores():
    scoreboard.clear()
    return jsonify({"status": "reset"})


if __name__ == "__main__":
    print("STARTE BALLUFF BITES DASHBOARD")
    print("BASE_URL:", BASE_URL)
    print("PORT:", BCM_PORT_ALIAS)

    app.run(host="0.0.0.0", port=5000, debug=True)