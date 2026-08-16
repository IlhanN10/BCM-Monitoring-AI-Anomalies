import sqlite3
import tempfile
import unittest
from pathlib import Path

from monitoring.data_logger import BCMDataLogger


class BCMDataLoggerTests(unittest.TestCase):
    def test_stores_measurement_with_timestamp(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            database_path = Path(temporary_directory) / "measurements.sqlite3"
            logger = BCMDataLogger(database_path)
            logger.log_measurement({
                "v_rms_x": 1.0, "v_rms_y": 2.0, "v_rms_z": 3.0,
                "v_peak_x": 4.0, "v_peak_y": 5.0, "v_peak_z": 6.0,
                "contact_temperature": 20.5, "status_raw": 7,
            }, collected_at="2026-08-16T10:00:00+00:00")
            logger.close()

            connection = sqlite3.connect(database_path)
            row = connection.execute(
                "SELECT collected_at, v_rms_x, contact_temperature, status_raw "
                "FROM bcm_profile1_measurements"
            ).fetchone()
            connection.close()

        self.assertEqual(row, ("2026-08-16T10:00:00+00:00", 1.0, 20.5, 7))

    def test_rejects_measurement_with_wrong_value_count(self):
        logger = BCMDataLogger(":memory:")
        with self.assertRaisesRegex(ValueError, "semantischen Profile-1-Felder"):
            logger.log_measurement({"v_rms_x": 1.0})
        logger.close()
