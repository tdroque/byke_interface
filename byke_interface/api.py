# --------------------------------------------
# File: upload
# Date: 19/10/2019
# Author: Tanner L
# Modified:
# Desc: Upload trip gps entries and trip stats for
#       given trip number form given database
# --------------------------------------------
import sqlite3
import requests
from requests.auth import HTTPBasicAuth
import logging
import interface


# -----------------------------------------------------
# Function: upload
# Author: Tanner L
# Date: 19/10/19
# Desc: uploads trip data to byke web app via api
# Inputs: username, password, trip number
# Outputs:
# -----------------------------------------------------
def upload(username, password, tripnum):

    baseurl = 'https://byke.ca/'  # base url for web app api urls

    tripnum = int(tripnum)  # make sure tripnum is an integer

    tok = requests.get(baseurl + 'api/login', auth=HTTPBasicAuth(username, password))  # user authentication
    token = tok.json()  # user token, pars json data into variable

    conn = sqlite3.connect('information/byke.db')  # connect to byke sqlite database
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM GPS_DATA WHERE trip_id=?", (tripnum,)) # select all entries with matching trip number
        gpsentries = cur.fetchall()

        cur.execute("SELECT * FROM TRIP_STATS WHERE trip_id=?", (tripnum,))  # select trip stats entry for trip number
        tripstats = cur.fetchone()

    except:
        logging.error('API error')

    conn.close()

    for row in gpsentries:      # upload each entry to web app individually, not correct - needs work
        data = {"time": row[1],
                "speed": row[2],
                "lng": row[4],
                "lat": row[3],
                "climb": row[5],
                "user": username,
                "trip_id": row[7],
                "entry_id": int(row[0])}
        # post request to set data to web app
        response = requests.post(baseurl + 'api/trip/add/gps', headers={'login_token': token['token']}, json=data)

        if response.status_code is not '200':
            logging.error('Trip GPS Upload Error Code {}'.format(response.status_code))
            break

    stats = {                 # putting data into format for sending to web app
        "time": tripstats[1],
        "date": tripstats[2],
        "max_speed": tripstats[3],
        "avg_speed": tripstats[4],
        "uphill": tripstats[6],
        "downhill": tripstats[7],
        "distance": tripstats[5],
        "trip_id": tripstats[0],
        "user": username}
    # post request to upload trip stats to web app
    response = requests.post(baseurl + 'api/trip/add/stats', headers={'login_token': token['token']}, json=stats)
    print(response.status_code)
    print("Done")
    if response.status_code is 200:
        interface.apiResponse = 'Successful Upload'
    elif response.status_code is 209:
        interface.apiResponse = 'Already Uploaded'
    else:
        interface.apiResponse = 'Error ' + str(response.status_code)
        logging.error('Trip Stats Upload Error Code {}'.format(response.status_code))

