import logging
from typing import Any, List, Dict

from stock_trading.clients.mongo_client import sessions_collection
from stock_trading.clients.mongo_client import portfolios_collection
from stock_trading.utils.logger import configure_logger
from stock_trading.clients.alpha_vantage_client import get_stock_price
from stock_trading.clients.mongo_client import get_mongo_client

logger = logging.getLogger(__name__)
configure_logger(logger)

def initialize_user_portfolio(user_id: int) -> None:
    """
    Initialize an empty portfolio for a new user.
    
    Args:
        user_id (int): The ID of the user.
    """
    client = get_mongo_client()
    db = client.stock_trading
    
    # Create initial portfolio document
    portfolio = {
        'user_id': user_id,
        'holdings': [],
        'total_value': 0.0,
        'cash_balance': 10000.00  # Starting cash balance
    }

    try:
        portfolios_collection.insert_one(portfolio)
        logger.info("Portfolio initialized successfully for user %d", user_id)
        return portfolio
    except Exception as e:
        logger.error("Error initializing portfolio for user %d: %s", user_id, str(e))
        raise


def get_user_portfolio(user_id: int) -> Dict[str, Any]:
    """
    Get a user's portfolio with current stock prices and values.
    """
    logger.info("Retrieving portfolio for user %d", user_id)
    
    portfolio = portfolios_collection.find_one({'user_id': user_id})
    if not portfolio:
        logger.info("No portfolio found for user %d. Creating new portfolio.", user_id)
        portfolio = initialize_user_portfolio(user_id)
    
    # Calculate current values for each holding
    holdings = []
    total_stock_value = 0.0
    
    for holding in portfolio['holdings']:
        current_price = get_stock_price(holding['symbol'])
        holding_value = current_price * holding['shares']
        total_stock_value += holding_value
        
        holdings.append({
            'symbol': holding['symbol'],
            'shares': holding['shares'],
            'current_price': current_price,
            'total_value': holding_value,
            'avg_purchase_price': holding.get('avg_purchase_price', 0.0),
            'gain_loss': holding_value - (holding['shares'] * holding.get('avg_purchase_price', 0.0))
        })
    
    return {
        'holdings': holdings,
        'cash_balance': portfolio['cash_balance'],
        'total_stock_value': total_stock_value,
        'total_portfolio_value': total_stock_value + portfolio['cash_balance']
    }


def update_portfolio_holding(user_id: int, symbol: str, quantity: int) -> None:
    """
    Update or add a stock holding in user's portfolio.
    
    Args:
        user_id (int): The ID of the user whose portfolio is to be updated.
        symbol (str): The stock symbol to update.
        quantity (int): The new quantity (positive for buy, negative for sell).
    """
    logger.info("Updating portfolio for user ID %d, symbol %s, quantity %d", 
                user_id, symbol, quantity)
    
    session = sessions_collection.find_one({"user_id": user_id})
    if not session:
        logger.error("No session found for user ID %d", user_id)
        raise ValueError(f"User with ID {user_id} not found")
    
    portfolio = session.get("portfolio", {"holdings": []})
    holdings = portfolio.get("holdings", [])
    
    # Find existing holding
    existing_holding = next(
        (h for h in holdings if h["symbol"] == symbol),
        None
    )
    
    if existing_holding:
        new_quantity = existing_holding["quantity"] + quantity
        if new_quantity <= 0:
            # Remove holding if quantity becomes 0 or negative
            holdings = [h for h in holdings if h["symbol"] != symbol]
        else:
            existing_holding["quantity"] = new_quantity
    elif quantity > 0:
        # Add new holding only if quantity is positive
        holdings.append({
            "symbol": symbol,
            "quantity": quantity
        })
    
    # Update MongoDB
    sessions_collection.update_one(
        {"user_id": user_id},
        {"$set": {"portfolio": {"holdings": holdings}}}
    )
    logger.info("Portfolio updated successfully for user ID %d", user_id)


def buy_stock(user_id: int, symbol: str, shares: int, price: float) -> None:
    """
    Execute a stock purchase for a user.
    
    Args:
        user_id (int): The ID of the user making the purchase
        symbol (str): The stock symbol
        shares (int): Number of shares to buy
        price (float): Current price per share
        
    Raises:
        ValueError: If the user cannot afford the purchase or if other validation fails
    """
    total_cost = shares * price
    
    # Get user's portfolio
    portfolio = portfolios_collection.find_one({'user_id': user_id})
    if not portfolio:
        raise ValueError("User portfolio not found")
        
    # Check if user has enough cash
    if portfolio['cash_balance'] < total_cost:
        raise ValueError(f"Insufficient funds. Cost: ${total_cost:.2f}, Available: ${portfolio['cash_balance']:.2f}")
    
    # Find existing holding for this stock
    existing_holding = None
    for holding in portfolio['holdings']:
        if holding['symbol'] == symbol:
            existing_holding = holding
            break
    
    if existing_holding:
        # Update existing holding
        total_shares = existing_holding['shares'] + shares
        total_cost_basis = (existing_holding['shares'] * existing_holding['avg_purchase_price']) + (shares * price)
        new_avg_price = total_cost_basis / total_shares
        
        portfolios_collection.update_one(
            {'user_id': user_id, 'holdings.symbol': symbol},
            {
                '$set': {
                    'holdings.$.shares': total_shares,
                    'holdings.$.avg_purchase_price': new_avg_price
                }
            }
        )
    else:
        # Add new holding
        portfolios_collection.update_one(
            {'user_id': user_id},
            {
                '$push': {
                    'holdings': {
                        'symbol': symbol,
                        'shares': shares,
                        'avg_purchase_price': price
                    }
                }
            }
        )
    
    # Update cash balance
    portfolios_collection.update_one(
        {'user_id': user_id},
        {'$inc': {'cash_balance': -total_cost}}
    )
    
    logger.info(
        "User %d purchased %d shares of %s at $%.2f per share",
        user_id, shares, symbol, price
    )