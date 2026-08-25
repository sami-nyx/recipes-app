import os

import pytest
import requests


# ============================================================
# Base API URL
# ============================================================

@pytest.fixture(scope="session")
def base_url():
    """
    Base URL of the Recipes API.

    Defaults to localhost so the integration tests can be run
    directly from the developer machine.

    Docker Compose / CI can override this with API_BASE_URL.
    """

    return os.getenv(
        "API_BASE_URL",
        "http://localhost"
    ).rstrip("/")


# ============================================================
# Shared HTTP session
# ============================================================

@pytest.fixture
def api_session():
    """
    Provide a requests Session for integration tests.
    """

    session = requests.Session()

    yield session

    session.close()


# ============================================================
# Primary authenticated test user
# ============================================================

@pytest.fixture
def auth_headers(base_url, api_session):
    """
    Register a unique test user and return its Authorization header.
    """

    suffix = os.urandom(4).hex()

    user_data = {
        "name": "Integration Test User",
        "username": f"integration_{suffix}",
        "email": f"integration_{suffix}@example.com",
        "password": "SecurePassword123!"
    }

    response = api_session.post(
        f"{base_url}/api/users/register",
        json=user_data
    )

    assert response.status_code == 201, response.text

    token = response.json()["accessToken"]

    return {
        "Authorization": f"Bearer {token}"
    }


# ============================================================
# Secondary authenticated test user
# ============================================================

@pytest.fixture
def second_auth_headers(base_url, api_session):
    """
    Register a second unique user.

    Used to test ownership and authorization boundaries.
    """

    suffix = os.urandom(4).hex()

    user_data = {
        "name": "Second Integration User",
        "username": f"second_{suffix}",
        "email": f"second_{suffix}@example.com",
        "password": "SecurePassword123!"
    }

    response = api_session.post(
        f"{base_url}/api/users/register",
        json=user_data
    )

    assert response.status_code == 201, response.text

    token = response.json()["accessToken"]

    return {
        "Authorization": f"Bearer {token}"
    }