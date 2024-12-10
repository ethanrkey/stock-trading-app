from flask import Flask
from stock_trading.routes import portfolio

def create_app():
    app = Flask(__name__)
    # ... other app configuration ...
    
    app.register_blueprint(portfolio)
    
    return app