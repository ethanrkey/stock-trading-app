import requests
import os

from stock_trading.models.kitchen_model import Stock

ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
BASE_URL = "https://www.alphavantage.co/query"

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
