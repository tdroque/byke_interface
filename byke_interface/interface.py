# -----------------------------------------------------
# Function: class - App
# Author: Tanner L
# Date: 09/20/19
# Desc: App interface
# Inputs:
# Outputs:
# -----------------------------------------------------
import tkinter as tk
import csv
import os
from PIL import ImageTk, Image
import logging
import sqlite3
from subprocess import call
import smbus
from gpiozero import LED

import api
import gps
import buttons
import temperature
import motion

logging.basicConfig(filename='information/error.log', level=logging.DEBUG)  # logging file

i2cBus = smbus.SMBus(1)     # Setup for i2c communication via smbus
taillightPicAddress = 0x55    # i2c address of tail end pic
motorPicAddress = 0x45    # i2c address of battery location pic

headlight_dim = LED(26)     # dim headlight
headlight_bright = LED(21)  # bright headlight


global recordRunning    # variable for recording trip
recordRunning = False

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

global temperature_queue
temperature_queue = 0

global entryid

try:
    conn = sqlite3.connect('information/byke.db')

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


except:
    logging.error('byke_data table error')

conn.close()


class App(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)

        global entryid
        self.distance = 0

        logging.info('--------------------INTERFACE START----------------------------')

        conn = sqlite3.connect('information/byke.db')
        cur = conn.cursor()
        cur.execute("SELECT ENTRY_ID, TRIP_ID FROM GPS_DATA WHERE ENTRY_ID = (SELECT MAX(ENTRY_ID) FROM GPS_DATA)")
        max_entry = cur.fetchone()
        conn.close()

        try:
            entryid = max_entry[0]
        except:
            entryid = 0

        try:
            self.tripid = max_entry[1]
        except:
            self.tripid = 1
        print('entryid: {}'.format(entryid))
        print('tripid: {}'.format(self.tripid))

        self.data = []
        try:
            with open('information/settings.txt', 'r') as file:  # read save file
                csvReader = csv.reader(file)
                for i, entry in enumerate(csvReader):
                    self.data.append(entry)
            self.themeSetting, self.maxPwmSetting, self.timeZoneSetting, self.dstSetting, self.unitSetting, \
            self.xRotationSet, self.yRotationSet, self.flashTaillightSetting, *_ = self.data[0]

        except:
            logging.critical('Load Save File Error')
            print('error')
        # i2cBus.write_byte_data(motorPicAddress, 4, int(self.maxPwmSetting))  # send max pwn setting to battery pic

        if self.themeSetting is '0':  # theme setting
            self.colour = "black"  # dark colour
            self.textColour = 'white'
        else:
            self.colour = 'white'
            self.textColour = 'black'

        self.title('byke')  # main window title
        self.geometry('450x300')  # window size
        self.rowconfigure(0, weight=10)
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=2)
        self.columnconfigure(2, weight=1)
        self.config(bg=self.colour)  # window background colour
        # self.attributes('-fullscreen', True)   # make window fullscreen
        self.bind('<Escape>', lambda e: os._exit(0))  # kill app with escape key

        self.tripframe = tk.Frame(self, bg=self.colour)  # screen for displaying trip data
        self.tripframe.grid(row=0, column=0, columnspan=3, sticky='nswe', ipady=20)

        self.settingsframe = tk.Frame(self, bg=self.colour)  # screen for settings
        self.settingsframe.grid(row=0, column=0, columnspan=3, sticky='nswe')

        self.uploadframe = tk.Frame(self, bg=self.colour)  # upload screen
        self.uploadframe.grid(row=0, column=0, columnspan=3, sticky='nswe')

        self.homeframe = tk.Frame(self, bg=self.colour)  # main/home screen
        self.homeframe.grid(row=0, column=0, columnspan=3, sticky='nswe')

        self.tripbutton = tk.Button(self, text='TRIPS', highlightbackground=self.colour, bg=self.colour,
                                    activebackground=self.colour, borderwidth=2, fg=self.textColour,
                                    command=lambda: self.tripframe.tkraise())  # button to raise trip screen
        self.tripbutton.grid(row=1, column=0, sticky='nswe', ipady=5, ipadx=10)

        self.homebutton = tk.Button(self, text='HOME', highlightbackground=self.colour, bg=self.colour,
                                    activebackground=self.colour, borderwidth=2, fg=self.textColour,
                                    command=lambda: self.homeframe.tkraise())  # button to raise home screen
        self.homebutton.grid(row=1, column=1, sticky='nswe')

        self.settingsbutton = tk.Button(self, text='SETTINGS', highlightbackground=self.colour, bg=self.colour,
                                        activebackground=self.colour, borderwidth=2, fg=self.textColour,
                                        command=lambda: self.settingsframe.tkraise())  # button to raise settings screen
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

        self.batteryload = Image.open('static/100battery.png')
        self.batteryrender = ImageTk.PhotoImage(self.batteryload)
        self.batteryimage = tk.Label(self.homeleft, image=self.batteryrender, text='100%', compound='left',
                                     bg=self.colour, font=(None, 12), fg=self.textColour)
        self.batteryimage.grid(row=0, column=0, sticky='wn', padx=10, pady=10)

        self.currentdisplay = tk.Label(self.homeleft, text=0, bg=self.colour, fg=self.textColour)
        self.currentdisplay.grid(row=1, column=0, sticky='nw', padx=5)

        self.temperaturedisplay = tk.Label(self.homeleft, text=0, bg=self.colour, fg=self.textColour, font=(None, 15))
        self.temperaturedisplay.grid(row=2, column=0, sticky='nw', padx=5)

        self.timedisplay = tk.Label(self.homeframe, text='Time', bg=self.colour, fg=self.textColour, font=(None, 15))
        self.timedisplay.grid(row=0, column=2, sticky='NEW', pady=10)

        self.headLight = tk.Label(self.homeframe, text='\u263C', bg=self.colour, fg=self.textColour, font=(None, 40))
        self.headLight.grid(row=0, column=4, sticky='ne', padx=10)

        self.shutdownbutton = tk.Button(self.homeleft, text='Shutdown', highlightbackground=self.colour, bg=self.colour,
                                        activebackground=self.colour, borderwidth=2, fg=self.textColour, command=self.quit_app)
        self.shutdownbutton.grid(row=3, column=0, sticky='sw', pady=5, padx=5, ipadx=5, ipady=5)

        self.speeddisplay = tk.Label(self.homeframe, text='SPEED', bg=self.colour, fg=self.textColour, font=(None, 40))
        self.speeddisplay.grid(row=1, column=2, sticky='new')

        self.startStop = tk.Label(self.homeframe, text='START', bg=self.colour, fg='#00FF00', font=(None, 16))
        self.startStop.grid(row=2, column=4, rowspan=2, sticky='nesw')
        self.startStop.bind('<Button-1>', self.record)

        self.unitdisplay = tk.Label(self.homeframe, text='KMH', bg=self.colour, fg=self.textColour, font=(None, 18))
        self.unitdisplay.grid(row=2, column=2)
        if self.unitSetting is '0':  # set unit selection from save data
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

        self.unitsText = tk.LabelFrame(self.settingsframe, text='Units', bg=self.colour, fg=self.textColour,
                                       borderwidth=0, font=(None, 13))
        self.unitsText.grid(row=0, column=0, sticky='nsew', pady=20, padx=0, rowspan=3)
        self.unitsText.rowconfigure(0, weight=1)
        self.unitsText.rowconfigure(1, weight=1)
        self.unitsText.rowconfigure(2, weight=1)
        self.unitsText.columnconfigure(0, weight=1)

        self.unitsOption = tk.IntVar()
        self.unitsOption.set(int(self.unitSetting))

        self.imperialText = tk.Radiobutton(self.unitsText, bg=self.colour, activebackground=self.colour,
                                           highlightcolor=self.colour, text='Imperial (MPH, \u2109)',
                                           highlightthickness=0, fg=self.textColour, selectcolor=self.colour,
                                           variable=self.unitsOption, value=1, command=self.imperial_units,
                                           font=(None, 13))
        self.imperialText.grid(row=0, column=0, sticky='w')

        self.metrictext = tk.Radiobutton(self.unitsText, activebackground=self.colour, highlightcolor=self.colour,
                                         highlightthickness=0, text='Metric (KMH, \u2103)', fg=self.textColour,
                                         bg=self.colour, variable=self.unitsOption, value=0, selectcolor=self.colour,
                                         command=self.metric_units, font=(None, 13))

        self.metrictext.grid(row=1, column=0, sticky='w')

        self.flashtaillight = tk.IntVar()
        self.flashtaillight.set(int(self.flashTaillightSetting))

        self.taillightflash = tk.Checkbutton(self.unitsText, text='Flashing Tail Light', activebackground=self.colour,
                                             highlightcolor=self.colour, fg=self.textColour, selectcolor=self.colour,
                                             highlightthickness=0, bg=self.colour, variable=self.flashtaillight,
                                             command=self.tail_light_flash, font=(None, 13))

        self.taillightflash.grid(row=2, column=0, sticky='w')

        self.displaytheme = tk.LabelFrame(self.settingsframe, text='Theme', bg=self.colour, borderwidth=0,
                                          fg=self.textColour, font=(None, 13))
        self.displaytheme.grid(row=0, column=1, sticky='nsew', pady=20, padx=0, rowspan=3)
        self.displaytheme.rowconfigure(0, weight=1)
        self.displaytheme.rowconfigure(1, weight=1)
        self.displaytheme.rowconfigure(2, weight=1)
        self.displaytheme.columnconfigure(0, weight=1)

        self.themeselect = tk.IntVar()
        self.themeselect.set((int(self.themeSetting)))

        self.lighttheme = tk.Radiobutton(self.displaytheme, bg=self.colour, activebackground=self.colour,
                                         highlightcolor=self.colour, fg=self.textColour, selectcolor = self.colour,
                                         text='Light', highlightthickness=0, variable=self.themeselect, value=1,
                                         command=self.themechange, font=(None, 13))
        self.lighttheme.grid(row=0, column=0, sticky='w')

        self.darktheme = tk.Radiobutton(self.displaytheme, activebackground=self.colour, highlightcolor=self.colour,
                                        highlightthickness=0, text='Dark', bg=self.colour, variable=self.themeselect,
                                        fg=self.textColour, value=0, command=self.themechange, selectcolor = self.colour,
                                        font=(None, 13))
        self.darktheme.grid(row=1, column=0, sticky='w')

        self.motioncal = tk.Button(self.displaytheme, text='Motion', highlightbackground=self.colour, bg=self.colour,
                                   activebackground=self.colour, borderwidth=0, command=self.motion_calibrate,
                                   fg=self.textColour, font=(None, 13))
        self.motioncal.grid(row=2, column=0)

        self.maxPowerframe = tk.LabelFrame(self.settingsframe, text='Max Power % ', bg=self.colour, borderwidth=0,
                                           fg=self.textColour, font=(None, 13))
        self.maxPowerframe.grid(row=0, column=3, sticky='nsew', pady=20)
        self.maxPowerframe.rowconfigure(0, weight=1)
        self.maxPowerframe.columnconfigure(0, weight=1)

        self.powerSpinner = tk.Spinbox(self.maxPowerframe, width=4, from_=30, to=100, increment=10, font=(None, 18),
                                       buttonbackground=self.colour, highlightbackground=self.colour, fg=self.textColour,
                                       bg=self.colour)
        self.powerSpinner.delete(0, 'end')
        self.powerSpinner.insert(0, int(self.maxPwmSetting))
        self.powerSpinner.grid(row=0, column=0, sticky='nsew')

        self.timesetframe = tk.LabelFrame(self.settingsframe, text='Time Zone', bg=self.colour, borderwidth=0,
                                          fg=self.textColour, font=(None, 13))
        self.timesetframe.grid(row=1, column=3, sticky='nsew', pady=10)
        self.timesetframe.rowconfigure(0, weight=1)
        self.timesetframe.columnconfigure(0, weight=1)

        self.timespinner = tk.Spinbox(self.timesetframe, width=3, from_=-11, to=12, font=(None, 18), bg=self.colour,
                                      fg=self.textColour, buttonbackground=self.colour, highlightbackground=self.colour)
        self.timespinner.delete(0, 'end')
        self.timespinner.insert(0, int(self.timeZoneSetting) - 23)
        self.timespinner.grid(row=0, column=0, sticky='nsew')

        self.timedstselect = tk.IntVar()
        self.timedstselect.set(int(self.dstSetting))

        self.timedst = tk.Checkbutton(self.settingsframe, text='DST ON', activebackground=self.colour,
                                      highlightcolor=self.colour, fg=self.textColour, selectcolor = self.colour,
                                      highlightthickness=0, bg=self.colour, variable=self.timedstselect,
                                      font=(None, 13))
        self.timedst.grid(row=2, column=3, pady=10)

        self.tripframe.rowconfigure(0, weight=1)
        self.tripframe.rowconfigure(1, weight=1)
        self.tripframe.columnconfigure(0, weight=1)
        self.tripframe.columnconfigure(1, weight=1)

        self.ptripframe = tk.LabelFrame(self.tripframe, text='Trip', bg=self.colour, borderwidth=0, fg=self.textColour)
        self.ptripframe.grid(row=0, column=0, sticky='nsew', pady=10, padx=10, rowspan=2)
        self.ptripframe.rowconfigure(0, weight=1)
        self.ptripframe.rowconfigure(1, weight=2)
        self.ptripframe.rowconfigure(2, weight=2)
        self.ptripframe.rowconfigure(3, weight=2)
        self.ptripframe.columnconfigure(0, weight=1)

        self.ptripselect = tk.Spinbox(self.ptripframe, width=4, from_=0, to=self.tripid, font=(None, 18),
                                      command=self.previousTripDisplay, buttonbackground=self.colour,
                                      fg=self.textColour, highlightbackground=self.colour, bg=self.colour)
        self.ptripselect.delete(0, 'end')
        self.ptripselect.insert(0, 1)
        self.ptripselect.grid(row=0, column=0, sticky='nsw', padx=10, pady=10)

        self.pvtDate = tk.Label(self.ptripframe, text=('Date: ' + "03" + "/" +
                                                       "04" + "/" + "05"),
                                bg=self.colour, font=(None, 13), fg=self.textColour)
        self.pvtDate.grid(row=1, column=0, sticky='nsw')

        self.pvtTime = tk.Label(self.ptripframe, text=('Time: ' + '11' + ":" + '11'),
                                bg=self.colour, font=(None, 13), fg=self.textColour)
        self.pvtTime.grid(row=2, column=0, sticky='nsw')

        self.apibutton = tk.Button(self.ptripframe, text='Upload', highlightbackground=self.colour, bg=self.colour,
                                   activebackground=self.colour, borderwidth=2, fg=self.textColour,
                                   command=lambda: self.uploadframe.tkraise())
        self.apibutton.grid(row=3, column=0, sticky='sw', pady=0, padx=0, ipadx=6, ipady=6)

        self.ptripframe2 = tk.Frame(self.tripframe, bg=self.colour, borderwidth=0)
        self.ptripframe2.grid(row=0, column=1, rowspan=2, sticky='nsew')
        self.ptripframe2.rowconfigure(0, weight=1)
        self.ptripframe2.rowconfigure(1, weight=1)
        self.ptripframe2.rowconfigure(2, weight=1)
        self.ptripframe2.rowconfigure(3, weight=1)
        self.ptripframe2.columnconfigure(0, weight=1)

        self.pvtMaxSpeed = tk.Label(self.ptripframe2, text=('Max Speed: ' + '10'), bg=self.colour, fg=self.textColour,
                                    font=(None, 13))
        self.pvtMaxSpeed.grid(row=0, column=0, sticky='w')

        self.pvtDistance = tk.Label(self.ptripframe2, text=('Distance: ' + '10'), bg=self.colour, fg=self.textColour,
                                    font=(None, 13))
        self.pvtDistance.grid(row=1, column=0, sticky='w')

        self.pvtDUp = tk.Label(self.ptripframe2, text=('Uphill Distance: ' + '10'), bg=self.colour, fg=self.textColour,
                               font=(None, 13))
        self.pvtDUp.grid(row=2, column=0, sticky='w')

        self.pvtDDown = tk.Label(self.ptripframe2, text=('Downhill Distance: ' + '10'), bg=self.colour,
                                 fg=self.textColour, font=(None, 13))
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
        self.uploadframe.config(bg=self.colour)

        self.userlabel = tk.Label(self.uploadframe, text="Username: ", bg=self.colour, fg=self.textColour)
        self.userlabel.grid(row=0, column=0)

        self.usernameentry = tk.Entry(self.uploadframe, bd=5, bg=self.colour,)
        self.usernameentry.grid(row=0, column=1)

        self.passwordlabel = tk.Label(self.uploadframe, text="Password: ", bg=self.colour, fg=self.textColour)
        self.passwordlabel.grid(row=1, column=0)

        self.passwordentry = tk.Entry(self.uploadframe, bd=5, bg=self.colour,)
        self.passwordentry.grid(row=1, column=1)

        self.buttonSend = tk.Button(self.uploadframe, height=1, width=12, text="Upload Trip", fg=self.textColour,
                                    highlightbackground=self.colour, bg=self.colour, activebackground=self.colour,
                                    borderwidth=2, command=lambda: api.upload(username=self.usernameentry.get(),
                                                                              password=self.passwordentry.get(),
                                                                              tripnum=self.ptripselect.get()))
        self.buttonSend.grid(row=1, column=2)

        self.buttonKeyboard = tk.Button(self.uploadframe, height=1, width=12, text="Keyboard", fg=self.textColour,
                                        highlightbackground=self.colour, bg=self.colour, activebackground=self.colour,
                                        borderwidth=2, command=lambda: call("matchbox-keyboard", shell=True))
        self.buttonSend.grid(row=3, column=2)

        self.tail_light_flash()

        self.after(1000, self.rungps)
        self.after(500, self.runbutton)

        self.temperature_thread = temperature.temperatureThread()  # start temperature sensor thread
        self.temperature_thread.start()

    # -----------------------------------------------------
    # Function: rungps
    # Author: Tanner L
    # Date: 10/10/19
    # Desc: function to be called every 1 sec and poll gps
    # Inputs:
    # Outputs:
    # -----------------------------------------------------
    def rungps(self):

        global savetimehr
        global savetimemin
        global starttimehr
        global starttimemin

        gpsValues, gpsdistance = gps.gps(record=recordRunning, tripid=self.tripid, xFlat=self.xRotationSet,
                                         yFlat=self.yRotationSet)

        speed, time, savetimemin, savetimehr = gps.gpsdisplay(gpsValues=gpsValues, timezone=int(self.timespinner.get()),
                                                              dst=int(self.timedstselect.get()),
                                                              units=int(self.unitSetting))

        self.speeddisplay.config(text=str(speed))
        self.timedisplay.config(text=str(time))

        if recordRunning is True:  # calculate trip time
            if savetimemin < starttimemin:
                savetimemin = savetimemin + 60
            if savetimehr < starttimehr:
                savetimehr = savetimehr + 24
            mindif = (savetimemin - starttimemin)
            hrdif = (savetimehr - starttimehr)
            diftime = int(hrdif/60 + mindif)

            self.pvtTime.config(text=str('Time: {} MINS'.format(diftime)))  # display current elapsed time
            self.pvtDate.config(text=str(gpsValues['time'][:10]))

            maxSpeed = self.pvtMaxSpeed.cget('text')
            maxSpeed = maxSpeed[11:(len(maxSpeed)-3)]

            if float(maxSpeed) < speed:
                self.pvtMaxSpeed.config(text='Max Speed: {} KMH'.format(speed))

            self.distance += gpsdistance

            self.pvtDistance.config(text='Distance: {} KM'.format(round(self.distance, 1)))

            if gpsValues['climb'] is 1:
                dup = self.pvtDUp.cget('text')
                dup = round(float(dup[16:(len(dup)-2)]) + self.distance, 1)
                self.pvtDUp.config(text='Uphill Distance: {} KM'.format(dup))
            elif gpsValues['climb'] is -1:
                ddown = self.pvtDDown.cget('text')
                ddown = round(float(ddown[19:(len(ddown)-2)]) + self.distance, 1)
                self.pvtDUp.config(text='Downhill Distance: {} KM'.format(ddown))

        self.tempUpdate()
        self.after(1000, self.rungps)

    # -----------------------------------------------------
    # Function: runbutton
    # Author: Tanner L
    # Date: 10/10/19
    # Desc: function to be called every 500ms and poll buttons
    # Inputs:
    # Outputs:
    # -----------------------------------------------------
    def runbutton(self):

        buttonStatus = buttons.buttonspress(maxPower=int(self.powerSpinner.get()))

        if buttonStatus['leftTurn'] is True:
            self.leftTurnSignal.config(fg='#00FF00')
        else:
            self.leftTurnSignal.config(fg=self.colour)

        if buttonStatus['rightTurn'] is True:
            self.rightTurnSignal.config(fg='#00FF00')
        else:
            self.rightTurnSignal.config(fg=self.colour)

        if buttonStatus['headLight'] is True:
            self.headLight.config(text='\u2600', fg='blue')
            headlight_bright.on()
        else:
            self.headLight.config(text='\u263C', fg=self.textColour)
            headlight_bright.off()

        self.after(500, self.runbutton)

    # -----------------------------------------------------
    # Function: quit_app
    # Author: Tanner L
    # Date: 09/20/19
    # Desc: Kill temperature thread, save settings, and shutdown pi
    # Inputs:
    # Outputs:
    # -----------------------------------------------------
    def quit_app(self):

        temperature.temperatureThread.stop_thread(self)

        self.data.clear()
        self.data.append(str(self.themeselect.get()))  # save theme selected
        self.data.append(str(self.powerSpinner.get()))  # save max power value
        self.data.append(str(int(self.timespinner.get()) + 23))  # save time zone
        self.data.append(str(self.timedstselect.get()))  # save daylight savings on/off
        self.data.append(str(self.unitSetting))
        self.data.append(str(self.xRotationSet))
        self.data.append(str(self.yRotationSet))
        self.data.append(str(self.flashtaillight.get()))

        try:
            with open('information/settings.txt', 'w') as file:  # write data out to save file
                csvWriter = csv.writer(file)
                csvWriter.writerow(self.data)
                logging.info('Successful Save')
        except:
            logging.error('Save Error')

        logging.info('---------------------------END OF PROGRAM------------------------')

        # call("sudo shutdown -h now", shell=True) # shutdown raspi
        os._exit(0)

    # -----------------------------------------------------
    # Function: tempUpdate
    # Author: Tanner L
    # Date: 09/20/19
    # Desc: Updates displays from queued data
    # Inputs:
    # Outputs:
    # -----------------------------------------------------
    def tempUpdate(self):
        try:
            currenttemperature = temperature_queue

            if self.unitSetting is '1':
                currenttemperature = str(round((currenttemperature * 1.8 + 32), 1)) + '\u2109'  # display temperature in F
            else:
                currenttemperature = str(round(currenttemperature, 1)) + '\u2103'  # display temperature in C

            self.temperaturedisplay.config(text=str(currenttemperature))

        except:
            pass

    # -----------------------------------------------------
    # Function: motion_calibrate
    # Author: Tanner L
    # Date: 09/20/19
    # Desc: Records starting x and y rotation
    # Inputs:
    # Outputs:
    # -----------------------------------------------------
    def motion_calibrate(self):
        self.xRotationSet,  self.yRotationSet = motion.motion()
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
            i2cBus.write_byte_data(taillightPicAddress, 1, True)
            headlight_dim.blink(on_time=0.2, off_time=0.2, n=None, background=True)
            self.flashTaillightSetting = '1'
        else:
            i2cBus.write_byte_data(taillightPicAddress, 1, False)
            headlight_dim.on()
            self.flashTaillightSetting = '0'

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
            temp = float(temp[0:len(temp)-1])  # error when less than 3 digits, try taking value from queue
            self.temperaturedisplay.config(text=(str(round(((temp - 32) * 0.55556), 1)) + '\u2103'))
            self.unitSetting = '0'
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
    def imperial_units(self):  # set units to imperial
        #try:
        self.unitdisplay.config(text='MPH')
        temp = str(self.temperaturedisplay.cget('text'))
        temp = float(temp[0:len(temp)-1])
        self.temperaturedisplay.config(text=(str(round((temp * 1.8 + 32), 1)) + '\u2109'))
        self.unitSetting = '1'
        self.previousTripDisplay()
        #except:
           # print('error')

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
        global savetimehr
        global savetimemin
        global recordRunning
        global currentTrip
        global gpslist

        #   try:
        if recordRunning is False:  # true when starting a trip recording
            recordRunning = True

            self.tripid += 1

            self.ptripselect.config(to=self.tripid)
            self.ptripselect.delete(0, 'end')  # Set trip spinner
            self.ptripselect.insert(0, self.tripid)

            starttimemin = savetimemin
            starttimehr = savetimehr

            self.pvtDDown.config(text='Downhill Distance: 0 KM')
            self.pvtDistance.config(text='Distance: 0 KM')
            self.pvtDUp.config(text='Uphill Distance: 0 KM')
            self.pvtMaxSpeed.config(text='Max Speed: 0 KMH')

            # self.previousTripDisplay()  # display current trip values

            self.startStop.config(text='STOP')

        else:  # true when stopping a recording
            recordRunning = False

            listStats = []

            self.startStop.configure(text='START')

            #try:
            conn = sqlite3.connect('information/byke.db')
            cur = conn.cursor()

            entry = "INSERT INTO GPS_DATA (ENTRY_ID, TIME, SPEED, LAT, LNG, ALT, CLIMB, TRIP_ID) \
                                  VALUES (?, ?, ?, ? ,?, ?, ?, ?)"

            cur.executemany(entry, gpslist)
            try:
                cur.execute("select avg(speed) from GPS_DATA WHERE trip_id =?", self.tripid)
                avgSpeed = cur.fetchone()
            except:
                avgSpeed = 0

            maxSpeed = self.pvtMaxSpeed.cget('text')
            maxSpeed = maxSpeed[11:(len(maxSpeed) - 3)]

            triptime = self.pvtTime.cget('text')
            triptime = triptime[6:len(triptime)-4]

            tripupdist = self.pvtDUp.cget('text')
            tripupdist = tripupdist[16: len(tripupdist)-3]

            tripdowndist = self.pvtDDown.cget('text')
            tripdowndist = tripdowndist[18: len(tripdowndist)-3]

            tripdate = self.pvtDate.cget('text')

            listStats.append((triptime, tripdate, float(maxSpeed), avgSpeed, totaldistance, tripupdist, tripdowndist,
                              self.tripid))
            print(listStats)
            entry2 = "INSERT INTO TRIP_STATS (TIME, DATE, MAX_SPEED, AVG_SPEED, DISTANCE, " \
                     "UPHILL, DOWNHILL, TRIP_ID)" \
                     " VALUES (?, ?, ?, ?, ?, ?, ?, ?)"

            conn.executemany(entry2, listStats)
            conn.commit()
            conn.close()

            gpslist.clear()
            listStats.clear()
            # except:
            #     pass

    # -----------------------------------------------------
    # Function: previousTripDisplay
    # Author: Tanner L
    # Date: /18
    # Desc: Displays previous recorded trip data
    # Inputs:
    # Outputs:
    # -----------------------------------------------------
    def previousTripDisplay(self):  # function to scroll through trip data, selection from scroll box

        if recordRunning is True:
            pass
        else:
            tripNumber = int(self.ptripselect.get())  # get current value of trip select spin box

            conn = sqlite3.connect('information/byke.db')
            cur = conn.cursor()

            cur.execute("select * from TRIP_STATS WHERE trip_id =?", (tripNumber,))
            tripData = cur.fetchone()
            print(tripData)
            conn.close()
            try:
                self.pvtDate.config(text='Date: {}'.format(tripData[1]))
                self.pvtTime.config(text='Time: {}'.format(tripData[2]))

                if self.unitsOption.get() == 1:
                    self.pvtMaxSpeed.config(text='Max Speed: ' + str(round((tripData[3] * 0.621371), 1)) + ' MPH')
                    self.pvtDistance.config(text='Distance: ' + str(round((tripData[5] * 0.621371), 1)) + ' Miles')
                    self.pvtDUp.config(text='Uphill Distance: ' + str(round((tripData[6] * 0.621371), 1)) + ' Miles')
                    self.pvtDDown.config(text='Downhill Distance: ' + str(round((tripData[7] * 0.621371), 1)) + ' Miles')

                else:
                    self.pvtMaxSpeed.config(text='Max Speed: {} KM'.format(tripData[3]))
                    self.pvtDistance.config(text='Distance: {} KM'.format(tripData[5]))
                    self.pvtDUp.config(text='Uphill Distance: {} KM'.format(tripData[6]))
                    self.pvtDDown.config(text='Downhill Distance: {} KM'.format(tripData[7]))
            except:
                pass

    # -----------------------------------------------------
    # Function: motorCurrent
    # Author: Tanner L
    # Date: 10/07/2019
    # Desc: Motor current display
    # Inputs:
    # Outputs:
    # -----------------------------------------------------
    def batteryLife(self):

        batteryPercent = i2cBus.read_byte_data(motorPicAddress, 1)

        self.batteryimage.config(text=str(batteryPercent) + '%')  # motor current

        if 76 <= batteryPercent <= 100:
            self.batteryload = Image.open('information/100battery.png')
            self.batteryrender = ImageTk.PhotoImage(self.batteryload)
        elif 51 <= batteryPercent <= 75:
            self.batteryload = Image.open('information/75battery.png')
            self.batteryrender = ImageTk.PhotoImage(self.batteryload)
        elif 26 <= batteryPercent <= 50:
            self.batteryload = Image.open('information/50battery.png')
            self.batteryrender = ImageTk.PhotoImage(self.batteryload)
        elif 0 <= batteryPercent <= 25:
            self.batteryload = Image.open('information/25battery.png')
            self.batteryrender = ImageTk.PhotoImage(self.batteryload)
        else:
            self.batteryload = Image.open('information/100battery.png')
            self.batteryrender = ImageTk.PhotoImage(self.batteryload)

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
            self.textColour = 'black'
        else:
            self.colour = 'black'
            self.textColour = 'white'

        self.config(bg=self.colour)
        self.tripbutton.config(highlightbackground=self.colour, bg=self.colour, activebackground=self.textColour,
                               fg=self.textColour)
        self.homebutton.config(highlightbackground=self.colour, bg=self.colour, activebackground=self.textColour,
                               fg=self.textColour)
        self.settingsbutton.config(highlightbackground=self.colour, bg=self.colour, activebackground=self.textColour,
                                   fg=self.textColour)

        self.homeframe.config(bg=self.colour)
        self.settingsframe.config(bg=self.colour)
        self.tripframe.config(bg=self.colour)
        self.homeleft.config(bg=self.colour)

        self.shutdownbutton.config(highlightbackground=self.colour, bg=self.colour, activebackground=self.colour, fg=self.textColour)
        self.currentdisplay.config(bg=self.colour, fg=self.textColour)
        self.batteryimage.config(bg=self.colour, fg=self.textColour)
        self.timedisplay.config(bg=self.colour, fg=self.textColour)
        self.headLight.config(bg=self.colour, fg=self.textColour)
        self.temperaturedisplay.config(bg=self.colour, fg=self.textColour)
        self.rightTurnSignal.config(bg=self.colour, fg=self.colour)
        self.leftTurnSignal.config(bg=self.colour, fg=self.colour)
        self.unitdisplay.config(bg=self.colour, fg=self.textColour)
        self.startStop.config(bg=self.colour)
        self.speeddisplay.config(bg=self.colour, fg=self.textColour)

        self.unitsText.config(bg=self.colour, fg=self.textColour)
        self.imperialText.config(bg=self.colour, activebackground=self.colour, highlightbackground=self.colour,
                                 selectcolor=self.colour, fg=self.textColour)
        self.metrictext.config(bg=self.colour, activebackground=self.colour, highlightbackground=self.colour,
                               selectcolor=self.colour, fg=self.textColour)
        self.displaytheme.config(bg=self.colour, fg=self.textColour)
        self.lighttheme.config(bg=self.colour, activebackground=self.colour, highlightbackground=self.colour,
                               selectcolor=self.colour, fg=self.textColour)
        self.darktheme.config(bg=self.colour, activebackground=self.colour, highlightbackground=self.colour,
                              selectcolor=self.colour, fg=self.textColour)
        self.motioncal.config(highlightbackground=self.colour, bg=self.colour, activebackground=self.colour,
                              fg=self.textColour)
        self.maxPowerframe.config(bg=self.colour, fg=self.textColour)
        self.powerSpinner.config(bg=self.colour, highlightbackground=self.colour, buttonbackground=self.colour,
                                 fg=self.textColour)
        self.timesetframe.config(bg=self.colour, fg=self.textColour)
        self.timespinner.config(bg=self.colour, highlightbackground=self.colour, buttonbackground=self.colour,
                                fg=self.textColour)
        self.timedst.config(bg=self.colour, activebackground=self.colour, highlightbackground=self.colour,
                            selectcolor=self.colour, fg=self.textColour)
        self.taillightflash.config(bg=self.colour, activebackground=self.colour, highlightbackground=self.colour,
                                   selectcolor=self.colour, fg=self.textColour)

        self.ptripframe.config(bg=self.colour, fg=self.textColour)
        self.ptripselect.config(bg=self.colour, highlightbackground=self.colour, buttonbackground=self.colour, fg=self.textColour)
        self.pvtDate.config(bg=self.colour, fg=self.textColour)
        self.pvtTime.config(bg=self.colour, fg=self.textColour)
        self.ptripframe2.config(bg=self.colour)
        self.pvtMaxSpeed.config(bg=self.colour, fg=self.textColour)
        self.pvtDistance.config(bg=self.colour, fg=self.textColour)
        self.pvtDUp.config(bg=self.colour, fg=self.textColour)
        self.pvtDDown.config(bg=self.colour, fg=self.textColour)
        self.apibutton.config(bg=self.colour, highlightbackground=self.colour, activebackground=self.colour, fg=self.textColour)

        self.uploadframe.config(bg=self.colour)
        self.userlabel.config(bg=self.colour, fg=self.textColour)
        self.usernameentry.config(bg=self.colour, fg=self.textColour)
        self.passwordlabel.config(bg=self.colour, fg=self.textColour)
        self.passwordentry.config(bg=self.colour, fg=self.textColour)
        self.triplabel.config(bg=self.colour, fg=self.textColour)
        self.buttonCommit.config(bg=self.colour, highlightbackground=self.colour, activebackground=self.colour, fg=self.textColour)
        self.buttonSend.config(bg=self.colour, highlightbackground=self.colour, activebackground=self.colour, fg=self.textColour)
        self.tripentry.config(bg=self.colour, fg=self.textColour)


App().mainloop()  # end of interface class, tkinter interface loop
