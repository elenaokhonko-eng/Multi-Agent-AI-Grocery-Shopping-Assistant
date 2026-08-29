import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

# Ensure packages and apps are in sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir / "packages") not in sys.path:
    sys.path.insert(0, str(root_dir / "packages"))
if str(root_dir / "apps") not in sys.path:
    sys.path.insert(0, str(root_dir / "apps"))

from apps.api.main import app, get_session  # noqa: E402

# In-memory shared engine per test session with StaticPool
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

def override_get_session():
    with Session(test_engine) as session:
        yield session

app.dependency_overrides[get_session] = override_get_session

@pytest.fixture(autouse=True)
def db_session():
    SQLModel.metadata.create_all(test_engine)
    yield
    SQLModel.metadata.drop_all(test_engine)

@pytest.fixture
def client():
    return TestClient(app)
