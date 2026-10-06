"""SQLite tables. Prices are USD; timestamps are stored in UTC."""
from datetime import datetime, timezone

from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Prediction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(36), unique=True, nullable=False, index=True)
    brand = db.Column(db.String(40), nullable=False, index=True)
    model = db.Column(db.String(40), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    kilometers_driven = db.Column(db.Integer, nullable=False)
    fuel_type = db.Column(db.String(20), nullable=False)
    transmission = db.Column(db.String(20), nullable=False)
    owner_type = db.Column(db.String(20), nullable=False)
    engine = db.Column(db.Integer, nullable=False)
    mileage = db.Column(db.Float, nullable=False)
    power = db.Column(db.Float, nullable=False)
    seats = db.Column(db.Integer, nullable=False)
    car_age = db.Column(db.Integer, nullable=False)
    location = db.Column(db.String(40), nullable=False)
    predicted_price = db.Column(db.Float, nullable=False)
    price_lower = db.Column(db.Float, nullable=False)
    price_upper = db.Column(db.Float, nullable=False)
    model_name = db.Column(db.String(80), nullable=False)
    is_demo = db.Column(db.Boolean, default=False, nullable=False)
    seed_key = db.Column(db.String(40), unique=True)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False, index=True)
