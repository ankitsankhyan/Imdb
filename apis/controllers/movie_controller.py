from flask import request, jsonify
from container.serviceContainer import movie_service


def get_movies():
      page = int(request.args.get("page", 1))
      page_size = int(request.args.get("page_size", 20))
      year = int(request.args.get("year")) if request.args.get("year") else None
      language = request.args.get("language")
      sort_by = request.args.get("sort_by", "release_date")
      order = request.args.get("order", "desc")

      result = movie_service.get_movies(page, page_size, year, language, sort_by, order)
      return result
