import base64
import os
import sys
from time import sleep
import socket
from PIL import Image

from dateutil.utils import today
from flask import Flask, redirect, render_template, request, session
from flask_session import Session
from flask_mysqldb import MySQL
from werkzeug.utils import secure_filename

import datetime
from pubnub.callbacks import SubscribeCallback
from pubnub.enums import PNStatusCategory, PNOperationType
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


app = Flask(__name__)
app.config['SECRET_KEY'] = 'super_secret_key'
app.config["SESSION_FILE_DIR"] = 'var/www/FlaskApp/FlaskApp/FlaskSession'

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.secret_key = "superSecret"

app.config['MYSQL_HOST'] = os.getenv("MYSQL_HOST")
app.config['MYSQL_USER'] = os.getenv("MYSQL_USER")
# app.config['MYSQL_PASSWORD'] = 'Password1#'
app.config['MYSQL_PASSWORD'] = os.getenv("MYSQL_PASSWORD")
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB')

# app.config['UPLOAD_FOLDER'] = 'var/www/FlaskApp/FlaskApp/static/images/'
app.config['UPLOAD_FOLDER'] = 'static/images/'
app.config['ALLOWED_EXTENSIONS'] = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

# PUBNUB
myChannel = "dmn-channel"
sensorList = ["finger_scanner, finger_scanner_new"]
data = {}

pnconfig = PNConfiguration()

pnconfig.subscribe_key = os.getenv("SUBSCRIBE_KEY")
pnconfig.publish_key = os.getenv("PUBLISH_KEY")
#pnconfig.uuid = 'webserver'
pnconfig.uuid = 'exterior-pi'

pubnub = PubNub(pnconfig)

#pubnub.subscribe() \
    #.channels(myChannel) \
    #.execute()

# def publish_callback(result, status):
#   if status.isError:
#     print(status.statusCode)
#   else:
#     print(result.timetoken)
#
# pubnub.publish()\
#   .channel(myChannel) \
#   .message({"text": "Hello World!"})\
#   .pn_async(publish_callback)

# mysql app
mysql = MySQL(app)
# flask session
Session(app)


def publish(custom_channel, msg):
    pubnub.publish().channel(custom_channel).message(msg).pn_async(my_publish_callback)


def my_publish_callback(envelope, status):
    # Check whether request successfully completed or not
    if not status.is_error():
        pass  # Message successfully published to specified channel.
    else:
        print("not published")
        print(status)
        print(status.is_error())
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
            pubnub.publish().channel(myChannel).message({"Connection": "Connected to PubNub"}).pn_async(
                my_publish_callback)
        elif status.category == PNStatusCategory.PNReconnectedCategory:
            pass
            # Happens as part of our regular operation. This event happens when
            # radio / connectivity is lost, then regained.
        elif status.category == PNStatusCategory.PNDecryptionErrorCategory:
            pass
            # Handle message decryption error. Probably client configured to
            # encrypt messages and on live data feed it received plain text.

    def message(self, pubnub, message):
        print("Message payload: %s" % message.message)
        print("Message publisher: %s" % message.publisher)
        msg = message.message

        with app.app_context():
            key = list(msg.keys())
            if key[0] == "finger_scanner":
                cur = mysql.connection.cursor()
                fingerID = str(message.message['finger_scanner'])
                print("FINGERID : ",fingerID)
                cur.execute(''' SELECT employee_id, employee_firstname, employee_surname FROM employee_table where fingerprint_id = {0}'''.format(fingerID))
                account = cur.fetchone()
                print(account[0])
                currentDay = today()
                currentTime = datetime.now().time()
                print(message.message['finger_scanner'])
                cur.execute(''' INSERT INTO employee_access_table VALUES(null,%s,%s,%s)''',
                            (currentDay, currentTime, account[0]))
                mysql.connection.commit()
                cur.close()

                #print("WE HERE ")
                #print(account[0])
                #print(account[1])
                #print(account[2])
                #print(account[3])
                #print(account[4])

                # receivedImg = open('receivedImg.jpg','wb')
                # receivedImg.write(account[4])
                # receivedImg.close()

                # base64_bytes = base64.b64encode(account[4])
                # base64_string = base64_bytes.decode("ascii")
                # print(base64_string)

                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                current_ip = s.getsockname()[0]
                s.close()

                accDetails = {"id": account[0], "firstName": account[1], "secondName": account[2]}
                print(accDetails)
                publish(myChannel, {"Account": accDetails})
                #sleep(3)


                # client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                # client.connect((current_ip, 1002))
                #
                # file = open('receivedImg.jpg', 'rb')
                # image_data = file.read(2048)
                #
                # while image_data:
                #     client.send(image_data)
                #     image_data = file.read(2048)
                #
                # file.close()
                # client.close()


                #     print("Opened fine")
                #     envelope = pubnub.send_file().channel(myChannel).file_name("test.jpg").message({"test_message": "test"}).should_store(True).file_object(fd).cipher_key("secret").sync()



            elif key[0] == "finger_scanner_new":



                print("new finger Scanned")
            else:
                print("Neither scan nor match")


pubnub.add_listener(MySubscribeCallback())


@app.route("/")
def index():
    if not session.get("email"):
        return redirect("/login")
    cursor = mysql.connection.cursor()
    cursor.execute(''' SELECT * FROM employee_table''')
    employees = cursor.fetchall()

    cursor.execute(''' SELECT DISTINCT ac.access_id, emp.employee_firstname, ac.employee_access_date, ac.employee_access_time FROM employee_access_table ac, employee_table emp WHERE ac.employee_id = emp.employee_id;
''')

    log = cursor.fetchall()
    cursor.close()

    encoded = []
    for row in employees:
        write_file(row[4], app.config['UPLOAD_FOLDER'] + row[5])
        # image = row[5]
        # encoded.append(base64.b64encode(image))

    return render_template("index.html", employees=employees, log=log)


@app.route("/login", methods=["GET", "POST"])
def login():
    msg = ''
    if request.method == 'GET':
        return render_template("login.html")
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        name = request.form.get("email")
        session["email"] = name
        password = request.form['password']
        cursor = mysql.connection.cursor()
        cursor.execute('''SELECT * FROM admin WHERE adminEmail = %s AND adminPassword = %s''', (name, password,))

        account = cursor.fetchone()
        cursor.close()

        if account:
            session["name"] = name
            return redirect("/")
            # # Create session data, we can access this data in other routes
            # session['loggedin'] = True
            # session['username'] = account['username']
            # # Redirect to home page
            # return 'Logged in successfully!'
        # else:
        #     # Account doesnt exist or username/password incorrect
        #     msg = 'Incorrect username/password!'

        return redirect("/login")

    return render_template('index.html', msg=msg)


@app.route("/logout")
def logout():
    session["name"] = None
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == 'POST':
        name = request.form.get("email")
        session["email"] = name
        password = request.form['password']
        cursor = mysql.connection.cursor()
        cursor.execute(''' INSERT INTO admin VALUES(null,%s,%s)''', (name, password))
        mysql.connection.commit()
        cursor.close()
        return redirect("/login")
    return render_template("registerAdmin.html")


@app.route("/deleteEmployee", methods=["GET", "POST"])
def deleteEmployee():
    if request.method == 'POST':
        id = request.form.get("employee_id")
        cursor = mysql.connection.cursor()
        cursor.execute('''DELETE FROM employee_access_table WHERE employee_id = %s''', [id])
        cursor.execute(''' DELETE FROM employee_table WHERE employee_id = %s''', [id])
        mysql.connection.commit()
        cursor.close()
        return redirect("/")
    return render_template("index.html")


@app.route("/registerEmployee", methods=["GET", "POST"])
def registerEmployee():
    if request.method == 'POST':
        firstname = request.form.get("firstname")
        surname = request.form.get("surname")
        email = request.form.get("email")
        finger = request.form.get("finger")
        face = request.files.get("face")
        if not face:
            return 'No Image Uploaded', 400
        else:
            filename = secure_filename(face.filename)
            face.save(app.config['UPLOAD_FOLDER'] + filename)

        cursor = mysql.connection.cursor()
        empPicture = convertToBinaryData(app.config['UPLOAD_FOLDER'] + face.filename)
        img_filename = face.filename
        cursor.execute(''' INSERT INTO employee_table VALUES(null,%s,%s,%s,%s,%s,%s)''',
                       (firstname, surname, email, empPicture, img_filename, finger))
        mysql.connection.commit()
        cursor.close()
        return redirect("/")
    return render_template("index.html")

# @app.route("/viewEditEmployee/<int:employee_id>", methods=["GET", "POST", "PUT"])
# def viewEditEmployee(employee_id):
#     if request.method == 'POST':
#         emp_id = employee_id
#         cursor = mysql.connection.cursor()
#         cursor.execute(''' SELECT * FROM employee_table WHERE employee_id = %s''', (emp_id,))
#         employee = cursor.fetchone()
#         cursor.close()
#
#
#
#     return render_template("editEmployees.html", employee=employee)


@app.route("/viewEmployee/<int:employee_id>")
def viewOneEmployee(employee_id):
    emp_id = employee_id
    cursor = mysql.connection.cursor()
    cursor.execute(''' SELECT * FROM employee_table WHERE employee_id = %s''', (emp_id,))
    employee = cursor.fetchone()
    cursor.close()
    # encoded=[]

    return render_template("viewOneEmployee.html", employee=employee)


@app.route("/addEmployees")
def addEmployees():
    return render_template("addEmployees.html")


def convertToBinaryData(filename):
    # Convert digital data to binary format
    with open(filename, 'rb') as file:
        binaryData = file.read()
    return binaryData


def write_file(data, filename):
    # Convert binary data to proper format and write it on Hard Disk
    with open(filename, 'wb') as file:
        file.write(data)


@app.route("/editEmployeeData/<int:employee_id>", methods=["GET", "POST", "PUT"])
def editEmployeeData(employee_id):
    if request.method == 'POST':
        c = mysql.connection.cursor()
        emp_id = request.form.get("employee_id")
        firstname = request.form.get("firstname")
        secondname = request.form.get("surname")
        email = request.form.get("email")
        face = request.form.get("face")
        finger = request.form.get("finger")

        print(emp_id)
        c.execute(
            ''' UPDATE employee_table set employee_id = %s, employee_firstname  = %s, employee_surname = %s, employee_email =%s, face_test =%s, fingerprint_id =%s WHERE employee_id = %s''',
            (emp_id, firstname, secondname, email, face, finger, emp_id))
        print(firstname)
        mysql.connection.commit()
        c.close()


        return redirect("/")


@app.route("/viewEditEmployee/<int:employee_id>", methods=["GET", "POST", "PUT"])
def viewEditEmployee(employee_id):
    if request.method == 'POST':
        emp_id = employee_id
        cursor = mysql.connection.cursor()
        cursor.execute(''' SELECT * FROM employee_table WHERE employee_id = %s''', (emp_id,))
        employee = cursor.fetchone()
        cursor.close()

    return render_template("editEmployees.html", employee=employee)


if __name__ == '__main__':
    pubnub.subscribe().channels(myChannel).execute()
    app.run(port=5000)