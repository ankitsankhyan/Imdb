import logging
from flask import Blueprint, jsonify
from apis.controllers.movie_controller import get_movies

logger = logging.getLogger(__name__)

movie_routes = Blueprint("movie_routes", __name__, url_prefix="/api/movies")


@movie_routes.route("/", methods=["GET"])
def fetch_movies():
    """
    Get paginated list of movies
    ---
    tags:
      - Movies
    parameters:
      - name: page
        in: query
        type: integer
        default: 1
      - name: page_size
        in: query
        type: integer
        default: 20
      - name: year
        in: query
        type: integer
      - name: language
        in: query
        type: string
      - name: sort_by
        in: query
        type: string
        default: release_date
        enum: [release_date, vote_average]
      - name: order
        in: query
        type: string
        default: desc
        enum: [asc, desc]
    responses:
      200:
        description: Paginated list of movies
      400:
        description: Invalid query parameters
      500:
        description: Internal server error
    """
    try:
        return jsonify(get_movies()), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error fetching movies: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500
