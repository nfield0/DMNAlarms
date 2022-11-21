
#motion detection connected to pubnub as starting point

import RPi.GPIO as GPIO
import time, threading
import socket

#camera imports
# from picamera import PiCamera
import pygame.camera

#pubnub imports
from pubnub.callbacks import SubscribeCallback
from pubnub.enums import PNStatusCategory, PNOperationType
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub

PIR_pin = 23
Buzzer_pin = 24

lock_activator_pin = 25
press_input_pin = 19

myChannel = "dmn-channel"
sensorList = ["buzzer", "press"]
data = {}

pnconfig = PNConfiguration()

pnconfig.subscribe_key = 'sub-c-5efa4cb5-6f01-42ea-a6ac-98b3dccd764a'
pnconfig.publish_key = 'pub-c-6df66f48-e71d-41ea-a2a7-d696bda5a561'
pnconfig.uuid = 'exterior-pi'
pubnub = PubNub(pnconfig)

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(PIR_pin, GPIO.IN)
GPIO.setup(Buzzer_pin, GPIO.OUT)
GPIO.setup(lock_activator_pin, GPIO.OUT)
GPIO.setup(press_input_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

def beep(repeat):
    for i in range(0, repeat):
        for pulse in range(60):
            GPIO.output(Buzzer_pin, True)
            time.sleep(0.001)
            GPIO.output(Buzzer_pin, False)
            time.sleep(0.001)
        time.sleep(0.02)


def motionDetection():
    data["alarm"] = False
    print("Sensors started")
    trigger = False
    while True:
        if GPIO.input(PIR_pin):
            print("Motion detected")
            beep(4)
            trigger = True
            publish(myChannel, {"motion" : "Yes"})
            time.sleep(1)
        elif trigger:
            publish(myChannel, {"motion" : "No"})

        if data["alarm"]:
            beep(2)

def press_detection():
    data["press"] = False
    print("inside press detection")
    trigger = False
    while True:
        if(GPIO.input(press_input_pin)):
            print("press detected!")
            data["press"] = True
            toggle_lock()
            trigger = True
            publish(myChannel, {"press": "Yes"})
        else:
            data["press"] = False
            toggle_lock()
            print("No press")
            publish(myChannel, {"motion": "No"})
        time.sleep(0.5)

def toggle_lock():
    if data["press"] == True:
        GPIO.output(lock_activator_pin, 1)
    else:
        GPIO.output(lock_activator_pin, 0)


def boot():
    print("Starting exterior pi")


#start thread for each of these
    #motionDetection()
    #press_detection()
    #fingerprint_Sensing()
    facial_Recognition()





 # Fingerprint Function
def fingerprint_Sensing():
    print("Fingerprint started")

    #Facial Recognition Function
def facial_Recognition():
    print("Facial recognition started")


# initialize the camera



#pubnub
def publish(custom_channel, msg):
    pubnub.publish().channel(custom_channel).message(msg).pn_async(my_publish_callback)

def my_publish_callback(envelope, status):
    # Check whether request successfully completed or not
    if not status.is_error():
        pass  # Message successfully published to specified channel.
    else:
        pass  # Handle message publish error. Check 'category' property to find out possible issue
        # because of which request did fail.
        # Request can be resent using: [status retry];


class MySubscribeCallback(SubscribeCallback):
    def presence(self, pubnub, presence):
        pass  # handle incoming presence data

    def status(self, pubnub, status):
        if status.category == PNStatusCategory.PNUnexpectedDisconnectCategory:
            pass  # This event happens when radio / connectivity is lost

        elif status.category == PNStatusCategory.PNConnectedCategory:
            # Connect event. You can do stuff like publish, and know you'll get it.
            # Or just use the connected event to confirm you are subscribed for
            # UI / internal notifications, etc
            pubnub.publish().channel(myChannel).message('Connected to PubNub').pn_async(my_publish_callback)
        elif status.category == PNStatusCategory.PNReconnectedCategory:
            pass
            # Happens as part of our regular operation. This event happens when
            # radio / connectivity is lost, then regained.
        elif status.category == PNStatusCategory.PNDecryptionErrorCategory:
            pass
            # Handle message decryption error. Probably client configured to
            # encrypt messages and on live data feed it received plain text.

    def message(self, pubnub, message):
        # Handle new message stored in message.message
        try:
            print(message.message)
            msg = message.message
            key = list(msg.keys())
            if key[0] == "event":       #{"event" : {"sensor_name" : True}}
                self.handleEvent(msg)
        except Exception as e:
            print("Received: ", message.message)
            print(e)
            pass


    def handleEvent(self, msg):
        global data
        eventData = msg["event"]
        key = list(eventData.keys())
        if key[0] in sensorList:
            if eventData[key[0]] is True:
                data["alarm"] = True
            elif eventData[key[0]] is False:
                data["alarm"] = False


if __name__ == "__main__":
    sensorsThread = threading.Thread(target=boot)
    sensorsThread.start()
    pubnub.add_listener(MySubscribeCallback())
    pubnub.subscribe().channels(myChannel).execute()



