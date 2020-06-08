import serial
import CollectiveData
import crc16
import VariableReceiving
from tkinter import *
from tkinter.ttk import *


# ------------------------------------------------------- Opening ports and making connections -------------------------------------------------------
def Next():
    VariableReceiving.port = str(combo.get())
    button.destroy()
    combo.destroy()
    combo1.destroy()
    portLabel3.destroy()
    portLabel.destroy()
    portLabelx = Label(VariableReceiving.window,
                       text="Receiver: Opening the port: " + VariableReceiving.port,
                       font=("Arial Bold", 10))
    portLabelx.grid(column=0, row=0)

    # Opening the selected port
    try:
        VariableReceiving.serial_port = serial.Serial(VariableReceiving.port, 9600, 8, serial.PARITY_NONE,
                                                      serial.STOPBITS_ONE, 15)
        portLabel2 = Label(VariableReceiving.window,
                           text="Receiver: The port has been opened. Waiting for broadcasts....",
                           font=("Arial Bold", 10))
        portLabel2.grid(column=0, row=1)
    except:
        portLabel2 = Label(VariableReceiving.window,
                           text="Receiver: Failed to open port. ",
                           font=("Arial Bold", 10))
        portLabel2.grid(column=0, row=1)
        return

    # Initiating connection, receiving sent block
    VariableReceiving.serial_port.timeout = 10
    for i in range(6):
        VariableReceiving.serial_port.write(VariableReceiving.decision)
        if VariableReceiving.decision == CollectiveData.NAK:
            VariableReceiving.received_block = VariableReceiving.serial_port.read(132)
        elif VariableReceiving.decision == CollectiveData.CRC:
            VariableReceiving.received_block = VariableReceiving.serial_port.read(133)
        if VariableReceiving.received_block != b'':
            break
    if VariableReceiving.received_block == b'':
        print("Receiver: No answer. ")
        sys.exit()

    # Reading a received block, receiving subsequent blocks
    if not VariableReceiving.flag:
        VariableReceiving.window.after(100, receivingBlocks)


# ------------------------------------------------------------- Receiving blocks ---------------------------------------------------------------------
def receivingBlocks():
    portLabel3 = Label(VariableReceiving.window,
                       text="Receiver: I receive package no." + str(VariableReceiving.package_no + 1),
                       font=("Arial Bold", 10))
    portLabel3.grid(column=0, row=2)

    portLabel4 = Label(VariableReceiving.window,
                       text=str(VariableReceiving.received_block),
                       font=("Arial Bold", 10))
    portLabel4.grid(column=0, row=3)

    # Checking if this was the last block sent
    if VariableReceiving.received_block[0].to_bytes(1, 'big') == CollectiveData.EOT:
        portLabel7 = Label(VariableReceiving.window,
                           text=str("Receiver: The transmission has been completed. Last packet received. "),
                           font=("Arial Bold", 10))
        portLabel7.grid(column=0, row=5)
        VariableReceiving.serial_port.write(CollectiveData.ACK)

        # Saving the entire received file to a file
        file = open("Receive.txt", 'wb+')
        file.write(VariableReceiving.total_block)
        file.close()
        VariableReceiving.serial_port.close()
        sys.exit()

    # Reading the block number, completing the block number and checking that they have been read correctly
    block_no = int(VariableReceiving.received_block[1])
    completing_the_block_number = int(VariableReceiving.received_block[2])
    if completing_the_block_number + block_no != 255:
        print("Receiver: The packet was received incorrectly. Invalid packet number. I repeat broadcasts. ")
        VariableReceiving.serial_port.write(CollectiveData.NAK)
        return

    # Reading and calculating the checksum and checking the equality of checksums
    checksum_calculated = 0
    checksum_received = 0
    if VariableReceiving.decision == CollectiveData.NAK:
        checksum_received = VariableReceiving.received_block[-1]
        for i in VariableReceiving.received_block[3:-1]:
            checksum_calculated += i
        checksum_calculated %= 256
    if VariableReceiving.decision == CollectiveData.CRC:
        checksum_received = VariableReceiving.received_block[-1] + VariableReceiving.received_block[-2] * 256
        checksum_calculated = crc16.crc16xmodem(VariableReceiving.received_block[3:-2])
    if checksum_received != checksum_calculated:
        print("Receiver: The packet was received incorrectly. Invalid checksum. I repeat broadcasts. ")
        VariableReceiving.serial_port.write(CollectiveData.NAK)
        return

    portLabel6 = Label(VariableReceiving.window,
                       text="Receiver: The packet was received correctly. " + str(
                           VariableReceiving.package_no + 1) + " received correctly. ",
                       font=("Arial Bold", 10))
    portLabel6.grid(column=0, row=4)
    VariableReceiving.package_no += 1

    # Delete padding when saving a received package
    complement = bytearray(VariableReceiving.received_block)
    for i in range(len(complement)):
        if complement[i] == 26:
            if VariableReceiving.decision == CollectiveData.NAK:
                del complement[i:-1]
                VariableReceiving.received_block = bytes(complement)
                break
            if VariableReceiving.decision == CollectiveData.CRC:
                del complement[i:-2]
                VariableReceiving.received_block = bytes(complement)
                break

    # Add a received block with padding removed to other received blocks
    if VariableReceiving.decision == CollectiveData.NAK:
        VariableReceiving.total_block += VariableReceiving.received_block[3:-1]
    elif VariableReceiving.decision == CollectiveData.CRC:
        VariableReceiving.total_block += VariableReceiving.received_block[3:-2]
    VariableReceiving.serial_port.write(CollectiveData.ACK)

    # Reading the next block
    if VariableReceiving.decision == CollectiveData.NAK:
        VariableReceiving.received_block = VariableReceiving.serial_port.read(132)
    elif VariableReceiving.decision == CollectiveData.CRC:
        VariableReceiving.received_block = VariableReceiving.serial_port.read(133)
    if not VariableReceiving.flag:
        VariableReceiving.window.after(100, receivingBlocks)


# ---------------------------------------------------------------- Beginning of the program -----------------------------------------------------------------
# Getting the port number to open
VariableReceiving.window.title("Receiving")
VariableReceiving.window.geometry('1000x200')
VariableReceiving.window.grid_columnconfigure(1, weight=5)
portLabel = Label(VariableReceiving
                  .window,
                  text="Receiver: Select the serial port number:",
                  font=("Arial Bold", 10))
portLabel.grid(column=1, row=0)
combo = Combobox(VariableReceiving
                 .window)
combo['values'] = ("COM1", "COM2", "COM3", "COM4", "COM5")
combo.current(1)
combo.grid(column=1, row=1)

# The question is whether there is consent to broadcasts
portLabel3 = Label(VariableReceiving.window,
                   text="Receiver: Consent to broadcasts?",
                   font=("Arial Bold", 10))
portLabel3.grid(column=1, row=2)
combo1 = Combobox(VariableReceiving
                  .window)
combo1['values'] = ("Yes - Algebraic", "Yes - CRC", "No")
combo1.current(0)
combo1.grid(column=1, row=3)
agreement = combo1.get()
if agreement == "Yes - Algebraic":
    VariableReceiving.decision = CollectiveData.NAK
elif agreement == "Yes - CRC":
    VariableReceiving.decision = CollectiveData.CRC
elif agreement == "No":
    sys.exit()
button = Button(VariableReceiving
                .window, text="Next", command=Next)
button.grid(column=1, row=5)
VariableReceiving.window.mainloop()
