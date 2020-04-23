import serial
import sys
import ZbioroweDane
import crc16


def main():
    # Pobieranie numeru portu do otwarcia
    port = 'false'
    while port == 'false':
        port = input("Odbiornik: Wybierz numer portu szeregowego:\n1 - COM1\n2 - COM2\n3 - COM3\n4 - COM4\n5 - COM5\n")
        port = ZbioroweDane.wyborPortu(port)
        if port == 'false':
            print("Odbiornik: Niepoprawny numer portu. ")

    # Otwieranie portu
    print("Odbiornik: Otwieranie portu:", port)
    try:
        serialPort = serial.Serial(port, 9600 * 2, 8, serial.PARITY_NONE, serial.STOPBITS_ONE, 15)
        print("Odbiornik: Port zostal otwarty. Oczekiwanie na transmisje....")
    except:
        print("Odbiornik: Nie udało sie otworzyc portu")
        sys.exit()

    # Pytanie czy jest zgoda na transmisje
    while 1:
        zgoda = input("Odbiornik: zgoda na transmisje?\n1. Tak - Algebraiczna\n2. Tak - CRC\n3. Nie\n")
        if zgoda == "1":
            decyzja = ZbioroweDane.NAK
            break
        elif zgoda == "2":
            decyzja = ZbioroweDane.CRC
            break
        elif zgoda == "3":
            print("Odbiornik: Brak zgody. Transmisja zostala przerwana. ")
            sys.exit()

    # Inicjowanie polaczenia, odbieranie wysłanego bloku
    odebranyBlok = b''
    serialPort.timeout = 10
    for i in range(6):
        serialPort.write(decyzja)
        if decyzja == ZbioroweDane.NAK:
            odebranyBlok = serialPort.read(132)
        elif decyzja == ZbioroweDane.CRC:
            odebranyBlok = serialPort.read(133)
        if odebranyBlok != b'':
            break
    if odebranyBlok == b'':
        print("Odbiornik: Brak odpowiedzi. ")
        sys.exit()

    nrPakietu = 1
    calkowityBlok = b''
    while 1:
        print(odebranyBlok)

        # Sprawdzenie czy nie był to ostatni wyslany blok
        if odebranyBlok[0].to_bytes(1, 'big') == ZbioroweDane.EOT:
            print("Odbiornik: Trnasmisja zostala zakonczona. Odebrano ostatni pakiet. ")
            serialPort.write(ZbioroweDane.ACK)
            break

        # Odczytanie numeru bloku, dopelnienia numeru bloku oraz sprawdzenie czy zostaly poprawnie odczytane
        nrBloku = int(odebranyBlok[1])
        dopelnienieNrBloku = int(odebranyBlok[2])
        if dopelnienieNrBloku + nrBloku != 255:
            print("Odbiornik: Pakiet odebrano niepoprawnie. Niepoprawny numer pakeitu. Ponawiam transmisje. ")
            serialPort.write(ZbioroweDane.NAK)
            continue
        print("Odbiornik: Pakiet nr", nrPakietu, ": ", odebranyBlok[2:-1])

        # Odczytanie i obliczenie sumy kontrolnej oraz sprawdzenie rownosci sum kontrolnych
        sumaKontrolnaWyliczona = 0
        sumaKontrolnaOdebrana = 0
        if decyzja == ZbioroweDane.NAK:
            sumaKontrolnaOdebrana = odebranyBlok[-1]
            for i in odebranyBlok[3:-1]:
                sumaKontrolnaWyliczona += i
            sumaKontrolnaWyliczona %= 256
        if decyzja == ZbioroweDane.CRC:
            sumaKontrolnaOdebrana = odebranyBlok[-1] + odebranyBlok[-2] * 256
            sumaKontrolnaWyliczona = crc16.crc16xmodem(odebranyBlok[3:-2])
        if sumaKontrolnaOdebrana != sumaKontrolnaWyliczona:
            print("Odbiornik: Pakiet odebrano niepoprawnie. Niepoprawna suma kontrolna. Ponawiam transmisje. ")
            serialPort.write(ZbioroweDane.NAK)
            continue
        print("Odbiornik: Pakiet nr", nrPakietu, "odebrano poprawnie. ")
        nrPakietu += 1
        dopelnienie = bytearray(odebranyBlok)
        for i in range(len(dopelnienie)):
            if dopelnienie[i] == 26:
                if decyzja == ZbioroweDane.NAK:
                    del dopelnienie[i:-1]
                    odebranyBlok = bytes(dopelnienie)
                    break
                if decyzja == ZbioroweDane.CRC:
                    del dopelnienie[i:-2]
                    odebranyBlok = bytes(dopelnienie)
                    break
        if decyzja == ZbioroweDane.NAK:
            calkowityBlok += odebranyBlok[3:-1]
        elif decyzja == ZbioroweDane.CRC:
            calkowityBlok += odebranyBlok[3:-2]
        serialPort.write(ZbioroweDane.ACK)

        # Odczytanie kolejnego bloku
        if decyzja == ZbioroweDane.NAK:
            odebranyBlok = serialPort.read(132)
        elif decyzja == ZbioroweDane.CRC:
            odebranyBlok = serialPort.read(133)

    # Zapis do pliku calego odebranego pliku
    file = open("Odbierana.txt", 'wb+')
    file.write(calkowityBlok)
    file.close()

    # Zamkniecie portu
    serialPort.close()


if __name__ == '__main__':
    main()
