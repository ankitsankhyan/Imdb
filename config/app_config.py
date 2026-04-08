import os
from dotenv import load_dotenv

load_dotenv()


class AppConfig:
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    DB_NAME = os.getenv("DB_NAME", "imdb")
    BATCH_SIZE = int(os.getenv("BATCH_SIZE", 1000))
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024 * 1024
