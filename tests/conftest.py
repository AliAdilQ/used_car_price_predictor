import html
import re

import pytest

from app import create_app
from database import Admin
from extensions import db


@pytest.fixture
def app():
    application = create_app({
        "TESTING": True, "SECRET_KEY": "isolated-test-secret-key",
        "APP_ENV": "testing", "SESSION_COOKIE_SECURE": False,
        "SQLALCHEMY_DATABASE_URI": "sqlite://",
    })
    with application.app_context():
        account = Admin(username="admin")
        account.set_password("Admin@123")
        db.session.add(account)
        db.session.commit()
    yield application
    with application.app_context():
        db.session.remove()
        db.engine.dispose()


@pytest.fixture
def client(app):
    return app.test_client()


def csrf_token(client, path):
    response = client.get(path)
    token = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', response.text)
    assert token, f"CSRF input missing from {path}"
    return html.unescape(token.group(1))


@pytest.fixture
def vehicle():
    return dict(brand="Toyota", model="Corolla", year="2020", kilometers_driven="48000",
                fuel_type="Petrol", transmission="Automatic", owner_type="First",
                engine="1800", mileage="17", power="139", seats="5", location="Los Angeles")


@pytest.fixture
def logged_in(client):
    response = client.post("/admin/login", data={"csrf_token": csrf_token(client, "/admin/login"),
                                               "username": "admin", "password": "Admin@123"})
    assert response.status_code == 302
    return client
