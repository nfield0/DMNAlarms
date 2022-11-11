
from flask import Flask, redirect, render_template, request, session
from flask_session import Session
from flask_mysqldb import MySQL


app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'dmntest'

mysql = MySQL(app)

Session(app)

@app.route("/")
def index():
    if not session.get("name"):
        return redirect("/login")
    return render_template("index.html")


@app.route("/login", methods=["POST"])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        cursor = mysql.connection.cursor()
        cursor.execute(''' INSERT INTO admin VALUES(%s,%s)''', (email, password))
        mysql.connection.commit()
        cursor.close()
        return f"Done!!"

    return render_template("login.html")

@app.route("/logout")
def logout():
    session["name"] = None
    return redirect("/")


if __name__ == '__main__':
    app.run()


















# from flask import Flask, render_template, request, redirect
# import json
#
# app = Flask(__name__)
#
# alive = 0
# data = {}
#
# @app.route("/")
# def index():
#     return render_template("index.html")
#
# @app.route("/keep_alive")
# def keep_alive():
#     global alive, data
#     alive += 1
#     keep_alive_count = str(alive)
#     data['keep_alive'] = keep_alive_count
#     parsed_json = json.dumps(data)
#     print(parsed_json)
#     return str(parsed_json)
#
# app.run(port = 5000)