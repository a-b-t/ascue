import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from datetime import datetime as dt
from webapp.queries import df_number_obj


#DASH_LAYOUT-------------------------------------------------------------------------------------------------------------
#navbar-----------------------------------------------------------------------------------------------------------------
navbar = dbc.NavbarSimple(
children=[
    dbc.NavItem(dbc.NavLink("Link", href='')),
    dbc.DropdownMenu(
        nav=True,
        in_navbar=True,
        label="Меню",
        children=[
            dbc.DropdownMenuItem("Отчеты", href='/dash/reports'),
            dbc.DropdownMenuItem("Графики", href='/dash/'),
            dbc.DropdownMenuItem(divider=True),
            dbc.DropdownMenuItem("Выйти", href="/users/logout", external_link=True),
        ],
    ),
],
brand="Главная",
brand_href="/",
brand_external_link=True,
sticky="top",
)
#/end_navbar---------------------------------------------------------------------------
#body------------------------------------------------------------------------------
body1 = dbc.Container(
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
                        html.Div(html.A(id='download-link', children='Сохранить отчет за месяц'))
                    ],
                    md=4, 
                ),
                dbc.Col(
                    [
                        #html.H4("График за месяц"),
                        html.Div(
                            [dcc.Loading(id='loading-1', 
                                         children=
                                                [html.Div(
                                                          dcc.Graph(id='month-graph', style={'height': '400px'}))], 
                                        type='circle', fullscreen=True                                               
                                        )
                            ]),
                        html.Div(id='json-month-data', style={'display': 'none'})
                    ]
                ),
            ], style={'height': '401px'}
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
layout1 = html.Div([navbar, body1])    
layout2 = html.Div([navbar])    
#/END_DASH_LAYOUT-----------------------------------------------------------------------------------------------