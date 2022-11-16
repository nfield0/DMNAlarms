
from flask import Flask, redirect, render_template, request, session
from flask_session import Session
from flask_mysqldb import MySQL


app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'dmn_alarms'

mysql = MySQL(app)

Session(app)

@app.route("/")
def index():
    if not session.get("email"):
        return redirect("/login")
    return render_template("index.html")


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

@app.route("/registerEmployee", methods=["GET","POST"])
def registerEmployee():
    if request.method == 'POST':
        firstname = request.form.get("firstname")
        surname = request.form.get("surname")
        email = request.form.get("email")
        face = request.form.get("face")
        finger = request.form.get("finger")

        cursor = mysql.connection.cursor()
        cursor.execute(''' INSERT INTO employee_table VALUES(null,%s,%s,%s,%s,%s)''', (firstname, surname, email, face, finger))
        mysql.connection.commit()
        cursor.close()
        return redirect("/")
    return render_template("index.html")

@app.route("/viewEmployee", methods=["GET","POST"])
def viewEmployee():

    if request.method == 'GET':
        cursor = mysql.connection.cursor()
        cursor.execute(''' SELECT * FROM employee_table''')
        mysql.connection.commit()
        cursor.close()

    return render_template("index")

if __name__ == '__main__':
    app.run(port = 5000)