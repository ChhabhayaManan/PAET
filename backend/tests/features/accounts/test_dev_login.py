"""The dev-login bypass. The tests that matter are the two that prove it is OFF."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.database import Base, get_db
from app.features.accounts.models import User


@pytest.fixture
def db():
    # StaticPool: TestClient serves the request on another thread, which would
    # otherwise open a second, empty in-memory database.
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with sessionmaker(bind=engine)() as session:
        yield session


@pytest.fixture
def user(db):
    u = User(email="dev@example.com", username="devuser", hashed_password="x")
    db.add(u)
    db.commit()
    return u


@pytest.fixture
def client(db):
    from app.main import app

    app.dependency_overrides[get_db] = lambda: db
    # Constructed without `with`, so the lifespan never runs against the real DB.
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def enabled(monkeypatch, user):
    monkeypatch.setattr(settings, "DEBUG", True)
    monkeypatch.setattr(settings, "DEV_LOGIN_EMAIL", user.email)


def test_disabled_without_the_setting(client, monkeypatch, user):
    monkeypatch.setattr(settings, "DEBUG", True)
    monkeypatch.setattr(settings, "DEV_LOGIN_EMAIL", "")
    assert client.post("/api/v1/auth/dev-login").status_code == 404


def test_disabled_when_debug_is_off(client, monkeypatch, user):
    monkeypatch.setattr(settings, "DEBUG", False)
    monkeypatch.setattr(settings, "DEV_LOGIN_EMAIL", user.email)
    assert client.post("/api/v1/auth/dev-login").status_code == 404


def test_returns_tokens_without_password_or_otp(client, enabled):
    response = client.post("/api/v1/auth/dev-login")
    assert response.status_code == 200
    body = response.json()
    assert body["access_token"] and body["refresh_token"]
    assert body["token_type"] == "bearer"


def test_the_token_authenticates(client, enabled):
    token = client.post("/api/v1/auth/dev-login").json()["access_token"]
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "dev@example.com"


def test_unknown_email_is_rejected(client, monkeypatch, user):
    monkeypatch.setattr(settings, "DEBUG", True)
    monkeypatch.setattr(settings, "DEV_LOGIN_EMAIL", "nobody@example.com")
    assert client.post("/api/v1/auth/dev-login").status_code == 401


def test_inactive_user_is_rejected(client, enabled, db, user):
    user.is_active = False
    db.commit()
    assert client.post("/api/v1/auth/dev-login").status_code == 401


def test_availability_probe_404s_when_disabled(client, monkeypatch, user):
    monkeypatch.setattr(settings, "DEBUG", True)
    monkeypatch.setattr(settings, "DEV_LOGIN_EMAIL", "")
    assert client.get("/api/v1/auth/dev-login").status_code == 404


def test_availability_probe_names_the_account(client, enabled):
    response = client.get("/api/v1/auth/dev-login")
    assert response.status_code == 200
    assert response.json()["message"] == "dev@example.com"
