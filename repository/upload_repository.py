from pymongo.database import Database
import logging

logger = logging.getLogger(__name__)

class UploadRepository:
    def __init__(self, db: Database):
        self.collection = db["movies"]

    def bulk_operation(self, operations: list) -> dict:
        if not operations:
            return {"inserted_count": 0, "updated_count": 0}
        result = self.collection.bulk_write(operations, ordered=False)
        return {
            "inserted_count": result.inserted_count + result.upserted_count,
            "updated_count": result.modified_count,
        }
