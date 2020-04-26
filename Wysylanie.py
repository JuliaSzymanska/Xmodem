import crc16
import serial
import ZbioroweDane
from tkinter import *
from tkinter.ttk import *
import Zmienne


def dalej():
    Zmienne.port = str(combo.get())
    button.destroy()
    combo.destroy()
    portLabel.destroy()
    portLabelx = Label(Zmienne.window,
                       text="Nadajnik: Otwieranie portu: " + Zmienne.port,
                       font=("Arial Bold", 10))
    portLabelx.grid(column=0, row=0)
    try:
        Zmienne.serialPort = serial.Serial(Zmienne.port, 9600, 8, serial.PARITY_NONE, serial.STOPBITS_ONE, 15)
        portLabel2 = Label(Zmienne.window,
                           text="Nadajnik: Port zostal otwarty. Oczekiwanie na transmisje....",
                           font=("Arial Bold", 10))
        portLabel2.grid(column=0, row=1)
    except:
        portLabel2 = Label(Zmienne.window,
                           text="Nadajnik: Nie udało sie otworzyc portu",
                           font=("Arial Bold", 10))
        portLabel2.grid(column=0, row=1)
        return

    Zmienne.odpowiedz = Zmienne.serialPort.read()
    if Zmienne.odpowiedz == ZbioroweDane.CRC or Zmienne.odpowiedz == ZbioroweDane.NAK:
        portLabel3 = Label(Zmienne.window,
                           text="Nadajnik: Zgoda na transmisje",
                           font=("Arial Bold", 10))
        portLabel3.grid(column=0, row=2)
    else:
        sys.exit()

    # Wysylanie pakietu
    portLabel4 = Label(Zmienne.window,
                       text="Nadajnik: Wysylanie pakietu",
                       font=("Arial Bold", 10))
    portLabel4.grid(column=0, row=3)

    if Zmienne.nrBloku - 1 < len(Zmienne.blok):
        Zmienne.window.after(100, wysylanieBloku)


def wysylanieBloku():
    Zmienne.serialPort.write(ZbioroweDane.SOH)
    pakiet = bytearray(Zmienne.nrBloku.to_bytes(1, 'big'))
    pakiet.append(255 - Zmienne.nrBloku)

    # Wysyłanie numeru bloku, dopełnienie numeru bloku do 255
    Zmienne.serialPort.write(bytes(pakiet))

    if Zmienne.nrWyslanegoBloku + 1 == len(Zmienne.blok):
        dopel = bytearray(Zmienne.blok[Zmienne.nrWyslanegoBloku])
        while len(dopel) < 128:
            dopel.append(26)
        Zmienne.blok[Zmienne.nrWyslanegoBloku] = bytes(dopel)

    # Wysyłanie bloku danych
    for i in Zmienne.blok[Zmienne.nrWyslanegoBloku]:
        Zmienne.serialPort.write(i.to_bytes(1, 'big'))

    # Liczenie i wysyłanie sumy kontrolnej
    sumaKontrolna = 0
    if Zmienne.odpowiedz == ZbioroweDane.NAK:
        for i in Zmienne.blok[Zmienne.nrWyslanegoBloku]:
            sumaKontrolna += i
        sumaKontrolna %= 256
        sumaKontrolna = bytearray(sumaKontrolna.to_bytes(1, 'big'))
    else:
        sumaKontrolna = crc16.crc16xmodem(Zmienne.blok[Zmienne.nrWyslanegoBloku])
        sumaKontrolna = bytearray(sumaKontrolna.to_bytes(2, 'big'))
    Zmienne.serialPort.write(bytes(sumaKontrolna))

    # Sprawdzenie statusu przesłanego bloku
    portLabel5 = Label(Zmienne.window,
                       text="",
                       font=("Arial Bold", 10))
    portLabel5.grid(column=0, row=4)
    while 1:
        odpowiedzOdbierana = Zmienne.serialPort.read()
        if odpowiedzOdbierana == ZbioroweDane.ACK:
            portLabel5["text"] = "Nadajnik: Pakiet nr." + str(Zmienne.nrWyslanegoBloku + 1) + " przeslany poprawnie. "
            Zmienne.nrWyslanegoBloku += 1
            if Zmienne.nrBloku == 255:
                Zmienne.nrBloku = 1
            else:
                Zmienne.nrBloku += 1
            break
        elif odpowiedzOdbierana == ZbioroweDane.NAK:
            portLabel5[
                "text"] = "Nadajnik: Pakiet nr." + str(
                Zmienne.nrWyslanegoBloku + 1) + "przeslany nie poprawnie. Ponawiam transmisje. "
            break
        elif odpowiedzOdbierana == ZbioroweDane.CAN:
            portLabel5["text"] = "Nadajnik: Polaczenie zostalo przerwane. "
            sys.exit()
    if Zmienne.nrBloku - 1 == len(Zmienne.blok):
        # Po wysłaniu wszystkich bloków, wysyłanie EOT
        portLabel6 = Label(Zmienne.window,
                           text="Nadajnik: Zakonczono wysylanie ostatniego pakietu",
                           font=("Arial Bold", 10))
        portLabel6.grid(column=0, row=5)
        portLabel7 = Label(Zmienne.window,
                           text="",
                           font=("Arial Bold", 10))
        portLabel7.grid(column=0, row=6)

        while 1:
            Zmienne.serialPort.write(ZbioroweDane.EOT)
            Zmienne.odpowiedz = Zmienne.serialPort.read()
            if Zmienne.odpowiedz == ZbioroweDane.ACK:
                portLabel7["text"] = "Nadajnik: Otrzymano potwierdzenie na zakonczenie transmisji. "
                break
            if Zmienne.odpowiedz == ZbioroweDane.CAN:
                portLabel7["text"] = "Nadajnik: Polaczenie zostalo przerwane. "
                break

        # Zamkniecie portu, zakonczenie transmisji
        portLabel8 = Label(Zmienne.window,
                           text="Nadajnik: Transfer zostal zakonczony. ",
                           font=("Arial Bold", 10))
        portLabel8.grid(column=0, row=7)
    if Zmienne.nrBloku - 1 < len(Zmienne.blok):
        Zmienne.window.after(100, wysylanieBloku)


# Otwieranie pliku do wyslania i pobranie tekstu
file = open("Wysylana.txt", 'rb')
wiadomosc = file.read()

# Podzial tekstu na 128 bajtowe sekcje
Zmienne.blok = [wiadomosc[i:i + 128] for i in range(0, len(wiadomosc), 128)]
file.close()

Zmienne.window.title("Wysylanie")
Zmienne.window.geometry('400x200')
Zmienne.window.grid_columnconfigure(1, weight=5)
portLabel = Label(Zmienne.window,
                  text="Nadajnik: Wybierz numer portu szeregowego:",
                  font=("Arial Bold", 10))
portLabel.grid(column=1, row=0)
combo = Combobox(Zmienne.window)
combo['values'] = ("COM1", "COM2", "COM3", "COM4", "COM5")
combo.current(1)
combo.grid(column=1, row=1)
button = Button(Zmienne.window, text="Dalej", command=dalej)
button.grid(column=1, row=5)

Zmienne.window.mainloop()
