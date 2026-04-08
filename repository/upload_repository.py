from pymongo.database import Database


class UploadRepository:
    def __init__(self, db: Database):
        self.collection = db["movies"]

    def bulk_operation(self, operations: list) -> int:
        if not operations:
            return 0
        result = self.collection.bulk_write(operations, ordered=False)
        return result.upserted_count + result.modified_count + result.inserted_count
