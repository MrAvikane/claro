import cx_Oracle

#First connection for imei or iccid

dsn_tns = cx_Oracle.makedsn('Host Name', 'Port Number', service_name='Service Name')
conn = cx_Oracle.connect(user=r'User Name', password='Personal Password', dsn=dsn_tns)
cur = conn.cursor()
if(selection1 == 'IMEI')
    cur.execute(''' SELECT w.*, w.rowid FROM SISCAD_MATERIAL W WHERE W.MATV_NRO_PEDIDO in
    (SELECT x.pedv_nro_pedido from siscad_pedido x where x.pedv_punto_venta in ('0004850257') and x.pedv_estado = '02') 
    AND w.MATV_ESTADO = 'L'
    AND w.MATV_TIPO_MAT = '01' -- 01 CHIPS - 02 EQUIPOS
    AND w.matv_serie IN (select LTRIM(o.SERIC_CODSERIE, '0') FROM SSAPT_SERIE@DBL_MSSAP o where o.INTEV_CODINTERLOCUTOR = '0004850257')
    ''')
    list = cur.fetchall()
    list = [i for sub in list for i in sub]
    flag = 1
else:
    cur.execute(''' SELECT w.*, w.rowid FROM SISCAD_MATERIAL W WHERE W.MATV_NRO_PEDIDO in
    (SELECT x.pedv_nro_pedido from siscad_pedido x where x.pedv_punto_venta in ('0004850257') and x.pedv_estado = '02') 
    AND w.MATV_ESTADO = 'L'
    AND w.MATV_TIPO_MAT = '02' -- 01 CHIPS - 02 EQUIPOS
    AND w.matv_serie IN (select LTRIM(o.SERIC_CODSERIE, '0') FROM SSAPT_SERIE@DBL_MSSAP o where o.INTEV_CODINTERLOCUTOR = '0004850257')
    ''')
    list = cur.fetchall()
    list = [i for sub in list for i in sub]
    flag = 0
#for row in c:
#   print (row[0], '-', row[1])
conn.close()

#checking with local db if number already  used

conn = pymysql.connect(host='localhost', user='root', passwd='root123', database='clarodb')
cur = conn.cursor()
index = 0
length = len(list)
if flag == 1:
    while index < length:
        cur.execute("SELECT * FROM IN_USE_IMEI WHERE IMEI_NO='"+list[index]+"'")
        row = cur.fetchall()
        if row > 0:
            list.pop(index)
            index = index-1
            length = len(list)
        index += 1

else:
    while index < length:
        cur.execute("SELECT * FROM IN_USE_ICCID WHERE ICCID='" + list[index] + "'")
        row = cur.fetchall()
        if row > 0:
            list.pop(index)
            index = index - 1
            length = len(list)
        index += 1

#checking if ID in use. First set of errors
dsn_tns = cx_Oracle.makedsn('Host Name', 'Port Number', service_name='Service Name')
conn = cx_Oracle.connect(user=r'User Name', password='Personal Password', dsn=dsn_tns)
cur = conn.cursor()
index = 0
length = len(list)
while index < length:
        cur.execute('''select x.*,rowid from MSSAP60.ssapt_serie x where x.seric_codserie in ("'''+list[index]+'''");''')
        r1 = cur.fetchall()
        cur.execute('''select s.*, rowid from MSSAP60.ssapt_stockimei s where s.stckc_codserie in ("'''+list[index]+'''");''')
        r2 = cur.fetchall()
        cur.execute('''select p.*, rowid from MSSAP60.ssapt_detallepedido p where p.seric_codserie in ("'''+list[index]+'''");''')
        r3 = cur.fetchall()
        if r1 > 0 || r2 > 0 || r3 > 0:
            list.pop(index)
            index = index-1
            length = len(list)
        index += 1
conn.close()

#checking if ID in use. Second set of errors
dsn_tns = cx_Oracle.makedsn('Host Name', 'Port Number', service_name='Service Name')
conn = cx_Oracle.connect(user=r'User Name', password='Personal Password', dsn=dsn_tns)
cur = conn.cursor()
index = 0
length = len(list)
while index < length:
        cur.execute('''select pre.EQUIPO_SERIE, PRE.*, ROWID from sisact_venta_repo_pre pre where pre.EQUIPO_SERIE ("'''+list[index]+'''");''')
        r1 = cur.fetchall()
        cur.execute('''select pre.iccid_serie_nuevo, PRE.*, ROWID from sisact_venta_repo_pre pre where pre.iccid_serie_nuevo in ("'''+list[index]+'''");''')
        r2 = cur.fetchall()
        cur.execute('''select v.dvpr_serie, v.*, ROWID from sisact_detalle_venta_prepago v where v.dvpr_serie in ("'''+list[index]+'''");''')
        r3 = cur.fetchall()
        cur.execute('''select v.dvev_serie, v.* from sisact_detalle_venta v where v.dvev_serie in ("'''+list[index]+'''");''')
        if r1 > 0 || r2 > 0 || r3 > 0:
            list.pop(index)
            index = index-1
            length = len(list)
        index += 1
conn.close()