# -----------------------------------------------------
# Function: buttonspress
# Author: Tanner L
# Date: 09/20/19
# Desc: Handles button presses
# Inputs:
# Outputs:
# -----------------------------------------------------
import logging
import interface

# raspberry pi libraries
# import smbus    # i2c smbus for pic communication
# import gpsd     # Gps library import
# from gpiozero import Button, LED     # import gpio function for raspberry pi
# i2c addresses
#i2cBus = smbus.SMBus(1)     # Setup for i2c communication via smbus
tailEndPicAddress = 0x55    # i2c address of tail end pic
batteryPicAddress = 0x45    # i2c address of battery location pic
headEndPicAddress = 0x35    # i2c address of head end pic

# gpio pins
# leftButton = Button(6)     # left turn button
# rightButton = Button(5)    # right turn button
# headLightButton = Button(19)    # headlight button
# hornButton = Button(13)     # horn button
# brakeButton = Button(20)      # brake lever

# headlight_dim = LED(26)     # dim headlight
# headlight_bright = LED(21)  # bright headlight


def buttonspress():  # function for handling button presses

    rightpressed = 0
    leftpressed = 0
    brakepressed = 0
    buttonspressed = [False, False, False, False, False]

    try:
        if leftButton.is_pressed and leftpressed == 0:  # left signal button
            i2cBus.write_byte_data(tailEndPicAddress, 0, True)
            leftpressed = 1
            buttonspressed[0] = True

        elif leftButton.is_pressed == 0:
            leftpressed = 0
            i2cBus.write_byte_data(tailEndPicAddress, 0, False)
            buttonspressed[0] = False

        if rightButton.is_pressed and rightpressed == 0:  # right signal button
            rightpressed = 1
            i2cBus.write_byte_data(tailEndPicAddress, 1, True)
            buttonspressed[1] = True

        elif rightButton.is_pressed == 0:
            rightpressed = 0
            i2cBus.write_byte_data(tailEndPicAddress, 1, False)
            buttonspressed[1] = False

        if brakeButton.is_pressed and brakepressed == 0:  # brake signal button
            brakepressed = 1
            i2cBus.write_byte_data(tailEndPicAddress, 5, True)
            buttonspressed[2] = True

        elif brakeButton.is_pressed == 0:
            brakepressed = 0
            i2cBus.write_byte_data(tailEndPicAddress, 5, False)
            buttonspressed[2] = False

        if headLightButton.is_pressed:  # headlight button
            i2cBus.write_byte_data(tailEndPicAddress, 2, True)
            i2cBus.write_byte_data(tailEndPicAddress, 3, True)
            buttonspressed[3] = True
        else:
            i2cBus.write_byte_data(tailEndPicAddress, 2, False)
            i2cBus.write_byte_data(tailEndPicAddress, 3, False)
            buttonspressed[3] = False

        i2cBus.write_byte_data(batteryPicAddress, 4, int(interface.powerSpinner.get()))  # send max power values to pic

    except:
        logging.error('Buttons Error')

    return buttonspressed
