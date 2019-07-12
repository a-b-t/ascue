import cx_Oracle
import pandas as pd
from webapp.config import USER_NAME, PASSWORD, dns_tsn

#получение списка объектов из БД
try:
    conn = cx_Oracle.connect(USER_NAME, PASSWORD, dns_tsn)
    cur = conn.cursor()
    cur.execute("""
                ALTER SESSION SET NLS_DATE_FORMAT = 'YYYY-MM-DD HH24:MI:SS' NLS_TIMESTAMP_FORMAT = 'YYYY-MM-DD HH24:MI:SS.FF'
                """)
    query = """
                SELECT DISTINCT
                N_OB, TXT_N_OB_25
                -- COUNT(1) 
                FROM
                CNT.V_FID_SH
                WHERE SYB_RNK=5
                ORDER BY N_OB
                
                """
    df_number_obj = pd.read_sql(query, con=conn).rename(columns={"N_OB": "value", "TXT_N_OB_25": "label"}).to_dict('records')
except(cx_Oracle.DatabaseError):
    print('УУУУУУУУУУУУУУУУУУУУУУУУУУУУУУПППППППППППППППППППППППППСССССССССССССССССССССС')    
finally:
    cur.close()
    conn.close()