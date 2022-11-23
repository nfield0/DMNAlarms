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
from flask_mysqldb import MySQL
from datetime import datetime


app = Flask(__name__)
app.config['SECRET_KEY'] = 'super_secret_key'
app.config["SESSION_FILE_DIR"] = 'var/www/FlaskApp/FlaskApp/FlaskSession'

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.secret_key = "superSecret"

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
#app.config['MYSQL_PASSWORD'] = 'Password1#'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'dmn_alarms'

#app.config['UPLOAD_FOLDER'] = 'var/www/FlaskApp/FlaskApp/static/images/'
app.config['UPLOAD_FOLDER'] = 'static/images/'
app.config['ALLOWED_EXTENSIONS'] = {'txt','pdf','png','jpg','jpeg','gif'}

#PUBNUB
myChannel = "dmn-channel"
sensorList = ["finger_scanner, finger_scanner_new"]
data = {}

pnconfig = PNConfiguration()

pnconfig.subscribe_key = 'sub-c-5efa4cb5-6f01-42ea-a6ac-98b3dccd764a'
pnconfig.publish_key = 'pub-c-6df66f48-e71d-41ea-a2a7-d696bda5a561'
pnconfig.uuid = 'exterior-pi'
pubnub = PubNub(pnconfig)

pubnub.subscribe()\
  .channels(myChannel)\
  .execute()



#mysql app
mysql = MySQL(app)
#flask session
Session(app)


class SubscribeHandler(SubscribeCallback):
    def message(self, pubnub, message):
        print("Message payload: %s" % message.message)
        print("Message publisher: %s" % message.publisher)

        with app.app_context():
            cur = mysql.connection.cursor()
            cur.execute(''' SELECT * FROM employee_table where employee_id == message.message['finger_scanner']''')
            account = cur.fetchone()
            currentDay = today()
            currentTime = datetime.now().time()
            print(message.message['finger_scanner'])
            cur.execute(''' INSERT INTO employee_access_table VALUES(null,%s,%s,%s)''', (currentDay,currentTime, 6))
            mysql.connection.commit()
            cur.close()


pubnub.add_listener(SubscribeHandler())
@app.route("/")
def index():
    if not session.get("email"):
        return redirect("/login")
    cursor = mysql.connection.cursor()
    cursor.execute(''' SELECT * FROM employee_table''')
    employees = cursor.fetchall()

    cursor.execute(''' SELECT ac.access_id, emp.employee_firstname, ac.employee_access_date, ac.employee_access_time
    FROM employee_access_table ac, employee_table emp
    INNER JOIN employee_table ON employee_table.employee_id = employee_table.employee_id''')

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
    msg=''
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

@app.route("/register", methods=["GET","POST"])
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

@app.route("/deleteEmployee", methods=["GET","POST"])
def deleteEmployee():
    if request.method == 'POST':
        id = request.form.get("employee_id")
        cursor = mysql.connection.cursor()
        cursor.execute('''DELETE FROM employee_access_table WHERE employee_id = %s''',[id])
        cursor.execute(''' DELETE FROM employee_table WHERE employee_id = %s''', [id])
        mysql.connection.commit()
        cursor.close()
        return redirect("/")
    return render_template("index.html")

@app.route("/registerEmployee", methods=["GET","POST"])
def registerEmployee():
    if request.method == 'POST':
        firstname = request.form.get("firstname")
        surname = request.form.get("surname")
        email = request.form.get("email")
        finger = 7

        face = request.files.get("face")
        if not face:
             return 'No Image Uploaded', 400
        else:
            filename = secure_filename(face.filename)
            face.save(app.config['UPLOAD_FOLDER'] + filename)

        cursor = mysql.connection.cursor()
        empPicture = convertToBinaryData(app.config['UPLOAD_FOLDER'] + face.filename)
        img_filename = face.filename
        cursor.execute(''' INSERT INTO employee_table VALUES(null,%s,%s,%s,%s,%s,%s)''', (firstname, surname, email, empPicture,img_filename,finger))
        mysql.connection.commit()
        cursor.close()
        return redirect("/")
    return render_template("index.html")

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
@app.route("/editEmployeeData/<int:employee_id>", methods=["GET","POST", "PUT"])
def editEmployeeData(employee_id):
    if request.method == 'POST':
        c = mysql.connection.cursor()
        emp_id = request.form.get("employee_id")
        firstname = request.form.get("firstname")
        secondname = request.form.get("surname")
        email = request.form.get("email")
        face = request.form.get("face")
        finger = 7

        print(emp_id)
        c.execute(''' UPDATE employee_table set employee_id = %s, employee_firstname  = %s, employee_surname = %s, employee_email =%s, face_test =%s WHERE employee_id = %s''',(emp_id, firstname, secondname, email,  face, emp_id))
        print(firstname)
        mysql.connection.commit()
        c.close()

        return redirect("/")
@app.route("/viewEditEmployee/<int:employee_id>", methods=["GET","POST", "PUT"])
def viewEditEmployee(employee_id):
    if request.method == 'POST':
        emp_id = employee_id
        cursor = mysql.connection.cursor()
        cursor.execute(''' SELECT * FROM employee_table WHERE employee_id = %s''', (emp_id,))
        employee = cursor.fetchone()
        cursor.close()

    return render_template("editEmployees.html", employee=employee)






if __name__ == '__main__':
    app.run(port = 5000)


