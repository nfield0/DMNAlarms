
from flask import Flask, redirect, render_template, request, session
from flask_session import Session
from flask_mysqldb import MySQL
from werkzeug.utils import secure_filename

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



mysql = MySQL(app)

Session(app)

@app.route("/")
def index():
    if not session.get("email"):
        return redirect("/login")
    cursor = mysql.connection.cursor()
    cursor.execute(''' SELECT * FROM employee_table''')
    employees = cursor.fetchall()

    cursor.execute(''' SELECT * FROM log''')
    employees = cursor.fetchall()
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
        finger = "finger"

        face = request.files.get("face")
        if not face:
             return 'No Image Uploaded', 400
        else:
            filename = secure_filename(face.filename)
            face.save(app.config['UPLOAD_FOLDER'] + filename)

        cursor = mysql.connection.cursor()
        empPicture = convertToBinaryData(app.config['UPLOAD_FOLDER'] + face.filename)
        img_filename = face.filename
        cursor.execute(''' INSERT INTO employee_table VALUES(null,%s,%s,%s,%s,%s)''', (firstname, surname, email, empPicture,img_filename))
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
        print("hreer bitch")
        c = mysql.connection.cursor()
        emp_id = request.form.get("employee_id")
        firstname = request.form.get("firstname")
        secondname = request.form.get("surname")
        email = request.form.get("email")
        face = request.form.get("face")

        print(emp_id)
        c.execute(''' UPDATE employee_table set employee_id = %s, employee_firstname  = %s, employee_surname = %s, employee_email =%s, face_test = %s WHERE employee_id = %s''',(emp_id, firstname, secondname, email,  face, emp_id))
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