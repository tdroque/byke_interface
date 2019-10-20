# -----------------------------------------------------
# Function: gps
# Author: Tanner L
# Date: 10/10/19
# Desc: gps module communication, and setup data for proper displaying
# Inputs:
# Outputs:
# -----------------------------------------------------
import logging
import motion
import interface

# raspberry pi libraries
import gpsd  # Gps library import


# -----------------------------------------------------
# Function: gps
# Author: Tanner L
# Date: 10/10/19
# Desc: communicates with gps module
# Inputs: record, tripid, xFlat, yFlat
# Outputs: gpsvalues, distance
# -----------------------------------------------------
def gps(record, tripid, xFlat, yFlat):  # communicate with gps module

    # dictionary to store values from gps, loaded with default values
    gpsvalues = {'speed': 10, 'time': '2019-09-23T22:53:41.000Z', 'lat': '40.1', 'lng': '80.1', 'alt': 0, 'climb': 0}
    distance = 0

    try:
        gpsd.connect()  # connect to gps module
        gpsData = gpsd.get_current()  # get data packet from gps

        if gpsData.mode > 1:  # if gps mode is greater than 1 gps has a fix
            gpsvalues['time'] = gpsData.time  # time with date
            gpsvalues['speed'] = gpsData.hspeed  # horizontal speed
            gpsvalues['lat'] = gpsData.lat  # latitude
            gpsvalues['lng'] = gpsData.lon  # longitude
            gpsvalues['alt'] = gpsData.alt  # altitude

            xrotate, yrotate = motion.motion()  # motion function to for current angle

            gpsvalues['climb'] = xrotate

            # if xRotate > xFlat:  # to determine if travelling uphill/downhill/flat
            #     gpsValues['climb'] = 1
            # elif xRotate < xFlat:
            #     gpsValues['climb'] = -1
            # else:
            #     gpsValues['climb'] = 0

            if gpsvalues['speed'] > 0.2:  # filter speed
                gpsvalues['speed'] = round(gpsvalues['speed'] * 3.6, 1)  # convert speed from m/s to km/h and round to 1 decimal
                distance = gpsvalues['speed'] / 3600  # calculate distance travelled in last second
            else:
                gpsvalues['speed'] = 0.0

            if record is True:  # if recording trip save values
                interface.entryid += 1  # increment entry_id, entry_id must be unique for entry into database
                interface.gpslist.append((interface.entryid, gpsvalues['time'], float(gpsvalues['speed']),
                                          float(gpsvalues['lat']), float(gpsvalues['lng']), gpsvalues['alt'],
                                          gpsvalues['climb'], tripid))

        # except:
        #   logging.error('GPS Read Error')
    except:
        pass

    return gpsvalues, distance


# -----------------------------------------------------
# Function: gps_data
# Author: Tanner L
# Date: 10/10/19
# Desc: Adjusts gps values based on settings for display
# Inputs: gpsValues, dst, timezone, units
# Outputs: Time, speed
# -----------------------------------------------------
def gpsdisplay(gpsValues, dst, timezone, units):

    tempdata = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

    ampm = 'ampm'  # variable for setting am/pm

    timeoffset = int(timezone + dst)

    timeInHr = list(gpsValues['time'][11:13])  # get hours from time list
    timeInHr = ''.join(str(e) for e in timeInHr)  # put characters into list
    timeInHr = int(timeInHr)  # convert characters to integers

    savetimemin = list(gpsValues['time'][14:16])
    savetimemin = ''.join(str(e) for e in savetimemin)  # put characters into list
    savetimemin = int(savetimemin)

    savetimehr = timeInHr

    tempdata[0] = int(gpsValues['time'][8:10])

    if timeInHr + timeoffset > 24:  # day record, adjusted for timezone
        tempdata[1] = (tempdata[0] + 1)
    elif timeInHr - timezone < 0:
        tempdata[1] = (tempdata[0] - 1)

    tempdata[2] = (gpsValues['time'][5:7])  # month record
    tempdata[3] = (gpsValues['time'][2:4])  # year record

    if 0 <= (timeInHr + timeoffset) < 12 or timeInHr + timeoffset > 23:  # determine am or pm
        ampm = 'AM'
    else:
        ampm = 'PM'

    if timeoffset is 0 or timeoffset is 12 or timeoffset is 13:
        if 0 < timeInHr > 12:
            timeInHr = timeInHr - 12 + dst
        elif timeInHr is 0:
            timeInHr = 12 + dst
        else:
            timeInHr = timeInHr + dst

    if -1 >= timeoffset >= -11:
        if 0 <= timeInHr <= abs(timeoffset):
            timeInHr = timeInHr + (12 - abs(timeoffset))
        elif (abs(timeoffset) + 1) <= timeInHr <= (12 + abs(timeoffset)):
            timeInHr = timeInHr - abs(timeoffset)
        else:
            timeInHr = timeInHr - 12 - abs(timeoffset)

    if 1 <= timeoffset <= 11:
        if 0 <= timeInHr <= 11 - (timeoffset - 1):
            timeInHr = timeInHr + timezone
        elif (13 - timeoffset) <= timeInHr <= (24 - timeoffset):
            timeInHr = timeInHr - (12 - timeoffset)
        else:
            timeInHr = timeInHr - (24 - timeoffset)

    timedisplay = (str(timeInHr) + ':' + str(gpsValues['time'][14:16]) + ampm)  # set time to be displayed

    if units is 1:  # imperial speed convert
        speed = int(gpsValues['speed']) * 0.621371
        speed = str(round(speed, 1))
    else:
        speed = gpsValues['speed']

    return speed, timedisplay, savetimemin, savetimehr
