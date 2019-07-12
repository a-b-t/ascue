import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from flask import Flask
from flask_login import LoginManager, login_required
from flask_migrate import Migrate
from webapp.db import db
from webapp.user.models import User
from webapp.user.views import blueprint as user_blueprint
from webapp.news.views import blueprint as news_blueprint
from webapp.admin.views import blueprint as admin_blueprint
from webapp.layouts import layout1, layout2


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
for view_func in dashapp.server.view_functions:
    if view_func.startswith('/dash/'):
        dashapp.server.view_functions[view_func] = login_required(dashapp.server.view_functions[view_func])

dashapp.config.suppress_callback_exceptions = True
dashapp.layout = html.Div([dcc.Location(id='url', refresh=False), html.Div(id='page-content')])

import webapp.callbacks
@dashapp.callback(Output('page-content', 'children'),
                  [Input('url', 'pathname')])
def display_page(pathname):
    print(pathname)
    if pathname == '/dash/':
        return layout1
    elif pathname == '/dash/reports':
        return layout2
    else:
        return '404'




@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

    

