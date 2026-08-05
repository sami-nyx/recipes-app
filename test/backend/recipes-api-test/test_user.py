# test/backend/recipes-api-test/test_user.py
import os

def test_user_registration_and_login(base_url, api_session):
    unique_suffix = os.urandom(4).hex()
    user_data = {
        "name": "HTTP Test User",
        "username": f"user_{unique_suffix}",
        "email": f"user_{unique_suffix}@example.com",
        "password": "SecurePassword123!",
        "bio": "Testing API endpoints with pure JSON",
        "avatarUrl": "https://example.com/avatar.png"
    }

    # 1. Register User
    reg_res = api_session.post(f"{base_url}/api/users/register", json=user_data)
    assert reg_res.status_code == 201
    
    res_json = reg_res.json()
    assert "user" in res_json
    assert "accessToken" in res_json
    assert res_json["user"]["username"] == user_data["username"]

    # 2. Login User
    login_payload = {
        "usernameOrEmail": user_data["username"],
        "password": user_data["password"]
    }
    login_res = api_session.post(f"{base_url}/api/users/login", json=login_payload)
    assert login_res.status_code == 200
    assert "accessToken" in login_res.json()

def test_duplicate_user_registration_fails(base_url, api_session):
    duplicate_payload = {
        "name": "Duplicate User",
        "username": "test-user",  # Hardcoded duplicate in UserController logic
        "email": "dup@example.com",
        "password": "Password123!"
    }

    res = api_session.post(f"{base_url}/api/users/register", json=duplicate_payload)
    assert res.status_code == 409
    assert res.json()["message"] == "Username is already taken"