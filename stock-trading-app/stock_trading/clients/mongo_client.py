import logging
import os
from typing import Any

from pymongo import MongoClient
from pymongo.database import Database  # Add this import


from stock_trading.utils.logger import configure_logger


logger = logging.getLogger(__name__)
configure_logger(logger)


MONGO_HOST = os.environ.get('MONGO_HOST', 'localhost')
MONGO_PORT = int(os.environ.get('MONGO_PORT', 27017))

logger.info("Connecting to MongoDB at %s:%d", MONGO_HOST, MONGO_PORT)
mongo_client = MongoClient(host=MONGO_HOST, port=MONGO_PORT)
db = mongo_client['stock_trading']
sessions_collection = db['sessions']
portfolios_collection = db['portfolios']  # Add this line

def get_mongo_client() -> Database[Any]:
    """
    Get the MongoDB client instance.
    
    Returns:
        Database: The MongoDB database instance.
    """
    return db

# Initialize indexes for portfolios collection
portfolios_collection.create_index('user_id', unique=True)
