# PyQTDPS
Linux GUI for all DPS variable power supplies with USB or Bluetooth connection.

## Dependencies
> sudo pip3 install minimalmodbus

> sudo pip3 install pyqt5

## HowTo
- Modify config.json:
	- "dev_init_command": OS-Command to connect to device and set read/write privileges if needed
		- You will need your Device-MAC-Adress for bluetooth connection
	- "dev_path": Set directory, where the device is mounted
	- Leave anything else (you can change "update_rate", which sets GUI-update-rate)
- Run the following command:

> python3 pyQtDPS.py
- You may need to run as root for read/write privileges:

> sudo python3 pyQtDPS.py