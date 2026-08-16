"""Persistent storage for BCM measurement time series."""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from monitoring.bcm_reader import PROFILE_1_FIELD_NAMES


MEASUREMENT_TABLE = "bcm_profile1_measurements"
MEASUREMENT_FIELDS = (*PROFILE_1_FIELD_NAMES, "status_raw")


class BCMDataLogger:
    """Store validated BCM measurements in a local SQLite database."""

    def __init__(self, database_path):
        if database_path != ":memory:":
            Path(database_path).parent.mkdir(parents=True, exist_ok=True)

        self.connection = sqlite3.connect(database_path)
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS bcm_profile1_measurements (
                id INTEGER PRIMARY KEY,
                collected_at TEXT NOT NULL,
                v_rms_x REAL NOT NULL,
                v_rms_y REAL NOT NULL,
                v_rms_z REAL NOT NULL,
                v_peak_x REAL NOT NULL,
                v_peak_y REAL NOT NULL,
                v_peak_z REAL NOT NULL,
                contact_temperature REAL NOT NULL,
                status_raw INTEGER NOT NULL
            )
            """
        )
        self.connection.commit()

    def log_measurement(self, measurement, collected_at=None):
        if set(measurement) != set(MEASUREMENT_FIELDS):
            raise ValueError(
                "Die Messung muss genau die semantischen Profile-1-Felder enthalten."
            )

        timestamp = collected_at or datetime.now(timezone.utc).isoformat()
        self.connection.execute(
            """
            INSERT INTO bcm_profile1_measurements (
                collected_at, v_rms_x, v_rms_y, v_rms_z,
                v_peak_x, v_peak_y, v_peak_z, contact_temperature, status_raw
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (timestamp, *(measurement[field] for field in MEASUREMENT_FIELDS)),
        )
        self.connection.commit()

    def close(self):
        self.connection.close()
