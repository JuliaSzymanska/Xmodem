import crc16
import serial
import sys
import ZbioroweDane


def main():
    # Otwieranie pliku do wyslania i pobranie tekstu
    file = open("Wysylana.txt", 'rb')
    wiadomosc = file.read()

    # Podzial tekstu na 128 bajtowe sekcje
    blok = [wiadomosc[i:i + 128] for i in range(0, len(wiadomosc), 128)]
    file.close()

    # Pobieranie numeru portu do otwarcia
    port = 'false'
    while port == 'false':
        port = input("Nadajnik: Wybierz numer portu szeregowego:\n1 - COM1\n2 - COM2\n3 - COM3\n4 - COM4\n5 - COM5\n")
        port = ZbioroweDane.wyborPortu(port)
        if port == 'false':
            print("Nadajnik: Niepoprawny numer portu. ")

    # Otwieranie portu
    print("Nadajnik: Otwieranie portu:", port)
    try:
        serialPort = serial.Serial(port, 9600, 8, serial.PARITY_NONE, serial.STOPBITS_ONE, 15)
        print("Nadajnik: Port zostal otwarty. Oczekiwanie na transmisje....")
    except:
        print("Nadajnik: Nie udało sie otworzyc portu")
        sys.exit()

    nrBloku = 1
    nrWyslanegoBloku = 0

    # Odczytywanie odpoweidzi odbiornika
    while 1:
        odpowiedz = serialPort.read()
        if odpowiedz == ZbioroweDane.CRC or odpowiedz == ZbioroweDane.NAK:
            print("Nadajnik: Zgoda na transmisje")
            break
        else:
            sys.exit()

    # Wysylanie pakietu
    print("Nadajnik: Wysylanie pakietu")
    while nrWyslanegoBloku < len(blok):
        if odpowiedz == ZbioroweDane.NAK or odpowiedz == ZbioroweDane.CRC:
            serialPort.write(ZbioroweDane.SOH)

        pakiet = bytearray(nrBloku.to_bytes(1, 'big'))
        pakiet.append(255 - nrBloku)

        # Wysyłanie numeru bloku, dopełnienie numeru bloku do 255
        serialPort.write(bytes(pakiet))

        if nrWyslanegoBloku + 1 == len(blok):
            dopel = bytearray(blok[nrWyslanegoBloku])
            while len(dopel) < 128:
                dopel.append(ZbioroweDane.SUB)
            blok[nrWyslanegoBloku] = bytes(dopel)

        # Wysyłanie bloku danych
        for i in blok[nrWyslanegoBloku]:
            serialPort.write(i.to_bytes(1, 'big'))

        # Liczenie i wysyłanie sumy kontrolnej
        sumaKontrolna = 0
        if odpowiedz == ZbioroweDane.NAK:
            for i in blok[nrWyslanegoBloku]:
                sumaKontrolna += i
            sumaKontrolna %= 256
            sumaKontrolna = bytearray(sumaKontrolna.to_bytes(1, 'big'))
        else:
            sumaKontrolna = crc16.crc16xmodem(blok[nrWyslanegoBloku])
            sumaKontrolna = bytearray(sumaKontrolna.to_bytes(2, 'big'))
        serialPort.write(bytes(sumaKontrolna))

        # Sprawdzenie statusu przesłanego bloku
        while 1:
            odpowiedzOdbierania = serialPort.read()
            if odpowiedzOdbierania == ZbioroweDane.ACK:
                print("Nadajnik: Pakiet nr.", nrWyslanegoBloku + 1, "przeslany poprawnie. ")
                nrWyslanegoBloku += 1
                if nrBloku == 255:
                    nrBloku = 1
                else:
                    nrBloku += 1
                break
            elif odpowiedzOdbierania == ZbioroweDane.NAK:
                print("Nadajnik: Pakiet nr.", nrWyslanegoBloku + 1, "przeslany nie poprawnie. Ponawiam transmisje. ")
                break
            elif odpowiedzOdbierania == ZbioroweDane.CAN:
                print("Nadajnik: Polaczenie zostalo przerwane. ")
                sys.exit()

    # Po wysłaniu wszystkich bloków, wysyłanie EOT
    print("Nadajnik: Zakonczono wysylanie ostatniego pakietu")
    while 1:
        serialPort.write(ZbioroweDane.EOT)
        odpowiedz = serialPort.read()
        if odpowiedz == ZbioroweDane.ACK:
            print("Nadajnik: Otrzymano potwierdzenie na zakonczenie transmisji. ")
            break
        if odpowiedz == ZbioroweDane.CAN:
            print("Nadajnik: Polaczenie zostalo przerwane. ")
            break

    # Zamkniecie portu, zakonczenie transmisji
    serialPort.close()
    print("Nadajnik: Transfer zostal zakonczony. ")


if __name__ == '__main__':
    main()
