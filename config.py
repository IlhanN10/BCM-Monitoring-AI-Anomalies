BNI_IP = "192.168.1.1"
BCM_PORT_ALIAS = "master1port1"

TOKEN = "mfibrx7rkt1sj62"
SESSION_ID = "znul3md3v4s5nwa"

BCM_URL = f"http://{BNI_IP}/iolink/v1/devices/{BCM_PORT_ALIAS}/processdata/value?format=byteArray"
PORTS_URL = f"http://{BNI_IP}/iolink/v1/masters/1/ports"