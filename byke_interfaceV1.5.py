# -----------------------------------------------------
# Program: Capstone - byke - raspi interface
# File: byke_interfaceV1.5.py
# Author: Tanner L
# Date: 09/10/19
# Desc: Raspberry pi interface - V 1.5, main app - communicates with gps, motion sensor, all pics, and buttons.
# -----------------------------------------------------
import tkinter as tk
from tkinter import re  # imports re function
import threading as th
import queue as qu
import math
from PIL import ImageTk, Image
import logging
import sqlite3


# raspberry pi libraries
# import smbus    # i2c smbus for pic communication
# import gpsd     # Gps library import
# from gpiozero import Button, LED     # import gpio function for raspberry pi

logging.basicConfig(filename='datalog.log', level=logging.DEBUG) # logging file
logging.info('--------------------PROGRAM START----------------------------')

try:
    conn = sqlite3.connect('byke.db')

    logging.info('Opened database successfully')

except:
    logging.error('Database connection error')

try:
    conn.execute('''CREATE TABLE IF NOT EXISTS TRIP_STATS
            (TRIP_ID  INTEGER PRIMARY KEY NOT NULL,
            DATE          TEXT,
            TIME          INTEGER,
            MAX_SPEED     REAL,
            AVG_SPEED     REAL,
            DISTANCE      REAL,
            UPHILL        REAL,
            DOWNHILL      REAL);''')

    conn.execute('''CREATE TABLE IF NOT EXISTS GPS_DATA
             (ENTRY_ID INT PRIMARY KEY     NOT NULL,
             TIME           TEXT    NOT NULL,
             SPEED          REAL,
             LAT            REAL,
             LNG            REAL,
             ALT            REAL,
             CLIMB          REAL,
             TRIP_ID        INTEGER NOT NULL);''')

    logging.info('byke_data table created/exists successfully')

except:
    logging.error('byke_data table error')

conn.close()


# Global Variables
global recordRunning    # variable for recording trip
recordRunning = 0

global totaldistance    # total trip distance
totaldistance = 0

global gpsdistance      # gps distance calculated
gpsdistance = 0

global savetimehr       # trip time hour
savetimehr = 0

global savetimemin      # trip time minute
savetimemin = 0

global starttimemin
starttimemin = 0

global starttimehr
starttimehr = 0

global gpslist
gpslist=[]

global currentTrip
currentTrip = 0

global gpstime
global gpsSpeed
global username
global password
global tripnum
global dbname
global baseurl
baseurl = 'http://127.0.0.1:8000/'

# i2c addresses
#i2cBus = smbus.SMBus(1)     # Setup for i2c communication via smbus
tailEndPicAddress = 0x55    # i2c address of tail end pic
batteryPicAddress = 0x45    # i2c address of battery location pic
headEndPicAddress = 0x35    # i2c address of head end pic

motionAddress = 0x68        # address for mpu5060 motion sensor
motionPowerMgmt1 = 0x6b     # memory location of power register
motionPowerMgmt2 = 0x6c     # memory location of power register

# gpio pins
# leftButton = Button(6)     # left turn button
# rightButton = Button(5)    # right turn button
# headLightButton = Button(19)    # headlight button
# hornButton = Button(13)     # horn button
# brakeButton = Button(20)      # brake lever

# headlight_dim = LED(26)     # dim headlight
# headlight_bright = LED(21)  # bright headlight


# -----------------------------------------------------
# Function: class - temperatureThread
# Author: Tanner L
# Date: 09/20/19
# Desc: Temperature sensor communication
# Inputs:
# Outputs: temperature
# -----------------------------------------------------
class temperatureThread(th.Thread):
    def __init__(self, temperature_data):
        th.Thread.__init__(self)

        self.temperaturedatapass = temperature_data
        self.go = True
        self.humidity = 0
        self.temperature = 0

    # -----------------------------------------------------
    # Function: run
    # Author: Tanner L
    # Date: 09/20/19
    # Desc: Loop for temperatureThread, gets temperature from sensor
    # Inputs:
    # Outputs:
    # -----------------------------------------------------
    def run(self):

        import time
        # import adafruit_dht  # import library for temperature sensor
        # import board

        logging.info('Temperature Sensor Thread Start')

        while self.go:

            try:
                sensor = adafruit_dht.DHT11(board.D16)

                self.temperature = sensor.temperature  # read in temperature

                self.temperaturedatapass(self.temperature)  # send temperature to be put in queue

            except:
                logging.error('Temperature Sensor Error')

            time.sleep(10)  # send new temperature every ten seconds

    # -----------------------------------------------------
    # Function: stop_thread
    # Author: Tanner L
    # Date: 09/20/19
    # Desc: Stops thread for shutdown
    # -----------------------------------------------------
    def stop_thread(self):  # used to kill thread
        self.go = False


# -----------------------------------------------------
# Function: class - App
# Author: Tanner L
# Date: 09/20/19
# Desc: App interface
# Inputs:
# Outputs: 
# -----------------------------------------------------
class App(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)

        try:
            with open('save.txt', 'r') as f:   # read save file
                self.data = f.readline()  # read 1st line in file
                self.data = re.findall(r'\d*\.\d+|\d+', self.data)  # get all positive numbers from file
        except:
            logging.critical('Load Save File Error')

        #i2cBus.write_byte_data(batteryPicAddress, 4, self.data[1])  # send max pwn setting to battery pic
        #i2cBus.write_byte_data(tailEndPicAddress, 1, int(self.data[7])) # set flashing tail light
            
        if self.data[0] == '0':  # theme setting
            self.colour = "#606563"  # dark colour
        else:
            self.colour = 'white'

        self.title('Byke')  # main window title
        self.geometry('450x300')    # window size
        self.rowconfigure(0, weight=10)
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=2)
        self.columnconfigure(2, weight=1)
        self.config(bg=self.colour)  # window background colour
        #self.attributes('-fullscreen', True)   # make window fullscreen
        self.bind('<Escape>', lambda e: self.destroy())  # kill app with escape key

        self.tripframe = tk.Frame(self, bg=self.colour)  # screen for displaying trip data
        self.tripframe.grid(row=0, column=0, columnspan=3, sticky='nswe', ipady=20)

        self.settingsframe = tk.Frame(self, bg=self.colour)  # screen for settings
        self.settingsframe.grid(row=0, column=0, columnspan=3, sticky='nswe')

        self.uploadframe = tk.Frame(self, bg=self.colour)  # upload screen
        self.uploadframe.grid(row=0, column=0, columnspan=3, sticky='nswe')

        self.homeframe = tk.Frame(self, bg=self.colour)  # main/home screen
        self.homeframe.grid(row=0, column=0, columnspan=3, sticky='nswe')

        self.tripbutton = tk.Button(self, text='TRIPS', highlightbackground=self.colour, bg=self.colour,
                                    activebackground=self.colour, borderwidth=2, command=lambda: self.tripframe.tkraise())  # button to raise trip screen
        self.tripbutton.grid(row=1, column=0, sticky='nswe', ipady=5, ipadx=10)

        self.homebutton = tk.Button(self, text='HOME', highlightbackground=self.colour,bg=self.colour,
                                    activebackground=self.colour, borderwidth=2, command=lambda: self.homeframe.tkraise())  # button to raise home screen
        self.homebutton.grid(row=1, column=1, sticky='nswe')

        self.settingsbutton = tk.Button(self, text='SETTINGS', highlightbackground=self.colour, bg=self.colour,
                                        activebackground=self.colour, borderwidth=2, command=lambda: self.settingsframe.tkraise())  # button to raise settings screen
        self.settingsbutton.grid(row=1, column=2, sticky='nswe')

        self.homeframe.columnconfigure(0, weight=1)
        self.homeframe.columnconfigure(1, weight=1)
        self.homeframe.columnconfigure(2, weight=1)
        self.homeframe.columnconfigure(3, weight=1)
        self.homeframe.columnconfigure(4, weight=1)

        self.homeframe.rowconfigure(0, weight=1)
        self.homeframe.rowconfigure(1, weight=1)
        self.homeframe.rowconfigure(2, weight=1)

        self.homeleft = tk.Frame(self.homeframe, borderwidth=0, bg=self.colour)  # left column of home screen
        self.homeleft.grid(row=0, column=0, rowspan=3, sticky='nsew')

        self.homeleft.rowconfigure(0, weight=1)
        self.homeleft.rowconfigure(1, weight=1)
        self.homeleft.rowconfigure(2, weight=1)
        self.homeleft.rowconfigure(3, weight=1)

        self.batteryload = Image.open('100battery.png')
        self.batteryrender = ImageTk.PhotoImage(self.batteryload)
        self.batteryimage = tk.Label(self.homeleft, image=self.batteryrender, text='100%', compound='left',
                                     bg=self.colour, font=(None, 12))
        self.batteryimage.grid(row=0, column=0, sticky='wn', padx=10, pady=10)

        self.currentdisplay = tk.Label(self.homeleft, text=0, bg=self.colour)
        self.currentdisplay.grid(row=1, column=0, sticky='nw', padx=5)

        self.temperaturedisplay = tk.Label(self.homeleft, text=0, bg=self.colour, font=(None, 15))
        self.temperaturedisplay.grid(row=2, column=0, sticky='nw', padx=5)

        self.timedisplay = tk.Label(self.homeframe, text='Time', bg=self.colour, font=(None, 15))
        self.timedisplay.grid(row=0, column=2, sticky='NEW', pady=10)

        self.headLight = tk.Label(self.homeframe, text='\u263C', bg=self.colour, fg='black', font=(None, 40))
        self.headLight.grid(row=0, column=4, sticky='ne', padx=10)

        self.shutdownbutton = tk.Button(self.homeleft, text='Shutdown', highlightbackground=self.colour, bg=self.colour,
                                        activebackground=self.colour, borderwidth=2, command=self.quit_app)
        self.shutdownbutton.grid(row=3, column=0, sticky='sw', pady=5, padx=5, ipadx=5, ipady=5)

        self.speeddisplay = tk.Label(self.homeframe, text='SPEED', bg=self.colour, font=(None, 40))
        self.speeddisplay.grid(row=1, column=2, sticky='new')

        self.startStop = tk.Label(self.homeframe, text='START', bg=self.colour, fg='green', font=(None, 20))
        self.startStop.grid(row=2, column=4, rowspan=2, sticky='nesw')
        self.startStop.bind('<Button-1>', self.record)

        self.unitdisplay = tk.Label(self.homeframe, text='KMH', bg=self.colour, font=(None, 18))
        self.unitdisplay.grid(row=2, column=2)
        if self.data[4] == '0':   # set unit selection from save data
            self.unitdisplay.config(text='KMH')
        else:
            self.unitdisplay.config(text='MPH')

        self.leftTurnSignal = tk.Label(self.homeframe, fg=self.colour, bg=self.colour, text='\u2190', font=(None, 50))
        self.leftTurnSignal.grid(row=2, column=1)

        self.rightTurnSignal = tk.Label(self.homeframe, fg=self.colour, bg=self.colour, text='\u2192', font=(None, 50))
        self.rightTurnSignal.grid(row=2, column=3)

        self.settingsframe.columnconfigure(0, weight=1)
        self.settingsframe.columnconfigure(1, weight=1)
        self.settingsframe.columnconfigure(2, weight=1)

        self.settingsframe.rowconfigure(0, weight=1)
        self.settingsframe.rowconfigure(1, weight=1)
        self.settingsframe.rowconfigure(2, weight=1)

        self.unitsText = tk.LabelFrame(self.settingsframe, text='Units', bg=self.colour, borderwidth=0, font=(None, 13))
        self.unitsText.grid(row=0, column=0, sticky='nsew', pady=20, padx=0, rowspan=3)
        self.unitsText.rowconfigure(0, weight=1)
        self.unitsText.rowconfigure(1, weight=1)
        self.unitsText.rowconfigure(2, weight=1)
        self.unitsText.columnconfigure(0, weight=1)

        self.unitsOption = tk.IntVar()
        self.unitsOption.set(int(self.data[4]))

        self.imperialText = tk.Radiobutton(self.unitsText, bg=self.colour, activebackground=self.colour,
                                           highlightcolor=self.colour, text='Imperial (MPH, \u2109)', highlightthickness=0,
                                           variable=self.unitsOption, value=1, command=self.imperial_units, font=(None, 13))
        self.imperialText.grid(row=0, column=0, sticky='w')

        self.metrictext = tk.Radiobutton(self.unitsText, activebackground=self.colour, highlightcolor=self.colour,
                                         highlightthickness=0, text='Metric (KMH, \u2103)', bg=self.colour,
                                         variable=self.unitsOption, value=0, command=self.metric_units, font=(None, 13))
        self.metrictext.grid(row=1, column=0, sticky='w')

        self.flashtaillight = tk.IntVar()
        self.flashtaillight.set(int(self.data[5]))

        self.taillightflash = tk.Checkbutton(self.unitsText, text='Flashing Tail Light', activebackground=self.colour, highlightcolor=self.colour,
                                             highlightthickness=0, bg=self.colour, variable=self.flashtaillight, command=self.tail_light_flash, font=(None, 13))

        self.taillightflash.grid(row=2, column=0, sticky='w')

        self.displaytheme = tk.LabelFrame(self.settingsframe, text='Theme',  bg=self.colour, borderwidth=0, font=(None, 13))
        self.displaytheme.grid(row=0, column=1, sticky='nsew', pady=20, padx=0, rowspan=3)
        self.displaytheme.rowconfigure(0, weight=1)
        self.displaytheme.rowconfigure(1, weight=1)
        self.displaytheme.rowconfigure(2, weight=1)
        self.displaytheme.columnconfigure(0, weight=1)

        self.themeselect = tk.IntVar()
        self.themeselect.set((int(self.data[0])))

        self.lighttheme = tk.Radiobutton(self.displaytheme, bg=self.colour, activebackground=self.colour, highlightcolor=self.colour,
                                         text='Light', highlightthickness=0, variable=self.themeselect, value=1,
                                         command=self.themechange, font=(None, 13))
        self.lighttheme.grid(row=0, column=0, sticky='w')

        self.darktheme = tk.Radiobutton(self.displaytheme, activebackground=self.colour, highlightcolor=self.colour,
                                        highlightthickness=0, text='Dark', bg=self.colour, variable=self.themeselect,
                                        value=0, command=self.themechange, font=(None, 13))
        self.darktheme.grid(row=1, column=0, sticky='w')

        self.motioncal = tk.Button(self.displaytheme, text='Motion', highlightbackground=self.colour, bg=self.colour,
                                   activebackground=self.colour, borderwidth=0, command=self.motion_calibrate,
                                   font=(None, 13))
        self.motioncal.grid(row=2, column=0)

        self.maxPowerframe = tk.LabelFrame(self.settingsframe, text='Max Power % ', bg=self.colour, borderwidth=0, font=(None, 13))
        self.maxPowerframe.grid(row=0, column=3, sticky='nsew', pady=20)
        self.maxPowerframe.rowconfigure(0, weight=1)
        self.maxPowerframe.columnconfigure(0, weight=1)

        self.powerSpinner = tk.Spinbox(self.maxPowerframe, width=4, from_=30, to=100, increment=10, font=(None, 18),
                                       buttonbackground=self.colour, highlightbackground=self.colour, bg=self.colour)
        self.powerSpinner.delete(0, 'end')
        self.powerSpinner.insert(0, int(self.data[1]))
        self.powerSpinner.grid(row=0, column=0, sticky='nsew')

        self.timesetframe = tk.LabelFrame(self.settingsframe, text='Time Zone', bg=self.colour, borderwidth=0, font=(None, 13))
        self.timesetframe.grid(row=1, column=3, sticky='nsew', pady=10)
        self.timesetframe.rowconfigure(0, weight=1)
        self.timesetframe.columnconfigure(0, weight=1)

        self.timespinner = tk.Spinbox(self.timesetframe, width=3, from_=-11, to=12, font=(None, 18), bg=self.colour,
                                      buttonbackground=self.colour, highlightbackground=self.colour)
        self.timespinner.delete(0, 'end')
        self.timespinner.insert(0, int(self.data[2])-23)
        self.timespinner.grid(row=0, column=0, sticky='nsew')

        self.timedstselect = tk.IntVar()
        self.timedstselect.set(int(self.data[3]))

        self.timedst = tk.Checkbutton(self.settingsframe, text='DST ON', activebackground=self.colour, highlightcolor=self.colour,
                                      highlightthickness=0, bg=self.colour, variable=self.timedstselect, font=(None, 13))
        self.timedst.grid(row=2, column=3, pady=10)

        self.tripframe.rowconfigure(0, weight=1)
        self.tripframe.rowconfigure(1, weight=1)
        self.tripframe.columnconfigure(0, weight=1)
        self.tripframe.columnconfigure(1, weight=1)

        self.ptripframe = tk.LabelFrame(self.tripframe, text='Trip', bg=self.colour, borderwidth=0)
        self.ptripframe.grid(row=0, column=0, sticky='nsew', pady=10, padx=10, rowspan=2)
        self.ptripframe.rowconfigure(0, weight=1)
        self.ptripframe.rowconfigure(1, weight=2)
        self.ptripframe.rowconfigure(2, weight=2)
        self.ptripframe.rowconfigure(3, weight=2)
        self.ptripframe.columnconfigure(0, weight=1)

        self.ptripselect = tk.Spinbox(self.ptripframe, width=4, from_=0, to=10, font=(None, 18),
                                      command=self.previousTripDisplay, buttonbackground=self.colour,
                                      highlightbackground=self.colour, bg=self.colour)
        self.ptripselect.delete(0, 'end')
        self.ptripselect.insert(0, 1)
        self.ptripselect.grid(row=0, column=0, sticky='nsw', padx=10, pady=10)

        self.pvtDate = tk.Label(self.ptripframe, text=('Date: ' + "03" + "/" +
                                                       "04" + "/" + "05"),
                                bg=self.colour, font=(None, 13))
        self.pvtDate.grid(row=1, column=0, sticky='nsw')

        self.pvtTime = tk.Label(self.ptripframe, text=('Time: ' + '11' + ":" + '11'),
                                bg=self.colour, font=(None, 13))
        self.pvtTime.grid(row=2, column=0, sticky='nsw')

        self.apibutton = tk.Button(self.ptripframe, text='Upload', highlightbackground=self.colour, bg=self.colour,
                                   activebackground=self.colour, borderwidth=2, command=lambda: self.uploadframe.tkraise())
        self.apibutton.grid(row=3, column=0, sticky='sw', pady=0, padx=0, ipadx=6, ipady=6)

        self.ptripframe2 = tk.Frame(self.tripframe, bg=self.colour, borderwidth=0)
        self.ptripframe2.grid(row=0, column=1, rowspan=2, sticky='nsew')
        self.ptripframe2.rowconfigure(0, weight=1)
        self.ptripframe2.rowconfigure(1, weight=1)
        self.ptripframe2.rowconfigure(2, weight=1)
        self.ptripframe2.rowconfigure(3, weight=1)
        self.ptripframe2.columnconfigure(0, weight=1)

        self.pvtMaxSpeed = tk.Label(self.ptripframe2, text=('Max Speed: ' + '10'), bg=self.colour, font=(None, 13))
        self.pvtMaxSpeed.grid(row=0, column=0, sticky='w')

        self.pvtDistance = tk.Label(self.ptripframe2, text=('Distance: ' + '10'), bg=self.colour, font=(None, 13))
        self.pvtDistance.grid(row=1, column=0, sticky='w')

        self.pvtDUp = tk.Label(self.ptripframe2, text=('Uphill Distance: ' + '10'), bg=self.colour, font=(None, 13))
        self.pvtDUp.grid(row=2, column=0, sticky='w')

        self.pvtDDown = tk.Label(self.ptripframe2, text=('Downhill Distance: ' + '10'), bg=self.colour, font=(None, 13))
        self.pvtDDown.grid(row=3, column=0, sticky='w')

        self.previousTripDisplay()

        self.uploadframe.columnconfigure(0, weight=1)
        self.uploadframe.columnconfigure(1, weight=1)
        self.uploadframe.columnconfigure(2, weight=1)
        self.uploadframe.columnconfigure(3, weight=1)
        self.uploadframe.rowconfigure(0, weight=1)
        self.uploadframe.rowconfigure(1, weight=1)
        self.uploadframe.rowconfigure(2, weight=1)
        self.uploadframe.rowconfigure(3, weight=1)
        self.uploadframe.config(bg='white')

        self.userlabel = tk.Label(self.uploadframe, text="Username: ", bg='white')
        self.userlabel.grid(row=1, column=0)

        self.usernameentry = tk.Entry(self.uploadframe, bd=5)
        self.usernameentry.grid(row=1, column=1)

        self.passwordlabel = tk.Label(self.uploadframe, text="Password: ", bg='white')
        self.passwordlabel.grid(row=2, column=0)

        self.passwordentry = tk.Entry(self.uploadframe, bd=5)
        self.passwordentry.grid(row=2, column=1)

        self.triplabel = tk.Label(self.uploadframe, text="Trip Number: ", bg='white')
        self.triplabel.grid(row=0, column=0)

        self.buttonCommit = tk.Button(self.uploadframe, height=1, width=12, text="Get Input", bg='white',
                                      command=lambda: self.retrievevalues())
        self.buttonCommit.grid(row=3, column=0)

        self.buttonSend = tk.Button(self.uploadframe, height=1, width=12, text="Upload Trip", bg='white',
                                    command=lambda: self.upload())
        self.buttonSend.grid(row=3, column=1)

        self.tripentry = tk.Entry(self.uploadframe, bd=5)
        self.tripentry.grid(row=0, column=1)

        # queues for data from other threads
        self.temperature_queue = qu.Queue()

        self.after(1000, self.gps)

        self.after(500, self.buttonspress)  # call button press function every 500ms

        self.temperature_thread = temperatureThread(self.temperature_data)   # start temperature sensor thread
        # self.temperature_thread.start()

    # -----------------------------------------------------
    # Function: gps
    # Author: Tanner L
    # Date: 09/15/19
    # Desc: Gets time and speed from gps module
    # Inputs:
    # Outputs:
    # -----------------------------------------------------
    def gps(self):  # communicate with gps module

        global gpstime
        global gpsSpeed
        global gpslist
        global currentTrip
        global totaldistance

        try:
            gpstime = 0
            gpsSpeed = 0

            gpsData = gpsd.get_current()

            if gpsData.mode > 1:
                gpstime = gpsData.time
                gpsSpeed = gpsData.hspeed
                gpsLat = gpsData.lat
                gpsLong = gpsData.lon

                mClimb = self.motion()

                gpsSpeed = gpsSpeed * 3.6

                self.gps_data()

                if recordRunning is True:
                    gpslist.append(str(gpstime), float(gpsSpeed), float(gpsLat), float(gpsLong),
                                   mClimb, int(currentTrip))

                    gpsSpeed = float(gpsSpeed)

                    if gpsSpeed > 0.5:
                        distance = speed / 3600
                        totaldistance = totaldistance + distance

                else:
                    conn = sqlite3.connect('byke.db')

                    c = conn.cursor()

                    entry = "INSERT INTO GPS_DATA (TIME, SPEED, LAT, LNG, CLIMB, TRIP_ID) \
                          VALUES (?, ?, ?, ? ,?, ?, ?)"

                    c.executemany(entry, gpslist)

                    conn.commit()

                    conn.close()

        except:
            logging.error('GPS Read Error')

        self.after(1000, self.gps)

    # -----------------------------------------------------
    # Function: gps_data
    # Author: Tanner L
    # Date: 09/20/19
    # Desc: Adjusts time based on setting and speed units
    # Inputs:
    # Outputs: Time, speed
    # -----------------------------------------------------
    def gps_data(self):

        global gpstime
        global speed

        ampm = 'ampm'   # variable for setting am/pm

        timezone = int(self.timespinner.get()) + self.timedstselect.get()

        timeInHr = list(gpstime[11:13])    # get hours from time list
        timeInHr = ''.join(str(e)for e in timeInHr)  # put characters into list
        timeInHr = int(timeInHr)    # convert characters to integers

        global savetimehr
        global savetimemin
        savetimemin = list(gpstime[14:16])
        savetimemin = ''.join(str(e)for e in savetimemin)  # put characters into list
        savetimemin = int(savetimemin)

        savetimehr = timeInHr

        self.tempdata[0] = (gpstime[8:10])

        if timeInHr+timezone > 24:  # day record, adjusted for timezone
            self.tempdata[1] = (self.tempdata[0] + 1)
        elif timeInHr-timezone < 0:
            self.tempdata[1] = (self.tempdata[0] - 1)

        self.tempdata[2] = (gpstime[5:7])    # month record
        self.tempdata[3] = (gpstime[2:4])    # year record

        if 0 <= (timeInHr+timezone) < 12 or timeInHr+timezone > 23:  # determine am or pm
            ampm = 'AM'
        else:
            ampm = 'PM'

        if timezone == 0 or timezone == 12 or timezone == 13:
            if 0 < timeInHr > 12:
                timeInHr = timeInHr - 12 + self.timedstselect.get()

            elif timeInHr == 0:
                timeInHr = 12 + self.timedstselect.get()

            else:
                timeInHr = timeInHr + self.timedstselect.get()

        if -1 >= timezone >= -11:
            if 0 <= timeInHr <= abs(timezone):
                timeInHr = timeInHr + (12-abs(timezone))

            elif (abs(timezone)+1) <= timeInHr <= (12+abs(timezone)):
                timeInHr = timeInHr - abs(timezone)

            else:
                timeInHr = timeInHr - 12 - abs(timezone)

        if 1 <= timezone <= 11:
            if 0 <= timeInHr <= 11 - (timezone - 1):
                timeInHr = timeInHr + timezone

            elif (13 - timezone) <= timeInHr <= (24 - timezone):
                timeInHr = timeInHr - (12 - timezone)

            else:
                timeInHr = timeInHr - (24 - timezone)

        self.timedisplay.config(text=str(timeInHr) + ':' + str(gpstime[14:16]) + ampm)  # set time to be displayed

        if self.data[4] == '1':  # imperial speed convert
            speed = int(speed) * 0.621371
            speed = str(round(speed, 1))

        if recordRunning == 1 and float(speed) > self.tempdata[4]:   # record max trip speed
            self.tempdata[4] = int(speed)
            self.pvtMaxSpeed.config(text='Max Speed: ' + str(speed))  # display current max trip speed

        if recordRunning == 1:  # calculate trip time
            if savetimemin < starttimemin:
                savetimemin = savetimemin + 60
            if savetimehr < starttimehr:
                savetimehr = savetimehr + 24
            self.tempdata[5] = (savetimemin - starttimemin)
            self.tempdata[6] = (savetimehr - starttimehr)
            self.pvtTime.config(text='Time: ' + str(self.tempdata[6]) + ":" + str(self.tempdata[5]))    # display current elapsed time

    # -----------------------------------------------------
    # Function: temperature_data
    # Author: Tanner L
    # Date: 09/20/19
    # Desc: Put temperature from temperature sensor thread into queue
    # Inputs:
    # Outputs:
    # -----------------------------------------------------
    def temperature_data(self, temperatureread):

        if self.data[4] == '1':
            temperatureread = str(round((temperatureread * 1.8 + 32), 1)) + '\u2109'    # display temperature in F
        else:
            temperatureread = str(round(temperatureread, 1)) + '\u2103'     # display temperature in C

        self.temperature_queue.put(temperatureread)  # put temperature in queue

    # -----------------------------------------------------
    # Function: quit_app
    # Author: Tanner L
    # Date: 09/20/19
    # Desc: Kill thread and shutdown pi
    # Inputs:
    # Outputs: Time, speed
    # -----------------------------------------------------
    def quit_app(self):

        self.temperature_thread.stop_thread()

        logging.info('Temperature Thread Alive: %d', self.temperature_thread.is_alive())
        logging.info('---------------------------END OF PROGRAM------------------------')
        
        # call("sudo shutdown -h now", shell=True) # shutdown raspi
        self.destroy()

    # -----------------------------------------------------
    # Function: check_queue
    # Author: Tanner L
    # Date: 09/20/19
    # Desc: Updates displays from queued data
    # Inputs:
    # Outputs:
    # -----------------------------------------------------
    def check_queue(self):
        try:

            currenttemperature = self.temperature_queue.get_nowait()
            self.temperaturedisplay.config(text=str(currenttemperature))

        except qu.Empty:
            pass

        self.after_idle(self.check_queue) # make another check in 100 msec time

    # -----------------------------------------------------
    # Function: motion_calibrate
    # Author: Tanner L
    # Date: 09/20/19
    # Desc: Records starting x and y rotation
    # Inputs:
    # Outputs:
    # -----------------------------------------------------
    def motion_calibrate(self):
        self.data[6] = self.data_yrotate_queue.get_nowait()
        self.data[7] = self.data_xrotate_queue.get_nowait()
        self.motioncal.config(text='Calibrated')

    # -----------------------------------------------------
    # Function: tail_light_flash
    # Author: Tanner L
    # Date: 09/20/19
    # Desc: Sets bit for flashing the tail light
    # Inputs:
    # Outputs:
    # -----------------------------------------------------
    def tail_light_flash(self):
        if self.flashtaillight.get():
            i2cBus.write_byte_data(tailEndPicAddress, 1, True)
            headlight_dim.blink(on_time=0.2, off_time=0.2, n=None, background=True)
            self.data[5] = '1'
        else:
            i2cBus.write_byte_data(tailEndPicAddress, 1, False)
            headlight_dim.on()
            self.data[5] = '0'

    # -----------------------------------------------------
    # Function: metric_units
    # Author: Tanner L
    # Date: /18
    # Desc: Sets units displayed to metric
    # Inputs:
    # Outputs:
    # -----------------------------------------------------
    def metric_units(self):  # set units to metric
        try:
            self.unitdisplay.config(text='KMH')
            temp = str(self.temperaturedisplay.cget('text'))
            temp = float(temp[0:4])  # error when less than 3 digits, try taking value from queue
            self.temperaturedisplay.config(text=(str(round(((temp - 32) * 0.55556), 1)) + '\u2103'))
            self.data[4] = '0'
            self.previousTripDisplay()
        except:
            print('error')

    # -----------------------------------------------------
    # Function: imperial_units
    # Author: Tanner L
    # Date: /18
    # Desc: Sets units displayed to imperial
    # Inputs:
    # Outputs:
    # -----------------------------------------------------
    def imperial_units(self):   # set units to imperial
        try:
            self.unitdisplay.config(text='MPH')
            temp = str(self.temperaturedisplay.cget('text'))
            temp = float(temp[0:4])
            self.temperaturedisplay.config(text=(str(round((temp * 1.8 + 32), 1)) + '\u2109'))
            self.data[4] = '1'
            self.previousTripDisplay()
        except:
            print('error')

    # -----------------------------------------------------
    # Function: left_flash_on
    # Author: Tanner L
    # Date: /18
    # Desc: Turns on left turn indicator, used with left_flash_off to flash indicator
    # -----------------------------------------------------
    def left_flash_on(self):
        self.leftTurnSignal.config(fg='green')
        self.after(500, self.left_flash_off)

    # -----------------------------------------------------
    # Function: left_flash_off
    # Author: Tanner L
    # Date: /18
    # Desc: Turns off left turn indicator, used with left_flash_on to flash indicator
    # -----------------------------------------------------
    def left_flash_off(self):
        self.leftTurnSignal.config(fg=self.colour)
        if leftButton.is_pressed == 1:
            self.after(500, self.left_flash_on)

    # -----------------------------------------------------
    # Function: right_flash_on
    # Author: Tanner L
    # Date: /18
    # Desc: Turns on right turn indictor, used with right_flash_off to flash indicator
    # -----------------------------------------------------
    def right_flash_on(self):
        self.rightTurnSignal.config(fg='green')
        self.after(500, self.right_flash_off)

    # -----------------------------------------------------
    # Function: right_flash_off
    # Author: Tanner L
    # Date: /18
    # Desc: Turns on right turn indicator, used with right_flash_on to flash indicator
    # -----------------------------------------------------
    def right_flash_off(self):
        self.rightTurnSignal.config(fg=self.colour)
        if rightButton.is_pressed == 1:
            self.after(500, self.right_flash_on)

    # -----------------------------------------------------
    # Function: record
    # Author: Tanner L
    # Date: /18
    # Desc: Records trip data
    # Inputs:
    # Outputs:
    # -----------------------------------------------------
    def record(self, event):  # function to record data, called when start is pressed

        global starttimemin
        global starttimehr
        global recordRunning
        global currentTrip

        #   try:
        if recordRunning == 0:  # true when starting a trip recording
            recordRunning = 1

            self.ptripselect.delete(0, 'end')   # Set trip spinner to 0
            self.ptripselect.insert(0, 0)

            starttimemin = savetimemin
            starttimehr = savetimehr

            try:
                conn = sqlite3.connect('byke.db')

                cur = conn.cursor()

                cur.execute("select max(trip_id) from GPS_DATA")

                entry = cur.fetchone()

                print(entry)

                conn.close()

                currentTrip = entry + 1

            except:
                
                currentTrip = 0

           # self.previousTripDisplay()  # display current trip values

            self.startStop.config(text='STOP')

        else:    # true when stopping a recording
            recordRunning = 0

            self.startStop.configure(text='START')

            try:
                conn = sqlite3.connect('byke.db')
                cur = conn.cursor()

                cur.execute("select max(speed) from GPS_DATA WHERE trip_id =?", tripnum)

                maxSpeed = cur.fetchone()

                cur.execute("select avg(speed) from GPS_DATA WHERE trip_id =?", tripnum)

                avgSpeed = cur.fetchone()

                listStats = ((triptime, tripdate, maxSpeed, avgSpeed, totaldistance, tripupdist, tripdowndist, tripnum))

                entry2 = "INSERT INTO TRIP_STATS (TRIP_TIME, TRIP_DATE, TRIP_MAXSPEED, TRIP_AVGSPEED, TRIP_DISTANCE, " \
                         "TRIP_UPDISTANCE, TRIP_DOWNDISTANCE, TRIP_ID)" \
                         " VALUES (?, ?, ?, ?, ?, ?, ?, ?)"

                conn.executemany(entry2, listStats)

                conn.commit()

                conn.close()
            except:
                pass

            self.data[0] = str(self.themeselect.get())  # save theme selected
            self.data[1] = str(self.powerSpinner.get())  # save max power value
            self.data[2] = str(int(self.timespinner.get())+23)  # save time zone
            self.data[3] = str(self.timedstselect.get())  # save daylight savings on/off

            try:
                with open('save.txt', 'w') as f:    # write data out to save file
                    f.writelines(str(self.data))    # write data in single line
            except:
                logging.error('Save Error')

            self.ptripselect.delete(0, 'end')  # set trip spinner to 1
            self.ptripselect.insert(0, 1)
            self.previousTripDisplay()  # update displayed values
    #    except:

    # -----------------------------------------------------
    # Function: previousTripDisplay
    # Author: Tanner L
    # Date: /18
    # Desc: Displays previouly recorded trip data
    # Inputs:
    # Outputs:
    # -----------------------------------------------------
    def previousTripDisplay(self):  # function to scroll through trip data, selection from scroll box

        tripnum = int(self.ptripselect.get())   # get current value of trip select spin box

        conn = sqlite3.connect('byke.db')
        cur = conn.cursor()

        cur.execute("select * from TRIP_STATS WHERE trip_id =?", (tripnum,))

        tripData = cur.fetchone()

        conn.close()
        print(tripData)
        self.pvtDate.config(text=f'Date: {tripData[1]}')
        self.pvtTime.config(text=f'Time: {tripData[2]}')

        if self.unitsOption.get() == 1:
            self.pvtMaxSpeed.config(text='Max Speed: ' + str(round((tripData[3] * 0.621371), 1)) + ' MPH')
            self.pvtDistance.config(text='Distance: ' + str(round((tripData[5] * 0.621371), 1)) + ' Miles')
            self.pvtDUp.config(text='Uphill Distance: ' + str(round((tripData[6] * 0.621371), 1)) + ' Miles')
            self.pvtDDown.config(text='Downhill Distance: ' + str(round((tripData[7] * 0.621371), 1)) + ' Miles')

        else:
            self.pvtMaxSpeed.config(text=f'Max Speed: {tripData[3]} KM')
            self.pvtDistance.config(text=f'Distance: {tripData[5]} KM')
            self.pvtDUp.config(text=f'Uphill Distance: {tripData[6]} KM')
            self.pvtDDown.config(text=f'Downhill Distance: {tripData[7]} KM')

    # --------------------------------------------
    # Function: retrievevalues
    # Date: 04/10/2019
    # Author: Tanner L
    # Desc: get user input from text fields and place into variables
    # Inputs:
    # Outputs:
    # --------------------------------------------
    #@staticmethod
    def retrievevalues(self):

        global username
        global password
        global tripnum
        global dbname

        username = self.usernameentry.get()
        password = self.passwordentry.get()
        tripnum = self.tripentry.get()

    # -----------------------------------------------------
    # Function: buttonspress
    # Author: Tanner L
    # Date: /18
    # Desc: Handles button presses
    # Inputs:
    # Outputs:
    # -----------------------------------------------------
    def buttonspress(self):  # function for handling button presses

        rightpressed = 0
        leftpressed = 0
        brakepressed = 0

        try:

            if leftButton.is_pressed and leftpressed == 0:  # left signal button
                i2cBus.write_byte_data(tailEndPicAddress, 0, True)
                leftpressed = 1
                self.after(500, self.left_flash_on())

            elif leftButton.is_pressed == 0:
                leftpressed = 0
                i2cBus.write_byte_data(tailEndPicAddress, 0, False)

            if rightButton.is_pressed and rightpressed == 0:  # right signal button
                rightpressed = 1
                i2cBus.write_byte_data(tailEndPicAddress, 1, True)
                self.after(500, self.right_flash_on())

            elif rightButton.is_pressed == 0:
                rightpressed = 0
                i2cBus.write_byte_data(tailEndPicAddress, 1, False)

            if brakeButton.is_pressed and brakepressed == 0:  # brake signal button
                brakepressed = 1
                i2cBus.write_byte_data(tailEndPicAddress, 5, True)

            elif brakeButton.is_pressed == 0:
                brakepressed = 0
                i2cBus.write_byte_data(tailEndPicAddress, 5, False)

            if headLightButton.is_pressed:  # headlight button
                i2cBus.write_byte_data(tailEndPicAddress, 2, True)
                i2cBus.write_byte_data(tailEndPicAddress, 3, True)
                headlight_bright.on()
                self.headLight.config(text='\u2600', fg='blue')
            else:
                i2cBus.write_byte_data(tailEndPicAddress, 2, False)
                i2cBus.write_byte_data(tailEndPicAddress, 3, False)
                headlight_bright.off()
                self.headLight.config(text='\u263C', fg='black')

            i2cBus.write_byte_data(batteryPicAddress, 4, int(self.powerSpinner.get()))  # send max power values to pic

        except:
            logging.error('Buttons Error')

        self.after(500, self.buttonspress)

    # -----------------------------------------------------
    # Function: motorCurrent
    # Author: Tanner L
    # Date: 10/07/2019
    # Desc: Motor current display
    # Inputs:
    # Outputs:
    # -----------------------------------------------------
    def motorCurrent(self):

        receivedCurrent = i2cBus.read_byte_data(batteryPicAddress, 1)

        self.currentdisplay.config(text=str(receivedCurrent) + '%')  # motor current

        if receivedCurrent >= 100:
            self.batteryload = Image.open('100battery.png')
            self.batteryrender = ImageTk.PhotoImage(self.batteryload)
        elif 75 <= receivedCurrent <= 80:
            self.batteryload = Image.open('100battery.png')
            self.batteryrender = ImageTk.PhotoImage(self.batteryload)
        elif 50 <= receivedCurrent <= 74:
            self.batteryload = Image.open('100battery.png')
            self.batteryrender = ImageTk.PhotoImage(self.batteryload)
        elif 25 <= receivedCurrent <= 49:
            self.batteryload = Image.open('100battery.png')
            self.batteryrender = ImageTk.PhotoImage(self.batteryload)
        else:
            self.batteryload = Image.open('100battery.png')
            self.batteryrender = ImageTk.PhotoImage(self.batteryload)

    # -----------------------------------------------------
    # Function: motion_read_word
    # Author:
    # Date: /18
    # Desc: Read data from motion sensor
    # Inputs:
    # Outputs:
    # -----------------------------------------------------
    @staticmethod
    def motion_read_word(self, adr):   # function for reading motion sensor data
        high = i2cBus.read_byte_data(motionAddress, adr)
        low = i2cBus.read_byte_data(motionAddress, adr+1)
        val = (high << 8) + low
        return val

    # -----------------------------------------------------
    # Function: readWordMotion
    # Author:
    # Date: /18
    # Desc: Corrects high and low byte when put together
    # Inputs:
    # Outputs:
    # -----------------------------------------------------
    def readWordMotion(self, adr):  # function for calculating motion sensor data
        val = self.motion_read_word(adr)
        if val >= 0x8000:
            return -((65535 - val) + 1)
        else:
            return val

    # -----------------------------------------------------
    # Function: motion
    # Author:
    # Date: /18
    # Desc: Gets values from motion sensor, scales them
    # Inputs:
    # Outputs:
    # -----------------------------------------------------
    def motion(self):   # function for communicating with motion sensor, mpu5060

        try:
            i2cBus.write_byte_data(motionAddress, motionPowerMgmt1, 0)

            accel_xout_scaled = self.readWordMotion(0x3b) / 16384.0
            accel_yout_scaled = self.readWordMotion(0x3d) / 16384.0
            accel_zout_scaled = self.readWordMotion(0x3f) / 16384.0

            yRotate = -math.degrees(math.atan2(accel_xout_scaled, (math.sqrt((accel_yout_scaled*accel_yout_scaled) +
                                                                             (accel_zout_scaled*accel_zout_scaled)))))
            xRotate = -math.degrees(math.atan2(accel_yout_scaled, (math.sqrt((accel_xout_scaled*accel_xout_scaled) +
                                                                             (accel_zout_scaled*accel_zout_scaled)))))

            xyRotate = (yRotate, xRotate)

            return xyRotate

        except:
            logging.critical('Motion Read Error')

    # --------------------------------------------
    # Function: upload
    # Date: 04/10/2019
    # Author: Tanner L
    # Desc: Upload trip gps entries and trip stats for given trip number form given database
    # Modified:
    # Inputs:
    # Outputs:
    # --------------------------------------------
    def upload(self):

        import requests
        from requests.auth import HTTPBasicAuth

        global dbname
        global tripnum
        tripnum = int(tripnum)
        print(tripnum)

        req = requests.get(baseurl + 'api/login', auth=HTTPBasicAuth(username, password))
        token = req.json()

        conn = sqlite3.connect(dbname)

        cur = conn.cursor()
        cur.execute("SELECT * FROM GPS_DATA WHERE trip_id=?", (tripnum,))

        rows = cur.fetchall()

        cur.execute("SELECT * FROM TRIP_STATS WHERE trip_id=?", (tripnum,))

        tripStats = cur.fetchone()

        conn.close()

        for row in rows:
            data = {"time": row[1],
                    "speed": row[2],
                    "lng": row[4],
                    "lat": row[3],
                    "climb": row[5],
                    "user": username,
                    "trip_id": row[7],
                    "entry_id": row[0]}

            response = requests.post(baseurl + 'api/trip/add/gps', headers={'login_token': token['token']}, json=data)
            print(response.status_code)

        stats = {
            "time": tripStats.time,
            "date": tripStats.date,
            "max_speed": tripStats.max_speed,
            "avg_speed": tripStats.avg_speed,
            "uphill": tripStats.uphill,
            "downhill": tripStats.downhill,
            "distance": tripStats.distance,
            "trip_id": tripStats.trip_id,
            "user": username}
        response = requests.post(baseurl + 'api/trip/add/stats', headers={'login_token': token['token']}, json=stats)
        print(response.status_code)
        print("Done\n")

    # -----------------------------------------------------
    # Function: themechange
    # Author: Tanner L
    # Date: /18
    # Desc: Changes theme, between light and dark
    # Inputs:
    # Outputs:
    # -----------------------------------------------------
    def themechange(self):  # function to change theme colour

        if self.themeselect.get() == 1:
            self.colour = 'white'
        else:
            self.colour = "#606563"

        self.config(bg=self.colour)
        self.tripbutton.config(highlightbackground=self.colour, bg=self.colour, activebackground=self.colour)
        self.homebutton.config(highlightbackground=self.colour, bg=self.colour, activebackground=self.colour)
        self.settingsbutton.config(highlightbackground=self.colour, bg=self.colour, activebackground=self.colour)
        self.homeframe.config(bg=self.colour)
        self.settingsframe.config(bg=self.colour)
        self.tripframe.config(bg=self.colour)
        self.homeleft.config(bg=self.colour)
        self.shutdownbutton.config(highlightbackground=self.colour, bg=self.colour, activebackground=self.colour)
        self.currentdisplay.config(bg=self.colour)
        self.batteryimage.config(bg=self.colour)
        self.timedisplay.config(bg=self.colour)
        self.headLight.config(bg=self.colour)
        self.temperaturedisplay.config(bg=self.colour)
        self.rightTurnSignal.config(bg=self.colour, fg=self.colour)
        self.leftTurnSignal.config(bg=self.colour, fg=self.colour)
        self.unitdisplay.config(bg=self.colour)
        self.startStop.config(bg=self.colour)
        self.speeddisplay.config(bg=self.colour)

        self.unitsText.config(bg=self.colour)
        self.imperialText.config(bg=self.colour, activebackground=self.colour, highlightbackground=self.colour)
        self.metrictext.config(bg=self.colour, activebackground=self.colour, highlightbackground=self.colour)
        self.displaytheme.config(bg=self.colour)
        self.lighttheme.config(bg=self.colour, activebackground=self.colour, highlightbackground=self.colour)
        self.darktheme.config(bg=self.colour, activebackground=self.colour, highlightbackground=self.colour)
        self.motioncal.config(highlightbackground=self.colour, bg=self.colour, activebackground=self.colour)
        self.maxPowerframe.config(bg=self.colour)
        self.powerSpinner.config(bg=self.colour, highlightbackground=self.colour, buttonbackground=self.colour)
        self.timesetframe.config(bg=self.colour)
        self.timespinner.config(bg=self.colour, highlightbackground=self.colour, buttonbackground=self.colour)
        self.timedst.config(bg=self.colour, activebackground=self.colour, highlightbackground=self.colour)
        self.taillightflash.config(bg=self.colour, activebackground=self.colour, highlightbackground=self.colour)

        self.ptripframe.config(bg=self.colour)
        self.ptripselect.config(bg=self.colour, highlightbackground=self.colour, buttonbackground=self.colour)
        self.pvtDate.config(bg=self.colour)
        self.pvtTime.config(bg=self.colour)
        self.ptripframe2.config(bg=self.colour)
        self.pvtMaxSpeed.config(bg=self.colour)
        self.pvtDistance.config(bg=self.colour)
        self.pvtDUp.config(bg=self.colour)
        self.pvtDDown.config(bg=self.colour)


App().mainloop()    # end of interface class, tkinter interface loop
