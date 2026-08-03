import requests


class BNIClient:
    def __init__(self, ip: str):
        self.base_url = f"http://{ip}"

    def get_masters(self):
        return requests.get(f"{self.base_url}/iolink/v1/masters").json()

    def get_identification(self):
        return requests.get(f"{self.base_url}/iolink/v1/masters/1/identification").json()

    def get_ports(self):
        return requests.get(f"{self.base_url}/iolink/v1/masters/1/ports").json()