import requests
import json

url = "http://192.168.1.1/iolink/v1/masters/1/identification"

response = requests.get(url)

data = response.json()

with open("json/identification.json", "w") as f:
    json.dump(data, f, indent=4)

print("Identification gespeichert.")