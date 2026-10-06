"""Flask application factory and local development entry point."""
import os
import secrets
from pathlib import Path

from flask import Flask, render_template
from flask_wtf.csrf import CSRFError

from config import BASE_DIR, Config
from extensions import csrf, db
from services.prediction_service import PredictionService


def create_app(test_config=None):
    app = Flask(__name__, instance_path=str(BASE_DIR / "instance"))
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)
    Path(app.instance_path).mkdir(exist_ok=True)
    secret = app.config.get("SECRET_KEY")
    placeholders = {"change-this-secret-key", "replace-with-a-random-secret-generated-by-python"}
    if not secret or secret in placeholders:
        if app.config["APP_ENV"] == "production":
            raise RuntimeError("Set a unique SECRET_KEY before production startup.")
        key_file = Path(app.instance_path) / ".secret_key"
        if not key_file.exists():
            try:
                with key_file.open("x", encoding="utf-8") as stream:
                    stream.write(secrets.token_hex(32))
            except FileExistsError:
                pass
        app.config["SECRET_KEY"] = key_file.read_text(encoding="utf-8").strip()
    db.init_app(app)
    csrf.init_app(app)
    app.extensions["prediction_service"] = PredictionService(
        Path(app.config["MODEL_PATH"]), Path(app.config["METRICS_PATH"]))
    from routes.main import main
    from routes.admin import admin
    app.register_blueprint(main)
    app.register_blueprint(admin)
    with app.app_context():
        db.create_all()

    @app.template_filter("money")
    def money(value):
        return f"${value:,.0f}"

    @app.context_processor
    def shared_context():
        return {"metrics": app.extensions["prediction_service"].metrics,
                "github_url": "https://github.com/AliAdilQ/used_car_price_predictor"}

    @app.after_request
    def secure_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; img-src 'self' data:; style-src 'self'; "
            "font-src 'self'; script-src 'self'; connect-src 'self'; "
            "frame-ancestors 'none'; form-action 'self'; base-uri 'self'")
        if response.headers.get("Content-Type", "").startswith("text/html"):
            response.headers["Cache-Control"] = "no-store"
        if app.config["APP_ENV"] == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000"
        return response

    @app.errorhandler(404)
    def not_found(error):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def server_error(error):
        db.session.rollback()
        return render_template("500.html"), 500

    @app.errorhandler(CSRFError)
    def csrf_error(error):
        return render_template("400.html", message="Your session expired. Reload the page and try again."), 400

    return app


if __name__ == "__main__":
    application = create_app()
    application.run(host=os.getenv("HOST", "127.0.0.1"),
                    port=int(os.getenv("PORT", "5000")),
                    debug=os.getenv("FLASK_DEBUG", "0") == "1")
