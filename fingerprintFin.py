#!/usr/bin/env python3.5
# -*- coding:utf-8 -*-

import serial
import time
import threading
import sys
import RPi.GPIO as GPIO


from pubnub.callbacks import SubscribeCallback
from pubnub.enums import PNStatusCategory, PNOperationType
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub

myChannel = "dmn-channel"
sensorList = ["finger_scanner, finger_scanner_new"]
data = {}

pnconfig = PNConfiguration()

pnconfig.subscribe_key = 'sub-c-5efa4cb5-6f01-42ea-a6ac-98b3dccd764a'
pnconfig.publish_key = 'pub-c-6df66f48-e71d-41ea-a2a7-d696bda5a561'
pnconfig.uuid = 'exterior-pi'
pubnub = PubNub(pnconfig)

TRUE = 1
FALSE = 0

# Basic response message definition
ACK_SUCCESS = 0
ACK_FAIL = 1
ACK_FULL = 4
ACK_NO_USER = 5
ACK_TIMEOUT = 8
ACK_GO_OUT = 15  # The center of the fingerprint is out of alignment with sensor

# User information definition
ACK_ALL_USER = 0
ACK_GUEST_USER = 1
ACK_NORMAL_USER = 2
ACK_MASTER_USER = 3

USER_MAX_CNT = 1000  # Maximum fingerprint number

# Command definition
CMD_HEAD = 245
CMD_TAIL = 245
CMD_ADD_1 = 1
CMD_ADD_2 = 2
CMD_ADD_3 = 3
CMD_MATCH = 12
CMD_DEL = 4
CMD_DEL_ALL = 5
CMD_USER_COUNT = 9
CMD_SET_OR_QUERY_COMPARISON_LEVEL = 40
CMD_SLEEP_MODE = 44
CMD_TIMEOUT = 46

CMD_FINGER_DETECTED = 20 # NOT FOUND IN DOCUMENTATION

Finger_WAKE_Pin = 23
Finger_RST_Pin = 24

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(Finger_WAKE_Pin, GPIO.IN)
GPIO.setup(Finger_RST_Pin, GPIO.OUT)
GPIO.setup(Finger_RST_Pin, GPIO.OUT)
GPIO.output(Finger_RST_Pin, GPIO.HIGH)

g_rx_buf = []   #RXD
latest_scanned_id = 0
PC_Command_RxBuf = []   #Figure OUT
Finger_SleepFlag = 0

# rLock = threading.RLock()     Was here before i did anything
ser = serial.Serial(port="/dev/ttyS0", baudrate=19200, parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE, write_timeout=None, timeout=None, bytesize=8)
#Set up serial connection, cts and rts also available params


# ***************************************************************************
# @brief    send a command, and wait for the response of module
# ***************************************************************************/

def TxAndRxCmd(command_buf, rx_bytes_need, timeout): # [0x28, 0, level, 0, 0] , 8, 0.1
    global g_rx_buf
    CheckSum = 0
    tx_buf = []
    tx = b''

    print("COMMAND BUFFER: ", command_buf)

    tx_buf.append(CMD_HEAD) # [0xF5]
    for int_val in command_buf:
        tx_buf.append(int_val)
        CheckSum ^= int_val

    print("CHECKSUM: ", CheckSum)
    tx_buf.append(CheckSum)
    tx_buf.append(CMD_TAIL)

    for i in tx_buf:
        print(i)
        tx += i.to_bytes(1, "big")

    ser.reset_input_buffer()        # Old flushInput() is deprecated

    print("TYPE OF TX NOW!!!: ",type(tx))
    print("TX NOW: ", tx)

    print("Byte String TX: : ", tx)
    wrtn = ser.write(tx)

    print("Returned from write(): " + str(wrtn))

    g_rx_buf = []
    time_before = time.time()
    time_after = time.time()
    while time_after - time_before < timeout and len(g_rx_buf) < rx_bytes_need:  # Waiting for response
        bytes_can_recv = ser.in_waiting       #Old method deprecated
        if bytes_can_recv != 0:
            g_rx_buf += ser.read(bytes_can_recv)
        time_after = time.time()

    if len(g_rx_buf) != rx_bytes_need:
        print("RET 1")
        print("Length of g_rx_buf: " + str(len(g_rx_buf)))
        print(g_rx_buf)
        return ACK_TIMEOUT
    if g_rx_buf[0] != CMD_HEAD:
        print(g_rx_buf[0])
        print("RET 2")
        return ACK_FAIL
    if g_rx_buf[rx_bytes_need - 1] != CMD_TAIL:
        print("RET 3")
        return ACK_FAIL
    if g_rx_buf[1] != tx_buf[1]:
        print(g_rx_buf[1])
        print(tx_buf[1])
        print("RET 4")
        return ACK_FAIL                     #STOPPED HERE#################################

    CheckSum = 0
    for index, byte in enumerate(g_rx_buf):
        if index == 0:
            continue
        if index == 6:
            if CheckSum != byte:
                print("RET 5")
                return ACK_FAIL
        CheckSum ^= byte
    print("RET 6")
    return ACK_SUCCESS

# ***************************************************************************
# @brief    Get Compare Level
# ***************************************************************************/
def GetCompareLevel():
    global g_rx_buf
    command_buf = [CMD_SET_OR_QUERY_COMPARISON_LEVEL, 0, 0, 1, 0]
    r = TxAndRxCmd(command_buf, 8, 0.1)
    print(g_rx_buf)
    print("*******************************************")
    if r == ACK_TIMEOUT:
        return ACK_TIMEOUT
    if r == ACK_SUCCESS and g_rx_buf[4] == ACK_SUCCESS:
        return g_rx_buf[3]
    else:
        return 0xFF

def SetCompareLevel(level):
    global g_rx_buf
    command_buf = [CMD_SET_OR_QUERY_COMPARISON_LEVEL, 0, level, 0, 0]
    r = TxAndRxCmd(command_buf, 8, 0.1)

    if r == ACK_TIMEOUT:
        return ACK_TIMEOUT
    if r == ACK_SUCCESS and g_rx_buf[4] == ACK_SUCCESS:
        return g_rx_buf[3]
    else:
        return 0xFF


def GetUserCount():
    global g_rx_buf
    command_buf = [CMD_USER_COUNT, 0, 0, 0, 0]
    r = TxAndRxCmd(command_buf, 8, 0.1)
    if r == ACK_TIMEOUT:
        return ACK_TIMEOUT
    if r == ACK_SUCCESS and g_rx_buf[4] == ACK_SUCCESS:
        return g_rx_buf[3]
    else:
        return 0xFF

# ***************************************************************************
# @brief   Get the time that fingerprint collection wait timeout
# ***************************************************************************/
def GetTimeOut():
    global g_rx_buf
    command_buf = [CMD_TIMEOUT, 0, 0, 1, 0]
    r = TxAndRxCmd(command_buf, 8, 0.1)
    if r == ACK_TIMEOUT:
        return ACK_TIMEOUT
    if r == ACK_SUCCESS and g_rx_buf[4] == ACK_SUCCESS:
        return g_rx_buf[3]
    else:
        return 0xFF

# ***************************************************************************
# @brief    Register fingerprint
# ***************************************************************************/
def AddUser():
    global g_rx_buf
    r = GetUserCount()
    if r >= USER_MAX_CNT:
        return ACK_FULL
    count = 0
    return_var = ""

    while r != ACK_SUCCESS and g_rx_buf[4] != ACK_SUCCESS or count < 5:
        command_buf = [CMD_ADD_1, 0, r + 1, 3, 0]
        r = TxAndRxCmd(command_buf, 8, 6)
        print(g_rx_buf)
        print("****************************")
        if r == ACK_TIMEOUT:
            return_var = ACK_TIMEOUT
        if r == ACK_SUCCESS and g_rx_buf[4] == ACK_SUCCESS:
            command_buf[0] = CMD_ADD_3
            r = TxAndRxCmd(command_buf, 8, 6)
            latest_scanned_id = g_rx_buf[3]
            nvar = r+1
            publish(myChannel, {"finger_scanner_new": GetUserCount()})
            print(g_rx_buf)
            Analysis_PC_Command("CMD5")
            print("Change to cmd5")
            if r == ACK_TIMEOUT:
                return_var = ACK_TIMEOUT
            if r == ACK_SUCCESS and g_rx_buf[4] == ACK_SUCCESS:
                return_var = ACK_SUCCESS
            else:
                return_var = ACK_FAIL
        else:
            return_var = ACK_FAIL
        count += 1

    return return_var


# ***************************************************************************
# @brief    Clear fingerprints
# ***************************************************************************/
def ClearAllUser():
    global g_rx_buf
    command_buf = [CMD_DEL_ALL, 0, 0, 0, 0]
    r = TxAndRxCmd(command_buf, 8, 5)
    if r == ACK_TIMEOUT:
        return ACK_TIMEOUT
    if r == ACK_SUCCESS and g_rx_buf[4] == ACK_SUCCESS:
        return ACK_SUCCESS
    else:
        return ACK_FAIL


# ***************************************************************************
# @brief    Check if user ID is between 1 and 3
# ***************************************************************************/
def IsMasterUser(user_id):
    if user_id == 1 or user_id == 2 or user_id == 3:
        return TRUE
    else:
        return FALSE

# ***************************************************************************
# @brief    Fingerprint matching
# ***************************************************************************/
def VerifyUser():
    global g_rx_buf
    global latest_scanned_id
    command_buf = [CMD_MATCH, 0, 0, 0, 0]
    r = TxAndRxCmd(command_buf, 8, 5)
    print(g_rx_buf)
    print("****************************")
    if r == ACK_TIMEOUT:
        return ACK_TIMEOUT
    if r == ACK_SUCCESS and IsMasterUser(g_rx_buf[4]) == TRUE:
        latest_scanned_id = g_rx_buf[3]
        publish(myChannel, {"finger_scanner": latest_scanned_id})
        time.sleep(4)
        return ACK_SUCCESS
    elif g_rx_buf[4] == ACK_NO_USER:
        return ACK_NO_USER
    elif g_rx_buf[4] == ACK_TIMEOUT:
        return ACK_TIMEOUT
    else:
        return ACK_GO_OUT  # The center of the fingerprint is out of alignment with sensor


# ***************************************************************************
# @brief    Analysis the command from PC terminal
# ***************************************************************************/
def Analysis_PC_Command(command):
    global Finger_SleepFlag

    if command == "CMD1" and Finger_SleepFlag != 1:
        print("Number of fingerprints already available:  %d" % GetUserCount())
    elif command == "CMD2" and Finger_SleepFlag != 1:
        print("Add fingerprint  (Put your finger on sensor until successfully/failed information returned) ")
        r = AddUser()
        if r == ACK_SUCCESS:
            print("Fingerprint added successfully !")
        elif r == ACK_FAIL:
            print(
                "Failed: Please try to place the center of the fingerprint flat to sensor, or this fingerprint already exists !")
        elif r == ACK_FULL:
            print("Failed: The fingerprint library is full !")
    elif command == "CMD3" and Finger_SleepFlag != 1:
        print("Waiting Finger......Please try to place the center of the fingerprint flat to sensor !")
        r = VerifyUser()
        if r == ACK_SUCCESS:
            print("Matching successful !")
        elif r == ACK_NO_USER:
            print("Failed: This fingerprint was not found in the library !")
        elif r == ACK_TIMEOUT:
            print("Failed: Time out !")
        elif r == ACK_GO_OUT:
            print("Failed: Please try to place the center of the fingerprint flat to sensor !")
    elif command == "CMD4" and Finger_SleepFlag != 1:
        ClearAllUser()
        print("All fingerprints have been cleared !")
    elif command == "CMD5" and Finger_SleepFlag != 1:
        GPIO.output(Finger_RST_Pin, GPIO.LOW)
        Finger_SleepFlag = 1
        print(
            "Module has entered sleep mode: you can use the finger Automatic wake-up function, in this mode, only CMD6 is valid, send CMD6 to pull up the RST pin of module, so that the module exits sleep !")
    elif command == "CMD6":
        Finger_SleepFlag = 0
        GPIO.output(Finger_RST_Pin, GPIO.HIGH)
        print("The module is awake. All commands are valid !")
    else:
        print("commands are invalid !")


# ***************************************************************************
# @brief   If you enter the sleep mode, then open the Automatic wake-up function of the finger,
#         begin to check if the finger is pressed, and then start the module and match
# ***************************************************************************/
def Auto_Verify_Finger():
    while True:
        if Finger_SleepFlag == 1:
            if GPIO.input(Finger_WAKE_Pin) == 1:  # If you press your finger
                time.sleep(0.01)
                if GPIO.input(Finger_WAKE_Pin) == 1:
                    GPIO.output(Finger_RST_Pin,
                                GPIO.HIGH)  # Pull up the RST to start the module and start matching the fingers
                    time.sleep(0.25)  # Wait for module to start
                    print("Waiting Finger......Please try to place the center of the fingerprint flat to sensor !")
                    r = VerifyUser()
                    if r == ACK_SUCCESS:
                        print("Matching successful !")
                        #Finger_SleepFlag = 1
                        #break
                    elif r == ACK_NO_USER:
                        print("Failed: This fingerprint was not found in the library !")
                    elif r == ACK_TIMEOUT:
                        print("Failed: Time out !")
                    elif r == ACK_GO_OUT:
                        print("Failed: Please try to place the center of the fingerprint flat to sensor !")

                    # After the matching action is completed, drag RST down to sleep
                    # and continue to wait for your fingers to press
                    GPIO.output(Finger_RST_Pin, GPIO.LOW)
        time.sleep(0.2)




def main():
    GPIO.output(Finger_RST_Pin, GPIO.LOW)
    time.sleep(0.25)
    GPIO.output(Finger_RST_Pin, GPIO.HIGH)
    time.sleep(0.25)  # Wait for module to start
    while SetCompareLevel(5) != 5:
        print(
            "***ERROR***: Please ensure that the module power supply is 3.3V or 5V, the serial line connection is correct.")
    time.sleep(1)
    print("OUTSIDE LOOP OF DEATH")
    print("***************************** WaveShare Capacitive Fingerprint Reader Test *****************************")
    print("Compare Level:  5    (can be set to 0-9, the bigger, the stricter)")
    print("Number of fingerprints already available:  %d " % GetUserCount())
    print(" send commands to operate the module: ")
    print("  CMD1 : Query the number of existing fingerprints")
    print(
        "  CMD2 : Register fingerprint  (Put your finger on the sensor until successfully/failed information returned) ")
    print("  CMD3 : Fingerprint matching  (Send the command, put your finger on sensor) ")
    print("  CMD4 : Clear fingerprints ")
    print(
        "  CMD5 : Switch to sleep mode, you can use the finger Automatic wake-up function (In this state, only CMD6 is valid. When a finger is placed on the sensor,the module is awakened and the finger is matched, without sending commands to match each time. The CMD6 can be used to wake up) ")
    print("  CMD6 : Wake up and make all commands valid ")
    print("***************************** WaveShare Capacitive Fingerprint Reader Test ***************************** ")

    t = threading.Thread(target=Auto_Verify_Finger)
    t.daemon = True
    t.start()

    global latest_scanned_id





    # while True:
    #     print("Latest Scanned ID: ", latest_scanned_id)
    #     str = input("Please input command (CMD1-CMD6):")
    #     Analysis_PC_Command(str)
    Analysis_PC_Command("CMD5")
    #Analysis_PC_Command("CMD3")


class SubscribeHandler(SubscribeCallback):
    def message(self, pubnub, message):
        print("Message payload: %s" % message.message)
        print("Message publisher: %s" % message.publisher)


        if message.publisher == "serverJS":
            print(message.message['description'])
        if message.message['title'] == "Command":
            Analysis_PC_Command("CMD6")
            time.sleep(5)
            Analysis_PC_Command(message.message['description'])

        #msg = message.message

        Analysis_PC_Command("CMD5")





        #key = list(msg.keys())
        #if key[0] == "Account":
            #print("Account matched")
            ##start facial recognition






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


if __name__ == '__main__':
    try:
        main()
        # pubnub.add_listener(main())
        pubnub.add_listener(SubscribeHandler())
        pubnub.subscribe().channels(myChannel).execute()

    except KeyboardInterrupt:
        if ser != None:
            ser.close()
        GPIO.cleanup()
        print("\n\n Test finished ! \n")
        sys.exit()
