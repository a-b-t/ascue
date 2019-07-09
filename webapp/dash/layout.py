import dash_core_components as dcc
import dash_html_components as html
from datetime import datetime as dt
import cx_Oracle
from webapp.config import USER_NAME, PASSWORD, dns_tsn
import pandas as pd

def make_layout():
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
        df = pd.read_sql(query, con=conn)
        
    finally:
        cur.close()
        conn.close()

    df_number_obj = df.rename(columns={"N_OB": "value", "TXT_N_OB_25": "label"}).to_dict('records')

    layout = html.Div([html.Div(
                                    dcc.Graph(id='graph')), 
                                    html.Div(dcc.DatePickerSingle(id='date-picker-single', date=dt(2018, 10,10))),
                                    dcc.Dropdown(id='my-dropdown', options=df_number_obj, value='', placeholder='Выберите объект'),
                                    html.Div(dcc.Dropdown(id='list-counters', value='', placeholder='Выберите фидер')),
                                    #html.Div(html.Table(id='table')),                                
                                    html.Div(html.Button(id='submit-button', children='Показать')), 
                                    html.Div(id='intermediate-value'),
                                    html.Div(id='num-object-to-submit')
                                ])
    return layout
