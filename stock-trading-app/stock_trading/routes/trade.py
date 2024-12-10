from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from stock_trading.models.mongo_session_model import get_user_portfolio
from stock_trading.clients.alpha_vantage_client import get_stock_price, get_stock_info
import logging
from stock_trading.utils.logger import configure_logger

logger = logging.getLogger(__name__)
configure_logger(logger)

# Create the Blueprint first
trade = Blueprint('trade', __name__)

@trade.route('/buy', methods=['GET', 'POST'])
@login_required
def buy_stock_route():
    if request.method == 'POST':
        symbol = request.form.get('symbol', '').upper()
        shares = request.form.get('shares')
        
        try:
            # Validate inputs
            if not symbol or not shares:
                flash('Please provide both stock symbol and number of shares.')
                return redirect(url_for('trade.buy_stock_route'))
            
            shares = int(shares)
            if shares <= 0:
                flash('Number of shares must be positive.')
                return redirect(url_for('trade.buy_stock_route'))
            
            # Get stock information and validate
            stock_info = get_stock_info(symbol)
            if not stock_info:
                flash(f'Invalid stock symbol: {symbol}')
                return redirect(url_for('trade.buy_stock_route'))
            
            # Get current price and execute purchase
            current_price = get_stock_price(symbol)
            total_cost = current_price * shares
            
            # Show confirmation with stock details
            return render_template('trade/confirm_buy.html',
                                symbol=symbol,
                                shares=shares,
                                price=current_price,
                                total_cost=total_cost,
                                stock_info=stock_info)
            
        except ValueError as e:
            flash(str(e))
        except Exception as e:
            flash('An error occurred while processing your request.')
            logger.error("Error in buy_stock_route: %s", str(e))
            
    # Get user's current cash balance for the template
    portfolio = get_user_portfolio(current_user.id)
    return render_template('trade/buy.html', cash_balance=portfolio['cash_balance'])

    
@trade.route('/sell', methods=['GET', 'POST'])
@login_required
def sell_stock_route():
    if request.method == 'POST':
        symbol = request.form.get('symbol', '').upper()
        shares = request.form.get('shares')
        
        try:
            # Validate inputs
            if not symbol or not shares:
                flash('Please provide both stock symbol and number of shares.')
                return redirect(url_for('trade.sell_stock_route'))
            
            shares = int(shares)
            if shares <= 0:
                flash('Number of shares must be positive.')
                return redirect(url_for('trade.sell_stock_route'))
            
            # Get stock information and validate
            stock_info = get_stock_info(symbol)
            if not stock_info:
                flash(f'Invalid stock symbol: {symbol}')
                return redirect(url_for('trade.sell_stock_route'))
            
            # Get current price
            current_price = get_stock_price(symbol)
            total_value = current_price * shares
            
            # Show confirmation with stock details
            return render_template('trade/confirm_sell.html',
                                symbol=symbol,
                                shares=shares,
                                price=current_price,
                                total_value=total_value,
                                stock_info=stock_info)
            
        except ValueError as e:
            flash(str(e))
        except Exception as e:
            flash('An error occurred while processing your request.')
            logger.error("Error in sell_stock_route: %s", str(e))
    
    # Get user's current portfolio for the template
    portfolio = get_user_portfolio(current_user.id)
    return render_template('trade/sell.html', portfolio=portfolio)

