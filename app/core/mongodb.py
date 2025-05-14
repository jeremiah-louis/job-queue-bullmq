from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError, ConfigurationError
import os
import logging

logger = logging.getLogger(__name__)

class MongoDB:
    _instance = None
    _client = None
    _db = None
    _collection = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDB, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if self._client is None:
            try:
                # Get MongoDB configuration from environment variables
                mongo_uri = os.getenv("MONGO_URI")
                db_name = os.getenv("MONGO_DB_NAME")
                collection_name = os.getenv("MONGO_COLLECTION_NAME")

                if not all([mongo_uri, db_name, collection_name]):
                    raise ConfigurationError("Required MongoDB environment variables are not set")

                # Initialize MongoDB client
                self._client = MongoClient(mongo_uri)
                self._db = self._client[db_name]
                self._collection = self._db[collection_name]

                # Create indexes
                self._collection.create_index("job_id", unique=True)
                self._collection.create_index("status")

                logger.info("MongoDB connection established successfully")
            except (ServerSelectionTimeoutError, ConfigurationError) as e:
                logger.error(f"MongoDB connection error: {str(e)}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error during MongoDB setup: {str(e)}")
                raise

    @property
    def collection(self):
        if self._collection is None:
            raise ServerSelectionTimeoutError("MongoDB connection not initialized")
        return self._collection

    def close(self):
        if self._client:
            self._client.close()
            self._client = None
            self._db = None
            self._collection = None
            logger.info("MongoDB connection closed") 