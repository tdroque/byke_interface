# -----------------------------------------------------
# Function: gps
# Author: Tanner L
# Date: 09/15/19
# Desc: Gets time and speed from gps module
# Inputs:
# Outputs:
# -----------------------------------------------------
import logging
import sqlite3
import motion

# raspberry pi libraries
# import smbus    # i2c smbus for pic communication
# import gpsd     # Gps library import
# from gpiozero import Button, LED


def gps():  # communicate with gps module

    gpsValues = {'speed': 0, 'time': '', 'lat': '', 'lng': '', 'climb': 0}

    try:

        gpsData = gpsd.get_current()

        if gpsData.mode > 1:
            gpsValues['time'] = gpsData.time
            gpsValues['speed'] = gpsData.hspeed
            gpsValues['lat'] = gpsData.lat
            gpsValues['lng'] = gpsData.lon

            gpsValues['clmib'] = motion.motion()

            gpsValues['speed'] = gpsValues['speed'] * 3.6

    except:
        logging.error('GPS Read Error')

    listvalues = gps_data(gpsValues)

    return listvalues


# -----------------------------------------------------
# Function: gps_data
# Author: Tanner L
# Date: 09/20/19
# Desc: Adjusts time based on setting and speed units
# Inputs:
# Outputs: Time, speed
# -----------------------------------------------------
def gps_data():
    data = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    tempdata = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    pvtMaxSpeed = 0
    pvtTime = 0
    ampm = 'ampm'  # variable for setting am/pm

    timezone = int(timespinner + timedstselect)

    timeInHr = list(gpstime[11:13])  # get hours from time list
    timeInHr = ''.join(str(e) for e in timeInHr)  # put characters into list
    timeInHr = int(timeInHr)  # convert characters to integers

    savetimemin = list(gpstime[14:16])
    savetimemin = ''.join(str(e) for e in savetimemin)  # put characters into list
    savetimemin = int(savetimemin)

    savetimehr = timeInHr

    tempdata[0] = int(gpstime[8:10])

    if timeInHr + timezone > 24:  # day record, adjusted for timezone
        tempdata[1] = (tempdata[0] + 1)
    elif timeInHr - timezone < 0:
        tempdata[1] = (tempdata[0] - 1)

    tempdata[2] = (gpstime[5:7])  # month record
    tempdata[3] = (gpstime[2:4])  # year record

    if 0 <= (timeInHr + timezone) < 12 or timeInHr + timezone > 23:  # determine am or pm
        ampm = 'AM'
    else:
        ampm = 'PM'

    if timezone == 0 or timezone == 12 or timezone == 13:
        if 0 < timeInHr > 12:
            timeInHr = timeInHr - 12 + timedstselect

        elif timeInHr == 0:
            timeInHr = 12 + timedstselect

        else:
            timeInHr = timeInHr + timedstselect

    if -1 >= timezone >= -11:
        if 0 <= timeInHr <= abs(timezone):
            timeInHr = timeInHr + (12 - abs(timezone))

        elif (abs(timezone) + 1) <= timeInHr <= (12 + abs(timezone)):
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
    timeInHr = 10
    timedisplay =(str(timeInHr) + ':' + str(gpstime[14:16]) + ampm)  # set time to be displayed

    if data[4] == '1':  # imperial speed convert
        speed = int(speed) * 0.621371
        speed = str(round(speed, 1))

    if recordRunning == 1:  # calculate trip time
        if savetimemin < starttimemin:
            savetimemin = savetimemin + 60
        if savetimehr < starttimehr:
            savetimehr = savetimehr + 24
        tempdata[5] = (savetimemin - starttimemin)
        tempdata[6] = (savetimehr - starttimehr)
        pvtTime =('Time: ' + str(tempdata[6]) + ":" + str(tempdata[5]))  # display current elapsed time

    return tempdata[4], timedisplay
