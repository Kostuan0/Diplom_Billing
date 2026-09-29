from flask import Flask, render_template, session, request, redirect, url_for
import pymysql.connections
from params_win_base import *

try:
    con = pymysql.connect(
        host=hostname,
        port=3306,
        user=user,
        password=password,
        database=db_name,
        cursorclass=pymysql.cursors.DictCursor
    )
    print("connect")
except Exception as ex:
    print("no connect")
    print(ex)

cur = con.cursor()
app = Flask(__name__)
app.secret_key = "kozko"


@app.route('/')
def start_page():
    return render_template("index.html")


@app.route('/user_info')
def user_info():
    cur = con.cursor()
    username = session['username']
    cur.execute(f"SELECT * FROM users u "
                f"JOIN tariff t ON u.TARIFF_NAME=t.TARIFF_NAME "
                f"WHERE u.USER_LOGIN='{username}'")
    record = cur.fetchone()
    cur.close()
    print("RESULT--------->", record)
    return render_template("user_info.html", username=session['username'], record=record)


@app.route('/login', methods=['GET', 'POST'])
def login():
    cur = con.cursor()
    msg = ''
    if request.method == 'POST':
        username = request.form['username']
        user_password = request.form['password']
        cur.execute('SELECT * FROM users WHERE USER_LOGIN=%s AND USER_PASSWORD=%s', (username, user_password))
        record = cur.fetchone()
        cur.close()
        print(record)
        if record:
            session['loggedin'] = True
            session['username'] = record['USER_LOGIN']
            return redirect(url_for('user_info'))
        else:
            msg = 'Неккоректный логин или пароль'
    return render_template('index.html', msg=msg)


@app.route('/tariff_info')
def tariff_info():
    username = session['username']
    return render_template("tariff_info.html", username=session['username'])


@app.route('/user_operations')
def user_operations():
    cur = con.cursor()
    username = session['username']
    cur.execute(f"SELECT * FROM operations "
                f"WHERE USER_LOGIN = '{username}'")
    data_operations = cur.fetchall()
    cur.close()
    print("DATA--->", data_operations)
    return render_template("user_operations.html", username=session['username'], data=data_operations)


@app.route('/user_control')
def user_control():
    username = session['username']
    return render_template("user_control.html", username=session['username'])


@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('username', None)
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)