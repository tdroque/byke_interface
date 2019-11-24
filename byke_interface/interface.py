# -----------------------------------------------------
# Function: class - App
# Author: Tanner L
# Date: 09/09/19
# Desc: App interface
# Inputs:
# Outputs:
# -----------------------------------------------------
import tkinter as tk            # gui builder
import csv                      # used to parse settings file
import os                       # used for shutdown application
from PIL import ImageTk, Image  # used for battery percent image
import logging                  # used for app logging
import sqlite3                  # used to interact with sqlite database
from subprocess import Popen     # used to call on screen keyboard and shutdown raspberry pi
# import smbus                    # used for i2c communication via smbus protocol
# from gpiozero import LED        # used to control the headlight circuits
#
import api                      # byke api module, api function
import gps                      # byke gps module, gps functions
# import buttons                  # byke buttons module, button functions
# import temperature              # byke temperature module, temperature sensor thread
# import motion                   # byke motion module, motion sensor functions

logging.basicConfig(filename='information/error.log', level=logging.DEBUG)  # logging file

# i2cBus = smbus.SMBus(1)     # Setup for i2c communication via smbus
taillightPicAddress = 0x55  # i2c address of tail end pic
motorPicAddress = 0x45      # i2c address of battery location pic

# headlight_led = LED(21)   # headlight

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
global apiResponse
apiResponse = 'Upload'

try:
    conn = sqlite3.connect('information/byke.db')   # connect to/create byke database in information folder

    logging.info('Opened database successfully')    # log correct database opening

except:
    logging.error('Database connection error')      # log database connection error

try:
    # create table in db for storing trip stats
    conn.execute('''CREATE TABLE IF NOT EXISTS TRIP_STATS
            (TRIP_ID  INTEGER PRIMARY KEY NOT NULL,
            DATE          TEXT,
            TIME          INTEGER,
            MAX_SPEED     REAL,
            AVG_SPEED     REAL,
            DISTANCE      REAL,
            UPHILL        REAL,
            DOWNHILL      REAL);''')

    # create table for storing gps entries
    conn.execute('''CREATE TABLE IF NOT EXISTS GPS_DATA
             (ENTRY_ID INT PRIMARY KEY     NOT NULL,
             TIME           TEXT    NOT NULL,
             SPEED          REAL,
             LAT            REAL,
             LNG            REAL,
             ALT            REAL,
             CLIMB          REAL,
             TRIP_ID        INTEGER NOT NULL);''')
    print('DB Create')

except:
    logging.error('byke_data table error')  # log table creation error

conn.close()    # disconnect from database


# -----------------------------------------------------
# Function: class - App
# Author: Tanner L
# Date: 09/09/19
# Desc: main application class, interface creation and loop
# Inputs:
# Outputs:
# -----------------------------------------------------
class App(tk.Tk):   # creat class and inherit tkinter functions
    def __init__(self):
        tk.Tk.__init__(self)

        global apiResponse
        global entryid              # used to track entryid for gps entries into database
        self.total_distance = 0     # distance travelled
        self.uphill_distance = 0    # uphill distance travelled
        self.downhill_distance = 0  # downhill distance travelled

        logging.info('--------------------INTERFACE START----------------------------')  # log interface start

        connection = sqlite3.connect('information/byke.db')  # connect to db
        cur = connection.cursor()
        # query to get max entryid and trip number from db
        cur.execute("SELECT ENTRY_ID, TRIP_ID FROM GPS_DATA WHERE ENTRY_ID = (SELECT MAX(ENTRY_ID) FROM GPS_DATA)")
        max_gps_entry = cur.fetchone()
        cur.execute("SELECT TRIP_ID FROM TRIP_STATS WHERE TRIP_ID = (SELECT MAX(TRIP_ID) FROM TRIP_STATS)")
        max_trip_id = cur.fetchone()
        connection.close()

        try:
            entryid = max_gps_entry[0]      # set entryid to max entryid from db
        except:
            entryid = 0                 # entryid is 0 if no trips in db

        try:
            if max_gps_entry[1] > max_trip_id[0]:
                logging.info('Trip id Mismatch')
                conn = sqlite3.connect('information/byke.db')  # connect to db
                cur = conn.cursor()
                entryList = ((0, 0, 0, 0, 0, 0, 0, max_gps_entry[1]))
                tripStatsEntry = "INSERT INTO TRIP_STATS (TIME, DATE, MAX_SPEED, AVG_SPEED, DISTANCE, " \
                                 "UPHILL, DOWNHILL, TRIP_ID)" \
                                 " VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
                cur.execute(tripStatsEntry, entryList)
                conn.commit()
                conn.close()

            elif max_gps_entry[1] < max_trip_id[0]:
                logging.info('Trip id Mismatch')
                listStats = []
                listStats.append((entryid+1, 0, 0, 0, 0, 0, 0, max_trip_id[0]))
                conn = sqlite3.connect('information/byke.db')
                cur = conn.cursor()

                entry = "INSERT INTO GPS_DATA (ENTRY_ID, TIME, SPEED, LAT, LNG, ALT, CLIMB, TRIP_ID) \
                                                  VALUES (?, ?, ?, ? ,?, ?, ?, ?)"

                cur.executemany(entry, listStats)
                conn.commit()
                conn.close()

                entryid += 1
        except:
            pass

        try:
            self.tripid = max_trip_id[0]
        except:
            self.tripid = 0             # if no trips in db, start with trip set to 0

        # Setting Load from settings.txt file --------------------------------------------------------------------------
        try:
            with open('information/settings.txt', 'r') as file:  # open settings file file
                csvreader = csv.DictReader(file)                     # setup csv reader
                for entry in csvreader:            # read values from file
                    self.settings = dict(entry)

        except:
            logging.critical('Load Save File Error')

        # i2cBus.write_byte_data(motorPicAddress, 4, int(self.settings['Max_PWM']))  # send max pwn setting to battery pic

        # Set theme colour from settings file --------------------------------------------------------------------------
        if self.settings['Theme'] is '0':   # theme setting
            self.colour = "black"      # background colour
            self.textColour = 'white'  # text colour
        else:
            self.colour = 'white'
            self.textColour = 'black'

        # setup tkinter window -----------------------------------------------------------------------------------------
        self.title('byke')                          # main window title
        self.geometry('450x300')                    # window size
        self.rowconfigure(0, weight=10)
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=2)
        self.columnconfigure(2, weight=1)
        self.config(bg=self.colour)                 # window background colour
        # self.attributes('-fullscreen', True)      # make window fullscreen
        self.bind('<Escape>', lambda e: os._exit(0))  # kill app with escape key

        # previous trip data screen
        self.tripframe = tk.Frame(self, bg=self.colour)
        self.tripframe.grid(row=0, column=0, columnspan=3, sticky='nswe', ipady=20)

        # settings screen
        self.settingsframe = tk.Frame(self, bg=self.colour)
        self.settingsframe.grid(row=0, column=0, columnspan=3, sticky='nswe')

        # trip upload screen
        self.uploadframe = tk.Frame(self, bg=self.colour)
        self.uploadframe.grid(row=0, column=0, columnspan=3, sticky='nswe')

        # home screen
        self.homeframe = tk.Frame(self, bg=self.colour)  # main/home screen
        self.homeframe.grid(row=0, column=0, columnspan=3, sticky='nswe')

        # button to show trip screen
        self.tripbutton = tk.Button(self, text='TRIPS', highlightbackground=self.colour, bg=self.colour,
                                    activebackground=self.colour, borderwidth=2, fg=self.textColour,
                                    command=lambda: self.tripframe.tkraise())
        self.tripbutton.grid(row=1, column=0, sticky='nswe', ipady=5, ipadx=10)

        # button to show home screen
        self.homebutton = tk.Button(self, text='HOME', highlightbackground=self.colour, bg=self.colour,
                                    activebackground=self.colour, borderwidth=2, fg=self.textColour,
                                    command=lambda: self.homeframe.tkraise())  # button to raise home screen
        self.homebutton.grid(row=1, column=1, sticky='nswe')

        # button to show setting screen
        self.settingsbutton = tk.Button(self, text='SETTINGS', highlightbackground=self.colour, bg=self.colour,
                                        activebackground=self.colour, borderwidth=2, fg=self.textColour,
                                        command=lambda: self.settingsframe.tkraise())  # button to raise settings screen
        self.settingsbutton.grid(row=1, column=2, sticky='nswe')

        # home screen layout configuration -----------------------------------------------------------------------------
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

        # battery percent image display
        self.batteryload = Image.open('static/100battery.png')
        self.batteryrender = ImageTk.PhotoImage(self.batteryload)
        self.batteryimage = tk.Label(self.homeleft, image=self.batteryrender, text='100%', compound='left',
                                     bg=self.colour, font=(None, 12), fg=self.textColour)
        self.batteryimage.grid(row=0, column=0, sticky='wn', padx=10, pady=10)

        # motor current draw
        self.currentdisplay = tk.Label(self.homeleft, text=0, bg=self.colour, fg=self.textColour)
        self.currentdisplay.grid(row=1, column=0, sticky='nw', padx=5)

        # temperature display
        self.temperaturedisplay = tk.Label(self.homeleft, text=0, bg=self.colour, fg=self.textColour, font=(None, 15))
        self.temperaturedisplay.grid(row=2, column=0, sticky='nw', padx=5)

        # time display
        self.timedisplay = tk.Label(self.homeframe, text='Time', bg=self.colour, fg=self.textColour, font=(None, 15))
        self.timedisplay.grid(row=0, column=2, sticky='NEW', pady=10)

        # display if headlight is on or off
        self.headLight = tk.Label(self.homeframe, text='\u263C', bg=self.colour, fg=self.textColour, font=(None, 40))
        self.headLight.grid(row=0, column=4, sticky='ne', padx=10)

        # button to shutdown
        self.shutdownbutton = tk.Button(self.homeleft, text='Shutdown', highlightbackground=self.colour, bg=self.colour,
                                        activebackground=self.colour, borderwidth=2, fg=self.textColour, command=self.quit_app)
        self.shutdownbutton.grid(row=3, column=0, sticky='sw', pady=5, padx=5, ipadx=5, ipady=5)

        # speed display
        self.speeddisplay = tk.Label(self.homeframe, text='SPEED', bg=self.colour, fg=self.textColour, font=(None, 40))
        self.speeddisplay.grid(row=1, column=2, sticky='new')

        # trip record button
        self.startStop = tk.Label(self.homeframe, text='START', bg=self.colour, fg='#00FF00', font=(None, 16))
        self.startStop.grid(row=2, column=4, rowspan=2, sticky='nesw')
        self.startStop.bind('<Button-1>', self.record)

        # speed units
        self.unitdisplay = tk.Label(self.homeframe, text='KMH', bg=self.colour, fg=self.textColour, font=(None, 18))
        self.unitdisplay.grid(row=2, column=2)
        if self.settings['Units'] is '0':  # set unit selection from save data
            self.unitdisplay.config(text='KMH')
        else:
            self.unitdisplay.config(text='MPH')

        # display if left turn signal is active
        self.leftTurnSignal = tk.Label(self.homeframe, fg=self.colour, bg=self.colour, text='\u2190', font=(None, 50))
        self.leftTurnSignal.grid(row=2, column=1)

        # display if right turn is active
        self.rightTurnSignal = tk.Label(self.homeframe, fg=self.colour, bg=self.colour, text='\u2192', font=(None, 50))
        self.rightTurnSignal.grid(row=2, column=3)

        # setting screen configuration ---------------------------------------------------------------------------------
        self.settingsframe.columnconfigure(0, weight=1)
        self.settingsframe.columnconfigure(1, weight=1)
        self.settingsframe.columnconfigure(2, weight=1)

        self.settingsframe.rowconfigure(0, weight=1)
        self.settingsframe.rowconfigure(1, weight=1)
        self.settingsframe.rowconfigure(2, weight=1)

        # radio buttons to select metric or imperial units
        self.unitsText = tk.LabelFrame(self.settingsframe, text='Units', bg=self.colour, fg=self.textColour,
                                       borderwidth=0, font=(None, 13))
        self.unitsText.grid(row=0, column=0, sticky='nsew', pady=20, padx=0, rowspan=3)
        self.unitsText.rowconfigure(0, weight=1)
        self.unitsText.rowconfigure(1, weight=1)
        self.unitsText.rowconfigure(2, weight=1)
        self.unitsText.columnconfigure(0, weight=1)

        self.unitsOption = tk.IntVar()
        self.unitsOption.set(int(self.settings['Units']))

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

        # check box to select flashing tail light option
        self.flashtaillight = tk.IntVar()
        self.flashtaillight.set(int(self.settings['Flashing_Taillight']))

        self.taillightflash = tk.Checkbutton(self.unitsText, text='Flashing Tail Light', activebackground=self.colour,
                                             highlightcolor=self.colour, fg=self.textColour, selectcolor=self.colour,
                                             highlightthickness=0, bg=self.colour, variable=self.flashtaillight,
                                             command=self.tail_light_flash, font=(None, 13))

        self.taillightflash.grid(row=2, column=0, sticky='w')

        # radio button to select between light and dark theme
        self.displaytheme = tk.LabelFrame(self.settingsframe, text='Theme', bg=self.colour, borderwidth=0,
                                          fg=self.textColour, font=(None, 13))
        self.displaytheme.grid(row=0, column=1, sticky='nsew', pady=20, padx=0, rowspan=3)
        self.displaytheme.rowconfigure(0, weight=1)
        self.displaytheme.rowconfigure(1, weight=1)
        self.displaytheme.rowconfigure(2, weight=1)
        self.displaytheme.columnconfigure(0, weight=1)

        self.themeselect = tk.IntVar()
        self.themeselect.set((int(self.settings['Theme'])))

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

        # button to calibrate motion setting
        self.motioncal = tk.Button(self.displaytheme, text='Motion', highlightbackground=self.colour, bg=self.colour,
                                   activebackground=self.colour, borderwidth=0, command=self.motion_calibrate,
                                   fg=self.textColour, font=(None, 13))
        self.motioncal.grid(row=2, column=0)

        # spinner box to set max pwm, 30-100% in 10% increments
        self.maxPowerframe = tk.LabelFrame(self.settingsframe, text='Max Power % ', bg=self.colour, borderwidth=0,
                                           fg=self.textColour, font=(None, 13))
        self.maxPowerframe.grid(row=0, column=3, sticky='nsew', pady=20)
        self.maxPowerframe.rowconfigure(0, weight=1)
        self.maxPowerframe.columnconfigure(0, weight=1)

        self.powerSpinner = tk.Spinbox(self.maxPowerframe, width=4, from_=30, to=100, increment=10, font=(None, 18),
                                       buttonbackground=self.colour, highlightbackground=self.colour,
                                       fg=self.textColour, bg=self.colour)
        self.powerSpinner.delete(0, 'end')
        self.powerSpinner.insert(0, int(self.settings['Max_PWM']))
        self.powerSpinner.grid(row=0, column=0, sticky='nsew')

        # time zone settings, timezone spinner box and dst checkbox
        self.timesetframe = tk.LabelFrame(self.settingsframe, text='Time Zone', bg=self.colour, borderwidth=0,
                                          fg=self.textColour, font=(None, 13))
        self.timesetframe.grid(row=1, column=3, sticky='nsew', pady=10)
        self.timesetframe.rowconfigure(0, weight=1)
        self.timesetframe.columnconfigure(0, weight=1)

        self.timespinner = tk.Spinbox(self.timesetframe, width=3, from_=-11, to=12, font=(None, 18), bg=self.colour,
                                      fg=self.textColour, buttonbackground=self.colour, highlightbackground=self.colour)
        self.timespinner.delete(0, 'end')
        self.timespinner.insert(0, int(self.settings['Time_Zone']))
        self.timespinner.grid(row=0, column=0, sticky='nsew')

        self.timedstselect = tk.IntVar()
        self.timedstselect.set(int(self.settings['DST']))

        self.timedst = tk.Checkbutton(self.settingsframe, text='DST ON', activebackground=self.colour,
                                      highlightcolor=self.colour, fg=self.textColour, selectcolor = self.colour,
                                      highlightthickness=0, bg=self.colour, variable=self.timedstselect,
                                      font=(None, 13))
        self.timedst.grid(row=2, column=3, pady=10)

        # trip data screen configuration -------------------------------------------------------------------------------
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

        # spinner box to select which trip to display
        self.ptripselect = tk.Spinbox(self.ptripframe, width=4, from_=0, to=self.tripid, font=(None, 18),
                                      command=self.previousTripDisplay, buttonbackground=self.colour,
                                      fg=self.textColour, highlightbackground=self.colour, bg=self.colour)
        self.ptripselect.delete(0, 'end')
        self.ptripselect.insert(0, 1)
        self.ptripselect.grid(row=0, column=0, sticky='nsw', padx=10, pady=10)

        # date of trip
        self.pvtDate = tk.Label(self.ptripframe, text='Date: 00-00-0000',
                                bg=self.colour, font=(None, 13), fg=self.textColour)
        self.pvtDate.grid(row=1, column=0, sticky='nsw')

        # trip time
        self.pvtTime = tk.Label(self.ptripframe, text='Time: 00',
                                bg=self.colour, font=(None, 13), fg=self.textColour)
        self.pvtTime.grid(row=2, column=0, sticky='nsw')

        # button to upload trip to web app
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

        # max speed of trip
        self.pvtMaxSpeed = tk.Label(self.ptripframe2, text='Max Speed: 0', bg=self.colour, fg=self.textColour,
                                    font=(None, 13))
        self.pvtMaxSpeed.grid(row=0, column=0, sticky='w')

        # total distance of trip
        self.pvtDistance = tk.Label(self.ptripframe2, text='Distance: 0', bg=self.colour, fg=self.textColour,
                                    font=(None, 13))
        self.pvtDistance.grid(row=1, column=0, sticky='w')

        # uphill distance of trip
        self.pvtDUp = tk.Label(self.ptripframe2, text='Uphill Distance: 0', bg=self.colour, fg=self.textColour,
                               font=(None, 13))
        self.pvtDUp.grid(row=2, column=0, sticky='w')

        # downhill distance of trip
        self.pvtDDown = tk.Label(self.ptripframe2, text='Downhill Distance: 0', bg=self.colour,
                                 fg=self.textColour, font=(None, 13))
        self.pvtDDown.grid(row=3, column=0, sticky='w')

        self.previousTripDisplay()

        # trip upload screen configure ---------------------------------------------------------------------------------
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

        # username entry box
        self.usernameentry = tk.Entry(self.uploadframe, bd=5, bg=self.colour,)
        self.usernameentry.grid(row=0, column=1)

        self.passwordlabel = tk.Label(self.uploadframe, text="Password: ", bg=self.colour, fg=self.textColour)
        self.passwordlabel.grid(row=1, column=0)

        # password entry box
        self.passwordentry = tk.Entry(self.uploadframe, bd=5, bg=self.colour,)

        self.passwordentry.grid(row=1, column=1)

        # button to upload
        self.buttonSend = tk.Button(self.uploadframe, height=1, width=12, text="Upload Trip", fg=self.textColour,
                                    highlightbackground=self.colour, bg=self.colour, activebackground=self.colour,
                                    borderwidth=2,
                                    command=lambda: api.upload(username=self.usernameentry.get(),
                                                               password=self.passwordentry.get(),
                                                               tripnum=self.ptripselect.get()))
        self.buttonSend.grid(row=2, column=2)

        # button to open on screen keyboard
        self.buttonKeyboard = tk.Button(self.uploadframe, height=1, width=12, text="Keyboard", fg=self.textColour,
                                        highlightbackground=self.colour, bg=self.colour, activebackground=self.colour,
                                        borderwidth=2, command=lambda: Popen("matchbox-keyboard", shell=True))
        self.buttonKeyboard.grid(row=2, column=1)

        self.responseLabel = tk.Label(self.uploadframe, text=str(apiResponse), bg=self.colour, fg=self.textColour,
                                      font=(None, 13))
        self.responseLabel.grid(row=3, column=2)

        self.tail_light_flash()

        # tkinter functions to call functions
        self.after(1000, self.rungps)    # call rungps function every 1000ms
        # self.after(500, self.buttons_query)  # call runbutton function every 500ms

        # start temperature sensor thread
        # self.temperature_thread = temperature.TemperatureThread()  # start temperature sensor thread
        # self.temperature_thread.start()

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

        gpsValues, gpsdistance = gps.gps(record=recordRunning, tripid=self.tripid,
                                                        xFlat=self.settings['X_Rotation'],
                                                        yFlat=self.settings['Y_Rotation'])

        speed, time, savetimemin, savetimehr = gps.gpsdisplay(gpsValues=gpsValues,
                                                                             timezone=int(self.timespinner.get()),
                                                                             dst=int(self.timedstselect.get()),
                                                                             units=int(self.settings['Units']))

        self.speeddisplay.config(text=str(speed))   # display current speed from gps
        self.timedisplay.config(text=str(time))     # display current time from gps

        if recordRunning is True:  # calculate elapsed trip time to display
            if savetimemin < starttimemin:
                savetimemin = savetimemin + 60
            if savetimehr < starttimehr:
                savetimehr = savetimehr + 24
            mindif = (savetimemin - starttimemin)
            hrdif = (savetimehr - starttimehr)
            diftime = int(hrdif/60 + mindif)

            self.pvtTime.config(text=str('Time: {} MINS'.format(diftime)))  # display current elapsed time
            self.pvtDate.config(text=str(gpsValues['time'][:10]))

            max_speed = self.pvtMaxSpeed.cget('text')    # get max speed text currently being displayed
            max_speed = max_speed[11:(len(max_speed)-3)]   # get speed numbers from text

            if float(max_speed) < speed:                 # compare max speed to current speed
                self.pvtMaxSpeed.config(text='Max Speed: {} KMH'.format(speed))

            self.total_distance += gpsdistance    # add distance travelled from gps to total distance

            self.pvtDistance.config(text='Distance: {} KM'.format(round(self.total_distance, 1)))

            if gpsValues['climb'] is 1:
                self.uphill_distance += gpsdistance
                self.pvtDUp.config(text='Uphill Distance: {} KM'.format(round(self.uphill_distance, 1)))
            elif gpsValues['climb'] is -1:
                self.downhill_distance += gpsdistance
                self.pvtDUp.config(text='Downhill Distance: {} KM'.format(round(self.downhill_distance,1)))

        self.responseLabel.config(text=str(apiResponse))
        # self.temperature_update()               # call temperature update function
        self.picRead()     # call battery life update
        self.after(1000, self.rungps)   # tkinter function to call function every 1000ms

    # -----------------------------------------------------
    # Function: runbutton
    # Author: Tanner L
    # Date: 10/10/19
    # Desc: function to be called every 500ms and poll buttons
    # Inputs:
    # Outputs:
    # -----------------------------------------------------
    def buttons_query(self):

        button_status = buttons.buttonspressed(max_power=int(self.powerSpinner.get()))  # get max pwm setting from interface

        if button_status['leftTurn'] is True:            # turn on left turn signal indicator on interface
            self.leftTurnSignal.config(fg='#00FF00')
        else:
            self.leftTurnSignal.config(fg=self.colour)

        if button_status['rightTurn'] is True:           # turn on right turn signal indicator on interface
            self.rightTurnSignal.config(fg='#00FF00')
        else:
            self.rightTurnSignal.config(fg=self.colour)

        if button_status['headLight'] is True:           # turn on headlight on indicator
            self.headLight.config(text='\u2600', fg='blue')
            headlight_led.on()
        else:
            self.headLight.config(text='\u263C', fg=self.textColour)
            headlight_led.off()

        self.after(500, self.buttons_query)    # tkinter function to call function every 500ms

    # -----------------------------------------------------
    # Function: quit_app
    # Author: Tanner L
    # Date: 09/20/19
    # Desc: Kill temperature thread, save settings, and shutdown pi
    # Inputs:
    # Outputs:
    # -----------------------------------------------------
    def quit_app(self):

        try:
            try:
                self.temperature_thread.stop_thread()     # stop temperature thread
            except:
                logging.info('Temperature Thread Kill Error')

            try:
                self.settings['Theme'] = (str(self.themeselect.get()))                 # save theme selected
                self.settings['Max_PWM'] = (str(self.powerSpinner.get()))              # save max power value
                self.settings['Time_Zone'] = (str(self.timespinner.get()))             # save time zone
                self.settings['DST'] = (str(self.timedstselect.get()))                 # save daylight savings on/off
                self.settings['Units'] = (str(self.unitsOption.get()))                       # save unit setting
                self.settings['X_Rotation'] = self.settings['X_Rotation']                # save calibration for x direction
                self.settings['Y_Rotation'] = self.settings['Y_Rotation']                 # save calibration for y direction
                self.settings['Flash_Taillight'] = (str(self.flashtaillight.get()))    # save flashing light option setting
            except:
                logging.error('Saving Settings Error')

            try:
                with open('information/settings.txt', 'w') as file:                     # open settings file
                    csvwriter = csv.DictWriter(file, fieldnames=self.settings.keys())   # setup csv writer
                    csvwriter.writeheader()
                    csvwriter.writerow(self.settings)                                   # write settings to file
            except:
                logging.error('Setting File Write Error')

            logging.info('Successful Save')                                         # log if successful save

        except:
            logging.error('Save Error')                                             # log if error saving

        logging.info('---------------------------END OF PROGRAM------------------------')

        # Popen("sudo shutdown -h now", shell=True) # shutdown raspi
        os._exit(0)     # exit application

    # -----------------------------------------------------
    # Function: tempUpdate
    # Author: Tanner L
    # Date: 09/20/19
    # Desc: Updates displays from queued data
    # Inputs:
    # Outputs:
    # -----------------------------------------------------
    def temperature_update(self):
        try:
            current_temperature = temperature_queue

            if self.settings['Units'] is '1':
                current_temperature = str(round((current_temperature * 1.8 + 32), 1)) + '\u2109'  # display temperature in F
            else:
                current_temperature = str(round(current_temperature, 1)) + '\u2103'  # display temperature in C

            self.temperaturedisplay.config(text=str(current_temperature))

        except:
            pass

    # -----------------------------------------------------
    # Function: motion_calibrate
    # Author: Tanner L
    # Date: 09/20/19
    # Desc: Records flat x and y for uphill/downhill measuring
    # Inputs:
    # Outputs:
    # -----------------------------------------------------
    def motion_calibrate(self):
        self.settings['X_Rotation'],  self.settings['Y_Rotation'] = motion.motion()
        self.motioncal.config(text='Calibrated')

    # -----------------------------------------------------
    # Function: tail_light_flash
    # Author: Tanner L
    # Date: 09/20/19
    # Desc: Sets bit for flashing the taillight
    # Inputs:
    # Outputs:
    # -----------------------------------------------------
    def tail_light_flash(self):
        try:
            if self.flashtaillight.get():
                # i2cBus.write_byte_data(taillightPicAddress, 1, True)
                self.settings['Flash_Taillight'] = '1'
            else:
                # i2cBus.write_byte_data(taillightPicAddress, 1, False)
                self.settings['Flash_Taillight'] = '0'
        except:
            pass

    # -----------------------------------------------------
    # Function: metric_units
    # Author: Tanner L
    # Date: 07/10/19
    # Desc: Sets units displayed to metric
    # Inputs:
    # Outputs:
    # -----------------------------------------------------
    def metric_units(self):  # set units to metric
        try:
            self.unitdisplay.config(text='KMH')
            temp = str(self.temperaturedisplay.cget('text'))
            temp = float(temp[0:len(temp)-1])
            self.temperaturedisplay.config(text=(str(round(((temp - 32) * 0.55556), 1)) + '\u2103'))
            self.settings['Units'] = '0'
            self.previousTripDisplay()
        except:
            print('error')

    # -----------------------------------------------------
    # Function: imperial_units
    # Author: Tanner L
    # Date: 07/10/19
    # Desc: Sets units displayed to imperial
    # Inputs:
    # Outputs:
    # -----------------------------------------------------
    def imperial_units(self):  # set units to imperial
        try:
            self.unitdisplay.config(text='MPH')
            temp = str(self.temperaturedisplay.cget('text'))
            temp = float(temp[0:len(temp)-1])
            self.temperaturedisplay.config(text=(str(round((temp * 1.8 + 32), 1)) + '\u2109'))
            self.settings['Units'] = '1'
            self.previousTripDisplay()
        except:
           print('error')

    # -----------------------------------------------------
    # Function: record
    # Author: Tanner L
    # Date: 07/10/19
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
            tripStatsEntry = "INSERT INTO TRIP_STATS (TIME, DATE, MAX_SPEED, AVG_SPEED, DISTANCE, " \
                     "UPHILL, DOWNHILL, TRIP_ID)" \
                     " VALUES (?, ?, ?, ?, ?, ?, ?, ?)"

            conn.executemany(tripStatsEntry, listStats)
            conn.commit()
            conn.close()

            gpslist.clear()
            listStats.clear()
            # except:
            #     pass

    # -----------------------------------------------------
    # Function: previousTripDisplay
    # Author: Tanner L
    # Date: 07/10/19
    # Desc: Displays previous recorded trip data
    # Inputs:
    # Outputs:
    # -----------------------------------------------------
    def previousTripDisplay(self):  # function to scroll through trip data, selection from scroll box

        if recordRunning is True:
            self.ptripselect.delete(0, 'end')
            self.ptripselect.insert(0, self.tripid)
            pass
        else:
            tripNumber = int(self.ptripselect.get())  # get current value of trip select spin box

            conn = sqlite3.connect('information/byke.db')
            cur = conn.cursor()

            cur.execute("select * from TRIP_STATS WHERE trip_id =?", (tripNumber,))
            tripData = cur.fetchone()
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
    # Function: batterylife
    # Author: Tanner L
    # Date: 07/10/2019
    # Desc: battery life display, in 25% increments
    # Inputs:
    # Outputs:
    # -----------------------------------------------------
    def picRead(self):

        try:
            motorCurrent = i2cBus.read_byte_data(motorPicAddress, 1)
            self.currentdisplay.config(text=str(motorCurrent) + ' A')
        except:
            self.currentdisplay.config(text='Error')
            logging.error('Motor Current Error')

        try:
            batteryPercent = i2cBus.read_byte_data(motorPicAddress, 3)

            if 76 <= batteryPercent <= 100:
                self.batteryload = Image.open('static/100battery.png')
                self.batteryrender = ImageTk.PhotoImage(self.batteryload)
                self.batteryimage.config(image=self.batteryrender, text=' 100%')
            elif 51 <= batteryPercent <= 75:
                self.batteryload = Image.open('static/75battery.png')
                self.batteryrender = ImageTk.PhotoImage(self.batteryload)
                self.batteryimage.config(image=self.batteryrender, text=' 75%')
            elif 26 <= batteryPercent <= 50:
                self.batteryload = Image.open('static/50battery.png')
                self.batteryrender = ImageTk.PhotoImage(self.batteryload)
                self.batteryimage.config(image=self.batteryrender, text=' 50%')
            elif 0 <= batteryPercent <= 25:
                self.batteryload = Image.open('static/25battery.png')
                self.batteryrender = ImageTk.PhotoImage(self.batteryload)
                self.batteryimage.config(image=self.batteryrender, text=' 25%')
            elif batteryPercent == 0:
                self.batteryload = Image.open('static/0battery.png')
                self.batteryrender = ImageTk.PhotoImage(self.batteryload)
                self.batteryimage.config(image=self.batteryrender, text=' 0%')
            else:
                self.batteryload = Image.open('static/0battery.png')
                self.batteryrender = ImageTk.PhotoImage(self.batteryload)
                self.batteryimage.config(image=self.batteryrender, text=' Error')

        except:
            self.batteryload = Image.open('static/0battery.png')
            self.batteryrender = ImageTk.PhotoImage(self.batteryload)
            self.batteryimage.config(image=self.batteryrender, text=' Error')
            logging.error('Battery Percentage Read Error')

        try:
            motorPicTemp = i2cBus.read_byte_data(motorPicAddress, 7)
            if motorPicTemp >= 125:
                self.currentdisplay.config(text='Error')
                self.batteryimage.config(text='Error')
                logging.error('Motor Pic High Temp Shutdown')
            elif motorPicTemp == 100:
                logging.info('Motor Pic High Temp Warning')
        except:
            logging.error('Motor Pic Temp Read Error')

        try:
            motorPicTemp = i2cBus.read_byte_data(taillightPicAddress, 6)
            if motorPicTemp >= 125:
                self.rightTurnSignal.config(text='Error', fg='red', font=(None, 10))
                self.leftTurnSignal.config(text='Error', fg='red', font=(None, 10))
                logging.error('Tail Pic High Temp Shutdown')
            elif motorPicTemp == 100:
                logging.info('Tail Pic High Temp Warning')
        except:
            logging.error('Tail Pic Temp Read Error')

    # -----------------------------------------------------
    # Function: themechange
    # Author: Tanner L
    # Date: 07/10/19
    # Desc: Changes theme, between light and dark
    # Inputs:
    # Outputs:
    # -----------------------------------------------------
    def themechange(self):  # function to change theme colour

        try:
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

            self.shutdownbutton.config(highlightbackground=self.colour, bg=self.colour,
                                       activebackground=self.colour, fg=self.textColour)
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
            self.ptripselect.config(bg=self.colour, highlightbackground=self.colour,
                                    buttonbackground=self.colour, fg=self.textColour)
            self.pvtDate.config(bg=self.colour, fg=self.textColour)
            self.pvtTime.config(bg=self.colour, fg=self.textColour)
            self.ptripframe2.config(bg=self.colour)
            self.pvtMaxSpeed.config(bg=self.colour, fg=self.textColour)
            self.pvtDistance.config(bg=self.colour, fg=self.textColour)
            self.pvtDUp.config(bg=self.colour, fg=self.textColour)
            self.pvtDDown.config(bg=self.colour, fg=self.textColour)
            self.apibutton.config(bg=self.colour, highlightbackground=self.colour,
                                  activebackground=self.colour, fg=self.textColour)

            self.uploadframe.config(bg=self.colour)
            self.userlabel.config(bg=self.colour, fg=self.textColour)
            self.usernameentry.config(bg=self.colour, fg=self.textColour)
            self.passwordlabel.config(bg=self.colour, fg=self.textColour)
            self.passwordentry.config(bg=self.colour, fg=self.textColour)
            self.responseLabel.config(bg=self.colour, fg=self.textColour)
            self.buttonSend.config(bg=self.colour, highlightbackground=self.colour,
                                   activebackground=self.colour, fg=self.textColour)
            self.buttonKeyboard.config(bg=self.colour, highlightbackground=self.colour,
                                       activebackground=self.colour, fg=self.textColour)
        except:
            logging.error('Theme Change Error')

App().mainloop()  # end of interface class, tkinter interface loop
