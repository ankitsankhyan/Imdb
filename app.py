from flask import Flask, jsonify
from flasgger import Swagger
from config import AppConfig
from container.infroContainer import db
from apis.routes import register_blueprints
from config.logger_config import setup_logging

setup_logging()
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = AppConfig.MAX_CONTENT_LENGTH
app.config["SWAGGER"] = {"title": "IMDB Content API", "uiversion": 3}
Swagger(app)


# Register all routes
register_blueprints(app)


@app.route("/test", methods=["GET"])
def test():
    return jsonify({"message": "Hello, World!"})


if __name__ == "__main__":
    app.run(debug=AppConfig.DEBUG)
