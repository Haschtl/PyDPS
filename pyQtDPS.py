# Python3.6
import json
import os
import sys
import subprocess
import time
from threading import Thread, Lock

try:
	from PyQt5 import uic
	from PyQt5 import QtWidgets
	from PyQt5 import QtCore
	from PyQt5 import QtGui
except ImportError:
	sys.exit("\nERROR\nPyQt5 for Python3 not found! \nPlease install with 'pip3 install pyqt5\nOr apt install python3-pyqt5")
	
try:
	import minimalmodbus
except ImportError:
	sys.exit("\nERROR\nminimalmodbus for Python3 not found!\nPlease install with 'pip3 install minimalmodbus'")
try:
    import pyqtgraph as pg
    plotEnabled = True
except ImportError:
    plotEnabled = False

LOCK = Lock()

stopMe = False

class Updater(QtCore.QThread):
    received = QtCore.pyqtSignal()

    def run(self):
        config = load_config()
        while not stopMe:
            self.sleep(config["update_rate"])
            self.received.emit()

class UpdaterFast(QtCore.QThread):
    received = QtCore.pyqtSignal()

    def run(self):
        config = load_config()
        while not stopMe:
            self.sleep(config["plot_update_rate"])
            self.received.emit()
            
            
class PyQtDPS(QtWidgets.QMainWindow):
    def __init__(self):
        super(PyQtDPS, self).__init__()
        if not plotEnabled:
            self.plotButton.hide()
        uic.loadUi("dpsGUI.ui", self)
        app_icon = QtGui.QIcon("icon.png")
        self.setWindowIcon(app_icon)
        self.config = load_config()
        self.running = True
        self.splitter.hide()
        self.ampSpinBox.setMaximum(self.config["maxAmps"])
        
        self.setButton.clicked.connect(self.setValues)
        self.powerButton.clicked.connect(self.togglePower)
        self.lockedButton.clicked.connect(self.toggleLocked)
        self.plotButton.clicked.connect(self.startPlotThread)
        self.ok = False
        self.dataGetter = Thread(target= self.getData)
        self.dataGetter.start()
        self.show()
        
        #self.updater = Updater(self)
        #self.updater.received.connect(self.refresh)
        self.updater = QtCore.QTimer()
        self.updater.setInterval(self.config["update_rate"])
        self.updater.timeout.connect(self.refresh)
        self.updater.start()
        
    def getData(self):
        while self.running:
            try:
                with LOCK:
                    self.data=self.power_supply.read_registers(0,11) #read data from power supply
                #data[0] U-set x100 (R/W)
                #data[1] I-set x100 (R/W)
                #data[2] U-out x100
                #data[3] I-out x100
                #data[4] P-out x100
                #data[5] U-in x100
                #data[6] lock/unlock 1/0 (R/W)
                #data[7] Protected 1/0
                #data[8] operating mode CC/CV 1/0
                #data[9] on/off 1/0 (R/W)
                #data[10] display intensity 1..5 (R/W)
                self.ok = True
                time.sleep(0.05)
            except:
                print("Instrument not initialized yet")
                self.data= [0]*11
                self.ok = False
                if not os.path.exists(config["dev_path"]):
                    print("Initializing USB or Bluetooth communication")
                    try:
                        self.processRunning = True
                        self.process = subprocess.Popen(self.config["dev_init_command"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
                    except:
                        sys.exit("\nERROR\nSystem command from config.json exited with an error. \nPlease modify 'dev_init_command' in config.json")
                else:
                    self.processRunning = False
                print("Setting permissions to access device")
                ok = os.system("sudo chmod +rwx "+config["dev_path"])
                if ok != 0:
                    sys.exit("\nERROR\nCould not set read/write permissions for "+config["dev_path"])
                try:
                    self.power_supply = minimalmodbus.Instrument(self.config["dev_path"], 1)
                    self.power_supply.serial.baudrate = self.config["serial_baudrate"]
                    self.power_supply.serial.bytesize = self.config["serial_bytesize"]
                    self.power_supply.serial.timeout = self.config["serial_timeout"]
                    self.power_supply.mode = minimalmodbus.MODE_RTU
                except:
                    #self.closeWindow()
                    #sys.exit("\nERROR\nFailed to initialize minimalmodbus instrument!\nPlease check serial-settings in config.json")
                    print("\nERROR\nFailed to initialize minimalmodbus instrument!\nPlease check serial-settings in config.json")
                print("Starting thread to update GUI-values")
                time.sleep(1)
        
    def togglePower(self):
        if self.ok:
            try :
                print("Changing power-state")
                with LOCK:
                    onoff=self.power_supply.read_register(9)
                    # self.powerButton.setChecked(bool(onoff))
                    self.power_supply.write_register(9,(1-onoff))
                if onoff==0:
                    self.lockedButton.setText("Locked")
                else:
                    self.lockedButton.setText("Unlocked")
            except :
                print ("\nERROR\nChanging power-state failed!\n")
            
    def toggleLocked(self):
        if self.ok:
            try :
                print("Changing locked-state")
                with LOCK:
                    onoff=self.power_supply.read_register(6)
                    # self.powerButton.setChecked(bool(onoff))
                    self.power_supply.write_register(6,(1-onoff))
            except :
                print ("\nERROR\nChanging locked-state failed!\n")
            
    def setValues(self):
        if self.ok:
            try :
                print("Setting output values")
                volt = self.voltageSpinBox.value()
                amp = self.ampSpinBox.value()
                with LOCK:
                    self.power_supply.write_register(0,int(volt*100))
                    self.power_supply.write_register(1,int(amp*100))
            except :
                print ("\nERROR\nSetting output values failed!\n")
            
    def startPlotThread(self):
        if self.ok:
            self.initPlotWindow()
            
    def refresh(self):
        if self.ok:
            self.label_8.hide()
            self.splitter.show()
            self.ifValLCD(self.data[2]/100, self.voltageLCD)
            self.ifValLCD(self.data[3]/100, self.ampLCD)
            self.ifValLCD(self.data[4]/100, self.powerLCD)
            if self.vInLabel.text() != str(self.data[5]/100)+" V (V-In)":
                self.vInLabel.setText(str(self.data[5]/100)+" V (V-In)")
            if self.voltageSpinBox.maximum() != round(self.data[5]/100*0.909):
                self.voltageSpinBox.setMaximum(round(self.data[5]/100*0.909))
            if(self.data[9]==1):
                self.powerButton.setStyleSheet("background-color: green")
            else:
                self.powerButton.setStyleSheet("background-color: red")
            if self.data[0]/100==round(self.voltageSpinBox.value(),2):
                self.voltageSpinBox.setStyleSheet("background-color: green")
            else:
                self.voltageSpinBox.setStyleSheet("background-color: red")
            if self.data[1]/100==round(self.ampSpinBox.value(),2):
                self.ampSpinBox.setStyleSheet("background-color: green")
            else:
                self.ampSpinBox.setStyleSheet("background-color: red")
            if self.data[6]==1:
                self.lockedButton.setStyleSheet("background-color: red")
                self.lockedButton.setText("Locked")
            else:
                self.lockedButton.setStyleSheet("background-color: green")
                self.lockedButton.setText("Unlocked")
            if self.data[7]==1:
                self.protectedLabel.setStyleSheet("background-color: red")
                self.protectedLabel.setText("Not Protected")
            else:
                self.protectedLabel.setStyleSheet("background-color: green")
                self.protectedLabel.setText("Protected")
            if self.data[8]==1:
                self.cvccLabel.setText("Konst. Strom")
            else:
                self.cvccLabel.setText("Konst. Spannung")
        else:
            self.label_8.show()
            self.splitter.hide()
            
    def ifValLCD(self, value, QObject):
        if value != QObject.value():
            QObject.display(value)
            
    def closeEvent(self, event):
        self.closeWindow()

    def closeWindow(self):
        print("Closing PyQtDPS")
        if self.ok:
            with LOCK:
                self.power_supply.write_register(0,0)
                self.power_supply.write_register(1,0)
                self.power_supply.write_register(9,0)
        global stopMe
        stopMe = True
        self.running = False
        if self.processRunning:
            self.process.kill()
        self.close()
        
    def initPlotWindow(self):
        pg.setConfigOption('background', (49, 54, 59))
        self.plotDialog = QtWidgets.QDialog()
        layout = QtWidgets.QVBoxLayout(self.plotDialog)
        self.plotWidget = pg.PlotWidget()
        ax = self.plotWidget.getAxis('bottom')  # This is the trick
        # Set grid x and y-axis
        ax.setGrid(255)
        ax.setLabel("Zeit [s]")
        ay = self.plotWidget.getAxis('left')
        ay.setGrid(255)
        ay.setLabel("Daten")
        self.plotWidget.addLegend()
        self.plotWidget.getPlotItem().setTitle("Spannung/Strom/Leistung")
        layout.addWidget(self.plotWidget)
        self.p = [0]*3
        pen = pg.mkPen(color=(255, 61, 61))
        self.p[0] = self.plotWidget.plot(
            x=[0], y=[0], pen=pen, name='Spannung [V]')
        pen = pg.mkPen(color=(57, 255, 20), )
        self.p[1] = self.plotWidget.plot(
            x=[0], y=[0], pen=pen, name='Strom [A]')
        pen = pg.mkPen(color=(214, 255, 127), style=QtCore.Qt.DotLine)
        self.p[2] = self.plotWidget.plot(
            x=[0], y=[0], pen=pen, fillLevel=0, fillBrush=(214, 255, 127, 30), name='Leistung [W]')        
        self.plotTime = [0]
        self.plotVolt = [0]
        self.plotAmp = [0]
        self.plotPower = [0]
        self.plotDialog.show()
        # self.plotter = UpdaterFast(self)
        # self.plotter.received.connect(self.plotValues)
        self.plotter = QtCore.QTimer()
        self.plotter.setInterval(self.config["plot_update_rate"])
        self.plotter.timeout.connect(self.plotValues)
        self.plotter.start()
        
    def plotValues(self):
        if self.ok:
            now = time.time()
            self.plotTime.append(float(now))
            self.plotVolt.append(self.data[2]/100)
            self.plotAmp.append(self.data[3]/100)
            self.plotPower.append(self.data[4]/100)
            if float(now)-self.plotTime[0] > self.config["plotLength"]:
                self.plotTime = self.plotTime[1:]
                self.plotVolt = self.plotVolt[1:]
                self.plotAmp = self.plotAmp[1:]
                self.plotPower = self.plotPower[1:]
            plotTimeRelative = []
            for x in self.plotTime:
                plotTimeRelative.append(x-self.plotTime[len(self.plotTime)-1])
            self.p[0].setData(x=plotTimeRelative, y=self.plotVolt)
            self.p[1].setData(x=plotTimeRelative, y=self.plotAmp)
            self.p[2].setData(x=plotTimeRelative, y=self.plotPower)
            
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
