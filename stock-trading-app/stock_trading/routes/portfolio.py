from flask import Blueprint, render_template, jsonify, current_app
from stock_trading.models.mongo_session_model import get_user_portfolio
from flask_login import login_required, current_user 

portfolio = Blueprint('portfolio', __name__)

@portfolio.route('/portfolio')
@login_required
def view_portfolio():
    try:
        portfolio = get_user_portfolio(current_user.id)
        return render_template('portfolio.html', 
                             portfolio=portfolio,
                             error = None)
    except Exception as e:
        current_app.logger.error(f"Error fetching portfolio: {str(e)}")
        return render_template('portfolio.html', 
                             error="Unable to fetch portfolio at this time.")
