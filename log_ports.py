import requests
import json
from datetime import datetime

url = "http://192.168.1.1/iolink/v1/masters/1/ports"

ports = requests.get(url).json()

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

log_entry = {
    "timestamp": str(datetime.now()),
    "ports": ports
}

filename = f"json/port_log_{timestamp}.json"

with open(filename, "w") as f:
    json.dump(log_entry, f, indent=4)

print(f"Log gespeichert: {filename}")