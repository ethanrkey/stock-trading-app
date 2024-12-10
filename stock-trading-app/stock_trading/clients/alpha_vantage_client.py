import requests
import os
from typing import Optional, Dict, Any 
import logging 

from stock_trading.models.stock_model import Stock
from stock_trading.utils.logger import configure_logger

logger = logging.getLogger(__name__)
configure_logger(logger)


ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')

BASE_URL = "https://www.alphavantage.co/query"

def validate_stock_symbol(symbol: str) -> bool:
    """
    Validate if a stock symbol exists and is tradeable.
    
    Args:
        symbol (str): The stock symbol to validate
        
    Returns:
        bool: True if the symbol is valid, False otherwise
    """
    logger.info("Validating stock symbol: %s", symbol)
    
    try:
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': symbol,
            'apikey': ALPHA_VANTAGE_API_KEY
        }
        
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        data = response.json()
        
        # Check if we got valid data back
        if "Global Quote" in data and data["Global Quote"]:
            logger.info("Stock symbol %s is valid", symbol)
            return True
        else:
            logger.warning("Invalid stock symbol: %s", symbol)
            return False
            
    except requests.exceptions.RequestException as e:
        logger.error("Error validating stock symbol %s: %s", symbol, str(e))
        return False

def get_stock_info(symbol: str) -> Optional[Dict[str, Any]]:
    """
    Get detailed information about a stock.
    
    Args:
        symbol (str): The stock symbol
        
    Returns:
        Optional[Dict[str, Any]]: Dictionary containing stock information or None if not found
    """
    logger.info("Getting information for stock: %s", symbol)
    
    try:
        params = {
            'function': 'OVERVIEW',
            'symbol': symbol,
            'apikey': ALPHA_VANTAGE_API_KEY
        }
        
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        logger.debug("API Response for %s info: %s", symbol, data)  # Debug log
        
        # Always return a dictionary with fallback values for missing data
        return {
            'symbol': data.get('Symbol', symbol),
            'name': data.get('Name', symbol),
            'description': data.get('Description', 'No description available'),
            'exchange': data.get('Exchange', 'Unknown'),
            'sector': data.get('Sector', 'Unknown'),
            'industry': data.get('Industry', 'Unknown')
        }
            
    except Exception as e:
        logger.error("Error getting stock information for %s: %s", symbol, str(e))
        # Return fallback data
        return {
            'symbol': symbol,
            'name': symbol,
            'description': 'Information temporarily unavailable',
            'exchange': 'Unknown',
            'sector': 'Unknown',
            'industry': 'Unknown'
        }

def get_stock_price(symbol):
    """
    Fetch the latest stock price for a given symbol.
    Args:
        symbol (str): The stock ticker symbol.
    Returns:
        dict: Stock price data from Alpha Vantage.
    """
    try:
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': symbol,
            'apikey': ALPHA_VANTAGE_API_KEY
        }
        
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        logger.debug("API Response for %s: %s", symbol, data)  # Debug log
        
        if "Global Quote" not in data:
            logger.error("Missing 'Global Quote' in response: %s", data)
            raise ValueError("Invalid API response format")
            
        quote = data["Global Quote"]
        if not quote:
            logger.error("Empty quote data for symbol %s", symbol)
            raise ValueError("No quote data available")
            
        price = quote.get("05. price")
        if not price:
            logger.error("No price found in quote data: %s", quote)
            raise ValueError("Price not found in quote data")
            
        price_float = float(price)
        logger.info("Successfully got price for %s: $%.2f", symbol, price_float)
        return price_float
            
    except requests.exceptions.RequestException as e:
        logger.error("Network error getting price for %s: %s", symbol, str(e))
        raise ValueError(f"Network error while fetching price")
    except ValueError as e:
        logger.error("Error getting price for %s: %s", symbol, str(e))
        raise ValueError(str(e))
    except Exception as e:
        logger.error("Unexpected error getting price for %s: %s", symbol, str(e))
        raise ValueError(f"Unexpected error while fetching price")


def get_historical_data(symbol, interval="1d", output_size="compact"):
    """
    Fetch historical stock price data for a given symbol.
    Args:
        symbol (str): The stock ticker symbol.
        interval (str): Time interval (e.g., '1d').
        output_size (str): 'compact' or 'full'.
    Returns:
        dict: Historical stock data from Alpha Vantage.
    """
    params = {
        "function": "TIME_SERIES_DAILY_ADJUSTED",
        "symbol": symbol,
        "outputsize": output_size,
        "apikey": ALPHA_VANTAGE_API_KEY
    }
    response = requests.get(BASE_URL, params=params)
    response.raise_for_status()
    return response.json()["Time Series (Daily)"]

def update_all_stock_prices():
    """
    Updates the current prices for all stocks in the database.
    Returns:
        dict: Summary of the update process.
    """
    stocks = Stock.query.all()
    success, errors = [], []

    for stock in stocks:
        try:
            stock_data = get_stock_price(stock.symbol)
            current_price = float(stock_data['05. price'])
            Stock.update_stock(stock.id, current_price=current_price)
            success.append({'symbol': stock.symbol, 'current_price': current_price})
        except Exception as e:
            errors.append({'symbol': stock.symbol, 'error': str(e)})

    return {'success': success, 'errors': errors}
