from services.upload_service import UploadService
from services.movie_service import MovieService
from container.RepositoryContainer import upload_repo, movie_repo


upload_service: UploadService = None
movie_service: MovieService = None

def setup_services():
    global upload_service, movie_service
    upload_service = UploadService(upload_repo)
    movie_service = MovieService(movie_repo)


setup_services()
