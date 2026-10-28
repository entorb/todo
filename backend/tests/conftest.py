import os

os.environ["JWT_SECRET_KEY"] = "test-secret-test-secret-test-secret-42"  # noqa: S105
os.environ.setdefault("APP_ENV", "Local")

from collections.abc import Iterator
from pathlib import Path

import bcrypt
import pytest
from app import crud
from app.core.config import get_settings
from app.core.db import get_engine
from app.main import app
from app.models import User
from fastapi.testclient import TestClient
from sqlmodel import Session

# low cost factor: fast tests
HASH_TEST = bcrypt.hashpw(b"test", bcrypt.gensalt(rounds=4)).decode()
HASH_OTHER = bcrypt.hashpw(b"other", bcrypt.gensalt(rounds=4)).decode()


@pytest.fixture(autouse=True)
def _tmp_db(tmp_path: Path) -> Iterator[None]:
    """Fresh SQLite DB per test, user 1 'Torben' (secret test), user 2 (other)."""
    os.environ["DB_PATH"] = str(tmp_path / "test.db")
    get_settings.cache_clear()
    get_engine.cache_clear()
    crud.init_db()
    with Session(get_engine()) as s:
        user = s.get(User, 1)
        assert user is not None
        user.secret_hashed = HASH_TEST
        s.add(user)
        s.add(User(id=2, name="Other", secret_hashed=HASH_OTHER))
        s.commit()
    yield
    get_engine().dispose()


@pytest.fixture
def session() -> Iterator[Session]:
    with Session(get_engine()) as s:
        yield s


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as c:
        yield c


def _headers(client: TestClient, secret: str) -> dict[str, str]:
    r = client.post("/api/auth/login", json={"secret": secret})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def auth_headers(client: TestClient) -> dict[str, str]:
    return _headers(client, "test")


@pytest.fixture
def other_headers(client: TestClient) -> dict[str, str]:
    return _headers(client, "other")
