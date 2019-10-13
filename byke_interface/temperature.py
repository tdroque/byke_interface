# -----------------------------------------------------
# Function: class - temperatureThread
# Author: Tanner L
# Date: 09/20/19
# Desc: Temperature sensor communication
# Inputs:
# Outputs: temperature
# -----------------------------------------------------
import threading as th
import logging
import interface


class temperatureThread(th.Thread):
    def __init__(self):
        th.Thread.__init__(self)

        logging.basicConfig(filename='information\\temperature.log', level=logging.DEBUG)  # logging file
        logging.info('--------------------TEMPERATURE START----------------------------')

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

            interface.temperature_queue += 2

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
