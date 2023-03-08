from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'secret-key-goes-here'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:''@localhost/db4deltamate'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False 
    app.config['UPLOAD_FOLDER'] = 'static/uploads/'
    app.config['CURRENT_PAGE'] = 'home'
    db.init_app(app)

    login_manager = LoginManager() 
    login_manager.login_view = 'auth.login' 
    login_manager.init_app(app)
    from models import Mocdm_users
    @login_manager.user_loader
    def load_user(user_id): 
        return Mocdm_users.query.get(int(user_id))
    from auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)
    from main import main as main_blueprint
    app.register_blueprint(main_blueprint)
    from cron_srp import cron_srp as cron_srp_blueprint
    app.register_blueprint(cron_srp_blueprint)
    return app