"""Industrial dashboard for BCM Profile 1 vibration-velocity measurements."""

import sqlite3
from pathlib import Path

import pandas as pd
import requests
import streamlit as st

from config import BCM_PORT_ALIAS, DATABASE_PATH, PORTS_URL
from monitoring.bcm_reader import get_process_data_profile_assumption
from monitoring.data_logger import MEASUREMENT_TABLE
from security.status_check import evaluate_port_status


MEASUREMENT_COLUMNS = [
    "collected_at", "v_rms_x", "v_rms_y", "v_rms_z", "v_peak_x", "v_peak_y",
    "v_peak_z", "contact_temperature", "status_raw",
]


def load_measurements(database_path, limit):
    """Load Profile-1 measurements in chronological order."""
    if not Path(database_path).is_file():
        return pd.DataFrame(columns=MEASUREMENT_COLUMNS)

    try:
        with sqlite3.connect(database_path) as connection:
            table_exists = connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
                (MEASUREMENT_TABLE,),
            ).fetchone()
            if not table_exists:
                return pd.DataFrame(columns=MEASUREMENT_COLUMNS)
            measurements = pd.read_sql_query(
                f"""
                SELECT collected_at, v_rms_x, v_rms_y, v_rms_z,
                       v_peak_x, v_peak_y, v_peak_z, contact_temperature, status_raw
                FROM {MEASUREMENT_TABLE}
                ORDER BY id DESC
                LIMIT ?
                """,
                connection,
                params=(limit,),
            )
    except sqlite3.Error as error:
        st.error(f"Die Messdatenbank konnte nicht gelesen werden: {error}")
        return pd.DataFrame(columns=MEASUREMENT_COLUMNS)

    measurements["collected_at"] = pd.to_datetime(measurements["collected_at"], utc=True)
    return measurements.sort_values("collected_at")


@st.cache_data(ttl=5)
def load_port_states():
    """Read the current BNI port overview without changing master settings."""
    try:
        response = requests.get(PORTS_URL, timeout=3)
        response.raise_for_status()
        return evaluate_port_status(response.json()), None
    except (requests.RequestException, ValueError, KeyError, TypeError) as error:
        return [], str(error)


def render_velocity_metrics(latest_measurement):
    st.subheader("Aktuelle Vibrationsgeschwindigkeit")
    rms_columns = st.columns(3)
    for column, axis in zip(rms_columns, ("x", "y", "z"), strict=True):
        column.metric(f"v-RMS {axis.upper()}", f"{latest_measurement[f'v_rms_{axis}']:.4f} mm/s")

    peak_columns = st.columns(3)
    for column, axis in zip(peak_columns, ("x", "y", "z"), strict=True):
        column.metric(f"v-Peak {axis.upper()}", f"{latest_measurement[f'v_peak_{axis}']:.4f} mm/s")

    temperature_column, status_column = st.columns(2)
    temperature_column.metric("Kontakttemperatur", f"{latest_measurement['contact_temperature']:.1f} °C")
    status_column.metric("Status Bits Main (raw)", f"0x{int(latest_measurement['status_raw']):08X}")


def render_charts(measurements):
    st.subheader("Messverlauf")
    rms_tab, peak_tab, temperature_tab = st.tabs(
        ["v-RMS (mm/s)", "v-Peak (mm/s)", "Kontakttemperatur (°C)"]
    )

    with rms_tab:
        st.line_chart(
            measurements.set_index("collected_at")[["v_rms_x", "v_rms_y", "v_rms_z"]].rename(
                columns={"v_rms_x": "X", "v_rms_y": "Y", "v_rms_z": "Z"}
            ), height=300,
        )
    with peak_tab:
        st.line_chart(
            measurements.set_index("collected_at")[["v_peak_x", "v_peak_y", "v_peak_z"]].rename(
                columns={"v_peak_x": "X", "v_peak_y": "Y", "v_peak_z": "Z"}
            ), height=300,
        )
    with temperature_tab:
        st.line_chart(
            measurements.set_index("collected_at")[["contact_temperature"]].rename(
                columns={"contact_temperature": "Kontakttemperatur"}
            ), height=300,
        )


def render_live_data(record_limit):
    measurements = load_measurements(DATABASE_PATH, record_limit)
    port_states, port_error = load_port_states()

    summary_columns = st.columns(3)
    summary_columns[0].metric("Messungen in Ansicht", f"{len(measurements):,}")
    summary_columns[1].metric("Datenbank", Path(DATABASE_PATH).name)
    summary_columns[2].metric(
        "Letzte Messung",
        measurements.iloc[-1]["collected_at"].strftime("%d.%m.%Y %H:%M:%S UTC")
        if not measurements.empty else "Keine Daten",
    )

    if measurements.empty:
        st.warning("Noch keine Profile-1-Messdaten gefunden. Starte `python main.py`, damit neue, fachlich korrekt dekodierte Werte gespeichert werden.")
    else:
        latest_measurement = measurements.iloc[-1]
        render_velocity_metrics(latest_measurement)
        st.info("Sensorstatus: Die genaue Bitbelegung von Status Bits Main ist nicht im Projekt dokumentiert. Daher wird nur der Raw-Wert angezeigt.")
        render_charts(measurements)

    st.subheader("BNI-Portzustände")
    if port_error:
        st.error(f"Portübersicht nicht erreichbar: {port_error}")
        return

    target_port = next((port for port in port_states if port["alias"] == BCM_PORT_ALIAS), None)
    if target_port:
        if target_port["level"] == "OK":
            st.success(f"{target_port['alias']}: {target_port['status']} – {target_port['message']}")
        elif target_port["level"] == "WARNUNG":
            st.warning(f"{target_port['alias']}: {target_port['status']} – {target_port['message']}")
        else:
            st.info(f"{target_port['alias']}: {target_port['status']} – {target_port['message']}")
    st.dataframe(pd.DataFrame(port_states), width="stretch", hide_index=True)


def main():
    st.set_page_config(page_title="BCM Condition Monitoring", page_icon="📈", layout="wide")
    st.markdown("""
        <style>
        [data-testid="stAppViewContainer"] { background: #081018; color: #e7eef7; }
        [data-testid="stHeader"] { background: rgba(0, 0, 0, 0); }
        [data-testid="stMetric"] { background: #101d2a; border: 1px solid #1d4f77; border-radius: 8px; padding: 12px; }
        </style>
        """, unsafe_allow_html=True)
    st.title("BCM Condition Monitoring")
    st.caption("Profile 1 – Vibration Velocity | Industrial Edge Dashboard")

    profile_assumption = get_process_data_profile_assumption()
    with st.sidebar:
        st.header("Ansicht")
        record_limit = st.select_slider("Messwerte im Diagramm", options=[60, 300, 900, 3600], value=300)
        refresh_seconds = st.select_slider(
            "Automatisch aktualisieren", options=[5, 10, 30, 60], value=5,
            format_func=lambda seconds: f"alle {seconds} Sekunden",
        )
        if st.button("Jetzt aktualisieren", width="stretch"):
            st.cache_data.clear()
            st.rerun()
        st.divider()
        st.caption(f"Prozessdatenprofil: {profile_assumption['name']}")
        st.warning("Profil 1 ist aktuell eine dokumentierte Konfigurationsannahme, keine API-Verifikation.")

    @st.fragment(run_every=f"{refresh_seconds}s")
    def live_dashboard():
        render_live_data(record_limit)

    live_dashboard()


if __name__ == "__main__":
    main()
