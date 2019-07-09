from datetime import datetime as dt
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import cx_Oracle
from webapp.config import USER_NAME, PASSWORD, dns_tsn
from flask import Flask, redirect, url_for, send_from_directory, render_template
from flask_login import LoginManager
from flask_migrate import Migrate
import os
import pandas as pd
import plotly.graph_objs as go
from webapp.db import db
from webapp.user.models import User
from webapp.user.views import blueprint as user_blueprint
from webapp.news.views import blueprint as news_blueprint
from webapp.admin.views import blueprint as admin_blueprint



def create_app():
    app = Flask(__name__)
    app.config.from_pyfile('config.py')
    db.init_app(app)
    migrate = Migrate(app, db)
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'user.login'
    app.register_blueprint(admin_blueprint)
    app.register_blueprint(user_blueprint)
    app.register_blueprint(news_blueprint)
    dashapp = dash.Dash(__name__, server=app, routes_pathname_prefix='/dash/', external_stylesheets=[dbc.themes.BOOTSTRAP])
    
    #layout
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

    #navbar
    navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("Link", href='')),
        dbc.DropdownMenu(
            nav=True,
            in_navbar=True,
            label="Menu",
            children=[
                dbc.DropdownMenuItem("Entry 1"),
                dbc.DropdownMenuItem("Entry 2"),
                dbc.DropdownMenuItem(divider=True),
                dbc.DropdownMenuItem("Entry 3"),
            ],
        ),
    ],
    brand="Главная",
    brand_href="/",
    sticky="top",
    )

    body = dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Div(dcc.RadioItems(id='day-or-month-choose', options=[
                                                                        {'label': 'День', 'value': 'day'}, 
                                                                        {'label': 'Месяц', 'value': 'month'}],
                                                                        value='day'))
                        ],
                        md=4,
                    )
                ]
            ),
            
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H4("Выберите дату и объект"),
                            html.Div(dcc.DatePickerSingle(id='date-picker-single', date=dt(2018, 10,10))),
                            dcc.Dropdown(id='my-dropdown', options=df_number_obj, value='', placeholder='Выберите объект'),
                            html.Div(dcc.Dropdown(id='list-counters', value='', placeholder='Выберите фидер')),
                            #html.Div(html.Table(id='table')),                                
                            #html.Div(html.Button(id='submit-button', children='Показать')), 
                            dbc.Button("Показать", id='submit-button', color="secondary"),
                            html.Div(html.A(id='download-link', children='Скачать файл')),
                            dcc.Dropdown(id='dropdown', options=[{'label': i, 'value': i} for i in ['NYC', 'LA', 'SF']],
                                         value='NYC',
                                         clearable=False),
                            html.Div(id='intermediate-value', style={'display': 'none'}),
                            html.Div(id='num-object-to-submit', style={'display': 'none'}),
                            #html.Div(id='selected-day-or-month', style={'display': 'none'})
                        ],
                        md=4,
                    ),
                    dbc.Col(
                        [
                            html.H2("График"),
                            html.Div(dcc.Graph(id='graph')),
                        ]
                    ),
                ]
            )
        ],
        className="mt-4",
    )

    
    dashapp.layout = html.Div([navbar, body])
    
   #callbacks

    @dashapp.callback(Output('intermediate-value', 'children'), 
                      [Input('date-picker-single', 'date')], 
                      [State('day-or-month-choose', 'value')])
    def update_output(date, value):
        if date is not None:
            if value == 'day':
                date = f"= '{}'"
                print(date)
                return date
            if value == 'month':
                date = f"LIKE '{date[:-3]}-%'"
                print(date)
                return date

    @dashapp.callback(Output('list-counters', 'options'), [Input('my-dropdown', 'value')])
    def get_list_counters_of_obj(num_obj):
        try:        
            conn = cx_Oracle.connect(USER_NAME, PASSWORD, dns_tsn)
            cur = conn.cursor()
            cur.execute("""
                        ALTER SESSION SET NLS_DATE_FORMAT = 'YYYY-MM-DD HH24:MI:SS'
                        NLS_TIMESTAMP_FORMAT = 'YYYY-MM-DD HH24:MI:SS.FF'
                        """)
            query = """
                SELECT 
                N_SH, TXT_FID
                -- COUNT(1) 
                FROM
                CNT.V_FID_SH
                WHERE 1=1
                AND N_OB = '{}'
                ORDER BY N_FID
                    """.format(num_obj)
            df = pd.read_sql(query, con=conn)
            df_list_counters = df.rename(columns={"N_SH": "value", "TXT_FID": "label"}).to_dict('records')        
            return df_list_counters
        finally:
            cur.close()
            conn.close()
        
    @dashapp.callback(Output('num-object-to-submit', 'children'), [Input('my-dropdown', 'value')])
    def get_num_obj(num_obj):
        return num_obj    
        

    @dashapp.callback(Output('download-link', 'href'), [Input('dropdown', 'value')])
    def update_href(dropdown_value):
        df = pd.DataFrame({dropdown_value: [1, 2, 3]})
        relative_filename = os.path.join(
            'downloads',
            '{}-download.xlsx'.format(dropdown_value)
        )
        absolute_filename = os.path.join(os.getcwd(), relative_filename)
        writer = pd.ExcelWriter(absolute_filename)
        df.to_excel(writer, 'Sheet1')
        writer.save()
        return '/{}'.format(relative_filename)


    @dashapp.server.route('/downloads/<path:path>')
    def serve_static(path):
        root_dir = os.getcwd()
        return send_from_directory(os.path.join(root_dir, 'downloads'), path)

        
    @dashapp.callback(Output('graph', 'figure'), 
                [Input('submit-button', 'n_clicks')],
                [State('intermediate-value', 'children'),
                State('num-object-to-submit', 'children'),
                State('list-counters', 'value')])
    def update_graph(n_clicks, new_date, number_object, number_counter):
        try:
            
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
                    AND DD_MM_YYYY {}
                    AND N_INTER_RAS BETWEEN 1 AND 48
                    AND N_OB = {}
                    AND N_GR_TY = 1
                    AND N_SH = '{}'
                    """.format(new_date, number_object, number_counter)
            df = pd.read_sql(query, con=conn)
            number_counter = int(df.iloc[1]['N_SH'])

            dict_convert_to_halfhour = {'1': '00:00', '2': '00:30', '3': '01:00', '4': '01:30', '5': '02:00', '6': '02:30', 
                                    '7': '03:00', '8': '03:30', '9': '04:00', '10': '04:30', '11': '05:00', '12': '05:30',
                                    '13': '06:00', '14': '06:30', '15': '07:00', '16': '07:30', '17': '08:00', '18': '08:30',
                                    '19': '09:00', '20': '09:30', '21': '10:00', '22': '10:30', '23': '11:00', '24': '11:30',
                                    '25': '12:00', '26': '12:30', '27': '13:00', '28': '13:30', '29': '14:00', '30': '14:30',
                                    '31': '15:00', '32': '15:30', '33': '16:00', '34': '16:30', '35': '17:00', '36': '17:30',
                                    '37': '18:00', '38': '18:30', '39': '19:00', '40': '19:30', '41': '20:00', '42': '20:30',
                                    '43': '21:00', '44': '21:30', '45': '22:00', '46': '22:30', '47': '23:00', '48': '23:30'}
            
            df.N_INTER_RAS = df.N_INTER_RAS.astype(str).replace(dict_convert_to_halfhour)
            df['DD_MM_YYYY'] = df['DD_MM_YYYY'].astype(str)
            df['new_date'] = pd.to_datetime(df['DD_MM_YYYY'] + ' ' + df['N_INTER_RAS'])
            df_freq_day = df.groupby(['N_SH', pd.Grouper(key='new_date', freq='D')])['VAL'].sum().reset_index()
            print
            
            figure = go.Figure(
                    data=[
                        go.Bar(
                            x=df_freq_day['new_date'].tolist(),
                            y=df_freq_day['VAL'].tolist(),
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



    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(user_id)
    
    return app

