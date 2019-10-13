
# -----------------------------------------------------
# Function: motion_read_word
# Author:
# Date: /18
# Desc: Read data from motion sensor
# Inputs:
# Outputs:
# -----------------------------------------------------
@staticmethod
def motion_read_word(adr):  # function for reading motion sensor data
    high = i2cBus.read_byte_data(motionAddress, adr)
    low = i2cBus.read_byte_data(motionAddress, adr + 1)
    val = (high << 8) + low
    return val


# -----------------------------------------------------
# Function: readWordMotion
# Author:
# Date: /18
# Desc: Corrects high and low byte when put together
# Inputs:
# Outputs:
# -----------------------------------------------------
def readWordMotion(adr):  # function for calculating motion sensor data
    val = motion_read_word(adr)
    if val >= 0x8000:
        return -((65535 - val) + 1)
    else:
        return val


# -----------------------------------------------------
# Function: motion
# Author:
# Date: /18
# Desc: Gets values from motion sensor, scales them
# Inputs:
# Outputs:
# -----------------------------------------------------
def motion():  # function for communicating with motion sensor, mpu5060

    try:
        i2cBus.write_byte_data(motionAddress, motionPowerMgmt1, 0)

        accel_xout_scaled = readWordMotion(0x3b) / 16384.0
        accel_yout_scaled = readWordMotion(0x3d) / 16384.0
        accel_zout_scaled = readWordMotion(0x3f) / 16384.0

        yRotate = -math.degrees(math.atan2(accel_xout_scaled, (math.sqrt((accel_yout_scaled * accel_yout_scaled) +
                                                                         (accel_zout_scaled * accel_zout_scaled)))))
        xRotate = -math.degrees(math.atan2(accel_yout_scaled, (math.sqrt((accel_xout_scaled * accel_xout_scaled) +
                                                                         (accel_zout_scaled * accel_zout_scaled)))))

        xyRotate = (xRotate, yRotate)

        return xyRotate

    except:
        logging.critical('Motion Read Error')
