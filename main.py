from config import DATABASE_PATH
from monitoring.bcm_reader import read_bcm_values
from monitoring.data_logger import BCMDataLogger
import time


def print_bcm_values(values):

    print("\n==============================")
    print("      BCM LIVE DATEN")
    print("==============================")

    print(f"Wert 1: {values[0]:.4f}")
    print(f"Wert 2: {values[1]:.4f}")
    print(f"Wert 3: {values[2]:.4f}")
    print(f"Wert 4: {values[3]:.4f}")
    print(f"Wert 5: {values[4]:.4f}")
    print(f"Wert 6: {values[5]:.4f}")
    print(f"Temperatur: {values[6]:.1f} °C")
    print(f"Wert 8: {values[7]:.4f}")

    print("==============================\n")


def main():
    logger = BCMDataLogger(DATABASE_PATH)
    print("Industrial Edge Monitoring System gestartet...")
    print("Warte auf BCM Daten...\n")

    try:
        while True:
            try:
                values = read_bcm_values()
                logger.log_measurement(values)
                print_bcm_values(values)
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
