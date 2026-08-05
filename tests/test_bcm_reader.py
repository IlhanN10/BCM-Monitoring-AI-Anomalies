import struct
import unittest
from unittest.mock import Mock

from monitoring.bcm_reader import (
    BCMAuthenticationError,
    BCMClient,
    BCMProcessDataError,
    EXPECTED_PROCESS_DATA_LENGTH,
    decode_float_values,
)


class DecodeFloatValuesTests(unittest.TestCase):
    def test_decodes_exactly_eight_big_endian_floats(self):
        expected = [1.25, -2.5, 0.0, 3.125, 4.0, 5.5, 23.4, 8.75]
        raw = list(struct.pack(">8f", *expected))

        self.assertEqual(decode_float_values(raw), expected)

    def test_rejects_incomplete_process_data(self):
        with self.assertRaisesRegex(BCMProcessDataError, "28 Byte erhalten"):
            decode_float_values([0] * (EXPECTED_PROCESS_DATA_LENGTH - 4))

    def test_rejects_process_data_with_invalid_byte_values(self):
        with self.assertRaisesRegex(BCMProcessDataError, "ungültige Byte-Werte"):
            decode_float_values([0] * 31 + [256])


class BCMClientTests(unittest.TestCase):
    def test_login_uses_bearer_token_from_response(self):
        client = BCMClient()
        response = Mock(ok=True, status_code=200, headers={})
        response.json.return_value = {"accessToken": "test-token"}
        client.session.post = Mock(return_value=response)

        with unittest.mock.patch("monitoring.bcm_reader.BCM_USERNAME", "operator"), \
             unittest.mock.patch("monitoring.bcm_reader.BCM_PASSWORD", "secret"):
            client.login()

        self.assertTrue(client.authenticated)
        self.assertEqual(client.session.headers["Authorization"], "Bearer test-token")

    def test_retries_login_once_after_unauthorized_process_data(self):
        client = BCMClient()
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
        client = BCMClient()

        with unittest.mock.patch("monitoring.bcm_reader.BCM_USERNAME", None), \
             unittest.mock.patch("monitoring.bcm_reader.BCM_PASSWORD", None), \
             self.assertRaises(BCMAuthenticationError):
            client.login()


if __name__ == "__main__":
    unittest.main()
