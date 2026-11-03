"""A self-hosted PAET opens without a login; a web one never does."""

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
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False},
                           poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with sessionmaker(bind=engine)() as session:
        yield session


@pytest.fixture
def client(db):
    from app.main import app

    app.dependency_overrides[get_db] = lambda: db
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_web_mode_has_no_local_login(client, db, monkeypatch):
    monkeypatch.setattr(settings, "DEPLOY_MODE", "web")
    assert client.post("/api/v1/auth/local-login").status_code == 404
    assert db.query(User).count() == 0


def test_local_mode_always_opens_the_same_student(client, db, monkeypatch):
    monkeypatch.setattr(settings, "DEPLOY_MODE", "local")
    first = client.post("/api/v1/auth/local-login").json()["access_token"]
    client.post("/api/v1/auth/local-login")

    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {first}"})
    assert me.status_code == 200
    assert db.query(User).count() == 1
