import datetime

import serial
import time
import threading
import sys
import RPi.GPIO as GPIO
from dateutil.utils import today
from datetime import datetime


from pubnub.callbacks import SubscribeCallback
from pubnub.enums import PNStatusCategory, PNOperationType
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub
from flask_mysqldb import MySQL
myChannel = "dmn-channel"
sensorList = ["finger_scanner, finger_scanner_new"]
data = {}

pnconfig = PNConfiguration()

pnconfig.subscribe_key = 'sub-c-5efa4cb5-6f01-42ea-a6ac-98b3dccd764a'
pnconfig.publish_key = 'pub-c-6df66f48-e71d-41ea-a2a7-d696bda5a561'
pnconfig.uuid = 'exterior-pi'
pubnub = PubNub(pnconfig)
mysql = MySQL()

pubnub.subscribe()\
  .channels(myChannel)\
  .execute()

class SubscribeHandler(SubscribeCallback):
    def message(self, pubnub, message):
        print("Message payload: %s" % message.message)
        print("Message publisher: %s" % message.publisher)
        fingerprint_id = message.message['finger_scanner']

        date = today()
        now = datetime.now().time()
        current_time = now.strftime("%H:%M:%S")
        cursor = mysql.connection.cursor()
        cursor.execute(''' INSERT INTO employee_access_table VALUES(null,%s,%s)''', (date, current_time, fingerprint_id))
        mysql.connection.commit()
        cursor.close()

pubnub.add_listener(SubscribeHandler())