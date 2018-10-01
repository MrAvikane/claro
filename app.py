from flask import Flask, render_template, redirect, url_for, request
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
    cur.execute("SELECT db_name FROM databaseNames")
    db_list = cur.fetchall()
    db_list = [i for sub in db_list for i in sub]

    cur.execute("SELECT testdata FROM testdata1")
    list1 = cur.fetchall()
    list1 = [i for sub in list1 for i in sub]

    cur.execute("SELECT Environment_Name FROM testdata2")
    list2 = cur.fetchall()
    list2 = [i for sub in list2 for i in sub]

    cur.execute("SELECT testdata FROM testdata3")
    list3 = cur.fetchall()
    list3 = [i for sub in list3 for i in sub]

    return render_template('home.html',db_list=db_list,list1=list1,list2=list2, list3=list3)


@app.route('/', methods=['GET', 'POST'])
def index():
    user = User()
    if request.method == 'POST':
        form_data_1 = request.form['id']
        form_data_2 = request.form['pass']
        valid = cur.execute("SELECT * FROM users WHERE UserId='" + form_data_1 + "' AND Password='" + form_data_2 + "'")
        if valid:
            user.id = form_data_1
            user.passwd = form_data_2
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            return "INCORRECT CREDENTIALS"

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
