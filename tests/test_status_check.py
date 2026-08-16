import unittest

from security.status_check import evaluate_port_status


class EvaluatePortStatusTests(unittest.TestCase):
    def test_device_online_is_reported_as_ok(self):
        result = evaluate_port_status([
            {"portNumber": 1, "deviceAlias": "master1port1", "statusInfo": "DEVICE_ONLINE"}
        ])

        self.assertEqual(result[0]["level"], "OK")
        self.assertEqual(result[0]["message"], "Gerät läuft normal.")
