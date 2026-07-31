"""Pytest fixtures for the REST API test suite.

Sets up an isolated in-memory SQLite database per test and a FastAPI
TestClient with the database dependency overridden, so tests never touch
the real home_lab_manager.db file.
"""

import os
import sys
from pathlib import Path

# Must run before importing any app module — config.py reads env at import time.
os.environ["DATABASE_URL"] = "sqlite:////tmp/home_lab_manager_test.db"
os.environ["API_KEY"] = "test-api-key"
os.environ["UNIFI_API_KEY"] = ""
os.environ["UNIFI_BASE_URL"] = ""
os.environ["UNIFI_SITE_ID"] = ""
os.environ["UNIFI_CLOUD_API_KEY"] = ""

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401 — ensure all models are registered on Base
from app.api.app import api
from app.api.deps import get_db
from app.database.db import Base

TEST_API_KEY = "test-api-key"


@pytest.fixture
def db_session():
    """A fresh in-memory SQLAlchemy session for direct service tests."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = TestSession()
    yield session
    session.close()
    engine.dispose()


@pytest.fixture
def client():
    """FastAPI TestClient with a fresh in-memory DB per test."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    def override_get_db():
        session = TestSession()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    api.dependency_overrides[get_db] = override_get_db
    with TestClient(api) as c:
        yield c
    api.dependency_overrides.clear()
    engine.dispose()


@pytest.fixture
def auth(client):
    """Valid X-API-KEY header for authenticated requests."""
    return {"X-API-KEY": TEST_API_KEY}
