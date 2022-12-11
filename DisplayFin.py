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











#os.add_dll_directory(r'C:\Program Files\VideoLAN\VLC')

#p = vlc.MediaPlayer("file:///C://Users//nfeda//PycharmProjects//pythonProject2//successSound.mp3")

#def play_success():
   # p = vlc.MediaPlayer("file:///C://Users//nfeda//PycharmProjects//pythonProject2//successSound.mp3")
   # p.play()
import argparse

# Load the cascade
#face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

# window_name = "window"
# interframe_wait_ms = 30
#
# # Captures video from laptop webcam
# cap = cv2.VideoCapture(0)
#
# if not cap.isOpened():
#     print("Error: Could not get video from camera.")
#     exit()
#
# cv2.namedWindow(window_name, cv2.WND_PROP_FULLSCREEN)
# cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

# Run this loop a few times so the person being recorded has a chance
# to get their face squarer to the camera before the picture is taken
# def start_camera_recog(loops):
#     counter = 0
#     while counter < loops:
#         _, img = cap.read()
#         # Convert to grayscale
#         gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
#         # Detect the faces
#         faces = face_cascade.detectMultiScale(gray, 1.1, 4)
#         # Draw the rectangle around each face
#
#         for (x, y, w, h) in faces:
#             cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
#             roi_color = img[y:y + h, x:x + w]
#
#         cv2.imshow(window_name, img)
#
#         if cv2.waitKey(interframe_wait_ms) & 0x7F == ord('q'):
#             print("Exit requested")
#         counter+=1
#
# def capture_faces():
#     captured_face = False
#     while True:
#         # Read the frame
#         _, img = cap.read()
#         # Convert to grayscale
#         gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
#         # Detect the faces
#         faces = face_cascade.detectMultiScale(gray, 1.1, 4)
#         # Draw the rectangle around each face
#
#         for (x, y, w, h) in faces:
#             cv2.rectangle(img, (x, y), (x+w, y+h), (255, 0, 0), 2)
#             roi_color = img[y:y + h, x:x + w]
#             cv2.imwrite(str(w) + str(h) + '_faces.jpg', roi_color)
#             captured_face = True
#
#         # Display
#         cv2.imshow(window_name, img)
#         # Stop if escape key is pressed
#         k = cv2.waitKey(33) & 0xff
#         if captured_face:
#             break

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
    image = cv2.putText(img, "Welcome " + name_for_auth, org, font,
                        fontScale, color, thickness, cv2.LINE_AA)
    cv2.imshow(window_name, image)
    quitKey = cv2.waitKey(113)
    if quitKey == 113:
        cv2.destroyAllWindows()

# def main():
#     #t2 = threading.Thread(target=ping_pubnub)
#     #t2.daemon = True
#     #t2.start()
#     print("YEEhee")
#
#
# if __name__ == '__main__':
#     try:
#         # t2 = threading.Thread(target=main)
#         # t2.daemon = True
#         # t2.start()
#         #main()

# class SubscribeHandler(SubscribeCallback):
#     def message(self, pubnub, message):
#         print("Message payload: %s" % message.message)
#         print("Message publisher: %s" % message.publisher)
#         name = message[1]
#         print(message[1])
#
#         show_drawn_text(name)

#pubnub.add_listener(SubscribeHandler())
    #
    # except KeyboardInterrupt:
    #     print("\n\n Test finished ! \n")

def main():
    #show_image_scan_finger()
    #show_drawn_text("name")
    print("We in main")

class SubscribeHandler(SubscribeCallback):



    def message(self, pubnub, message):

        # window_name = "window"
        #
        # cv2.namedWindow(window_name, cv2.WND_PROP_FULLSCREEN)
        # cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

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
            #time.sleep(5)
            #show_image_scan_finger(window_name)
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


#


#cap.release()
#cv2.destroyAllWindows()
