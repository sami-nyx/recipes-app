import unittest
import json
from tests.test_base import BaseTestCase

class TestUserRoutes(BaseTestCase):

    def test_block_reserved_test_user_registration(self):
        """Ensure 'test-user' registration is rejected with 409 Conflict."""
        payload = {
            "username": "test-user",
            "email": "testuser@example.com",
            "password": "Password123!",
            "name": "Test User"
        }
        response = self.client.post('/api/users/register',
                                     data=json.dumps(payload),
                                     content_type='application/json')
        
        data = response.get_json()
        # 1. Assert Status Code is 409
        self.assertEqual(response.status_code, 409)

        # 2. Assert message matches the new response
        self.assertEqual(data.get('message'), 'Username is already taken')

    def test_successful_user_registration(self):
        """Test valid user registration."""
        payload = {
            "username": "chef_mario",
            "email": "mario@example.com",
            "password": "xxxxPassword123xxxxPassword123!",
            "name": "Mario Rossi"
        }
        response = self.client.post('/api/users/register',
                                     data=json.dumps(payload),
                                     content_type='application/json')
        
        self.assertEqual(response.status_code, 201)

    def test_user_login(self):
        """Test user login returns a JWT access token."""
        # First register
        user_data = {
            "username": "valid_user",
            "email": "valid@example.com",
            "password": "xxxxPassword123xxxxPassword123!",
            "name": "Mario Rossi"
        }
        self.client.post('/api/users/register',
                         data=json.dumps(user_data),
                         content_type='application/json')

        # Then login
        login_data = {

            "usernameOrEmail": "valid@example.com",
            "password": "xxxxPassword123xxxxPassword123!"
        }

        response = self.client.post('/api/users/login',
                                     data=json.dumps(login_data),
                                     content_type='application/json')
        data = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertIn('accessToken', data)


if __name__ == '__main__':
    unittest.main()