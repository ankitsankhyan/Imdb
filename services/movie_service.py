import logging
import math
from repository.movie_repository import MovieRepository

logger = logging.getLogger(__name__)

ALLOWED_SORT_FIELDS = {"release_date", "vote_average"}
ALLOWED_ORDER = {"asc", "desc"}
MAX_PAGE_SIZE = 100


class MovieService:
    def __init__(self, movie_repo: MovieRepository):
        self.movie_repo = movie_repo

    def get_movies(self, page: int, page_size: int, year: int, language: str, sort_by: str, order: str) -> dict:
        if sort_by not in ALLOWED_SORT_FIELDS:
            raise ValueError(f"Invalid sort_by value. Allowed: {', '.join(sorted(ALLOWED_SORT_FIELDS))}")

        if order not in ALLOWED_ORDER:
            raise ValueError(f"Invalid order value. Allowed: asc, desc")

        page_size = min(page_size, MAX_PAGE_SIZE)

        filters = {}
        if year:
            filters["release_year"] = year
        if language:
            filters["original_language"] = language

        movies = self.movie_repo.find_movies(filters, sort_by, order, page, page_size)
        total_records = self.movie_repo.count_movies(filters)
        total_pages = math.ceil(total_records / page_size) if page_size else 1

        return {
            "data": movies,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_records": total_records,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1,
            },
        }
