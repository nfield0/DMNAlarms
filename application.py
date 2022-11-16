import os
import base64
from flask import Flask, redirect, render_template, request, session
from flask_session import Session
from flask_mysqldb import MySQL
from werkzeug.utils import secure_filename
from PIL import Image




app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'dmn_alarms'

app.config['UPLOAD_FOLDER'] = '/images'
app.config['ALLOWED_EXTENSIONS'] = {'txt','pdf','png','jpg','jpeg','gif'}

mysql = MySQL(app)

Session(app)


@app.route("/")
def index():
    if not session.get("email"):
        return redirect("/login")
    cursor = mysql.connection.cursor()
    cursor.execute(''' SELECT * FROM employee_table''')
    employees = cursor.fetchall()
    cursor.close()
    #encoded = []
    # for row in employees:
    #     image = row[5]
    #     encoded.append(base64.b64encode(image))
    # print(encoded[0])
    return render_template("index.html", employees=employees)



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
        cursor.execute(''' DELETE FROM employee_table WHERE employee_id = %s''', id)
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
        finger = request.form.get("finger")

        face = request.files.get("face")
        if not face:
             return 'No Image Uploaded', 400
        else:
            filename = secure_filename(face.filename)
            face.save("static/images/" + filename)

        cursor = mysql.connection.cursor()
        empPicture = convertToBinaryData("static/images/" + face.filename)
        img_filename = face.filename
        cursor.execute(''' INSERT INTO employee_table VALUES(null,%s,%s,%s,%s,%s,%s)''', (firstname, surname, email, finger, empPicture,img_filename))
        mysql.connection.commit()
        cursor.close()
        return redirect("/")
    return render_template("index.html")

@app.route("/viewEmployee", methods=["GET","POST"])
def viewEmployee():
    # if request.method == 'GET':
    # cursor = mysql.connection.cursor()
    # cursor.execute(''' SELECT * FROM employee_table''')
    # employees = cursor.fetchall()
    # cursor.close()
    # encoded=[]
    # for row in employees:
    #     image = row[5]
    #     encoded.append(base64.b64encode(image))
    # # print(employees)
    # print("hereeeeeeeeeee")
    # print(encoded)
    # print("hereeeeeeeeeee")

    return render_template("index.html", employees=employees,images=encoded)
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

@app.route("/editEmployee", methods=["GET","POST"])
def editEmployee():
    if request.method == 'POST':
        cursor = mysql.connection.cursor()
        emp_id = request.form.get("employee_id")
        print(emp_id)
        cursor.execute(''' SELECT * FROM employee_table WHERE employee_id = %s''', (emp_id,))


        employee = cursor.fetchone()
        cursor.close()
        return render_template("editEmployees.html", employee=employee)

    if request.method == 'POST':
        cursor = mysql.connection.cursor()
        emp_id = request.form("employee_id")
        firstname = request.form("firstname")
        secondname = request.form("surname")
        email = request.form("email")
        fingerprint = request.form("fingerprint")
        face = request.form("face")

        print(emp_id)
        cursor.execute(''' UPDATE employee_table set employee_firstname  = %s, employee_surname = %s, email =%s, fingerprint=%s, face = %s WHERE employee_id = %s ''',(emp_id, firstname, secondname, email, fingerprint, face))
        mysql.connection.commit()
        cursor.close()


        return render_template("index.html")

if __name__ == '__main__':
    app.run(port = 5000)