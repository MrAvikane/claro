import cx_Oracle
import pymysql

# working with dummy values
quantity = 2
selection = 'ICCID'

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
    = '0004850257')''')
    data = cur1.fetchall()
    data = [i for sub in data for i in sub]
    flag = 1
else:
    cur1.execute(''' SELECT MATV_SERIE FROM SISCAD_MATERIAL W WHERE W.MATV_NRO_PEDIDO in
    (SELECT x.pedv_nro_pedido from siscad_pedido x where x.pedv_punto_venta in ('0004850257') and x.pedv_estado = '02') 
    AND w.MATV_ESTADO = 'L'
    AND w.MATV_TIPO_MAT = '02' -- 01 CHIPS - 02 EQUIPOS
    AND w.matv_serie IN (select LTRIM(o.SERIC_CODSERIE, '0') FROM SSAPT_SERIE@DBL_MSSAP o where o.INTEV_CODINTERLOCUTOR 
    = '0004850257')''')
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
        cur3.execute("select p.*, rowid from MSSAP60.ssapt_detallepedido p where p.seric_codserie in ('" + x + "')")
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
            "select v.dvpr_serie,v.*,ROWID from sisact_detalle_venta_prepago v where v.dvpr_serie in('" + x + "')")
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
if len(usable) != 0:
    if flag == 1:
        print("IMEI numbers:")
    else:
        print("ICCID numbers:")
    print(usable)
else:
    print("nada")
