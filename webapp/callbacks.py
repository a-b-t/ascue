import cx_Oracle
from dash.dependencies import Input, Output, State
from datetime import timedelta
import json
from flask import send_from_directory
import pandas as pd
import openpyxl
import os
import plotly.graph_objs as go
import time
from webapp.config import USER_NAME, PASSWORD, dns_tsn
from webapp import dashapp


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
@dashapp.callback(Output('download-link', 'href'), 
                  [Input('list-counters', 'value')],   
                  [State('choose-object', 'value'),
                   State('date-picker-single', 'date')])
def update_href(number_counter, number_object, choosen_month):
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
    del df['N_SH']
    df_h = df.set_index('date').resample('H')['VAL'].sum()
    DFList = []
    for group in df_h.groupby(df_h.index.day):
        DFList.append(group[1])
    wb = openpyxl.load_workbook('/home/alex/template.xlsx')
    ws = wb.active

    for r_idx, row in enumerate(DFList, 10):
        for c_idx, value in enumerate(row, 2):
            ws.cell(row=r_idx, column=c_idx, value=value)

    #wb.save('/home/alex/df_out.xlsx')
    
    relative_filename = os.path.join(
        'downloads',
        '{}-download.xlsx'.format(number_counter)
    )
    absolute_filename = os.path.join(os.getcwd(), relative_filename)
    
    wb.save(absolute_filename)
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
   




    #рабочий пример с click-data
    #@dashapp.callback(Output('click-data', 'children'),
    #                  [Input('month-graph', 'clickData')])
    #def diplay_clickdata(clickData):
    #    return json.dumps(clickData, indent=2)
#/END_DASH_CALLBACKS-----------------------------------------------------------------------------------------------------------------
