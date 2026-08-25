import unittest
import json

from tests.test_base import BaseTestCase
from models.user import db, User


class TestUserRoutes(BaseTestCase):

    # ============================================================
    # Test Helpers
    # ============================================================

    def register_user(
        self,
        username="valid_user",
        email="valid@example.com",
        password="xxxxPassword123xxxxPassword123!",
        name="Mario Rossi"
    ):
        """Register a user and return the Flask test response."""

        payload = {
            "username": username,
            "email": email,
            "password": password,
            "name": name
        }

        return self.client.post(
            '/api/users/register',
            data=json.dumps(payload),
            content_type='application/json'
        )

    def register_and_get_auth(
        self,
        username="valid_user",
        email="valid@example.com",
        password="xxxxPassword123xxxxPassword123!",
        name="Mario Rossi"
    ):
        """
        Register a user and return:
        - user ID
        - access token
        - response data
        """

        response = self.register_user(
            username=username,
            email=email,
            password=password,
            name=name
        )

        data = response.get_json()

        return (
            data['user']['id'],
            data['accessToken'],
            data
        )

    def auth_headers(self, token):
        """Create an Authorization header for JWT protected routes."""

        return {
            "Authorization": f"Bearer {token}"
        }

    # ============================================================
    # Registration - successful registration
    # ============================================================

    def test_successful_user_registration(self):
        """A valid registration should create a user and return a JWT."""

        response = self.register_user(
            username="chef_mario",
            email="mario@example.com"
        )

        data = response.get_json()

        self.assertEqual(response.status_code, 201)
        self.assertIn('accessToken', data)
        self.assertIn('user', data)

        self.assertEqual(
            data['user']['username'],
            'chef_mario'
        )

        self.assertEqual(
            data['user']['email'],
            'mario@example.com'
        )

    # ============================================================
    # Registration - reserved username is rejected
    # ============================================================

    def test_block_reserved_test_user_registration(self):
        """The reserved 'test-user' username should return 409."""

        payload = {
            "username": "test-user",
            "email": "testuser@example.com",
            "password": "Password123!",
            "name": "Test User"
        }

        response = self.client.post(
            '/api/users/register',
            data=json.dumps(payload),
            content_type='application/json'
        )

        data = response.get_json()

        self.assertEqual(response.status_code, 409)

        self.assertEqual(
            data.get('message'),
            'Username is already taken'
        )

    # ============================================================
    # Registration - missing required field is rejected
    # ============================================================

    def test_registration_missing_required_field(self):
        """Registration without an email should return 400."""

        payload = {
            "username": "missing_email_user",
            "password": "xxxxPassword123xxxxPassword123!",
            "name": "Missing Email"
        }

        response = self.client.post(
            '/api/users/register',
            data=json.dumps(payload),
            content_type='application/json'
        )

        data = response.get_json()

        self.assertEqual(response.status_code, 400)

        self.assertEqual(
            data.get('message'),
            'email is required'
        )

    # ============================================================
    # Registration - duplicate email is rejected
    # ============================================================

    def test_registration_duplicate_email(self):
        """A second account cannot register with an existing email."""

        self.register_user(
            username="first_user",
            email="duplicate@example.com"
        )

        response = self.register_user(
            username="second_user",
            email="duplicate@example.com"
        )

        data = response.get_json()

        self.assertEqual(response.status_code, 409)

        self.assertEqual(
            data.get('message'),
            'Email is already registered'
        )

    # ============================================================
    # Login - successful login
    # ============================================================

    def test_user_login(self):
        """Valid credentials should return a JWT access token."""

        self.register_user()

        login_data = {
            "usernameOrEmail": "valid@example.com",
            "password": "xxxxPassword123xxxxPassword123!"
        }

        response = self.client.post(
            '/api/users/login',
            data=json.dumps(login_data),
            content_type='application/json'
        )

        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertIn('accessToken', data)

    # ============================================================
    # Login - incorrect password is rejected
    # ============================================================

    def test_login_with_wrong_password(self):
        """Login with an incorrect password should return 401."""

        self.register_user(
            username="login_user",
            email="login@example.com",
            password="xxxxPassword123xxxxPassword123!"
        )

        payload = {
            "usernameOrEmail": "login@example.com",
            "password": "WrongPassword123!"
        }

        response = self.client.post(
            '/api/users/login',
            data=json.dumps(payload),
            content_type='application/json'
        )

        data = response.get_json()

        self.assertEqual(response.status_code, 401)

        self.assertEqual(
            data.get('message'),
            'Invalid username/email or password'
        )

    # ============================================================
    # Update user - user can edit own profile
    # ============================================================

    def test_update_own_user(self):
        """Authenticated users can update their own editable fields."""

        user_id, token, _ = self.register_and_get_auth()

        update_payload = {
            "name": "Updated Mario",
            "bio": "Updated profile",
            "avatarUrl": "https://example.com/avatar.jpg"
        }

        response = self.client.patch(
            f'/api/users/{user_id}',
            data=json.dumps(update_payload),
            content_type='application/json',
            headers=self.auth_headers(token)
        )

        data = response.get_json()

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            data['user']['name'],
            "Updated Mario"
        )

        self.assertEqual(
            data['user']['bio'],
            "Updated profile"
        )

        self.assertEqual(
            data['user']['avatarUrl'],
            "https://example.com/avatar.jpg"
        )

        # Verify the database was actually updated.
        with self.app.app_context():
            user = db.session.get(User, user_id)

            self.assertEqual(
                user.name,
                "Updated Mario"
            )

    # ============================================================
    # Update user - email cannot be edited
    # ============================================================

    def test_update_user_rejects_email_change(self):
        """Email should be immutable through the profile endpoint."""

        user_id, token, _ = self.register_and_get_auth()

        response = self.client.patch(
            f'/api/users/{user_id}',
            data=json.dumps({
                "email": "different@example.com"
            }),
            content_type='application/json',
            headers=self.auth_headers(token)
        )

        data = response.get_json()

        self.assertEqual(response.status_code, 400)

        self.assertIn(
            'email',
            data['fields']
        )

    # ============================================================
    # Update user - username cannot be edited
    # ============================================================

    def test_update_user_rejects_username_change(self):
        """Username should be immutable through the profile endpoint."""

        user_id, token, _ = self.register_and_get_auth()

        response = self.client.patch(
            f'/api/users/{user_id}',
            data=json.dumps({
                "username": "new_username"
            }),
            content_type='application/json',
            headers=self.auth_headers(token)
        )

        data = response.get_json()

        self.assertEqual(response.status_code, 400)

        self.assertIn(
            'username',
            data['fields']
        )

    # ============================================================
    # Update user - empty name is rejected
    # ============================================================

    def test_update_user_rejects_empty_name(self):
        """A user's name cannot be changed to an empty value."""

        user_id, token, _ = self.register_and_get_auth(
            username="empty_name_user",
            email="emptyname@example.com"
        )

        response = self.client.patch(
            f'/api/users/{user_id}',
            data=json.dumps({
                "name": "   "
            }),
            content_type='application/json',
            headers=self.auth_headers(token)
        )

        data = response.get_json()

        self.assertEqual(response.status_code, 400)

        self.assertEqual(
            data.get('message'),
            'Name cannot be empty'
        )

    # ============================================================
    # Update user - modifying another user is forbidden
    # ============================================================

    def test_update_other_user_is_forbidden(self):
        """A user cannot modify another user's account."""

        user1_id, user1_token, _ = self.register_and_get_auth(
            username="user1",
            email="user1@example.com"
        )

        user2_id, _, _ = self.register_and_get_auth(
            username="user2",
            email="user2@example.com"
        )

        response = self.client.patch(
            f'/api/users/{user2_id}',
            data=json.dumps({
                "name": "Hacked Name"
            }),
            content_type='application/json',
            headers=self.auth_headers(user1_token)
        )

        self.assertEqual(
            response.status_code,
            403
        )

    # ============================================================
    # Update user - authentication is required
    # ============================================================

    def test_update_user_requires_authentication(self):
        """Profile updates without a JWT should return 401."""

        user_id, _, _ = self.register_and_get_auth()

        response = self.client.patch(
            f'/api/users/{user_id}',
            data=json.dumps({
                "name": "Updated Name"
            }),
            content_type='application/json'
        )

        self.assertEqual(
            response.status_code,
            401
        )

    # ============================================================
    # Update user - nonexistent user returns 404
    # ============================================================

    def test_update_nonexistent_user(self):
        """
        A valid JWT whose user no longer exists in the database
        should receive 404 during profile update.
        """

        user_id, token, _ = self.register_and_get_auth(
            username="deleted_user",
            email="deleted@example.com"
        )

        # Remove the user directly while retaining the JWT.
        with self.app.app_context():
            user = db.session.get(User, user_id)

            db.session.delete(user)
            db.session.commit()

        response = self.client.patch(
            f'/api/users/{user_id}',
            data=json.dumps({
                "name": "Should Not Update"
            }),
            content_type='application/json',
            headers=self.auth_headers(token)
        )

        data = response.get_json()

        self.assertEqual(response.status_code, 404)

        self.assertEqual(
            data.get('message'),
            'User not found'
        )

    # ============================================================
    # Logout - valid token can be revoked
    # ============================================================

    def test_user_logout(self):
        """Logout should revoke the current JWT."""

        user_id, token, _ = self.register_and_get_auth()

        response = self.client.post(
            '/api/users/logout',
            headers=self.auth_headers(token)
        )

        data = response.get_json()

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertEqual(
            data['message'],
            'Logged out successfully'
        )

        # Verify the same JWT is no longer usable.
        second_response = self.client.patch(
            f'/api/users/{user_id}',
            data=json.dumps({
                "name": "Should Not Work"
            }),
            content_type='application/json',
            headers=self.auth_headers(token)
        )

        self.assertEqual(
            second_response.status_code,
            401
        )

    # ============================================================
    # Logout - authentication is required
    # ============================================================

    def test_logout_requires_authentication(self):
        """Calling logout without a JWT should return 401."""

        response = self.client.post(
            '/api/users/logout'
        )

        self.assertEqual(
            response.status_code,
            401
        )

    # ============================================================
    # Delete user - user can delete own account
    # ============================================================

    def test_delete_own_user(self):
        """Authenticated users can delete their own account."""

        user_id, token, _ = self.register_and_get_auth()

        response = self.client.delete(
            f'/api/users/{user_id}',
            headers=self.auth_headers(token)
        )

        data = response.get_json()

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertEqual(
            data['message'],
            'User deleted successfully'
        )

        # Verify the user was actually removed.
        with self.app.app_context():
            user = db.session.get(
                User,
                user_id
            )

            self.assertIsNone(user)

    # ============================================================
    # Delete user - deleting another account is forbidden
    # ============================================================

    def test_delete_other_user_is_forbidden(self):
        """A user cannot delete another user's account."""

        _, user1_token, _ = self.register_and_get_auth(
            username="delete_user_1",
            email="delete1@example.com"
        )

        user2_id, _, _ = self.register_and_get_auth(
            username="delete_user_2",
            email="delete2@example.com"
        )

        response = self.client.delete(
            f'/api/users/{user2_id}',
            headers=self.auth_headers(
                user1_token
            )
        )

        self.assertEqual(
            response.status_code,
            403
        )

    # ============================================================
    # Delete user - authentication is required
    # ============================================================

    def test_delete_user_requires_authentication(self):
        """Deleting an account without a JWT should return 401."""

        user_id, _, _ = self.register_and_get_auth()

        response = self.client.delete(
            f'/api/users/{user_id}'
        )

        self.assertEqual(
            response.status_code,
            401
        )


if __name__ == '__main__':
    unittest.main()