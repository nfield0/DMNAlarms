import serial
import time
import threading
import sys
import RPi.GPIO as GPIO


Finger_WAKE_Pin = 23

Finger_RST_Pin = 24


GPIO.setmode(GPIO.BCM)

GPIO.setwarnings(False)

GPIO.setup(Finger_WAKE_Pin, GPIO.IN)

GPIO.setup(Finger_RST_Pin, GPIO.OUT)
GPIO.setup(Finger_RST_Pin, GPIO.OUT, initial=GPIO.HIGH)

# set query comparison level as command, set to 5
# checksum is 45
input_msg = b'\xf5\x28\x00\x06\x00\x00\x2e\xf5'

#input_msg =b'\xc3\xb5(\x00\x05\x00\x00-\xc3\xb5'

ser = serial.Serial(port="/dev/ttyS0", baudrate=19200, parity=serial.PARITY_NONE,

                    stopbits=serial.STOPBITS_ONE, write_timeout=None, timeout=2, bytesize=8)


ser.reset_input_buffer()

ser.write(input_msg)

time.sleep(5)

scanner_return = ser.read(size=800)

#print(scanner_return.decode())
print(scanner_return)

ser.close

GPIO.cleanup()
