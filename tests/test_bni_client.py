import unittest
from unittest.mock import Mock, patch

from monitoring.bni_client import BNIAuthenticationError, BNIClient, evaluate_port_status


class BNIClientTests(unittest.TestCase):
    def test_login_uses_bearer_token_from_response(self):
        client = BNIClient()
        response = Mock(ok=True, status_code=200, headers={})
        response.json.return_value = {"accessToken": "test-token"}
        client.session.post = Mock(return_value=response)

        with patch("monitoring.bni_client.BCM_USERNAME", "operator"), \
             patch("monitoring.bni_client.BCM_PASSWORD", "secret"):
            client.login()

        self.assertTrue(client.authenticated)
        self.assertEqual(client.session.headers["Authorization"], "Bearer test-token")

    def test_retries_login_once_after_unauthorized_process_data(self):
        client = BNIClient()
        client.authenticated = True
        unauthorized = Mock(status_code=401)
        success = Mock(status_code=200)
        success.raise_for_status = Mock()
        success.json.return_value = {"getData": {"ioLink": {"value": [0] * 32}}}
        client.session.get = Mock(side_effect=[unauthorized, success])
        client.login = Mock()

        self.assertEqual(client.get_process_data(), success.json.return_value)
        client.login.assert_called_once()
        self.assertEqual(client.session.get.call_count, 2)

    def test_login_requires_credentials(self):
        client = BNIClient()

        with patch("monitoring.bni_client.BCM_USERNAME", None), \
             patch("monitoring.bni_client.BCM_PASSWORD", None), \
             self.assertRaises(BNIAuthenticationError):
            client.login()

    def test_normalizes_device_online_port_status(self):
        status = evaluate_port_status([
            {"portNumber": 1, "deviceAlias": "master1port1", "statusInfo": "DEVICE_ONLINE"}
        ])

        self.assertEqual(status[0]["level"], "OK")

    def test_reads_port_statuses_through_central_client(self):
        client = BNIClient()
        response = Mock()
        response.json.return_value = [
            {"portNumber": 1, "deviceAlias": "master1port1", "statusInfo": "DEVICE_ONLINE"}
        ]
        client.session.get = Mock(return_value=response)

        statuses = client.get_port_statuses()

        self.assertEqual(statuses[0]["alias"], "master1port1")
        client.session.get.assert_called_once()
