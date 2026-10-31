import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_password_reset_token, decode_token

client = TestClient(app)


def test_forgot_password_generic_response():
    # User that does not exist
    res = client.post("/api/v1/auth/forgot-password", json={"identifier": "nonexistent@shuleconnect.co.tz"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "instructions have been dispatched" in data["message"]

    # User that does exist (admin)
    res_admin = client.post("/api/v1/auth/forgot-password", json={"identifier": "admin@shuleconnect.co.tz"})
    assert res_admin.status_code == 200
    data_admin = res_admin.json()
    assert data_admin["status"] == "success"
    assert data_admin["dev_reset_token"] is not None


def test_reset_password_invalid_token():
    res = client.post("/api/v1/auth/reset-password", json={"token": "invalid_token_xyz", "new_password": "NewSecretPassword2026!"})
    assert res.status_code == 400
    assert "invalid or has expired" in res.json()["detail"]
