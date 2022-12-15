import os
import socket
import time

from dateutil.utils import today
from flask import Flask, redirect, render_template, request, session
from flask_session import Session
from flask_mysqldb import MySQL
from werkzeug.utils import secure_filename
import bcrypt

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

app.config['MYSQL_PASSWORD'] = os.getenv("MYSQL_PASSWORD")
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB')

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
                if account:
                    print(account[0])
                    currentDay = today()
                    currentTime = datetime.now().time()
                    print(message.message['finger_scanner'])
                    cur.execute(''' INSERT INTO employee_access_table VALUES(null,%s,%s,%s)''',
                            (currentDay, currentTime, account[0]))




                    accDetails = {"id": account[0], "firstName": account[1], "secondName": account[2]}
                    print(accDetails)
                    publish(myChannel, {"Account": accDetails})
                mysql.connection.commit()
                cur.close()
            elif key[0] == "finger_scanner_new":
                print("new finger Scanned")
                time.sleep(2)
                publish(myChannel, {'title': 'Command', 'description': 'CMD5'})
            elif key[0] == "finger_prints_removed":
                print("fingerprints removed")
                time.sleep(3)
                publish(myChannel, {'title': 'Command', 'description': 'CMD5'})
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
        write_file(row[4].to_bytes(2, 'big'), app.config['UPLOAD_FOLDER'] + str(row[5]))

    return render_template("index.html", employees=employees, log=log)


@app.route("/login", methods=["GET", "POST"])
def login():
    msg = ''
    if request.method == 'GET':
        return render_template("login.html")
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        name = request.form.get("email")
        session["email"] = name
        passwordAttempt = request.form.get('password')
        cursor = mysql.connection.cursor()
        cursor.execute('''SELECT * FROM admin WHERE adminEmail = %s''', (name,))
        account = cursor.fetchone()
        accPassword = account[2]

        # Taking user entered password
        userPassword = passwordAttempt

        # encoding user password
        userBytes = userPassword.encode('ascii')

        # checking password
        result = bcrypt.checkpw(userBytes, accPassword.encode('ascii'))

        print(result)

        account = cursor.fetchone()
        cursor.close()

        if result:
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
        password = request.form.get('password')

        # Calculating a hash
        # converting password to array of bytes
        bytes = password.encode('ascii')

        # generating the salt
        salt = bcrypt.gensalt()

        # Hashing the password
        hash = bcrypt.hashpw(bytes, salt)

        cursor = mysql.connection.cursor()
        #cursor.execute(''' INSERT INTO admin VALUES(null,%s,%s)''', (name, password))
        cursor.execute(''' INSERT INTO admin VALUES(null,%s,%s)''', (name, hash))
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

        cursor.execute('''INSERT INTO face_table VALUES(NULL,%s,%s)''', (empPicture, img_filename))

        cursor.execute('''SELECT face_id FROM face_table WHERE img_filename =%s''', [img_filename])
        account = cursor.fetchone()
        print(account[0])

        cursor.execute('''INSERT INTO employee_table VALUES(null,%s,%s,%s,%s,%s)''',
                       (firstname, surname, email, account[0], finger))

        mysql.connection.commit()
        cursor.close()
        return redirect("/")
    return render_template("index.html")


@app.route("/viewEmployee/<int:employee_id>")
def viewOneEmployee(employee_id):
    emp_id = employee_id
    cursor = mysql.connection.cursor()

    cursor.execute(''' SELECT DISTINCT emp.employee_id,emp.employee_firstname, emp.employee_surname, emp.employee_email, 
                            fc.face_test, fc.img_filename FROM employee_table emp, 
                            face_table fc WHERE emp.face_id = fc.face_id 
                            AND emp.employee_id =%s''', (emp_id,))

    employee = cursor.fetchone()
    cursor.close()

    return render_template("viewOneEmployee.html", employee=employee)


@app.route("/addEmployees")
def addEmployees():
    return render_template("addEmployees.html")


def convertToBinaryData(filename):
    with open(filename, 'rb') as file:
        binaryData = file.read()
    return binaryData


def write_file(data, filename):
    with open(filename, 'wb') as file:
        file.write(data)


@app.route("/editEmployeeData/<int:employee_id>", methods=["GET", "POST", "PUT"])
def editEmployeeData(employee_id):
    if request.method == 'POST':
        c = mysql.connection.cursor()
        emp_id = request.form.get("employee_id")
        fc_id = request.form.get("face_id")
        firstname = request.form.get("firstname")
        secondname = request.form.get("surname")
        email = request.form.get("email")
        finger = request.form.get("finger")

        face = request.files.get("face")

        print(face)
        if not face:
            cursor = mysql.connection.cursor()

            print(emp_id)

            c.execute('''SELECT face_id FROM face_table WHERE face_id =%s''', [fc_id])
            account = c.fetchone()
            print(account[0])

            c.execute(
                ''' UPDATE employee_table set employee_id = %s, employee_firstname  = %s, employee_surname = %s, employee_email =%s, face_id =%s, fingerprint_id =%s WHERE employee_id = %s''',
                (emp_id, firstname, secondname, email, fc_id, finger, emp_id))
            print(firstname)
            mysql.connection.commit()
            c.close()

        else:

            filename = secure_filename(face.filename)
            face.save(app.config['UPLOAD_FOLDER'] + filename)

            cursor = mysql.connection.cursor()
            empPicture = convertToBinaryData(app.config['UPLOAD_FOLDER'] + face.filename)
            img_filename = face.filename
            cursor.execute('''UPDATE face_table SET face_id = %s, face_test =%s, img_filename = %s WHERE face_id =%s''',
                           (fc_id, empPicture, img_filename, fc_id))

            print(emp_id)

            c.execute('''SELECT face_id FROM face_table WHERE face_id =%s''', [fc_id])
            account = c.fetchone()
            print(account[0])

            c.execute(
                ''' UPDATE employee_table set employee_id = %s, employee_firstname  = %s, employee_surname = %s, employee_email =%s, face_id =%s, fingerprint_id =%s WHERE employee_id = %s''',
                (emp_id, firstname, secondname, email, fc_id, finger, emp_id))
            print(firstname)
            mysql.connection.commit()
            c.close()


        return redirect("/")


@app.route("/viewEditEmployee/<int:employee_id>", methods=["GET", "POST", "PUT"])
def viewEditEmployee(employee_id):
    if request.method == 'POST':
        emp_id = employee_id
        cursor = mysql.connection.cursor()
        cursor.execute(''' SELECT DISTINCT emp.employee_id,emp.employee_firstname, emp.employee_surname, emp.employee_email, 
                                      fc.face_test, fc.img_filename, emp.fingerprint_id, fc.face_id FROM employee_table emp, 
                                       face_table fc WHERE emp.face_id = fc.face_id 
                                       AND emp.employee_id =%s''', (emp_id,))

        employee = cursor.fetchone()
        cursor.close()

    return render_template("editEmployees.html", employee=employee)


if __name__ == '__main__':
    pubnub.subscribe().channels(myChannel).execute()
    app.run(port=5000)