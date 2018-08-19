# Python3.6
import json
# import os
import sys
import subprocess

try:
	from PyQt5 import uic
	from PyQt5 import QtWidgets
	from PyQt5 import QtCore
except ImportError:
	sys.exit("\nERROR\nPyQt5 for Python3 not found! \nPlease install with 'pip3 install pyqt5\nOr apt install python3-pyqt5")
	
try:
	import minimalmodbus
except ImportError:
	sys.exit("\nERROR\nminimalmodbus for Python3 not found!\nPlease install with 'pip3 install minimalmodbus'")



stopMe = False

class Updater(QtCore.QThread):
    received = QtCore.pyqtSignal()

    def run(self):
        config = load_config()
        while not stopMe:
            self.sleep(config["update_rate"])
            self.received.emit()
            
class PyQtDPS(QtWidgets.QMainWindow):
    def __init__(self):
        super(PyQtDPS, self).__init__()
        uic.loadUi("dpsGUI.ui", self)
        self.config = load_config()
		
        print("Initializing USB or Bluetooth communication")
        try:
            self.process = subprocess.Popen(self.config["dev_init_command"], shell=True)
        except:
            sys.exit("\nERROR\nSystem command from config.json exited with an error. \nPlease modify 'dev_init_command' in config.json")
        try:
            self.power_supply = minimalmodbus.Instrument(self.config["dev_path"], 1)
            self.power_supply.serial.baudrate = self.config["serial_baudrate"]
            self.power_supply.serial.bytesize = self.config["serial_bytesize"]
            self.power_supply.serial.timeout = self.config["serial_timeout"]
            self.power_supply.mode = minimalmodbus.MODE_RTU
        except:
            self.closeWindow()
            sys.exit("\nERROR\nFailed to initialize minimalmodbus instrument!\nPlease check serial-settings in config.json")
        print("Starting thread to update GUI-values")
        self.updater = Updater(self)
        self.updater.received.connect(self.refresh)
        self.updater.start()
        
        self.setButton.clicked.connect(self.setValues)
        self.powerButton.clicked.connect(self.togglePower)
        
        a=self.power_supply.read_registers(0,11) #read data from power supply
        self.voltageSpinBox.setValue(a[0]/100) # U-set x100 (R/W)
        self.ampSpinBox.setValue(a[1]/100) # I-set x100 (R/W)
        self.show()
        
    def togglePower(self):
        try :
            print("Changing power-state")
            onoff=self.power_supply.read_register(9)
            # self.powerButton.setChecked(bool(onoff))
            self.power_supply.write_register(9,(1-onoff))
        except :
            print ("\nERROR\nChanging power-state failed!\n")
            
    def setValues(self):
        try :
            print("Setting output values")
            volt = self.voltageSpinBox.value()
            amp = self.ampSpinBox.value()
            self.power_supply.write_register(0,volt*100)
            self.power_supply.write_register(1,amp*100)
        except :
            print ("\nERROR\nSetting output values failed!\n")
            
    def refresh(self):
        try :
            a=self.power_supply.read_registers(0,11) #read data from power supply
            #a[0] U-set x100 (R/W)
            #a[1] I-set x100 (R/W)
            #a[2] U-out x100
            #a[3] I-out x100
            #a[4] P-out x100
            #a[5] U-in x100
            #a[6] lock/unlock 1/0 (R/W)
            #a[7] ?
            #a[8] operating mode CC/CV 1/0
            #a[9] on/off 1/0 (R/W)
            #a[10] display intensity 1..5 (R/W)
            self.voltageLCD.display(a[2]/100)
            self.ampLCD.display(a[3]/100)
            self.powerLCD.display(a[4]/100)
            self.vInLabel.setText(str(a[5]/100)+" V (V-In)")
            self.voltageSpinBox.setMaximum(a[5]/100)
            if(a[9]==1):
                self.powerButton.setStyleSheet("background-color: green")
            else:
                self.powerButton.setStyleSheet("background-color: red")
            if a[0]==self.voltageSpinBox.value()*100:
                self.voltageSpinBox.setStyleSheet("background-color: green")
            else:
                self.voltageSpinBox.setStyleSheet("background-color: red")
            if a[1]==self.ampSpinBox.value()*100:
                self.ampSpinBox.setStyleSheet("background-color: green")
            else:
                self.ampSpinBox.setStyleSheet("background-color: red")
        except :
            print("\nERROR\nRefreshing GUI-values failed!\n")
            
    def closeEvent(self, event):
        self.closeWindow()

    def closeWindow(self):
        print("Closing PyQtDPS")
        global stopMe
        stopMe = True
        self.running = False
        self.process.kill()
        self.close()
        
def load_config(path="config.json"):
    with open(path, encoding="UTF-8") as jsonfile:
        config = json.load(jsonfile, encoding="UTF-8")
    return config
	
if __name__ == "__main__":
    # Initialize device
    config = load_config()
    app = QtWidgets.QApplication(sys.argv)
    myapp = PyQtDPS()
    app.exec_()
