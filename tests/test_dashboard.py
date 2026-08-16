import unittest

import pandas as pd

from dashboard import calculate_y_domain, select_chart_measurements


class DashboardAutoscaleTests(unittest.TestCase):
    def setUp(self):
        self.measurements = pd.DataFrame({
            "collected_at": pd.to_datetime([
                "2026-08-16T10:00:00Z",
                "2026-08-16T10:00:15Z",
                "2026-08-16T10:00:20Z",
            ]),
            "v_rms_x": [20.0, 0.2, 0.3],
            "v_rms_y": [15.0, 0.1, 0.2],
            "v_rms_z": [10.0, 0.3, 0.1],
            "contact_temperature": [28.0, 28.1, 28.2],
        })

    def test_old_vibration_peak_does_not_define_recent_axis_range(self):
        domain = calculate_y_domain(
            self.measurements,
            ["v_rms_x", "v_rms_y", "v_rms_z"],
            window_seconds=10,
            minimum_span=0.15,
            start_at_zero=True,
        )

        self.assertEqual(domain, (0, 0.345))

    def test_small_vibration_values_use_the_lower_minimum_range(self):
        measurements = self.measurements.copy()
        measurements.loc[1:, ["v_rms_x", "v_rms_y", "v_rms_z"]] = 0.1

        domain = calculate_y_domain(
            measurements,
            ["v_rms_x", "v_rms_y", "v_rms_z"],
            window_seconds=10,
            minimum_span=0.15,
            start_at_zero=True,
        )

        self.assertEqual(domain, (0, 0.15))

    def test_current_vibration_peak_expands_axis_range_with_padding(self):
        measurements = self.measurements.copy()
        measurements.loc[2, "v_rms_x"] = 2.0

        domain = calculate_y_domain(
            measurements,
            ["v_rms_x", "v_rms_y", "v_rms_z"],
            window_seconds=10,
            minimum_span=0.15,
            start_at_zero=True,
        )

        self.assertEqual(domain, (0, 2.3))

    def test_temperature_uses_a_separate_non_zero_centered_range(self):
        domain = calculate_y_domain(
            self.measurements,
            ["contact_temperature"],
            window_seconds=10,
            minimum_span=2.0,
            start_at_zero=False,
        )

        self.assertLess(domain[0], 28.1)
        self.assertGreater(domain[1], 28.2)

    def test_live_window_only_limits_displayed_measurements(self):
        displayed = select_chart_measurements(
            self.measurements, live_window_enabled=True, window_seconds=10
        )

        self.assertEqual(list(displayed.index), [1, 2])

    def test_history_view_keeps_all_selected_measurements(self):
        displayed = select_chart_measurements(
            self.measurements, live_window_enabled=False, window_seconds=10
        )

        self.assertEqual(len(displayed), 3)


if __name__ == "__main__":
    unittest.main()
