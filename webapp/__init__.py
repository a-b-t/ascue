from flask import Flask, g
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
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
    login_manager.login_message = u"Пожалуйста, авторизуйтесь, чтобы получить доступ к этой странице."
         
    with app.app_context():

        app.register_blueprint(admin_blueprint)
        app.register_blueprint(user_blueprint)
        app.register_blueprint(news_blueprint)
        
        from webapp.dashapp import my_dash_app
        app = my_dash_app.Add_Dash(app)

        @app.before_request
        def before_request():
            if current_user.is_authenticated:
                g.user = current_user
                print(g.user.n_ob)
                    
        @login_manager.user_loader
        def load_user(user_id):
            return User.query.get(user_id)
                
        return app    

