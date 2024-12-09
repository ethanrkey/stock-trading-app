import requests
import os
from typing import Optional, Dict, Any 
import logging 

from stock_trading.models.kitchen_model import Stock

ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
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
        
        if data and "Symbol" in data:
            logger.info("Successfully retrieved information for %s", symbol)
            return {
                'symbol': data['Symbol'],
                'name': data.get('Name'),
                'description': data.get('Description'),
                'exchange': data.get('Exchange'),
                'sector': data.get('Sector'),
                'industry': data.get('Industry'),
                'market_cap': data.get('MarketCapitalization'),
                'pe_ratio': data.get('PERatio'),
                'dividend_yield': data.get('DividendYield')
            }
        else:
            logger.warning("No information found for symbol %s", symbol)
            return None
            
    except requests.exceptions.RequestException as e:
        logger.error("Error getting stock information for %s: %s", symbol, str(e))
        return None

def get_stock_price(symbol):
    """
    Fetch the latest stock price for a given symbol.
    Args:
        symbol (str): The stock ticker symbol.
    Returns:
        dict: Stock price data from Alpha Vantage.
    """
    params = {
        "function": "GLOBAL_QUOTE",
        "symbol": symbol,
        "apikey": ALPHA_VANTAGE_API_KEY
    }
    response = requests.get(BASE_URL, params=params)
    response.raise_for_status()
    return response.json()["Global Quote"]

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
