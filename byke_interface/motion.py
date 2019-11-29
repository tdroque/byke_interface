# -----------------------------------------------------
# File: motion
# Author: Tanner L
# Date: 10/10/19
# Desc: Motion sensor
# -----------------------------------------------------
import logging
import math
import smbus


i2cBus = smbus.SMBus(1)     # Setup for i2c communication via smbus
motionAddress = 0x68  # address for mpu5060 motion sensor
motionPowerMgmt1 = 0x6b  # memory location of power register
motionPowerMgmt2 = 0x6c  # memory location of power register


# -----------------------------------------------------
# Function: motion_read_word
# Author:
# Modified: Tanner L
# Date: 10/10/19
# Desc: Read data from motion sensor
# Inputs: register address
# Outputs: values
# -----------------------------------------------------
def motion_read_word(adr):  # function for reading motion sensor data
    high = i2cBus.read_byte_data(motionAddress, adr)
    low = i2cBus.read_byte_data(motionAddress, adr + 1)
    val = (high << 8) + low
    return val


# -----------------------------------------------------
# Function: read_word_motion
# Author:
# Modified: Tanner L
# Date: 10/10/19
# Desc: Corrects high and low byte when put together
# Inputs: register address
# Outputs: value
# -----------------------------------------------------
def read_word_motion(adr):  # function for calculating motion sensor data
    val = motion_read_word(adr)
    if val >= 0x8000:
        return -((65535 - val) + 1)
    else:
        return val


# -----------------------------------------------------
# Function: motion
# Author:
# Modified: Tanner L
# Date: 10/10/19
# Desc: Gets values from motion sensor, scales them
# Inputs:
# Outputs: xyRotate, rotation value for x and y
# -----------------------------------------------------
def motion():  # function for communicating with motion sensor, mpu5060

    try:
        i2cBus.write_byte_data(motionAddress, motionPowerMgmt1, 0)

        accel_xout_scaled = read_word_motion(0x3b) / 16384.0
        accel_yout_scaled = read_word_motion(0x3d) / 16384.0
        accel_zout_scaled = read_word_motion(0x3f) / 16384.0

        y_rotate = -math.degrees(math.atan2(accel_xout_scaled, (math.sqrt((accel_yout_scaled * accel_yout_scaled) +
                                                                         (accel_zout_scaled * accel_zout_scaled)))))
        x_rotate = -math.degrees(math.atan2(accel_yout_scaled, (math.sqrt((accel_xout_scaled * accel_xout_scaled) +
                                                                         (accel_zout_scaled * accel_zout_scaled)))))

        xy_rotate = (x_rotate, y_rotate)

        print('Y: {} X: {} A: {} {} {}'.format(round(y_rotate, 2), round(x_rotate, 2), round(accel_xout_scaled, 2),
                                               round(accel_yout_scaled, 2), round(accel_zout_scaled, 2)))

        return xy_rotate

    except:
        logging.critical('Motion Sensor Read Error')
