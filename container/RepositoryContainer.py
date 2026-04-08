from repository.upload_repository import UploadRepository
from repository.movie_repository import MovieRepository
from container.infroContainer import db


upload_repo: UploadRepository = None
movie_repo: MovieRepository = None

def setup_repositories():
    global upload_repo, movie_repo
    upload_repo = UploadRepository(db)
    movie_repo = MovieRepository(db)

setup_repositories()