"""Environment configuration shared by CLI tools and the application."""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


class Config:
    APP_ENV = os.getenv("APP_ENV", "development")
    SECRET_KEY = os.getenv("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = "sqlite:///app.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = APP_ENV == "production"
    MAX_CONTENT_LENGTH = 32 * 1024
    PERMANENT_SESSION_LIFETIME = 60 * 60
    WTF_CSRF_TIME_LIMIT = 3600
    MODEL_PATH = BASE_DIR / "models" / "car_price_model.pkl"
    METRICS_PATH = BASE_DIR / "models" / "model_metrics.json"
    DATASET_PATH = BASE_DIR / "data" / "used_cars.csv"
