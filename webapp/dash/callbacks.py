from datetime import datetime as dt

import plotly.graph_objs as go
from dash.dependencies import Input, State
from dash.dependencies import Output
import cx_Oracle
from webapp.config import USER_NAME, PASSWORD, dns_tsn
import pandas as pd


def register_callbacks(dashapp):
    @dashapp.callback(Output('intermediate-value', 'children'),
                      [Input('date-picker-single', 'date')])
    def update_output(date):
        if date is not None:
            date = dt.strptime(date, '%Y-%m-%d')
            return date

        
    @dashapp.callback(Output('num_object', 'children'),
                      [Input('my-dropdown', 'value')])
    def update_num_obj(num_obj):
        return num_obj
    
    
    @dashapp.callback(Output('graph', 'figure'), 
                      [Input('submit-button', 'n_clicks')],
                      [State('intermediate-value', 'children'),
                      State('num_object', 'children')])
    def update_graph(n_clicks, new_date, number_object):
        try:
            print(n_clicks)
            conn = cx_Oracle.connect(USER_NAME, PASSWORD, dns_tsn)
            cur = conn.cursor()
            cur.execute("""
                        ALTER SESSION SET NLS_DATE_FORMAT = 'YYYY-MM-DD HH24:MI:SS'
                        NLS_TIMESTAMP_FORMAT = 'YYYY-MM-DD HH24:MI:SS.FF'
                        """)
            query = """
                    SELECT
                    N_INTER_RAS, VAL, N_SH, RASH_POLN
                    -- COUNT(1)
                    FROM
                    CNT.BUF_V_INT
                    WHERE 1=1
                    AND DD_MM_YYYY = '{}'
                    AND N_INTER_RAS BETWEEN 1 AND 48
                    AND N_OB = '{}'
                    AND N_GR_TY = 1
                    AND N_SH = 1211667
                    """.format(new_date, number_object)
            df = pd.read_sql(query, con=conn)
            number_counter = int(df.iloc[1]['N_SH'])
            figure = go.Figure(
                    data=[
                        go.Bar(
                            x=df['N_INTER_RAS'].tolist(),
                            y=df['VAL'].tolist(),
                            name='Расход',
                            marker=go.bar.Marker(
                                color='rgb(55, 83, 109)'
                            )
                        ),
                    ],
                    layout=go.Layout(
                        yaxis={'type': 'log', 'title': 'Энергия, кВтч'},
                        xaxis={'title': 'Номер получасовки'},
                        title=f"Расход электроэнергии за сутки {new_date } по счетчику № {number_counter}",
                        showlegend=True,
                        legend=go.layout.Legend(
                            x=0,
                            y=1.0
                        ),
                        margin=go.layout.Margin(l=40, r=0, t=40, b=30)
                    )
                )
            return figure
        finally:
            cur.close()
            conn.close()

