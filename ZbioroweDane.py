SOH = b'\x01'
EOT = b'\x04'
ACK = b'\x06'
NAK = b'\x15'
CAN = b'\x18'
SUB = b'\x1A'
CRC = b'C'


# Funkcja zwracająca nazwe wybranego portu
def wyborPortu(chosenPort):
    ports = {
        "1": "COM1",
        "2": "COM2",
        "3": "COM3",
        "4": "COM4",
        "5": "COM5"
    }
    return ports.get(chosenPort, "false")
