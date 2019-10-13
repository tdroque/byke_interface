# -----------------------------------------------------
# Program: Capstone - byke - raspi interface
# File: byke_interfaceV1.5.py
# Author: Tanner L
# Date: 09/10/19
# Desc: Raspberry pi interface - V 1.5, main app - communicates with gps, motion sensor, all pics, and buttons.
# -----------------------------------------------------
import logging
import sqlite3
import interface

logging.basicConfig(filename='information\\datalog.log', level=logging.DEBUG)  # logging file
logging.info('--------------------PROGRAM START----------------------------')

try:
    conn = sqlite3.connect('information\\byke.db')

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


interface.App()


