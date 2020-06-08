import crc16
import serial
from tkinter import *
from tkinter.ttk import *
import Variables
import CollectiveData


# ------------------------------------------------------- Opening ports and making connections -----------------------------------------------------
def next():
    Variables.port = str(combo.get())
    button.destroy()
    combo.destroy()
    port_label.destroy()
    portLabelx = Label(Variables.window,
                       text="Transmitter: Opening the port: " + Variables.port,
                       font=("Arial Bold", 10))
    portLabelx.grid(column=0, row=0)

    # Opening the selected port
    try:
        Variables.serial_port = serial.Serial(Variables.port, 9600, 8, serial.PARITY_NONE, serial.STOPBITS_ONE, 15)
        port_label2 = Label(Variables.window,
                           text="Transmitter: The port has been opened. Waiting for broadcasts....",
                           font=("Arial Bold", 10))
        port_label2.grid(column=0, row=1)
    except:
        port_label2 = Label(Variables.window,
                           text="Transmitter: Failed to open port",
                           font=("Arial Bold", 10))
        port_label2.grid(column=0, row=1)
        return

    # Start transmission
    Variables.decision = Variables.serial_port.read()
    if Variables.decision == CollectiveData.CRC or Variables.decision == CollectiveData.NAK:
        portLabel3 = Label(Variables.window,
                           text="Transmitter: Consent to broadcasts",
                           font=("Arial Bold", 10))
        portLabel3.grid(column=0, row=2)
    else:
        sys.exit()

    # Sending a packet
    port_label4 = Label(Variables.window,
                       text="Transmitter: Sending a packet",
                       font=("Arial Bold", 10))
    port_label4.grid(column=0, row=3)

    if Variables.block_no - 1 < len(Variables.block):
        Variables.window.after(100, sending_blocks)


# ------------------------------------------------------------- Sending blocks ---------------------------------------------------------------------
def sending_blocks():
    # Sending a SOH header
    Variables.serial_port.write(CollectiveData.SOH)

    # Sending a block number, completing the block number to 255
    package = bytearray(Variables.block_no.to_bytes(1, 'big'))
    package.append(255 - Variables.block_no)
    Variables.serial_port.write(bytes(package))

    # If it is a packet smaller than 128 bytes, it is filled to that number
    if Variables.shipped_block_no + 1 == len(Variables.block):
        complement = bytearray(Variables.block[Variables.shipped_block_no])
        while len(complement) < 128:
            complement.append(26)
        Variables.block[Variables.shipped_block_no] = bytes(complement)

    # Sending data block
    for i in Variables.block[Variables.shipped_block_no]:
        Variables.serial_port.write(i.to_bytes(1, 'big'))

    # Counting and sending a checksum
    check_sum = 0
    if Variables.decision == CollectiveData.NAK:
        for i in Variables.block[Variables.shipped_block_no]:
            check_sum += i
        check_sum %= 256
        check_sum = bytearray(check_sum.to_bytes(1, 'big'))
    else:
        check_sum = crc16.crc16xmodem(Variables.block[Variables.shipped_block_no])
        check_sum = bytearray(check_sum.to_bytes(2, 'big'))
    Variables.serial_port.write(bytes(check_sum))

    # Checking the status of the uploaded block
    port_label5 = Label(Variables.window,
                       text="",
                       font=("Arial Bold", 10))
    port_label5.grid(column=0, row=4)
    while 1:
        answer_received = Variables.serial_port.read()
        if answer_received == CollectiveData.ACK:
            port_label5["text"] = "Transmitter: Package no." + str(Variables.shipped_block_no + 1) + " uploaded correctly. "
            Variables.shipped_block_no += 1
            if Variables.block_no == 255:
                Variables.block_no = 0
            else:
                Variables.block_no += 1
            break
        elif answer_received == CollectiveData.NAK:
            port_label5[
                "text"] = "Transmitter: package no." + str(
                Variables.shipped_block_no + 1) + "uploaded incorrectly. I repeat broadcasts. "
            break
        elif answer_received == CollectiveData.CAN:
            port_label5["text"] = "Transmitter: The connection has been terminated. "
            sys.exit()

    # After sending all blocks, sending EOT
    if Variables.block_no - 1 == len(Variables.block):
        port_label6 = Label(Variables.window,
                           text="Transmitter: Finished sending last package. ",
                           font=("Arial Bold", 10))
        port_label6.grid(column=0, row=5)
        port_label7 = Label(Variables.window,
                           text="",
                           font=("Arial Bold", 10))
        port_label7.grid(column=0, row=6)

        # Sending EOT
        while 1:
            Variables.serial_port.write(CollectiveData.EOT)
            Variables.decision = Variables.serial_port.read()
            if Variables.decision == CollectiveData.ACK:
                port_label7["text"] = "Transmitter: Confirmation received at the end of the transmission. "
                break
            if Variables.decision == CollectiveData.CAN:
                port_label7["text"] = "Transmitter: The connection has been terminated. "
                break

        # Closing the port, ending the transmission
        Variables.serial_port.close()
        port_label8 = Label(Variables.window,
                           text="Transmitter: The transfer has been completed. ",
                           font=("Arial Bold", 10))
        port_label8.grid(column=0, row=7)

    # Sending next block
    if Variables.block_no - 1 < len(Variables.block):
        Variables.window.after(100, sending_blocks)


# ---------------------------------------------------------------- Beginning of the program -----------------------------------------------------------------

# Opening the file for sending and downloading the text
file = open("Sent.txt", 'rb')
wiadomosc = file.read()

# Split text into 128 bit sections
Variables.block = [wiadomosc[i:i + 128] for i in range(0, len(wiadomosc), 128)]
file.close()

Variables.window.title("Sending")
Variables.window.geometry('400x200')
Variables.window.grid_columnconfigure(1, weight=5)

# Downloading port to open
port_label = Label(Variables.window,
                   text="Transmitter: Select the serial port number:",
                   font=("Arial Bold", 10))
port_label.grid(column=1, row=0)
combo = Combobox(Variables.window)
combo['values'] = ("COM1", "COM2", "COM3", "COM4", "COM5")
combo.current(1)
combo.grid(column=1, row=1)
button = Button(Variables.window, text="Next", command=next)
button.grid(column=1, row=5)

Variables.window.mainloop()
