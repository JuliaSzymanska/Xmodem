import serial
import ZbioroweDane
import crc16
import ZmienOdbieranie
from tkinter import *
from tkinter.ttk import *


# ------------------------------------------------------- Otwieranie portow i nawiazywanie polaczenia -------------------------------------------------------
def dalej():
    ZmienOdbieranie.port = str(combo.get())
    button.destroy()
    combo.destroy()
    combo1.destroy()
    portLabel3.destroy()
    portLabel.destroy()
    portLabelx = Label(ZmienOdbieranie.window,
                       text="Odbiornik: Otwieranie portu: " + ZmienOdbieranie.port,
                       font=("Arial Bold", 10))
    portLabelx.grid(column=0, row=0)

    # Otwieranie wybranego portu
    try:
        ZmienOdbieranie.serialPort = serial.Serial(ZmienOdbieranie.port, 9600, 8, serial.PARITY_NONE,
                                                   serial.STOPBITS_ONE, 15)
        portLabel2 = Label(ZmienOdbieranie.window,
                           text="Odbiornik: Port zostal otwarty. Oczekiwanie na transmisje....",
                           font=("Arial Bold", 10))
        portLabel2.grid(column=0, row=1)
    except:
        portLabel2 = Label(ZmienOdbieranie.window,
                           text="Odbiornik: Nie udało sie otworzyc portu",
                           font=("Arial Bold", 10))
        portLabel2.grid(column=0, row=1)
        return

    # Inicjowanie polaczenia, odbieranie wysłanego bloku
    ZmienOdbieranie.serialPort.timeout = 10
    for i in range(6):
        ZmienOdbieranie.serialPort.write(ZmienOdbieranie.decyzja)
        if ZmienOdbieranie.decyzja == ZbioroweDane.NAK:
            ZmienOdbieranie.odebranyBlok = ZmienOdbieranie.serialPort.read(132)
        elif ZmienOdbieranie.decyzja == ZbioroweDane.CRC:
            ZmienOdbieranie.odebranyBlok = ZmienOdbieranie.serialPort.read(133)
        if ZmienOdbieranie.odebranyBlok != b'':
            break
    if ZmienOdbieranie.odebranyBlok == b'':
        print("Odbiornik: Brak odpowiedzi. ")
        sys.exit()

    # Odczytywanie odebranego bloku, odbieranie kolejnych blokow
    if not ZmienOdbieranie.flag:
        ZmienOdbieranie.window.after(100, odbieranieBloku)


# ------------------------------------------------------------- Odbieranie blokow ---------------------------------------------------------------------
def odbieranieBloku():
    portLabel3 = Label(ZmienOdbieranie.window,
                       text="Odbiornik: Odbieram pakiet nr." + str(ZmienOdbieranie.nrPakietu),
                       font=("Arial Bold", 10))
    portLabel3.grid(column=0, row=2)

    portLabel4 = Label(ZmienOdbieranie.window,
                       text=str(ZmienOdbieranie.odebranyBlok),
                       font=("Arial Bold", 10))
    portLabel4.grid(column=0, row=3)

    # Sprawdzenie czy nie był to ostatni wyslany blok
    if ZmienOdbieranie.odebranyBlok[0].to_bytes(1, 'big') == ZbioroweDane.EOT:
        portLabel7 = Label(ZmienOdbieranie.window,
                           text=str("Odbiornik: Trnasmisja zostala zakonczona. Odebrano ostatni pakiet. "),
                           font=("Arial Bold", 10))
        portLabel7.grid(column=0, row=5)
        ZmienOdbieranie.serialPort.write(ZbioroweDane.ACK)

        # Zapis do pliku calego odebranego pliku
        file = open("Odebrana.txt", 'wb+')
        file.write(ZmienOdbieranie.calkowityBlok)
        file.close()
        ZmienOdbieranie.serialPort.close()
        sys.exit()

    # Odczytanie numeru bloku, dopelnienia numeru bloku oraz sprawdzenie czy zostaly poprawnie odczytane
    nrBloku = int(ZmienOdbieranie.odebranyBlok[1])
    dopelnienieNrBloku = int(ZmienOdbieranie.odebranyBlok[2])
    if dopelnienieNrBloku + nrBloku != 255:
        print("Odbiornik: Pakiet odebrano niepoprawnie. Niepoprawny numer pakietu. Ponawiam transmisje. ")
        ZmienOdbieranie.serialPort.write(ZbioroweDane.NAK)
        return

    # Odczytanie i obliczenie sumy kontrolnej oraz sprawdzenie rownosci sum kontrolnych
    sumaKontrolnaWyliczona = 0
    sumaKontrolnaOdebrana = 0
    if ZmienOdbieranie.decyzja == ZbioroweDane.NAK:
        sumaKontrolnaOdebrana = ZmienOdbieranie.odebranyBlok[-1]
        for i in ZmienOdbieranie.odebranyBlok[3:-1]:
            sumaKontrolnaWyliczona += i
        sumaKontrolnaWyliczona %= 256
    if ZmienOdbieranie.decyzja == ZbioroweDane.CRC:
        sumaKontrolnaOdebrana = ZmienOdbieranie.odebranyBlok[-1] + ZmienOdbieranie.odebranyBlok[-2] * 256
        sumaKontrolnaWyliczona = crc16.crc16xmodem(ZmienOdbieranie.odebranyBlok[3:-2])
    if sumaKontrolnaOdebrana != sumaKontrolnaWyliczona:
        print("Odbiornik: Pakiet odebrano niepoprawnie. Niepoprawna suma kontrolna. Ponawiam transmisje. ")
        ZmienOdbieranie.serialPort.write(ZbioroweDane.NAK)
        return

    portLabel6 = Label(ZmienOdbieranie.window,
                       text="Odbiornik: Pakiet został odebrany poprawnie. " + str(
                           ZmienOdbieranie.nrPakietu + 1) + " odebrano poprawnie. ",
                       font=("Arial Bold", 10))
    portLabel6.grid(column=0, row=4)
    ZmienOdbieranie.nrPakietu += 1

    # Usuniecie dopelnienia przy zapisywaniu odebranego pakietu
    dopelnienie = bytearray(ZmienOdbieranie.odebranyBlok)
    for i in range(len(dopelnienie)):
        if dopelnienie[i] == 26:
            if ZmienOdbieranie.decyzja == ZbioroweDane.NAK:
                del dopelnienie[i:-1]
                ZmienOdbieranie.odebranyBlok = bytes(dopelnienie)
                break
            if ZmienOdbieranie.decyzja == ZbioroweDane.CRC:
                del dopelnienie[i:-2]
                ZmienOdbieranie.odebranyBlok = bytes(dopelnienie)
                break

    # Dodanie odebranego bloku z usunietym dopelnieniem do pozostalych odebranych blokow
    if ZmienOdbieranie.decyzja == ZbioroweDane.NAK:
        ZmienOdbieranie.calkowityBlok += ZmienOdbieranie.odebranyBlok[3:-1]
    elif ZmienOdbieranie.decyzja == ZbioroweDane.CRC:
        ZmienOdbieranie.calkowityBlok += ZmienOdbieranie.odebranyBlok[3:-2]
    ZmienOdbieranie.serialPort.write(ZbioroweDane.ACK)

    # Odczytanie kolejnego bloku
    if ZmienOdbieranie.decyzja == ZbioroweDane.NAK:
        ZmienOdbieranie.odebranyBlok = ZmienOdbieranie.serialPort.read(132)
    elif ZmienOdbieranie.decyzja == ZbioroweDane.CRC:
        ZmienOdbieranie.odebranyBlok = ZmienOdbieranie.serialPort.read(133)
    if not ZmienOdbieranie.flag:
        ZmienOdbieranie.window.after(100, odbieranieBloku)


# ---------------------------------------------------------------- Poczatek programu -----------------------------------------------------------------
# Pobieranie numeru portu do otwarcia
ZmienOdbieranie.window.title("Odbieranie")
ZmienOdbieranie.window.geometry('1000x200')
ZmienOdbieranie.window.grid_columnconfigure(1, weight=5)
portLabel = Label(ZmienOdbieranie
                  .window,
                  text="Nadajnik: Wybierz numer portu szeregowego:",
                  font=("Arial Bold", 10))
portLabel.grid(column=1, row=0)
combo = Combobox(ZmienOdbieranie
                 .window)
combo['values'] = ("COM1", "COM2", "COM3", "COM4", "COM5")
combo.current(1)
combo.grid(column=1, row=1)

# Pytanie czy jest zgoda na transmisje
portLabel3 = Label(ZmienOdbieranie.window,
                   text="Odbiornik: Zgoda na transmisje?",
                   font=("Arial Bold", 10))
portLabel3.grid(column=1, row=2)
combo1 = Combobox(ZmienOdbieranie
                  .window)
combo1['values'] = ("Tak - Algebraiczna", "Tak - CRC", "Nie")
combo1.current(0)
combo1.grid(column=1, row=3)
zgoda = combo1.get()
if zgoda == "Tak - Algebraiczna":
    ZmienOdbieranie.decyzja = ZbioroweDane.NAK
elif zgoda == "Tak - CRC":
    ZmienOdbieranie.decyzja = ZbioroweDane.CRC
elif zgoda == "Nie":
    sys.exit()
button = Button(ZmienOdbieranie
                .window, text="Dalej", command=dalej)
button.grid(column=1, row=5)
ZmienOdbieranie.window.mainloop()
