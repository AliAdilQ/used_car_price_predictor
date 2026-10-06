import json
import pandas as pd
import pytest

from config import BASE_DIR
from database import Admin, Prediction
from extensions import db
from seed import seed_database
from tests.conftest import csrf_token


@pytest.mark.parametrize("path, text", [("/", "Know your car"), ("/predict", "The basics"),
                                        ("/about", "Model comparison"), ("/admin/login", "Welcome back")])
def test_public_routes(client, path, text):
    response = client.get(path)
    assert response.status_code == 200
    assert text in response.text


def test_prediction_saved_and_result_private(app, client, vehicle):
    vehicle["csrf_token"] = csrf_token(client, "/predict")
    response = client.post("/predict", data=vehicle)
    assert response.status_code == 302
    result = client.get(response.location)
    assert result.status_code == 200
    assert "USD" in result.text and "Toyota Corolla" in result.text
    with app.app_context():
        saved = db.session.scalar(db.select(Prediction))
        assert 8000 < saved.predicted_price < 35000
        assert saved.price_lower < saved.predicted_price < saved.price_upper
        assert saved.car_age >= 6
        assert saved.model_name == app.extensions["prediction_service"].metrics["selected_model"]
    assert app.test_client().get(response.location).status_code == 404


@pytest.mark.parametrize("field, value", [
    ("year", "1900"), ("year", "9999"), ("year", "not-a-year"),
    ("kilometers_driven", "-1"), ("kilometers_driven", "500001"),
    ("brand", "Unknown"), ("model", "Mustang"), ("fuel_type", "Electric"),
    ("fuel_type", "Diesel"), ("transmission", "Unknown"), ("owner_type", "Unknown"),
    ("engine", "0"), ("power", "900"), ("mileage", "0"), ("mileage", "nan"),
    ("power", "inf"), ("seats", "20"), ("location", "Unknown"),
])
def test_invalid_inputs_rejected(app, client, vehicle, field, value):
    vehicle[field] = value
    vehicle["csrf_token"] = csrf_token(client, "/predict")
    response = client.post("/predict", data=vehicle)
    assert response.status_code == 422
    with app.app_context():
        assert db.session.scalar(db.select(db.func.count(Prediction.id))) == 0


def test_prediction_requires_csrf(client, vehicle):
    assert client.post("/predict", data=vehicle).status_code == 400


@pytest.mark.parametrize("path", ["/admin/", "/admin/predictions", "/admin/dataset"])
def test_admin_routes_protected(client, path):
    response = client.get(path)
    assert response.status_code == 302
    assert response.location.endswith("/admin/login")


def test_admin_login_and_pages(logged_in):
    for path in ["/admin/", "/admin/predictions", "/admin/dataset"]:
        assert logged_in.get(path).status_code == 200
    response = logged_in.post("/admin/logout", data={"csrf_token": csrf_token(logged_in, "/admin/")})
    assert response.status_code == 302
    assert logged_in.get("/admin/").status_code == 302


def test_invalid_login_and_throttle(client):
    for attempt in range(6):
        response = client.post("/admin/login", data={"csrf_token": csrf_token(client, "/admin/login"),
                                                   "username": "admin", "password": "wrong"})
        assert response.status_code == (429 if attempt == 5 else 401)
    assert client.get("/admin/").status_code == 302


def test_password_is_hashed(app):
    with app.app_context():
        account = db.session.scalar(db.select(Admin))
        assert "Admin@123" not in account.password_hash
        assert account.check_password("Admin@123")
        assert not account.check_password("wrong")


def test_seed_is_idempotent(app):
    seed_database(app)
    seed_database(app)
    with app.app_context():
        assert db.session.scalar(db.select(db.func.count(Prediction.id))) == 20
        assert db.session.scalar(db.select(db.func.count(Admin.id))) == 1
        assert all(item.is_demo for item in db.session.scalars(db.select(Prediction)))


def test_search_sort_pagination(app, logged_in):
    seed_database(app)
    response = logged_in.get("/admin/predictions?q=Toyota&sort=price_high")
    assert response.status_code == 200
    assert "Toyota" in response.text
    page_two = logged_in.get("/admin/predictions?page=2")
    assert page_two.status_code == 200
    assert "Showing 11–20 of 20" in page_two.text
    assert "No predictions found" in logged_in.get("/admin/predictions?q=not-present").text


def test_delete_and_clear_require_csrf_and_confirmation(app, logged_in):
    seed_database(app)
    with app.app_context():
        prediction_id = db.session.scalar(db.select(Prediction.id))
    target = f"/admin/predictions/{prediction_id}/delete"
    assert logged_in.get(target).status_code == 405
    assert logged_in.post(target).status_code == 400
    token = csrf_token(logged_in, "/admin/predictions")
    assert logged_in.post(target, data={"csrf_token": token}).status_code == 302
    logged_in.post("/admin/predictions/clear", data={"csrf_token": token, "confirmation": "wrong"})
    with app.app_context():
        assert db.session.scalar(db.select(db.func.count(Prediction.id))) == 19
    logged_in.post("/admin/predictions/clear", data={"csrf_token": token, "confirmation": "CLEAR"})
    with app.app_context():
        assert db.session.scalar(db.select(db.func.count(Prediction.id))) == 0


def test_error_and_security_headers(client):
    response = client.get("/missing-page")
    assert response.status_code == 404 and "A SMALL DETOUR" in response.text
    assert response.headers["X-Frame-Options"] == "DENY"
    assert "form-action 'self'" in response.headers["Content-Security-Policy"]


def test_local_assets_load(client):
    for name in ["css/style.css", "js/main.js", "js/charts.js", "images/hero-car.png",
                 "images/icons.svg", "fonts/manrope.ttf", "vendor/bootstrap.min.css", "vendor/chart.umd.min.js"]:
        assert client.get("/static/" + name).status_code == 200


def test_model_artifacts_and_dataset():
    metrics = json.loads((BASE_DIR / "models/model_metrics.json").read_text())
    frame = pd.read_csv(BASE_DIR / "data/used_cars.csv")
    assert len(frame) >= 1000
    assert len(frame.brand.unique()) == 12
    assert len(metrics["validation_models"]) == 3
    winner = max(metrics["validation_models"], key=lambda item: (item["r2"], -item["rmse"]))
    assert metrics["selected_model"] == winner["name"]
    assert metrics["test_metrics"]["r2"] > .8
    assert sum(metrics["split"][key] for key in ["training", "validation", "test"]) == len(frame)


def test_readme_images_exist():
    import re
    readme = (BASE_DIR / "README.md").read_text(encoding="utf-8")
    images = re.findall(r'!\[[^\]]*\]\((docs/screenshots/[^)]+)\)', readme)
    assert len(set(images)) >= 6
    assert all((BASE_DIR / image).exists() for image in images)
