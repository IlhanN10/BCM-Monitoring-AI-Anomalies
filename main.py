from monitoring.bcm_reader import read_bcm_values
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

    print("Industrial Edge Monitoring System gestartet...")
    print("Warte auf BCM Daten...\n")

    while True:

        try:

            values = read_bcm_values()

            print_bcm_values(values)

        except Exception as error:

            print("Fehler beim Lesen des BCM:")
            print(error)

        time.sleep(1)


if __name__ == "__main__":
    main()