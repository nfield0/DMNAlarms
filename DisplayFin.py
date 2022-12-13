from pubnub.callbacks import SubscribeCallback
from pubnub.enums import PNStatusCategory, PNOperationType
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub
import threading
import cv2
import json
import os
import time
#import vlc

myChannel = "dmn-channel"
sensorList = ["finger_scanner, finger_scanner_new"]

pnconfig = PNConfiguration()
pnconfig.subscribe_key = 'sub-c-5efa4cb5-6f01-42ea-a6ac-98b3dccd764a'
pnconfig.publish_key = 'pub-c-6df66f48-e71d-41ea-a2a7-d696bda5a561'
pnconfig.uuid = 'exterior-pi'
pubnub = PubNub(pnconfig)

#pubnub.subscribe().channels(myChannel).execute()

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

def show_image_scan_finger(window_name):
    image = cv2.imread("screen_img.jpg")
    cv2.imshow(window_name, image)
    quitKey = cv2.waitKey(113)
    if quitKey == 113:
        cv2.destroyAllWindows()

def show_image_scan_image_again(window_name):
    image = cv2.imread("screen_img.jpg")
    cv2.imshow(window_name, image)
    cv2.waitKey(0)

def show_drawn_text(name_for_auth, window_name):
    #play_success()

    img = cv2.imread("blank_screen.jpg")

    # font
    font = cv2.FONT_HERSHEY_SIMPLEX

    # org
    org = (50, 50)

    # fontScale
    fontScale = 1

    # Blue color in BGR
    color = (255, 0, 0)

    # Line thickness of 2 px
    thickness = 6

    # Using cv2.putText() method
    image = cv2.putText(img, "Unlocked for " + name_for_auth, org, font,
                        fontScale, color, thickness, cv2.LINE_AA)
    cv2.imshow(window_name, image)
    quitKey = cv2.waitKey(113)
    if quitKey == 113:
        cv2.destroyAllWindows()


def main():
    print("scan finger for screen to pop up")

class SubscribeHandler(SubscribeCallback):
    def message(self, pubnub, message):

        print("Message payload: %s" % message.message)
        print("Message publisher: %s" % message.publisher)

        keyVal = list(message.message.keys())
        print(keyVal)



        if keyVal[0] == 'lock_state' and message.message['lock_state'] == 0:

            window_name = "window"

            cv2.namedWindow(window_name, cv2.WND_PROP_FULLSCREEN)
            cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

            show_image_scan_finger(window_name)
            #show_image_scan_finger()
        elif keyVal[0] == "Account":

            window_name = "window"

            cv2.namedWindow(window_name, cv2.WND_PROP_FULLSCREEN)
            cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

            furtherKeys = list(message.message["Account"].keys())
            print(furtherKeys)
            name = furtherKeys[1]
            print(furtherKeys[1])
            print("FINBOY: ", message.message["Account"][name])
            name_of_our_boi = message.message["Account"][name]

            show_drawn_text(name_of_our_boi, window_name)
            publish(myChannel, {"lock_state": 1})
        else:
            print("Message from PB ignored")


if __name__ == '__main__':
    try:
        main()
        # pubnub.add_listener(main())
        pubnub.add_listener(SubscribeHandler())
        pubnub.subscribe().channels(myChannel).execute()

    except KeyboardInterrupt:
        print("\n\n Test finished ! \n")
