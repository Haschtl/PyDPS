from PyQt5 import QtCore
from PyQt5 import uic
from PyQt5 import QtWidgets
from PyQt5 import QtGui
import pyqtgraph as pg
import sys

import minimalmodbus
import time

stopMe = False

class Updater(QtCore.QThread):
    received = QtCore.pyqtSignal()

    def run(self):
        while not stopMe:
            self.sleep(1)
            self.received.emit()
            
class PyQtDPS(QtWidgets.QMainWindow):
    def __init__(self):
        super(PyQtDPS, self).__init__()
        uic.loadUi("dpsGUI.ui", self)
        
        self.power_supply = minimalmodbus.Instrument('/dev/rfcomm0', 1)
        self.power_supply.serial.baudrate = 9600
        self.power_supply.serial.bytesize = 8
        self.power_supply.serial.timeout = 2
        self.power_supply.mode = minimalmodbus.MODE_RTU
        
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
            onoff=self.power_supply.read_register(9)
            # self.powerButton.setChecked(bool(onoff))
            self.power_supply.write_register(9,(1-onoff))
        except :
            print ("write_error")
            
    def setValues(self):
        try :
            volt = self.voltageSpinBox.value()
            amp = self.ampSpinBox.value()
            self.power_supply.write_register(0,volt*100)
            self.power_supply.write_register(1,amp*100)
        except :
            print ("write_error")
            
    def refresh(self):
       # try :
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
        # except :
        #    print("read error")
            
    def closeEvent(self, event):
        global stopMe
        stopMe = True
        self.running = False
        self.close()
        
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    myapp = PyQtDPS()
    #self.stylesheet = pyqtlib.loadStyleSheet('data/ui/darkmode.html')
    #myapp.setStyleSheet(self.stylesheet)
    app.exec_()
