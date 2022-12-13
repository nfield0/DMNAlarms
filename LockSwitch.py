from pubnub.callbacks import SubscribeCallback
from pubnub.enums import PNStatusCategory, PNOperationType
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub

import RPi.GPIO as GPIO
import time, threading

myChannel = "dmn-channel"
sensorList = ["lock"]
data = {}

pnconfig = PNConfiguration()

pnconfig.subscribe_key = 'sub-c-5efa4cb5-6f01-42ea-a6ac-98b3dccd764a'
pnconfig.publish_key = 'pub-c-6df66f48-e71d-41ea-a2a7-d696bda5a561'
pnconfig.uuid = 'exterior-pi'
pubnub = PubNub(pnconfig)


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


pubnub.subscribe()\
  .channels(myChannel)\
  .execute()

lock_activator_pin = 23


GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(lock_activator_pin, GPIO.OUT)


def openLock():
    GPIO.output(lock_activator_pin, GPIO.HIGH)
    time.sleep(2)
    GPIO.output(lock_activator_pin, GPIO.LOW)
    publish(myChannel, {"lock_state": 0})

class SubscribeHandler(SubscribeCallback):
    def message(self, pubnub, message):
        print("Message payload: %s" % message.message)
        print("Message publisher: %s" % message.publisher)
        #fingerprint_id = message.message['finger_scanner']

        keyVal = list(message.message.keys())
        print(keyVal)

        if keyVal[0] == 'lock_state' and message.message['lock_state'] == 1:
            openLock()
        else:
            print("PB msg ignored")

if __name__ == '__main__':
    pubnub.add_listener(SubscribeHandler())




