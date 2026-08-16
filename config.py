import os


BNI_IP = os.getenv("BCM_MASTER_IP", "192.168.1.1")
BCM_PORT_ALIAS = os.getenv("BCM_PORT_ALIAS", "master1port1")
BCM_USERNAME = os.getenv("BCM_USERNAME")
BCM_PASSWORD = os.getenv("BCM_PASSWORD")
DATABASE_PATH = os.getenv("BCM_DATABASE_PATH", "data/bcm_monitoring.sqlite3")
# The BNI REST endpoints currently used by this project do not expose the
# active BCM process-data profile. Profile 1 is therefore an explicit,
# documented deployment assumption and must match the sensor configuration.
BCM_PROCESS_DATA_PROFILE = os.getenv(
    "BCM_PROCESS_DATA_PROFILE", "profile_1_vibration_velocity"
)

BASE_URL = f"http://{BNI_IP}"
LOGIN_URL = f"{BASE_URL}/api/balluff/v1/users/login"
BCM_URL = f"{BASE_URL}/iolink/v1/devices/{BCM_PORT_ALIAS}/processdata/value?format=byteArray"
PORTS_URL = f"{BASE_URL}/iolink/v1/masters/1/ports"
