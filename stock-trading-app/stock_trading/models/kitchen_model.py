from dataclasses import asdict, dataclass
import logging
from typing import Any, List

from sqlalchemy import event
from sqlalchemy.exc import IntegrityError

from stock_trading.clients.redis_client import redis_client
from stock_trading.db import db
from stock_trading.utils.logger import configure_logger


logger = logging.getLogger(__name__)
configure_logger(logger)


@dataclass
class Stock(db.Model):
    __tablename__ = 'stocks'

    id: int = db.Column(db.Integer, primary_key=True)
    symbol: str = db.Column(db.String(10), unique=True, nullable=False)
    name: str = db.Column(db.String(100), nullable=False)
    quantity: int = db.Column(db.Integer, nullable=False, default=0)
    buy_price: float = db.Column(db.Float, nullable=False)
    current_price: float = db.Column(db.Float, nullable=True)
    created_at: str = db.Column(db.DateTime, nullable=False, server_default=db.func.now())

    @classmethod
    def add_stock(cls, symbol: str, name: str, quantity: int, buy_price: float) -> None:
        """
        Add a new stock to the database.

        Args:
            symbol (str): Stock ticker symbol.
            name (str): Stock company name.
            quantity (int): Number of shares purchased.
            buy_price (float): Price per share at purchase.

        Raises:
            ValueError: If input data is invalid or if a stock with the same symbol already exists.
        """
        if quantity <= 0 or buy_price <= 0:
            raise ValueError("Quantity and buy price must be positive numbers.")
        new_stock = cls(symbol=symbol, name=name, quantity=quantity, buy_price=buy_price)
        try:
            db.session.add(new_stock)
            db.session.commit()
            logger.info("Stock successfully added to the database: %s (%s)", name, symbol)
        except IntegrityError:
            db.session.rollback()
            logger.error("Duplicate stock symbol: %s", symbol)
            raise ValueError(f"Stock with symbol '{symbol}' already exists.")
        except Exception as e:
            db.session.rollback()
            logger.error("Database error: %s", str(e))
            raise

    @classmethod
    def update_stock(cls, stock_id: int, **kwargs) -> None:
        """
        Update stock attributes.

        Args:
            stock_id (int): ID of the stock to update.
            kwargs: Fields to update (e.g., quantity, current_price).

        Raises:
            ValueError: If the stock is not found or if invalid attributes are provided.
        """
        stock = cls.query.get(stock_id)
        if not stock:
            logger.error("Stock with ID %s not found.", stock_id)
            raise ValueError(f"Stock with ID {stock_id} not found.")

        for key, value in kwargs.items():
            if hasattr(stock, key):
                setattr(stock, key, value)
            else:
                logger.warning("Invalid attribute: %s", key)
                raise ValueError(f"Invalid attribute: {key}")

        db.session.commit()
        logger.info("Stock with ID %s updated successfully.", stock_id)

    @classmethod
    def delete_stock(cls, stock_id: int) -> None:
        """
        Delete a stock from the database.

        Args:
            stock_id (int): ID of the stock to delete.

        Raises:
            ValueError: If the stock is not found.
        """
        stock = cls.query.get(stock_id)
        if not stock:
            logger.error("Stock with ID %s not found.", stock_id)
            raise ValueError(f"Stock with ID {stock_id} not found.")

        db.session.delete(stock)
        db.session.commit()
        logger.info("Stock with ID %s deleted successfully.", stock_id)

    @classmethod
    def get_stock_by_symbol(cls, symbol: str) -> dict[str, Any]:
        """
        Retrieve a stock by its symbol.

        Args:
            symbol (str): The ticker symbol of the stock.

        Returns:
            dict: Stock details.

        Raises:
            ValueError: If the stock is not found.
        """
        stock = cls.query.filter_by(symbol=symbol).first()
        if not stock:
            logger.error("Stock with symbol %s not found.", symbol)
            raise ValueError(f"Stock with symbol '{symbol}' not found.")
        return asdict(stock)

    @classmethod
    def get_portfolio_value(cls) -> float:
        """
        Calculate the total value of all stocks in the portfolio.

        Returns:
            float: The total portfolio value based on current prices.

        Note:
            Current prices must be updated via an external API before calling this method.
        """
        stocks = cls.query.all()
        portfolio_value = sum(stock.quantity * (stock.current_price or stock.buy_price) for stock in stocks)
        logger.info("Total portfolio value calculated: $%.2f", portfolio_value)
        return portfolio_value

    @classmethod
    def get_leaderboard(cls, sort_by: str = "value") -> List[dict[str, Any]]:
        """
        Retrieve a leaderboard of stocks sorted by total value or quantity.

        Args:
            sort_by (str): Sorting criteria ('value' or 'quantity').

        Returns:
            List[dict]: List of stocks with stats for leaderboard display.

        Raises:
            ValueError: If the sort_by parameter is invalid.
        """
        if sort_by not in ["value", "quantity"]:
            logger.error("Invalid sort_by parameter: %s", sort_by)
            raise ValueError(f"Invalid sort_by parameter: {sort_by}")

        query = cls.query
        if sort_by == "value":
            query = query.order_by((cls.quantity * (cls.current_price or cls.buy_price)).desc())
        elif sort_by == "quantity":
            query = query.order_by(cls.quantity.desc())

        leaderboard = [
            {
                "id": stock.id,
                "symbol": stock.symbol,
                "name": stock.name,
                "quantity": stock.quantity,
                "current_price": stock.current_price,
                "total_value": round(stock.quantity * (stock.current_price or stock.buy_price), 2),
            }
            for stock in query.all()
        ]
        logger.info("Leaderboard retrieved successfully.")
        return leaderboard

def update_cache_for_stock(mapper, connection, target):
    """
    Update the Redis cache for a stock entry after an update or delete operation.

    This function is intended to be used as an SQLAlchemy event listener for the
    `after_update` and `after_delete` events on the Stock model. When a stock is
    updated or deleted, this function will either update the corresponding Redis
    cache entry with the new stock details or remove the entry if the stock has
    been deleted.

    Args:
        mapper (Mapper): The SQLAlchemy Mapper object (automatically passed by SQLAlchemy).
        connection (Connection): The SQLAlchemy Connection object (automatically passed by SQLAlchemy).
        target (Stock): The instance of the Stock model that was updated or deleted.

    Side-effects:
        - If the stock is deleted, the corresponding cache entry is removed from Redis.
        - If the stock is updated, the Redis cache entry is updated with the latest stock details.
    """
    cache_key = f"stock:{target.id}"  # Unique cache key based on stock ID
    if not target.quantity:  # Assuming 'quantity = 0' implies the stock is effectively deleted
        redis_client.delete(cache_key)
    else:
        redis_client.hset(
            cache_key,
            mapping={k.encode(): str(v).encode() for k, v in asdict(target).items()}
        )

# Register the listener for update and delete events
event.listen(Stock, 'after_update', update_cache_for_stock)
event.listen(Stock, 'after_delete', update_cache_for_stock)