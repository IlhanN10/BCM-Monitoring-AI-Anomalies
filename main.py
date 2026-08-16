from config import DATABASE_PATH
from monitoring.bcm_reader import read_bcm_measurement
from monitoring.data_logger import BCMDataLogger
import time


def print_bcm_measurement(measurement):

    print("\n==============================")
    print("      BCM LIVE DATEN")
    print("==============================")

    print(f"v-RMS X: {measurement['v_rms_x']:.4f} mm/s")
    print(f"v-RMS Y: {measurement['v_rms_y']:.4f} mm/s")
    print(f"v-RMS Z: {measurement['v_rms_z']:.4f} mm/s")
    print(f"v-Peak X: {measurement['v_peak_x']:.4f} mm/s")
    print(f"v-Peak Y: {measurement['v_peak_y']:.4f} mm/s")
    print(f"v-Peak Z: {measurement['v_peak_z']:.4f} mm/s")
    print(f"Kontakttemperatur: {measurement['contact_temperature']:.1f} °C")
    print(f"Status Bits Main (raw): 0x{measurement['status_raw']:08X}")

    print("==============================\n")


def main():
    logger = BCMDataLogger(DATABASE_PATH)
    print("Industrial Edge Monitoring System gestartet...")
    print("Warte auf BCM Daten...\n")

    try:
        while True:
            try:
                measurement = read_bcm_measurement()
                logger.log_measurement(measurement)
                print_bcm_measurement(measurement)
            except Exception as error:
                print("Fehler beim Lesen oder Speichern der BCM-Daten:")
                print(error)

            time.sleep(1)
    except KeyboardInterrupt:
        print("\nMonitoring wird beendet.")
    finally:
        logger.close()


if __name__ == "__main__":
    main()
