import unittest
import json
from tests.test_base import BaseTestCase

class TestRecipeRoutes(BaseTestCase):

#=================================================================================
#    authentication helper method to get JWT token for testing protected routes
#=================================================================================
    def get_auth_header(self):
        """Helper to register, login, and return Authorization header."""
        user_payload = {
            "username": "recipe_creator",
            "email": "creator@example.com",
            "password": "Password123!",
            "name": "Recipe Creator"
        }
        self.client.post('/api/users/register',
                         data=json.dumps(user_payload),
                         content_type='application/json')

        login_res = self.client.post('/api/users/login',
                                      data=json.dumps({"usernameOrEmail": "creator@example.com", "password": "Password123!"}),
                                      content_type='application/json')
        
        token = login_res.get_json().get('accessToken')
        return {'Authorization': f'Bearer {token}'}

#=================================================================================
#    test get recipes when empty
#=================================================================================
    def test_get_recipes_empty(self):
        """GET /api/recipes should return an empty list initially."""
        response = self.client.get('/api/recipes')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), [])

#=================================================================================
#    test create recipe with authentication
#=================================================================================
    def test_create_recipe_authenticated(self):
        """POST /api/recipes/create with valid JWT should create a recipe."""
        headers = self.get_auth_header()
        recipe_payload = {
            "title": "Unit Test Pasta",
            "description": "Delicious test recipe",
            "prepTimeMinutes": 10,
            "cookTimeMinutes": 15,
            "servings": 2,
            "parts": [
                {
                    "title": "Sauce",
                    "instructions": ["Boil water", "Add pasta"],
                    "ingredients": [
                        {"name": "Pasta", "amount": 200, "unit": "g"}
                    ]
                }
            ]
        }

        response = self.client.post('/api/recipes/create',
                                     data=json.dumps(recipe_payload),
                                     headers=headers,
                                     content_type='application/json')

        data = response.get_json()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(data['title'], "Unit Test Pasta")
        self.assertIn('id', data)

    def test_create_recipe_unauthorized(self):
        """POST /api/recipes/create without JWT should return 401."""
        response = self.client.post('/api/recipes/create',
                                     data=json.dumps({"title": "No Auth"}),
                                     content_type='application/json')
        self.assertEqual(response.status_code, 401)

#=================================================================================
#    test update recipe
#=================================================================================
    def test_update_recipe_success(self):
        """PUT /api/recipes/<id> should update recipe title, description, and nested parts."""
        headers = self.get_auth_header()

        # 1. Create initial recipe
        initial_payload = {
            "title": "Original Title",
            "description": "Original Description",
            "prepTimeMinutes": 10,
            "cookTimeMinutes": 20,
            "servings": 2,
            "parts": [
                {
                    "title": "Part 1",
                    "instructions": ["Step 1"],
                    "ingredients": [{"name": "Salt", "amount": 5, "unit": "g"}]
                }
            ]
        }
        create_res = self.client.post('/api/recipes/create',
                                       data=json.dumps(initial_payload),
                                       headers=headers,
                                       content_type='application/json')
        recipe_id = create_res.get_json()['id']

        # 2. Prepare updated payload
        update_payload = {
            "title": "Updated Title",
            "description": "Updated Description",
            "prepTimeMinutes": 15,
            "cookTimeMinutes": 25,
            "servings": 4,
            "parts": [
                {
                    "title": "Updated Part 1",
                    "instructions": ["Step 1", "Step 2"],
                    "ingredients": [
                        {"name": "Salt", "amount": 10, "unit": "g"},
                        {"name": "Pepper", "amount": 2, "unit": "g"}
                    ]
                }
            ]
        }

        # 3. Send PUT request
        update_res = self.client.put(f'/api/recipes/{recipe_id}',
                                      data=json.dumps(update_payload),
                                      headers=headers,
                                      content_type='application/json')

        self.assertEqual(update_res.status_code, 200)
        updated_data = update_res.get_json()
        self.assertEqual(updated_data['title'], "Updated Title")
        self.assertEqual(updated_data['description'], "Updated Description")
        self.assertEqual(updated_data['servings'], 4)
        
        # Verify nested parts updated
        self.assertEqual(len(updated_data['parts']), 1)
        self.assertEqual(updated_data['parts'][0]['title'], "Updated Part 1")
        self.assertEqual(len(updated_data['parts'][0]['ingredients']), 2)

#=================================================================================
#    test update recipe unauthorized
#=================================================================================
    def test_update_recipe_unauthorized(self):
        """PUT /api/recipes/<id> should return 401 for unauthorized requests."""
        headers = self.get_auth_header()
                
        # 1. Create initial recipe
        initial_payload = {
            "title": "Original Title",
            "description": "Original Description",
            "prepTimeMinutes": 10,
            "cookTimeMinutes": 20,
            "servings": 2,
            "parts": [
                {
                    "title": "Part 1",
                    "instructions": ["Step 1"],
                    "ingredients": [{"name": "Salt", "amount": 5, "unit": "g"}]
                }
            ]
        }
        create_res = self.client.post('/api/recipes/create',
                                       data=json.dumps(initial_payload),
                                       headers=headers,
                                       content_type='application/json')
        recipe_id = create_res.get_json()['id']
                
        # 2. Prepare updated payload
        update_payload = {
            "title": "Updated Title",
            "description": "Updated Description",
            "prepTimeMinutes": 15,
            "cookTimeMinutes": 25,
            "servings": 4,
            "parts": [
                {
                    "title": "Updated Part 1",
                    "instructions": ["Step 1", "Step 2"],
                    "ingredients": [
                        {"name": "Salt", "amount": 10, "unit": "g"},
                        {"name": "Pepper", "amount": 2, "unit": "g"}
                    ]
                }
            ]
        }

        # 3. Send PUT request
        update_res = self.client.put(f'/api/recipes/{recipe_id}',
                                      data=json.dumps(update_payload),
                                      content_type='application/json')

        self.assertEqual(update_res.status_code, 401)
        
#=================================================================================
#    test delete recipe
#=================================================================================
    def test_delete_recipe(self):
        """DELETE /api/recipes/<id> should remove the recipe."""
        headers = self.get_auth_header()
        
        # 1. Create a recipe
        create_res = self.client.post('/api/recipes/create',
                                       data=json.dumps({
                                           "title": "To Be Deleted",
                                           "description": "Temp",
                                           "prepTimeMinutes": 5,
                                           "cookTimeMinutes": 5,
                                           "servings": 1
                                       }),
                                       headers=headers,
                                       content_type='application/json')
        
        recipe_id = create_res.get_json()['id']

        # 2. Delete it
        del_res = self.client.delete(f'/api/recipes/{recipe_id}', headers=headers)
        self.assertEqual(del_res.status_code, 200)

        # 3. Verify empty recipe list
        get_res = self.client.get('/api/recipes')
        self.assertEqual(len(get_res.get_json()), 0)

#=================================================================================
#    test unauthorized deletion of recipe
#=================================================================================
    def test_delete_recipe_unauthorized(self):
        """DELETE /api/recipes/<id> should return 403 for unauthorized users."""
        headers = self.get_auth_header()
                
        # 1. Create a recipe
        create_res = self.client.post('/api/recipes/create',
                                       data=json.dumps({
                                           "title": "To Be Deleted",
                                           "description": "Temp",
                                           "prepTimeMinutes": 5,
                                           "cookTimeMinutes": 5,
                                           "servings": 1
                                       }),
                                       headers=headers,
                                       content_type='application/json')
        
        recipe_id = create_res.get_json()['id']

        # 2. Delete it
        del_res = self.client.delete(f'/api/recipes/{recipe_id}')
        self.assertEqual(del_res.status_code, 401)

        # 3. Verify the recipe still exists
        get_res = self.client.get('/api/recipes')
        self.assertEqual(len(get_res.get_json()), 1)

if __name__ == '__main__':
    unittest.main()