# --------------------------------------------
# Function: upload
# Date: 04/10/2019
# Author: Tanner L
# Desc: Upload trip gps entries and trip stats for given trip number form given database
# Modified:
# Inputs:
# Outputs:
# --------------------------------------------

baseurl = 'https://byke.ca/'


def upload(username, password, tripnum):

    import sqlite3
    import requests
    from requests.auth import HTTPBasicAuth

    tripnum = int(tripnum)
    print(tripnum)

    req = requests.get(baseurl + 'api/login', auth=HTTPBasicAuth(username, password))
    token = req.json()

    conn = sqlite3.connect('byke.db')

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
