# test/backend/recipes-api-test/conftest.py
import os
import pytest
import requests

@pytest.fixture(scope="session")
def base_url():
    """Reads API target host from ENV, defaulting to Docker mapped port."""
    return os.getenv("API_BASE_URL", "http://localhost:5001")

@pytest.fixture(scope="session")
def api_session():
    """Reusable HTTP session with standard headers."""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Accept": "application/json"
    })
    return session

@pytest.fixture
def auth_headers(base_url, api_session):
    """Utility fixture to register/login a user and yield dynamic Bearer Auth headers."""
    unique_user = f"testuser_{os.urandom(4).hex()}"
    user_payload = {
        "name": "Integration Tester",
        "username": unique_user,
        "email": f"{unique_user}@example.com",
        "password": "Password123!"
    }

    # Register
    api_session.post(f"{base_url}/api/users/register", json=user_payload)

    # Login
    login_res = api_session.post(f"{base_url}/api/users/login", json={
        "usernameOrEmail": unique_user,
        "password": "Password123!"
    })

    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    token = login_res.json().get("accessToken")
    assert token, "accessToken missing from response body"

    return {"Authorization": f"Bearer {token}"}