# ----------------------------------
# file: main.py byke capstone - raspi interface
# date: 12/09/2019
# author: Tanner L
# Decs: Raspberry Pi Interface App for byke capstone project
# ----------------------------------
import tkinter as tk
from tkinter import ttk
from tkinter import *
from PIL import ImageTk, Image
import re

leftButton = 0
rightButton = 0
headLightButton = 0
hornButton = 0
unitSelect = 0

recordRunning = 0

previousTrips = []
for i in range(10):
    tripData = []
    for j in range(5):
        tripData.append(0)
    previousTrips.append(tripData)


def metricSet(event=None):
    unitS.config(text='Km/H')


def imperialSet(event=None):
    unitS.config(text='MPH')


def leftFlashG():
    leftTurnS.config(fg='green')


def leftFlashW():
    leftTurnS.config(fg='white')


def rightFlashG():
    rightTurnS.config(fg='green')


def rightFlashW():
    rightTurnS.config(fg='white')



def record(event):
    global recordRunning
    print(recordRunning)
    print(powerSpinner.get())
    global batteryrender
    batteryload = Image.open("25battery.png")
    batteryrender = ImageTk.PhotoImage(batteryload)
    batteryimage.configure(image=batteryrender)
    batteryimage.image = batteryrender
 #   try:
    if (recordRunning==0):
        recordRunning = 1
        startStopS.config(text='STOP')
        with open('save.txt', 'r') as f:
            data = f.readline()
            data = re.findall(r'\d*\.\d+|\d+', data)

        for i in range(10):
            for j in range(5):
                previousTrips[i][j] = float(data[i*5+j])

    elif recordRunning == 1:
        recordRunning=0
        startStopS.configure(text='START')
        timeIn=['12345678']
        timeInHr=list(timeIn[1:3])
        timeInHr = ''.join(str(e)for e in timeInHr)
        timeInHr=int(timeInHr)
        print(previousTrips[0][0])
        timeDifHr = int(previousTrips[0][0]) - timeInHr

        timeInMin=['23456']
        timeInMin=list(timeIn[3:5])
        timeInMin = ''.join(str(e)for e in timeInMin)
        timeInMin=int(timeInMin)

        timeDifHr = int(previousTrips[0][0]) - timeInHr
        timeDifMin = int(previousTrips[0][0]) - timeInMin

        previousTrips[0][0] = str(timeDifHr) + ':' + str(timeDifMin)

        print(previousTrips[0][0])

        with open('save.txt', 'w') as f:
            f.writelines(str(previousTrips))

#    except:
    #print('Start error')


# mainwindow--------------------------------------------
mainWindow = tk.Tk()
mainWindow.title('Byke')
mainWindow.geometry('480x300+0+0')
mainWindow.columnconfigure(0, weight=1)
mainWindow.rowconfigure(0, weight=1)
mainWindow.config(bg='white')

tabWhite = "#FFFFFF"
tabBlue = "#00FFFF"

style = ttk.Style()

style.theme_create( "byke_default", parent="alt", settings={
    "TNotebook": {"configure": {"tabmargins": [2, 5, 2, 0] } },
    "TNotebook.Tab": { "configure": {"padding": [5, 1], "background"
    : tabWhite }, "map":{"background": [("selected", tabBlue)],
                         "expand": [("selected", [1, 1, 1, 0])] } }})

style.theme_use("byke_default")


# Tab Configuration -----------------------------------------
tabControl = ttk.Notebook(mainWindow)
simpleTab = tk.Frame(tabControl)
settingsTab = tk.Frame(tabControl)
tabControl.add(simpleTab, text='Simple')
tabControl.add(settingsTab, text='Settings')
tabControl.grid(row=0, column=0, sticky='NESW')


# Simple Display Tab -------------------------------------------------
simpleTab.columnconfigure(0, weight=1)
simpleTab.columnconfigure(1, weight=1)
simpleTab.columnconfigure(2, weight=1)
simpleTab.columnconfigure(3, weight=1)

simpleTab.rowconfigure(0, weight=1)
simpleTab.rowconfigure(1, weight=1)
simpleTab.rowconfigure(2, weight=1)
simpleTab.rowconfigure(3, weight=1)

simpleTab.config(bg='white')

batteryload=Image.open("100battery.png")
batteryrender=ImageTk.PhotoImage(batteryload)
batteryimage = Label(simpleTab, image=batteryrender, text='100%')
batteryimage.grid(row=0, column=0, sticky='wn', padx=20, pady=20)

timeS = tk.Label(simpleTab, text='Time', bg='white', font=(None, 15))
timeS.grid(row=0, column=1, columnspan=2)

headLightS = tk.Label(simpleTab, text='\u263C', bg='white', fg='black', font=(None, 40))
headLightS.grid(row=0, column=3)

speedS = tk.Label(simpleTab, text='SPEED', bg='white', font=(None, 30))
speedS.grid(row=1, column=1, columnspan=2, rowspan=2, sticky='NESW')

startStopS = tk.Label(simpleTab, text='START', bg='white',fg='green', font=(None, 20))
startStopS.grid(row=3, column=0)
startStopS.bind('<Button-1>', record)

unitS = tk.Label(simpleTab, text='KM/H', bg='white', font=(None, 15))
unitS.grid(row=3, column=1, columnspan=2)

leftTurnS = tk.Label(simpleTab, fg='white', bg='white', text='\u2190', font=(None, 50))
leftTurnS.grid(row=3, column=1)

rightTurnS = tk.Label(simpleTab, fg='white', bg='white', text='\u2192', font=(None, 50))
rightTurnS.grid(row=3, column=2)


# Setting Tab ----------------------------------------------
settingsTab.columnconfigure(0, weight=1)
settingsTab.columnconfigure(1, weight=1)
settingsTab.columnconfigure(2, weight=1)

settingsTab.rowconfigure(0, weight=1)
settingsTab.rowconfigure(1, weight=1)
settingsTab.rowconfigure(2, weight=1)
settingsTab.rowconfigure(3, weight=1)
settingsTab.rowconfigure(4, weight=1)
settingsTab.rowconfigure(5, weight=1)

settingsTab.config(bg='white')

unitsText = tk.LabelFrame(settingsTab, text='Units',  bg='white', borderwidth=0)
unitsText.grid(row=0, column=0, sticky='nsew', padx=20, pady=10)
unitsText.rowconfigure(0, weight=1)
unitsText.rowconfigure(1, weight=1)
unitsText.columnconfigure(0, weight=1)

unitsOption = tk.IntVar()

imperialText = tk.Radiobutton(unitsText, bg='white', activebackground='white', highlightcolor='white', text='Imperial',
                              highlightthickness = 0, variable=unitsOption, value=1, command=imperialSet)
imperialText.grid(row=0, column=0, sticky='w')

metrictext = tk.Radiobutton(unitsText, activebackground='white', highlightcolor='white', text='Metric', bg='white',
                            variable=unitsOption, value=0, command=metricSet)
metrictext.grid(row=1, column=0, sticky='w')

maxPowerText = tk.LabelFrame(settingsTab, text='Max Power % ', bg='white', borderwidth=0)
maxPowerText.grid(row=1, column=0, sticky='nsew', padx=20)
maxPowerText.rowconfigure(0, weight=1)
maxPowerText.columnconfigure(0, weight=1)

powerSpinner = tk.Spinbox(maxPowerText, width=4, from_=30, to=100, increment=10, font=(None, 18))
powerSpinner.delete(0, 'end')
powerSpinner.insert(0, 100)
powerSpinner.grid(row=0, column=0, sticky='nsw')

previousTrip = tk.LabelFrame(settingsTab, text='Previous Trips', bg='white')
previousTrip.grid(row=0, column=2, rowspan=4, sticky='nsew')
previousTrip.rowconfigure(0, weight=1)
previousTrip.rowconfigure(1, weight=1)
previousTrip.rowconfigure(2, weight=1)
previousTrip.rowconfigure(3, weight=1)
previousTrip.rowconfigure(4, weight=1)

ptripselect = tk.Spinbox(previousTrip, width=2, from_=0, to=10, font=(None, 18))
ptripselect.grid(row=0, column=0, sticky='w')

pvtTime = tk.Label(previousTrip, text='Time: ', bg='white')
pvtTime.grid(row=1, column=0, sticky='w')

pvtMaxSpeed = tk.Label(previousTrip, text='Max Speed: ', bg='white')
pvtMaxSpeed.grid(row=2, column=0, sticky='w')

pvtDistance = tk.Label(previousTrip, text='Distance: ', bg='white')
pvtDistance.grid(row=3, column=0, sticky='w')

pvtDUp = tk.Label(previousTrip, text='Uphill Distance: ', bg='white')
pvtDUp.grid(row=4, column=0, sticky='w')

pvtDDown = tk.Label(previousTrip, text='Downhill Distance: ', bg='white')
pvtDDown.grid(row=5, column=0, sticky='w')

mainWindow.mainloop()

