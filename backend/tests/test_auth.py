from datetime import timedelta

import jwt
from app.core.config import get_settings
from app.core.security import create_access_token
from fastapi.testclient import TestClient


def test_login_ok(client: TestClient):
    r = client.post("/api/auth/login", json={"secret": "test"})
    assert r.status_code == 200
    data = r.json()
    assert data["token_type"] == "bearer"  # noqa: S105
    payload = jwt.decode(
        data["access_token"], get_settings().jwt_secret_key, algorithms=["HS256"]
    )
    assert (payload["user_id"], payload["username"]) == (1, "Torben")
    assert payload["exp"] - payload["iat"] == 365 * 24 * 3600


def test_login_wrong_secret(client: TestClient):
    r = client.post("/api/auth/login", json={"secret": "wrong"})
    assert r.status_code == 401
    assert r.json()["detail"] == "Invalid credentials"


def test_login_validation(client: TestClient):
    assert client.post("/api/auth/login", json={"secret": ""}).status_code == 422
    assert client.post("/api/auth/login", json={}).status_code == 422


def test_protected_requires_token(client: TestClient):
    assert client.get("/api/boards").status_code in {401, 403}


def test_expired_token(client: TestClient):
    token = create_access_token(1, "Torben", expires_delta=timedelta(seconds=-1))
    r = client.get("/api/boards", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401
    assert r.json()["detail"] == "Token has expired"


def test_wrong_signature_and_missing_claims(client: TestClient):
    bad = jwt.encode({"user_id": 1, "username": "x"}, "x" * 40, algorithm="HS256")
    no_user = jwt.encode({"foo": 1}, get_settings().jwt_secret_key, algorithm="HS256")
    for token in (bad, no_user, "garbage"):
        r = client.get("/api/boards", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 401
        assert r.json()["detail"] == "Could not validate credentials"
