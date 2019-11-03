# -----------------------------------------------------
# File: buttons.py
# Author: Tanner L
# Date: 10/10/19
# Desc: Handles button presses
# -----------------------------------------------------
import logging
# # import smbus    # i2c smbus for pic communication
# # from gpiozero import Button, LED, TonalBuzzer     # import gpio function for raspberry pi
# # from gpiozero.tones import Tone  # import tones for horn function
#
# # i2c addresses
# i2cBus = smbus.SMBus(1)     # Setup for i2c communication via smbus
# tailEndPicAddress = 0x55    # i2c address of tail end pic
# batteryPicAddress = 0x45    # i2c address of battery location pic
#
# # gpio pins
# leftButton = Button(6)        # left turn button
# rightButton = Button(5)       # right turn button
# headLightButton = Button(19)  # headlight button
# hornButton = Button(13)       # horn button
# brakeButton = Button(20)      # brake lever
# horn = TonalBuzzer(12)        # horn


# -----------------------------------------------------
# Function: buttonspressed
# Author: Tanner L
# Date: 10/10/19
# Desc: poll buttons and set registers in remote microcontrollers
# Inputs: maxpower
# Outputs: buttonStatus
# -----------------------------------------------------
def buttonspressed(max_power):  # function for handling button presses
    # dictionary to store if button is pressed
    button_status = {'leftTurn': False, 'rightTurn': False, 'brake': False, 'headLight': False, 'horn': False}

    try:
        if leftButton.is_pressed:  # left signal button
            i2cBus.write_byte_data(tailEndPicAddress, 0, 1)
            button_status['leftTurn'] = True
        else:
            i2cBus.write_byte_data(tailEndPicAddress, 0, 0)
            button_status['leftTurn'] = False

        if rightButton.is_pressed:  # right signal button
            i2cBus.write_byte_data(tailEndPicAddress, 1, True)
            button_status['rightTurn'] = True
        else:
            i2cBus.write_byte_data(tailEndPicAddress, 1, False)
            button_status['rightTurn'] = False

        if brakeButton.is_pressed:  # brake signal button
            i2cBus.write_byte_data(tailEndPicAddress, 5, True)
            button_status['brake'] = True
        else:
            i2cBus.write_byte_data(tailEndPicAddress, 5, False)
            button_status['brake'] = False

        if headLightButton.is_pressed:  # headlight button
            i2cBus.write_byte_data(tailEndPicAddress, 2, True)
            i2cBus.write_byte_data(tailEndPicAddress, 3, True)
            button_status['headLight'] = True
        else:
            i2cBus.write_byte_data(tailEndPicAddress, 2, False)
            i2cBus.write_byte_data(tailEndPicAddress, 3, False)
            button_status['headLight'] = False

        if hornButton.is_pressed:
            horn.play(Tone(220.0))
            button_status['horn'] = True
        else:
            horn.stop()
            button_status['horn'] = False

    # i2cBus.write_byte_data(batteryPicAddress, 4, int(max_power))  # send max power values to pic

    except:
        logging.error('Buttons Error')

    return button_status
