def evaluate_port_status(ports):
    results = []

    for port in ports:
        status = port["statusInfo"]

        if status in {"OPERATE", "DEVICE_ONLINE"}:
            level = "OK"
            message = "Gerät läuft normal."
        elif status == "COMMUNICATION_LOST":
            level = "WARNUNG"
            message = "Port erwartet Kommunikation, aber kein Gerät antwortet."
        elif status == "DEACTIVATED":
            level = "INFO"
            message = "Port ist deaktiviert oder nicht aktiv genutzt."
        else:
            level = "UNKNOWN"
            message = "Unbekannter Portstatus."

        results.append({
            "port": port["portNumber"],
            "alias": port["deviceAlias"],
            "status": status,
            "level": level,
            "message": message
        })

    return results
