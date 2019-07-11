from datetime import datetime as dt
from datetime import timedelta
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import json
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
    
#DASH_LAYOUT-------------------------------------------------------------------------------------------------------------
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

    #navbar-----------------------------------------------------------------------------------------------------------------
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
    #/end_navbar---------------------------------------------------------------------------
    #body------------------------------------------------------------------------------
    body = dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H4("1. Выберите объект:"),                            
                            dcc.Dropdown(id='choose-object', options=df_number_obj, value='', placeholder='Выберите объект'),                                                        
                            html.H4("2. Выберите месяц:"),
                            html.Div(dcc.DatePickerSingle(id='date-picker-single', date=dt(2018, 10,10))),
                            #dbc.Button("Загрузить данные", id='submit-button', color="secondary"),
                            html.Div(html.A(id='download-link', children='Скачать файл')),
                            dcc.Dropdown(id='dropdown', options=[{'label': i, 'value': i} for i in ['NYC', 'LA', 'SF']],
                                         value='NYC',
                                         clearable=False),
                        ],
                        md=4,
                    ),
                    dbc.Col(
                        [
                            #html.H4("График за месяц"),
                            html.Div(dcc.Graph(id='month-graph', style={'height': '400px'})),
                            html.Div(id='json-month-data', style={'display': 'none'})
                        ]
                    ),
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                          html.H4("3. Выберите фидер:"),
                          dbc.RadioItems(id='list-counters', className="form-check"),  
                        ],
                        md=4,
                    ),
                    dbc.Col(
                        [
                           #html.Div(html.Pre(id='click-data')),
                           html.Div(dcc.Graph(id='day-graph', style={'height': '400px'})) 
                        ],
                        md=8,
                    )
                ]
            )
        ],
        className="mt-4",
    )
    #/end_body------------------------------------------------------------------------------------------- 
    dashapp.layout = html.Div([navbar, body])
    
#/END_DASH_LAYOUT-----------------------------------------------------------------------------------------------
#DASH_CALLBACKS----------------------------------------------------------------------------------------------------------
    #выбор опций для radioitems с названиями фидеров выбранного объекта
    @dashapp.callback(Output('list-counters', 'options'), 
                      [Input('choose-object', 'value')])
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
            df_list_counters = pd.read_sql(query, con=conn).rename(columns={"N_SH": "value", "TXT_FID": "label"}).to_dict('records')        
            return df_list_counters
        except(cx_Oracle.DatabaseError):
            print('УУУУУУУУУУУУУУУУУУУУУУУУУУУУУУПППППППППППППППППППППППППСССССССССССССССССССССС')
        finally:
            cur.close()
            conn.close()
            
    #создание и скачивание файла отчета
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

    #создание датасетов DATAFRAME объекта за месяц, день   
    @dashapp.callback(Output('json-month-data', 'children'),
                      [Input('list-counters', 'value')],   
                      [State('choose-object', 'value'),
                       State('date-picker-single', 'date')])
    def get_month_data(number_counter, number_object, choosen_month):
        if choosen_month is not None:
            date = f"LIKE '{choosen_month[:-3]}-%'"
        try:
            
            conn = cx_Oracle.connect(USER_NAME, PASSWORD, dns_tsn)
            cur = conn.cursor()
            cur.execute("""
                        ALTER SESSION SET NLS_DATE_FORMAT = 'YYYY-MM-DD HH24:MI:SS'
                        NLS_TIMESTAMP_FORMAT = 'YYYY-MM-DD HH24:MI:SS.FF'
                        """)
            query = """
                    SELECT
                    DD_MM_YYYY, N_INTER_RAS, VAL, N_SH, RASH_POLN
                    -- COUNT(1)
                    FROM
                    CNT.BUF_V_INT
                    WHERE 1=1
                    AND DD_MM_YYYY {} 
                    AND N_INTER_RAS BETWEEN 1 AND 48
                    AND N_OB = {}
                    AND N_GR_TY = 1
                    AND N_SH = '{}'
                    """.format(date, number_object, number_counter)
            df = pd.read_sql(query, con=conn)
        except(cx_Oracle.DatabaseError):
            print('УУУУУУУУУУУУУУУУУУУУУУУУУУУУУУПППППППППППППППППППППППППСССССССССССССССССССССС')
        except IndexError:
            print('У выбранного фидера нет данных за указанный месяц')
        finally:
            cur.close()
            conn.close()

        
        #приведение Dataframe к TimeSeries 
        dict_convert_to_halfhour = {'1': '00:00', '2': '00:30', '3': '01:00', '4': '01:30', '5': '02:00', '6': '02:30', 
                                '7': '03:00', '8': '03:30', '9': '04:00', '10': '04:30', '11': '05:00', '12': '05:30',
                                '13': '06:00', '14': '06:30', '15': '07:00', '16': '07:30', '17': '08:00', '18': '08:30',
                                '19': '09:00', '20': '09:30', '21': '10:00', '22': '10:30', '23': '11:00', '24': '11:30',
                                '25': '12:00', '26': '12:30', '27': '13:00', '28': '13:30', '29': '14:00', '30': '14:30',
                                '31': '15:00', '32': '15:30', '33': '16:00', '34': '16:30', '35': '17:00', '36': '17:30',
                                '37': '18:00', '38': '18:30', '39': '19:00', '40': '19:30', '41': '20:00', '42': '20:30',
                                '43': '21:00', '44': '21:30', '45': '22:00', '46': '22:30', '47': '23:00', '48': '23:30'}        
        df['N_INTER_RAS'] = df['N_INTER_RAS'].astype(str).replace(dict_convert_to_halfhour)
        df['DD_MM_YYYY'] = df['DD_MM_YYYY'].astype(str)
        df['date'] = pd.to_datetime(df['DD_MM_YYYY'] + ' ' + df['N_INTER_RAS'])
        del df['DD_MM_YYYY']
        del df['N_INTER_RAS']
        df_1 = df.groupby(['N_SH', pd.Grouper(key='date', freq='D')])['VAL'].sum().reset_index()
        df_2 = df.groupby(['N_SH', pd.Grouper(key='date', freq='H')])['VAL'].sum().reset_index()
        df_3 = df.groupby(['N_SH', pd.Grouper(key='date', freq='30min')])['VAL'].sum().reset_index()
        datasets = {
                'df_1': df_1.to_json(orient='split', date_format='iso'),
                'df_2': df_2.to_json(orient='split', date_format='iso'),
                'df_3': df_3.to_json(orient='split', date_format='iso')
            }
               
        return json.dumps(datasets)
    
    
    #формирования графика потребления за месяц
    @dashapp.callback(Output('month-graph', 'figure'), 
                [Input('list-counters', 'value'), 
                 Input('json-month-data', 'children')])
    def update_graph(number_counter, json_month):
        datasets = json.loads(json_month)
        dff = pd.read_json(datasets['df_1'], orient='split', convert_dates='True')

        number_counter = int(dff.iloc[1]['N_SH'])        
        #график        
        figure = go.Figure(
                data=[
                    go.Bar(
                        x=dff['date'].tolist(),
                        y=dff['VAL'].tolist(),
                        name='Расход',
                        marker=go.bar.Marker(
                            color='rgb(55, 83, 109)'
                        )
                    ),
                ],
                layout=go.Layout(
                    yaxis={'type': 'log', 'title': 'Энергия, кВтч'},
                    xaxis={'title': ''},
                    title=f"Расход электроэнергии за месяц по счетчику № {number_counter}",
                    showlegend=True,
                    legend=go.layout.Legend(
                        x=0,
                        y=1.0
                    ),
                    margin=go.layout.Margin(l=40, r=0, t=40, b=30)
                )
            )
        return figure
    
    #формирования графика потребления за день
    @dashapp.callback(Output('day-graph', 'figure'),
                      [Input('month-graph', 'clickData'),
                      Input('json-month-data', 'children')])
    def update_daily_graph(clickData, json_month):
        datasets = json.loads(json_month)
        dff = pd.read_json(datasets['df_3'], orient='split', convert_dates='True')
        clickedData = clickData['points'][0]['x']
        begin_day = pd.Timestamp(clickedData)
        end_day = begin_day + timedelta(days=1)
        dff_day = dff[(dff['date'] >= begin_day) & (dff['date'] < end_day)] 
        number_counter = int(dff.iloc[1]['N_SH'])        
        #график        
        figure = go.Figure(
                data=[
                    go.Bar(
                        x=dff_day['date'].tolist(),
                        y=dff_day['VAL'].tolist(),
                        name='Расход',
                        marker=go.bar.Marker(
                            color='green'
                        )
                    ),
                ],
                layout=go.Layout(
                    yaxis={'type': 'log', 'title': 'Энергия, кВтч'},
                    xaxis={'title': ''},
                    title=f"Расход электроэнергии за день по счетчику № {number_counter}",
                    showlegend=True,
                    legend=go.layout.Legend(
                        x=0,
                        y=1.0
                    ),
                    margin=go.layout.Margin(l=40, r=0, t=40, b=30)
                )
            )
        return figure



        return json.dumps(clickData, indent=2)
    
    #рабочий пример с click-data
    #@dashapp.callback(Output('click-data', 'children'),
    #                  [Input('month-graph', 'clickData')])
    #def diplay_clickdata(clickData):
    #    return json.dumps(clickData, indent=2)
#/END_DASH_CALLBACKS-----------------------------------------------------------------------------------------------------------------


    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(user_id)
    
    return app

