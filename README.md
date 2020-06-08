## XModem Protocol
Breaks up the original data into blocks that are sent to the receiver, along with information allowing to determine whether that packet was correctly received(checksum,  block number, completing the block number). If an error is detected, the receiver requests that the packet be re-sent. 

Transmitter sends:
* SOH
* Block number, completing the block number
* Block of data
* Checksum
* ACK
* EOT

Receiver:
* Sends NAK to initiate transmission
* Receive data
* Check received data (calculate checksum)
* If received data is correct sends ACK
* After receiving EOT sends ACK to end transmission

Checksum:
* Algebraic
* CRC

#### Instalation
```text
pip install pyserial crc16
```

#### Usage

* Run [Transmitter.py](https://github.com/JuliaSzymanska/Xmodem/blob/master/Transmitter.py) or [Receiver.py](https://github.com/JuliaSzymanska/Sound/blob/master/Receiver.py)

#### GUI
* Transmitter:
![]()

* Receiver:
![]()

## License
[Apache License 2.0](https://github.com/JuliaSzymanska/Sound)
