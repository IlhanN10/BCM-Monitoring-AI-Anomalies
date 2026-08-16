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
            logger.log_measurement(
                [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 20.5, 8.0],
                collected_at="2026-08-16T10:00:00+00:00",
            )
            logger.close()

            connection = sqlite3.connect(database_path)
            row = connection.execute(
                "SELECT collected_at, value_1, temperature FROM bcm_measurements"
            ).fetchone()
            connection.close()

        self.assertEqual(row, ("2026-08-16T10:00:00+00:00", 1.0, 20.5))

    def test_rejects_measurement_with_wrong_value_count(self):
        logger = BCMDataLogger(":memory:")
        with self.assertRaisesRegex(ValueError, "8 BCM-Werte erwartet"):
            logger.log_measurement([1.0] * 7)
        logger.close()
