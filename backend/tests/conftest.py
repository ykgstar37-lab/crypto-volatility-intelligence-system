import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Use a separate test database file
TEST_DB = "sqlite:///./data/test.db"
os.environ["DATABASE_URL"] = TEST_DB

from app.database import Base, get_db
from app.main import app


@pytest.fixture(autouse=True)
def _clean_db():
    """Create fresh tables for each test."""
    eng = create_engine(TEST_DB, connect_args={"check_same_thread": False})
    Base.metadata.drop_all(bind=eng)
    Base.metadata.create_all(bind=eng)
    yield
    Base.metadata.drop_all(bind=eng)
    eng.dispose()


@pytest.fixture
def db():
    eng = create_engine(TEST_DB, connect_args={"check_same_thread": False})
    Session = sessionmaker(bind=eng)
    session = Session()
    yield session
    session.close()
    eng.dispose()


@pytest.fixture
def client(db):
    from fastapi.testclient import TestClient

    def _override_get_db():
        yield db

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()
