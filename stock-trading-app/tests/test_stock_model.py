
import sys
import os
from dataclasses import asdict
import pytest

# Adjust the Python path to include the project root
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from stock_trading.models.stock_model import Stock
from stock_trading.db import db

######################################################
#
#    Fixtures
#
######################################################

@pytest.fixture
def session():
    """Fixture to create a new database session for a test."""
    connection = db.engine.connect()
    transaction = connection.begin()
    session = db.create_scoped_session(options={"bind": connection, "binds": {}})
    db.session = session
    yield session

    transaction.rollback()
    connection.close()
    session.remove()

@pytest.fixture
def mock_redis_client(mocker):
    """Fixture to mock the Redis client."""
    mock_redis = mocker.Mock()
    mocker.patch('stock_trading.models.stock_model.redis_client', mock_redis)
    return mock_redis

######################################################
#
#    Add Stock
#
######################################################

def test_add_stock(session, mock_redis_client):
    """Test adding a stock to the database."""
    Stock.add_stock(symbol="AAPL", name="Apple Inc.", quantity=50, buy_price=150.0)

    stock = Stock.query.filter_by(symbol="AAPL").one()
    assert stock.name == "Apple Inc."
    assert stock.quantity == 50
    assert stock.buy_price == 150.0
    assert stock.current_price is None

def test_add_stock_invalid_quantity(session):
    """Test error when adding stock with invalid quantity."""
    with pytest.raises(ValueError, match="Quantity and buy price must be positive numbers."):
        Stock.add_stock(symbol="GOOGL", name="Alphabet Inc.", quantity=0, buy_price=100.0)

    with pytest.raises(ValueError, match="Quantity and buy price must be positive numbers."):
        Stock.add_stock(symbol="GOOGL", name="Alphabet Inc.", quantity=-10, buy_price=100.0)

def test_add_stock_invalid_buy_price(session):
    """Test error when adding invalid buy price."""
    with pytest.raises(ValueError, match="Quantity and buy price must be positive numbers."):
        Stock.add_stock(symbol="MSFT", name="Microsoft Corp.", quantity=30, buy_price=0.0)

    with pytest.raises(ValueError, match="Quantity and buy price must be positive numbers."):
        Stock.add_stock(symbol="MSFT", name="Microsoft Corp.", quantity=30, buy_price=-250.0)

def test_add_stock_duplicate_symbol(session, mocker, mock_redis_client):
    """Test adding with a duplicate symbol."""
    Stock.add_stock(symbol="TSLA", name="Tesla Inc.", quantity=20, buy_price=700.0)

    # Attempt to add another stock with the same symbol
    with pytest.raises(ValueError, match="Stock with symbol 'TSLA' already exists."):
        Stock.add_stock(symbol="TSLA", name="Tesla Motors", quantity=15, buy_price=720.0)

######################################################
#
#    Update Stock
#
######################################################

def test_update_stock(session, mock_redis_client):
    """Test updating stock attributes."""
    Stock.add_stock(symbol="FB", name="Facebook Inc.", quantity=40, buy_price=200.0)
    stock = Stock.query.filter_by(symbol="FB").one()

    Stock.update_stock(stock_id=stock.id, quantity=60, current_price=210.0)

    updated_stock = Stock.query.get(stock.id)
    assert updated_stock.quantity == 60
    assert updated_stock.current_price == 210.0

def test_update_stock_invalid_attribute(session, mock_redis_client):
    """Test updating stock with invalid attribute."""
    Stock.add_stock(symbol="AMZN", name="Amazon.com Inc.", quantity=25, buy_price=3300.0)
    stock = Stock.query.filter_by(symbol="AMZN").one()

    with pytest.raises(ValueError, match="Invalid attribute: invalid_field"):
        Stock.update_stock(stock_id=stock.id, invalid_field=123)

def test_update_stock_nonexistent(session, mock_redis_client):
    """Test updating nonexistent stock."""
    with pytest.raises(ValueError, match="Stock with ID 999 not found."):
        Stock.update_stock(stock_id=999, quantity=100)

def test_update_stock_triggers_cache_update(session, mocker, mock_redis_client):
    """Test updating triggers cache update in Redis."""
    Stock.add_stock(symbol="NVDA", name="NVIDIA Corp.", quantity=15, buy_price=500.0)
    stock = Stock.query.filter_by(symbol="NVDA").one()

    Stock.update_stock(stock_id=stock.id, current_price=550.0)

    mock_redis_client.hset.assert_called_once_with(
        f"stock:{stock.id}",
        mapping={k.encode(): str(v).encode() for k, v in asdict(stock).items()}
    )

def test_update_stock_with_zero_quantity(session, mocker, mock_redis_client):
    """Test that updating stock to zero triggers cache deletion."""
    Stock.add_stock(symbol="UBER", name="Uber Technologies", quantity=10, buy_price=45.0)
    stock = Stock.query.filter_by(symbol="UBER").one()

    Stock.update_stock(stock_id=stock.id, quantity=0)

    # Verify that Redis cache was deleted
    mock_redis_client.delete.assert_called_once_with(f"stock:{stock.id}")

######################################################
#
#    Delete Stock
#
######################################################

def test_delete_stock(session, mock_redis_client):
    """Test deleting stock from database."""
    Stock.add_stock(symbol="ORCL", name="Oracle Corporation", quantity=30, buy_price=90.0)
    stock = Stock.query.filter_by(symbol="ORCL").one()

    Stock.delete_stock(stock_id=stock.id)

    # Verify the stock is deleted from the database
    deleted_stock = Stock.query.get(stock.id)
    assert deleted_stock is None

def test_delete_stock_nonexistent(session, mock_redis_client):
    """Test deleting nonexistent stock."""
    with pytest.raises(ValueError, match="Stock with ID 999 not found."):
        Stock.delete_stock(stock_id=999)

def test_delete_stock_cache_delete(session, mock_redis_client):
    """Test deleting stock triggers cache removal in Redis."""
    Stock.add_stock(symbol="CRM", name="Salesforce.com", quantity=20, buy_price=250.0)
    stock = Stock.query.filter_by(symbol="CRM").one()

    Stock.delete_stock(stock_id=stock.id)

    # Verify that Redis cache was deleted
    mock_redis_client.delete.assert_called_once_with(f"stock:{stock.id}")

######################################################
#
#    Get Stock by Symbol
#
######################################################

def test_get_stock_by_symbol(session, mock_redis_client):
    """Test retrieving stock its symbol."""
    Stock.add_stock(symbol="INTC", name="Intel Corporation", quantity=100, buy_price=50.0)
    stock = Stock.query.filter_by(symbol="INTC").one()

    result = Stock.get_stock_by_symbol(symbol="INTC")
    expected = asdict(stock)
    assert result == expected

def test_get_stock_symbol_not_found(session, mock_redis_client):
    """Test retrieving stock by a nonexistent symbol."""
    with pytest.raises(ValueError, match="Stock with symbol 'XYZ' not found."):
        Stock.get_stock_by_symbol(symbol="XYZ")

######################################################
#
#    Get Portfolio Value
#
######################################################

def test_get_portfolio_value(session, mock_redis_client):
    """Test calculating the total portfolio value."""
    Stock.add_stock(symbol="AAPL", name="Apple Inc.", quantity=50, buy_price=150.0)
    Stock.add_stock(symbol="GOOGL", name="Alphabet Inc.", quantity=10, buy_price=2800.0)
    Stock.add_stock(symbol="TSLA", name="Tesla Inc.", quantity=5, buy_price=700.0, current_price=750.0)

    portfolio_value = Stock.get_portfolio_value()

    expected_value = (50 * 150.0) + (10 * 2800.0) + (5 * 750.0)
    assert portfolio_value == expected_value

def test_get_portfolio_value_missing_current_price(session, mock_redis_client):
    """Test calculating portfolio value when some stocks lack current_price."""
    Stock.add_stock(symbol="FB", name="Facebook Inc.", quantity=40, buy_price=200.0)
    Stock.add_stock(symbol="AMZN", name="Amazon.com Inc.", quantity=25, buy_price=3300.0)
    Stock.add_stock(symbol="MSFT", name="Microsoft Corp.", quantity=30, buy_price=250.0, current_price=255.0)

    portfolio_value = Stock.get_portfolio_value()

    expected_value = (40 * 200.0) + (25 * 3300.0) + (30 * 255.0)
    assert portfolio_value == expected_value

######################################################
#
#    Get Leaderboard
#
######################################################

def test_get_leaderboard_sort_by_value(session, mock_redis_client):
    """Test retrieving leaderboard by total value."""
    Stock.add_stock(symbol="AAPL", name="Apple Inc.", quantity=50, buy_price=150.0, current_price=155.0)
    Stock.add_stock(symbol="GOOGL", name="Alphabet Inc.", quantity=10, buy_price=2800.0, current_price=2850.0)
    Stock.add_stock(symbol="TSLA", name="Tesla Inc.", quantity=5, buy_price=700.0, current_price=750.0)

    leaderboard = Stock.get_leaderboard(sort_by="value")

    expected_order = ["GOOGL", "AAPL", "TSLA"]
    assert [stock['symbol'] for stock in leaderboard] == expected_order

def test_get_leaderboard_sort_by_quantity(session, mock_redis_client):
    """Test retrieving leaderboard by quantity."""
    Stock.add_stock(symbol="AAPL", name="Apple Inc.", quantity=50, buy_price=150.0)
    Stock.add_stock(symbol="GOOGL", name="Alphabet Inc.", quantity=10, buy_price=2800.0)
    Stock.add_stock(symbol="TSLA", name="Tesla Inc.", quantity=5, buy_price=700.0)

    leaderboard = Stock.get_leaderboard(sort_by="quantity")

    expected_order = ["AAPL", "GOOGL", "TSLA"]
    assert [stock['symbol'] for stock in leaderboard] == expected_order

######################################################
#
#    Update Cache for Stock
#
######################################################

def test_update_cache_for_update(session, mocker, mock_redis_client):
    """Test that updating a stock triggers the Redis cache update."""
    Stock.add_stock(symbol="NFLX", name="Netflix Inc.", quantity=20, buy_price=500.0)
    stock = Stock.query.filter_by(symbol="NFLX").one()

    Stock.update_stock(stock_id=stock.id, current_price=520.0)

    #verify update completed
    mock_redis_client.hset.assert_called_once_with(
        f"stock:{stock.id}",
        mapping={k.encode(): str(v).encode() for k, v in asdict(stock).items()}
    )

def test_update_cache_after_delete(session, mocker, mock_redis_client):
    """Test that deleting a stock triggers the Redis cache deletion."""
    Stock.add_stock(symbol="BABA", name="Alibaba Group", quantity=30, buy_price=200.0)
    stock = Stock.query.filter_by(symbol="BABA").one()

    Stock.delete_stock(stock_id=stock.id)

    #verify delete completed
    mock_redis_client.delete.assert_called_once_with(f"stock:{stock.id}")

def test_update_cache_after_update_zero_quantity(session, mocker, mock_redis_client):
    """Test that updating a stock's quantity to zero triggers cache deletion."""
    Stock.add_stock(symbol="SNAP", name="Snap Inc.", quantity=10, buy_price=60.0)
    stock = Stock.query.filter_by(symbol="SNAP").one()

    #update to 0
    Stock.update_stock(stock_id=stock.id, quantity=0)

    #verify delete completed
    mock_redis_client.delete.assert_called_once_with(f"stock:{stock.id}")

def test_update_cache_after_update_nonzero_quantity(session, mocker, mock_redis_client):
    """Test that updating a stock with non-zero quantity updates the Redis cache."""
    Stock.add_stock(symbol="ADBE", name="Adobe Inc.", quantity=40, buy_price=500.0)
    stock = Stock.query.filter_by(symbol="ADBE").one()

    Stock.update_stock(stock_id=stock.id, current_price=510.0)

    mock_redis_client.hset.assert_called_once_with(
        f"stock:{stock.id}",
        mapping={k.encode(): str(v).encode() for k, v in asdict(stock).items()}
    )
