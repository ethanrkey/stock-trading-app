from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
import logging
from stock_trading.clients.alpha_vantage_client import get_stock_info, get_stock_price
from stock_trading.utils.logger import configure_logger

logger = logging.getLogger(__name__)
configure_logger(logger)

lookup = Blueprint('lookup', __name__)

@lookup.route('/lookup', methods=['GET', 'POST'])
def lookup_stock():
    """Handle stock lookup requests."""
    if request.method == 'POST':
        symbol = request.form.get('symbol', '').upper()
        
        if not symbol:
            flash("Please enter a stock symbol")
            return redirect(url_for('lookup.lookup_stock'))
        
        try:
            # Get stock information
            stock_info = get_stock_info(symbol)
            current_price = get_stock_price(symbol)
            
            # Create stock data dictionary
            stock_data = {
                'symbol': symbol,
                'name': stock_info['name'],
                'description': stock_info['description'],
                'current_price': current_price,
                'exchange': stock_info['exchange'],
                'sector': stock_info['sector'],
                'industry': stock_info['industry']
            }
            
            return render_template('lookup/lookup.html', 
                                stock=stock_data,
                                searched_symbol=symbol)
            
        except Exception as e:
            logger.error("Error looking up stock %s: %s", symbol, str(e))
            flash(f"Error looking up stock {symbol}")
            return redirect(url_for('lookup.lookup_stock'))
    
    # GET request - show empty form
    return render_template('lookup/lookup.html')