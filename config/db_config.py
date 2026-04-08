from pymongo import MongoClient, ASCENDING
from pymongo.errors import OperationFailure
from config.app_config import AppConfig


class DBConfig:
    def __init__(self):
        client = MongoClient(AppConfig.MONGO_URI)
        self.db = client[AppConfig.DB_NAME]
        self._setup_indexes()

    def _setup_indexes(self):
        movies = self.db["movies"]
        try:
            movies.create_index(
                [("original_title", ASCENDING), ("release_date",  ASCENDING)],
                unique=True,
            )
            movies.create_index([("release_year", ASCENDING)])
            movies.create_index([("original_language", ASCENDING)])
            movies.create_index([("vote_average", ASCENDING)])
            movies.create_index([("release_date", ASCENDING)])
            movies.create_index(
                [("original_language", ASCENDING), ("release_year", ASCENDING)]
            )
        except OperationFailure as e:
            raise RuntimeError(f"Failed to create indexes: {e}")
