import struct
import unittest
from unittest.mock import Mock

from monitoring.bcm_reader import (
    BCMAuthenticationError,
    BCMClient,
    BCMProcessDataError,
    EXPECTED_PROCESS_DATA_LENGTH,
    decode_profile_1_measurement,
    decode_status_bits,
    get_process_data_profile_assumption,
)


class DecodeProfile1MeasurementTests(unittest.TestCase):
    def test_decodes_seven_float_values_and_raw_status(self):
        raw = list(struct.pack(">7f", 1.25, -2.5, 0.0, 3.125, 4.0, 5.5, 23.4))
        raw.extend([0x12, 0x34, 0x56, 0x78])

        self.assertEqual(
            decode_profile_1_measurement(raw),
            {
                "v_rms_x": 1.25,
                "v_rms_y": -2.5,
                "v_rms_z": 0.0,
                "v_peak_x": 3.125,
                "v_peak_y": 4.0,
                "v_peak_z": 5.5,
                "contact_temperature": 23.4,
                "status_raw": 0x12345678,
            },
        )

    def test_rejects_incomplete_process_data(self):
        with self.assertRaisesRegex(BCMProcessDataError, "28 Byte erhalten"):
            decode_profile_1_measurement([0] * (EXPECTED_PROCESS_DATA_LENGTH - 4))

    def test_rejects_process_data_with_invalid_byte_values(self):
        with self.assertRaisesRegex(BCMProcessDataError, "ungültige Byte-Werte"):
            decode_profile_1_measurement([0] * 31 + [256])

    def test_status_bits_are_not_interpreted_as_float(self):
        self.assertEqual(decode_status_bits(bytes([0, 0, 0, 1])), 1)

    def test_profile_assumption_is_explicitly_not_api_verified(self):
        profile = get_process_data_profile_assumption()
        self.assertFalse(profile["verified_via_api"])


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
