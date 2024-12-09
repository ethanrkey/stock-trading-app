from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from dotenv import load_dotenv
import os

load_dotenv()

#db = SQLAlchemy()
from stock_trading.db import db
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    
    # Configure the Flask app
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///stock_trading.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    # User loader for Flask-Login
    from stock_trading.models.user_model import Users
    
    @login_manager.user_loader
    def load_user(user_id):
        return Users.query.get(int(user_id))

    # Register blueprints
    from stock_trading.routes.portfolio import portfolio
    from stock_trading.routes.auth import auth 
    from stock_trading.routes.trade import trade
    app.register_blueprint(portfolio)
    app.register_blueprint(auth)
    app.register_blueprint(trade)

    # Create database tables
    with app.app_context():
        db.create_all()

    return app