"""Idempotent local demo seed; explicit --reset-admin permits credential rotation."""
import argparse
import os
from datetime import timedelta
from uuid import uuid4

import pandas as pd

from app import create_app
from database import Admin, Prediction, utc_now
from extensions import db


def seed_database(app, reset_admin=False):
    with app.app_context():
        db.create_all()
        username = os.getenv("ADMIN_USERNAME", "admin")
        password = os.getenv("ADMIN_PASSWORD", "Admin@123")
        if app.config["APP_ENV"] == "production" and (password == "Admin@123" or len(password) < 12):
            raise RuntimeError("Set ADMIN_PASSWORD to a unique 12+ character value before production seeding.")
        account = db.session.scalar(db.select(Admin).filter_by(username=username))
        if account is None:
            account = Admin(username=username)
            account.set_password(password)
            db.session.add(account)
        elif reset_admin:
            account.set_password(password)
        frame = pd.read_csv(app.config["DATASET_PATH"]).dropna().sample(n=20, random_state=17)
        service = app.extensions["prediction_service"]
        added = 0
        for index, (_, row) in enumerate(frame.iterrows()):
            key = f"demo-v1-{index:02d}"
            if db.session.scalar(db.select(Prediction.id).filter_by(seed_key=key)):
                continue
            inputs = {key: row[key].item() if hasattr(row[key], "item") else row[key]
                      for key in service.metrics["features"]}
            db.session.add(Prediction(public_id=str(uuid4()), **inputs, **service.predict(inputs),
                                      is_demo=True, seed_key=key,
                                      created_at=utc_now() - timedelta(days=index % 7, hours=index % 5)))
            added += 1
        db.session.commit()
        print(f"Database ready. Admin: {username}. Added {added} demo predictions.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reset-admin", action="store_true", help="Explicitly replace the chosen admin password")
    args = parser.parse_args()
    seed_database(create_app(), args.reset_admin)
