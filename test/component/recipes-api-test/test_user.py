# test/backend/recipes-api-test/test_user.py

import os


# ============================================================
# Test Helpers
# ============================================================

def build_unique_user(prefix="user"):
    unique_suffix = os.urandom(4).hex()

    return {
        "name": "HTTP Test User",
        "username": f"{prefix}_{unique_suffix}",
        "email": f"{prefix}_{unique_suffix}@example.com",
        "password": "SecurePassword123!",
        "bio": "Testing API endpoints with pure JSON",
        "avatarUrl": "https://example.com/avatar.png"
    }


def register_user(base_url, api_session, user_data=None):
    if user_data is None:
        user_data = build_unique_user()

    response = api_session.post(
        f"{base_url}/api/users/register",
        json=user_data
    )

    assert response.status_code == 201, response.text

    data = response.json()

    assert "user" in data
    assert "accessToken" in data

    return user_data, data


def auth_headers(token):
    return {
        "Authorization": f"Bearer {token}"
    }


# ============================================================
# Registration and login
# ============================================================

def test_user_registration_and_login(base_url, api_session):
    user_data, register_data = register_user(
        base_url,
        api_session
    )

    assert register_data["user"]["username"] == user_data["username"]
    assert register_data["user"]["email"] == user_data["email"]

    login_payload = {
        "usernameOrEmail": user_data["username"],
        "password": user_data["password"]
    }

    login_res = api_session.post(
        f"{base_url}/api/users/login",
        json=login_payload
    )

    assert login_res.status_code == 200, login_res.text

    login_data = login_res.json()

    assert "accessToken" in login_data
    assert login_data["user"]["username"] == user_data["username"]


# ============================================================
# Duplicate registration
# ============================================================

def test_duplicate_user_registration_fails(base_url, api_session):
    duplicate_payload = {
        "name": "Duplicate User",
        "username": "test-user",
        "email": "dup@example.com",
        "password": "Password123!"
    }

    response = api_session.post(
        f"{base_url}/api/users/register",
        json=duplicate_payload
    )

    assert response.status_code == 409, response.text
    assert response.json()["message"] == "Username is already taken"


# ============================================================
# Update user - own profile
# ============================================================

def test_user_can_update_own_profile(base_url, api_session):
    _, register_data = register_user(
        base_url,
        api_session,
        build_unique_user("update")
    )

    user_id = register_data["user"]["id"]
    token = register_data["accessToken"]

    update_payload = {
        "name": "Updated HTTP User",
        "bio": "Updated integration-test bio",
        "avatarUrl": "https://example.com/new-avatar.png"
    }

    response = api_session.patch(
        f"{base_url}/api/users/{user_id}",
        json=update_payload,
        headers=auth_headers(token)
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["user"]["name"] == update_payload["name"]
    assert data["user"]["bio"] == update_payload["bio"]
    assert data["user"]["avatarUrl"] == update_payload["avatarUrl"]


# ============================================================
# Update user - immutable fields
# ============================================================

def test_user_cannot_update_email_or_username(base_url, api_session):
    _, register_data = register_user(
        base_url,
        api_session,
        build_unique_user("immutable")
    )

    user_id = register_data["user"]["id"]
    token = register_data["accessToken"]

    response = api_session.patch(
        f"{base_url}/api/users/{user_id}",
        json={
            "email": "changed@example.com"
        },
        headers=auth_headers(token)
    )

    assert response.status_code == 400, response.text

    data = response.json()

    assert "email" in data["fields"]


# ============================================================
# Update user - another account is forbidden
# ============================================================

def test_user_cannot_update_another_user(base_url, api_session):
    _, user1_data = register_user(
        base_url,
        api_session,
        build_unique_user("owner1")
    )

    _, user2_data = register_user(
        base_url,
        api_session,
        build_unique_user("owner2")
    )

    response = api_session.patch(
        f"{base_url}/api/users/{user2_data['user']['id']}",
        json={
            "name": "Unauthorized Update"
        },
        headers=auth_headers(user1_data["accessToken"])
    )

    assert response.status_code == 403, response.text


# ============================================================
# Logout - token is revoked
# ============================================================

def test_user_logout_revokes_token(base_url, api_session):
    _, register_data = register_user(
        base_url,
        api_session,
        build_unique_user("logout")
    )

    user_id = register_data["user"]["id"]
    token = register_data["accessToken"]

    logout_response = api_session.post(
        f"{base_url}/api/users/logout",
        headers=auth_headers(token)
    )

    assert logout_response.status_code == 200, logout_response.text
    assert logout_response.json()["message"] == "Logged out successfully"

    # The same token must no longer work.
    update_response = api_session.patch(
        f"{base_url}/api/users/{user_id}",
        json={
            "name": "This Must Fail"
        },
        headers=auth_headers(token)
    )

    assert update_response.status_code == 401, update_response.text


# ============================================================
# Delete user - own account
# ============================================================

def test_user_can_delete_own_account(base_url, api_session):
    user_data, register_data = register_user(
        base_url,
        api_session,
        build_unique_user("delete")
    )

    user_id = register_data["user"]["id"]
    token = register_data["accessToken"]

    delete_response = api_session.delete(
        f"{base_url}/api/users/{user_id}",
        headers=auth_headers(token)
    )

    assert delete_response.status_code == 200, delete_response.text
    assert delete_response.json()["message"] == "User deleted successfully"

    # Confirm the account can no longer log in.
    login_response = api_session.post(
        f"{base_url}/api/users/login",
        json={
            "usernameOrEmail": user_data["username"],
            "password": user_data["password"]
        }
    )

    assert login_response.status_code == 401, login_response.text


# ============================================================
# Delete user - another account is forbidden
# ============================================================

def test_user_cannot_delete_another_user(base_url, api_session):
    _, user1_data = register_user(
        base_url,
        api_session,
        build_unique_user("delete_owner")
    )

    _, user2_data = register_user(
        base_url,
        api_session,
        build_unique_user("delete_target")
    )

    response = api_session.delete(
        f"{base_url}/api/users/{user2_data['user']['id']}",
        headers=auth_headers(user1_data["accessToken"])
    )

    assert response.status_code == 403, response.text