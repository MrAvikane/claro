from flask import Flask, flash, render_template, redirect, url_for, request, session
import xlrd
import cx_Oracle
import pymysql
from flask_bootstrap import Bootstrap
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, fresh_login_required

app = Flask(__name__)
Bootstrap(app)
conn = pymysql.connect(host='localhost', user='root', passwd='root', database='clarodb')
cur = conn.cursor()
app.config['SECRET_KEY'] = 'Thisissupposedtobesecret!'
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'index'


@app.route('/display', methods=['GET', 'POST'])
@fresh_login_required
def display():
    pid = session['pid']
    cur.execute("SELECT UserId FROM users WHERE PID='" + pid[0] + "'")
    name = cur.fetchall()
    name = [i for sub in name for i in sub]

    if request.method == 'POST':
        selection = request.form['list1']
        quantity = int(request.form['quantity'])
        input1 = request.form['list2']

        # list to store clean numbers after checking
        usable = []

        # connection 1 for searching imei & iccid
        # query to select all ids and save in a python list. flag to check if selection is imei or iccid
        dsn_tns = cx_Oracle.makedsn("172.19.74.245", 1521, service_name="QATEST11G")
        conn1 = cx_Oracle.connect(user="SISCAD", password="Ej4klB6J", dsn=dsn_tns)
        cur1 = conn1.cursor()

        if selection == 'IMEI':
            cur1.execute(''' SELECT MATV_SERIE FROM SISCAD_MATERIAL W WHERE W.MATV_NRO_PEDIDO in
            (SELECT x.pedv_nro_pedido from siscad_pedido x where x.pedv_punto_venta in ('0004850257') and x.pedv_estado = '02') 
            AND w.MATV_ESTADO = 'L'
            AND w.MATV_TIPO_MAT = '01' -- 01 CHIPS - 02 EQUIPOS
            AND w.matv_serie IN (select LTRIM(o.SERIC_CODSERIE, '0') FROM SSAPT_SERIE@DBL_MSSAP o where o.INTEV_CODINTERLOCUTOR 
            = '0004850257') ''')
            data = cur1.fetchall()
            data = [i for sub in data for i in sub]
            flag = 1
        else:
            cur1.execute(''' SELECT MATV_SERIE FROM SISCAD_MATERIAL W WHERE W.MATV_NRO_PEDIDO in 
            (SELECT x.pedv_nro_pedido from siscad_pedido x where x.pedv_punto_venta in ('0004850257') and x.pedv_estado = '02')
             AND w.MATV_ESTADO = 'L' 
             AND w.MATV_TIPO_MAT = '02' -- 01 CHIPS - 02 EQUIPOS 
             AND w.matv_serie IN (select LTRIM(o.SERIC_CODSERIE, '0') FROM SSAPT_SERIE@DBL_MSSAP o where o.INTEV_CODINTERLOCUTOR 
             = '0004850257') ''')
            data = cur1.fetchall()
            data = [i for sub in data for i in sub]
            flag = 0

        # connection 2 to check if data already exists in local database
        conn2 = pymysql.connect(host='localhost', user='root', passwd='root', database='clarodb')
        cur2 = conn2.cursor()

        # connection 3 to check first set of errors
        dsn_tns = cx_Oracle.makedsn("172.17.26.104", 1521, service_name="MSINCDB")
        conn3 = cx_Oracle.connect(user="usrqa", password="Claro2014", dsn=dsn_tns)
        cur3 = conn3.cursor()

        # connection 4 to check second set of errors
        dsn_tns = cx_Oracle.makedsn("172.17.26.104", 1521, service_name="PVUDB")
        conn4 = cx_Oracle.connect(user="USRPVU", password="USRPVU", dsn=dsn_tns)
        cur4 = conn4.cursor()

        # running all query on each data in list till we find required amount of clean id
        for x in data:

            if len(usable) == quantity:
                break

            # while loop runs once per number and exits while loop if number is not clean
            while 1:

                # check if data present in local database
                if flag == 1:
                    cur2.execute("SELECT * FROM in_use_imei WHERE IMEI='" + x + "'")
                    row = cur2.fetchall()
                    if row:
                        break

                else:
                    cur2.execute("SELECT * FROM in_use_iccid WHERE ICCID='" + x + "'")
                    row = cur2.fetchall()
                    if row:
                        break

                # query for first set of errors
                cur3.execute("select x.*,rowid from MSSAP60.ssapt_serie x where x.seric_codserie in ('" + x + "')")
                r1 = cur3.fetchall()
                cur3.execute("select s.*, rowid from MSSAP60.ssapt_stockimei s where s.stckc_codserie in ('" + x + "')")
                r2 = cur3.fetchall()
                cur3.execute(
                    "select p.*, rowid from MSSAP60.ssapt_detallepedido p where p.seric_codserie in ('" + x + "')")
                r3 = cur3.fetchall()

                if len(r1) >= 1 or len(r2) >= 1 or len(r3) >= 1:
                    break

                # query for second set of errors
                cur4.execute(
                    "select pre.EQUIPO_SERIE,PRE.*,ROWID from sisact_venta_repo_pre pre where pre.EQUIPO_SERIE in('" + x + "')")
                r1 = cur4.fetchall()
                cur4.execute("select pre.iccid_serie_nuevo, PRE.*, ROWID from sisact_venta_repo_pre pre where "
                             "pre.iccid_serie_nuevo in ('" + x + "')")
                r2 = cur4.fetchall()
                cur4.execute(
                    "select v.dvpr_serie,v.*,ROWID from sisact_detalle_venta_prepago v where v.dvpr_serie in('" +
                    x + "') ")
                r3 = cur4.fetchall()
                cur4.execute("select v.dvev_serie, v.* from sisact_detalle_venta v where v.dvev_serie in ('" + x + "')")
                r4 = cur4.fetchall()

                if len(r1) >= 1 or len(r2) >= 1 or len(r3) >= 1 or len(r4) >= 1:
                    break

                # this will execute only if all the conditions are passed
                # storing usable data in list
                usable.append(x)
                break

        # print clean data
        if len(usable) == 0:
            return "no id found"
        else:
            session['selection'] = selection
            session['usable'] = usable
            return render_template('display.html', usable=usable, name=name, selection=selection)


@app.route('/allocate', methods=['GET', 'POST'])
@fresh_login_required
def allocate():
    pid = session['pid']
    cur.execute("SELECT UserId FROM users WHERE PID='" + pid[0] + "'")
    name = cur.fetchall()
    name = [i for sub in name for i in sub]

    selection = session['selection']
    usable = session['usable']
    c = 0
    if selection == 'IMEI':
        for x in usable:
            x = str(x)
            cur.execute("SELECT * FROM in_use_imei WHERE IMEI='" + x + "'")
            r = cur.fetchall()
            if r:
                c = c + 1
        if c == 0:
            for x in usable:
                x = str(x)
                cur.execute("INSERT INTO in_use_imei (IMEI,PID) VALUES('" + x + "','" + pid[0] + "')")
                conn.commit()
            return "{0} id allocated to {1}".format(selection, name[0])
        else:
            return "nada"
    else:
        for x in usable:
            x = str(x)
            cur.execute("SELECT * FROM in_use_iccid WHERE ICCID='" + x + "'")
            r = cur.fetchall()
            if r:
                c = c + 1
        if c == 0:
            for x in usable:
                x = str(x)
                cur.execute("INSERT INTO in_use_iccid (ICCID,PID) VALUES('" + x + "','" + pid[0] + "')")
                conn.commit()
            return "{0} id allocated to {1}".format(selection, name[0])
        else:
            return "nada{0}".format(c)


'''
workbook = xlrd.open_workbook("employees.xlsx")
worksheet = workbook.sheet_by_index(0)
rows = worksheet.nrows

for x in range(rows):
    excel_data1 = str(worksheet.cell(x, 0).value)
    excel_data2 = str(worksheet.cell(x, 1).value)
    rv = cur.execute("SELECT * FROM users WHERE UserId='" + excel_data1 + "'")
    if rv == 0:
        cur.execute("INSERT INTO users(UserID,Password) VALUES('" + excel_data1 + "','" + excel_data2 + "')")
        conn.commit()
'''


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
        valid = cur.execute(
            "SELECT PID FROM users WHERE UserId='" + form_data_1 + "' AND Password='" + form_data_2 + "'")

        if valid:
            user.id = form_data_1
            user.passwd = form_data_2
            login_user(user)
            pid = cur.fetchall()
            pid = [str(i) for sub in pid for i in sub]
            session['pid'] = pid

            return redirect(url_for('user_page'))
        else:
            return "INCORRECT CREDENTIALS"

    return render_template('login.html')


@app.route('/dashboard')
@fresh_login_required
def user_page():
    pid = session['pid']

    cur.execute("SELECT UserId FROM users WHERE PID='" + pid[0] + "'")
    name = cur.fetchall()
    name = [i for sub in name for i in sub]

    cur.execute("SELECT IMEI FROM in_use_imei WHERE PID='" + pid[0] + "'")
    imei_list = cur.fetchall()
    imei_list = [i for sub in imei_list for i in sub]

    cur.execute("SELECT ICCID FROM in_use_iccid WHERE PID='" + pid[0] + "'")
    iccid_list = cur.fetchall()
    iccid_list = [i for sub in iccid_list for i in sub]
    return render_template('dashboard.html', name=name, imei_list=imei_list, iccid_list=iccid_list)


@app.route('/report')
@fresh_login_required
def report():
    pid = session['pid']

    cur.execute("SELECT IMEI FROM in_use_imei WHERE PID='" + pid[0] + "'")
    imei_list = cur.fetchall()
    imei_list = [i for sub in imei_list for i in sub]

    cur.execute("SELECT ICCID FROM in_use_iccid WHERE PID='" + pid[0] + "'")
    iccid_list = cur.fetchall()
    iccid_list = [i for sub in iccid_list for i in sub]
    return render_template('report.html', name=pid, imei_list=imei_list, iccid_list=iccid_list)


@app.route('/config', methods=['GET', 'POST'])
@login_required
def config():
    if request.method == 'POST':
        form_data_1 = request.form['id']
        form_data_2 = request.form['pass']
        valid = cur.execute(
            "SELECT PID FROM users WHERE UserId='" + form_data_1 + "' AND Password='" + form_data_2 + "'")

        if valid:
            return "USER ALREADY EXISTS"
        else:
            cur.execute(
                "INSERT INTO users(UserId,Password) VALUES('" + form_data_1 + "','" + form_data_2 + "')")
            conn.commit()

            flash("new user added")

    return render_template('config.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.pop('pid', None)
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
