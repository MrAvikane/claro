from flask import Flask, render_template, redirect, url_for, request, session
import xlrd
import pymysql
from flask_bootstrap import Bootstrap
from flask_login import fresh_login_required , LoginManager, UserMixin, login_user, login_required, logout_user, fresh_login_required

app = Flask(__name__)
Bootstrap(app)
conn = pymysql.connect(host='localhost', user='root', passwd='root123', database='clarodb')
cur = conn.cursor()

app.config['SECRET_KEY'] = 'Thisissupposedtobesecret!'
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'index'

workbook = xlrd.open_workbook("employees.xlsx")
worksheet = workbook.sheet_by_index(0)
rows = worksheet.nrows

for x in range(rows):
    excel_data1 = str(worksheet.cell(x, 0).value)
    excel_data2 = str(worksheet.cell(x, 1).value)
    rv = cur.execute("SELECT * FROM users WHERE UserId='" + excel_data1 + "'")
    if rv == 0:
        cur.execute("INSERT INTO users(id,pass) VALUES('" + excel_data1 + "','" + excel_data2 + "')")
        conn.commit()


class User(UserMixin):
    id = 0
    passwd = 'secret'


@login_manager.user_loader
def load_user(user_id):
    user = User()
    user.id = user_id
    user.passwd = cur.execute("SELECT Password FROM users WHERE UserId='" + user_id + "'")
    return user


@app.route('/home')
@fresh_login_required
def dashboard():
    cur.execute("SELECT testdata FROM testdata1")
    list1 = cur.fetchall()
    list1 = [i for sub in list1 for i in sub]

    cur.execute("SELECT Environment_Name FROM testdata2")
    list2 = cur.fetchall()
    list2 = [i for sub in list2 for i in sub]

    return render_template('home.html', list1=list1, list2=list2)


@app.route('/', methods=['GET', 'POST'])
def index():
    user = User()
    if request.method == 'POST':
        form_data_1 = request.form['id']
        form_data_2 = request.form['pass']
        valid = cur.execute("SELECT PID FROM users WHERE UserId='"+form_data_1+"' AND Password='"+form_data_2 + "'")

        if valid:
            user.id = form_data_1
            user.passwd = form_data_2
            login_user(user)
            pid = cur.fetchall()
            pid = [str(i) for sub in pid for i in sub]
            session['pid'] = pid

            return redirect(url_for('report'))
        else:
            return "INCORRECT CREDENTIALS"

    return render_template('login.html')


@app.route('/report')
@fresh_login_required
def report():
    pid = session['pid']

    cur.execute("SELECT IMEI FROM in_use_imei WHERE PID='"+pid[0]+"'")
    imei_list = cur.fetchall()
    imei_list = [i for sub in imei_list for i in sub]

    cur.execute("SELECT ICCID FROM in_use_iccid WHERE PID='"+pid[0]+"'")
    iccid_list = cur.fetchall()
    iccid_list = [i for sub in iccid_list for i in sub]
    return render_template('report.html', name=pid, imei_list=imei_list, iccid_list=iccid_list)


@app.route('/config')
@login_required
def config():
    user = User()
    if request.method == 'POST':
        form_data_1 = request.form['id']
        form_data_2 = request.form['pass']
        valid = cur.execute(
            "SELECT PID FROM users WHERE UserId='" + form_data_1 + "' AND Password='" + form_data_2 + "'")

        if valid:
            return "USER ALREADY EXISTS"
        else:
            workbook = xlrd.open_workbook("employees.xlsx")
            worksheet = workbook.sheet_by_index(0)
            rows = worksheet.nrows

            for x in range(rows):
                excel_data1 = str(worksheet.cell(x, 0).value)
                excel_data2 = str(worksheet.cell(x, 1).value)
                cur.execute("INSERT INTO users(id,pass) VALUES('" + excel_data1 + "','" + excel_data2 + "')")
                conn.commit()

            return redirect("new user added")

    return render_template('config.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.pop('pid', None)
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
