#!/usr/bin/env python3
from tkinter import *
import minimalmodbus
import time
import os

# os.system("sudo rfcomm connect rfcomm0 00:BA:55:89:13:49")
# os.system("sudo chmod +rwx /dev/rfcomm0")
coloron="green"
coloroff="red"
colorcursor="deep sky blue"
top = Tk()
top.title('Voeding')
top.geometry("250x200")
top.config(bd=2, relief='sunken')

power_supply = minimalmodbus.Instrument('/dev/rfcomm0', 1)
power_supply.serial.baudrate = 9600
power_supply.serial.bytesize = 8
power_supply.serial.timeout = 2
power_supply.mode = minimalmodbus.MODE_RTU

def on_off() :
    try :
        onoff=power_supply.read_register(9)
        power_supply.write_register(9,(1-onoff))
    except :
        print ("write_error")

def copy() :
    try :
        power_supply.write_register(0,int(str(set_volt.get())))
        power_supply.write_register(1,int(str(set_amp.get())))
    except :
        print ("write_error")

def refresh():
    try :
        a=power_supply.read_registers(0,11) #read data from power supply
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
        U_out.configure(text=str(a[2]/100)+" Volt")
        I_out.configure(text=str(a[3]/100)+" Amp")
        P_out.configure(text=str(a[4]/100)+" Watt")
        U_in.configure(text=str(a[5]/100)+" Volt U-in")
        if(a[9]==1):
            on_off.configure(bg = coloron)
        else:
            on_off.configure(bg = coloroff)
    except :
        print("read error")
        top.after(100,refresh)

U_out = Label(background = "Green Yellow", font=("Courier Bold", 14), relief="sunken")
U_out.place(x = 10,y = 70,width = 150)

I_out = Label(background = "Yellow", font=("Courier Bold", 14), relief="sunken")
I_out.place(x = 10,y = 100,width = 150)

P_out = Label(background = "Medium Orchid", font=("Courier Bold", 14), relief="sunken")
P_out.place(x = 10,y = 130,width = 150)

U_in = Label(background = "Deep Sky Blue", font=("Courier Bold", 14), relief="sunken")
U_in.place(x = 10,y = 160,width = 150)

set_volt = StringVar()
volt = Entry(top, background = "Green Yellow", font=("Courier Bold", 14), relief="sunken", textvariable=set_volt)
volt.place(x=10,y=10,width=55)
volt.insert(END, "0000")

U_set_info= Label(font=("Courier Bold", 14),text="SETpoint U/100")
U_set_info.place(x = 75,y = 10)

set_amp = StringVar()
amp = Entry(top, background = "Yellow", font=("Courier Bold", 14), relief="sunken", textvariable=set_amp)
amp.place(x=10,y=40,width=55)
amp.insert(END, "0000")

I_set_info= Label(font=("Courier Bold", 14),text="SETpoint I/100")
I_set_info.place(x = 75,y = 40)

power_supply.write_register(0,int(str(set_volt.get())))
power_supply.write_register(1,int(str(set_amp.get())))

copy = Button(top, text = "set", activebackground = colorcursor, command = copy, bd = 2)
copy.place(x = 180,y = 68,width=60)

on_off = Button(top, text = "on/off", activebackground = colorcursor, command = on_off, bd = 2)
on_off.place(x = 180,y = 158,width=60)

top.after(100,refresh)
top.mainloop()
