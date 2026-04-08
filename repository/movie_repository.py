from pymongo.database import Database
from pymongo import ASCENDING, DESCENDING


class MovieRepository:
    def __init__(self, db: Database):
        self.collection = db["movies"]

    def find_movies(self, filters: dict, sort_by: str, order: str, page: int, page_size: int) -> list:
        sort_order = ASCENDING if order == "asc" else DESCENDING
        skip = (page - 1) * page_size
        return list(
            self.collection.find(filters, {"_id": 0})
            .sort(sort_by, sort_order)
            .skip(skip)
            .limit(page_size)
        )

    def count_movies(self, filters: dict) -> int:
        return self.collection.count_documents(filters)
