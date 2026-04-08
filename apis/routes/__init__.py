from apis.routes.upload_routes import upload_routes
from apis.routes.movie_routes import movie_routes

def register_blueprints(app):
    app.register_blueprint(upload_routes)
    app.register_blueprint(movie_routes)
