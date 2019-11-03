# -----------------------------------------------------
# Program: Capstone - byke - raspberry pi app
# File: byke_app.py
# Author: Tanner L
# Date: 09/10/19
# Desc: Raspberry pi interface, main app - communicates with gps, motion sensor,
#       buttons, motor controller and taillight. Controls headlight, save trip
#       stats and upload to web app
# -----------------------------------------------------
import byke_interface.interface    # byke interface module

if __name__ is '__main__':
    byke_interface.interface.App()     # run app class from interface module
