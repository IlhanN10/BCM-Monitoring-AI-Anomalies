"""Persistent storage for BCM measurement time series."""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from monitoring.bcm_reader import EXPECTED_FLOAT_COUNT


class BCMDataLogger:
    """Store validated BCM measurements in a local SQLite database."""

    def __init__(self, database_path):
        if database_path != ":memory:":
            Path(database_path).parent.mkdir(parents=True, exist_ok=True)

        self.connection = sqlite3.connect(database_path)
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS bcm_measurements (
                id INTEGER PRIMARY KEY,
                collected_at TEXT NOT NULL,
                value_1 REAL NOT NULL,
                value_2 REAL NOT NULL,
                value_3 REAL NOT NULL,
                value_4 REAL NOT NULL,
                value_5 REAL NOT NULL,
                value_6 REAL NOT NULL,
                temperature REAL NOT NULL,
                value_8 REAL NOT NULL
            )
            """
        )
        self.connection.commit()

    def log_measurement(self, values, collected_at=None):
        if len(values) != EXPECTED_FLOAT_COUNT:
            raise ValueError(
                f"Es werden {EXPECTED_FLOAT_COUNT} BCM-Werte erwartet, "
                f"aber {len(values)} erhalten."
            )

        timestamp = collected_at or datetime.now(timezone.utc).isoformat()
        self.connection.execute(
            """
            INSERT INTO bcm_measurements (
                collected_at, value_1, value_2, value_3, value_4,
                value_5, value_6, temperature, value_8
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (timestamp, *values),
        )
        self.connection.commit()

    def close(self):
        self.connection.close()
