import unittest
import json
from tests.test_base import BaseTestCase
from extensions import db
from models.recipe import Recipe

class TestRecipeRoutes(BaseTestCase):

    def create_recipes(self, count):
        """Insert `count` bare recipes directly, bypassing the HTTP/auth
        flow - only the pagination behavior on GET is under test here."""
        with self.app.app_context():
            for i in range(count):
                db.session.add(Recipe(title=f"Recipe {i}"))
            db.session.commit()

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
#    test get recipes pagination
#=================================================================================
    def test_get_recipes_defaults_to_first_page(self):
        """With no query params, GET /api/recipes returns at most the
        default page size and reports the true total via headers."""
        self.create_recipes(25)

        response = self.client.get('/api/recipes')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.get_json()), 20)
        self.assertEqual(response.headers['X-Total-Count'], '25')
        self.assertEqual(response.headers['X-Page'], '1')
        self.assertEqual(response.headers['X-Page-Size'], '20')

    def test_get_recipes_respects_page_and_page_size(self):
        """?page=&pageSize= narrow the slice returned, in newest-first
        order, without changing the reported total."""
        self.create_recipes(5)

        response = self.client.get('/api/recipes?page=2&pageSize=2')
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 2)
        self.assertEqual(response.headers['X-Total-Count'], '5')
        self.assertEqual(response.headers['X-Page'], '2')
        self.assertEqual(response.headers['X-Page-Size'], '2')
        # Newest-first: page 1 is recipes 4,3; page 2 is recipes 2,1
        self.assertEqual(data[0]['title'], 'Recipe 2')
        self.assertEqual(data[1]['title'], 'Recipe 1')

    def test_get_recipes_page_size_is_capped(self):
        """An abusive ?pageSize= is clamped instead of honored as-is."""
        self.create_recipes(3)

        response = self.client.get('/api/recipes?pageSize=999999')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['X-Page-Size'], '100')

    def test_get_recipes_invalid_pagination_params_fall_back_to_defaults(self):
        """Non-numeric page/pageSize shouldn't error - just use defaults."""
        self.create_recipes(1)

        response = self.client.get('/api/recipes?page=not-a-number&pageSize=also-not-a-number')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['X-Page'], '1')
        self.assertEqual(response.headers['X-Page-Size'], '20')

#=================================================================================
#    test get single recipe by id
#=================================================================================
    def test_get_recipe_by_id_success(self):
        """GET /api/recipes/<id> should return the recipe, no auth required."""
        headers = self.get_auth_header()
        create_res = self.client.post('/api/recipes/create',
                                       data=json.dumps({"title": "Findable Recipe"}),
                                       headers=headers,
                                       content_type='application/json')
        recipe_id = create_res.get_json()['id']

        response = self.client.get(f'/api/recipes/{recipe_id}')
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['id'], recipe_id)
        self.assertEqual(data['title'], "Findable Recipe")

    def test_get_recipe_by_id_not_found(self):
        """GET /api/recipes/<id> for an unknown id should return 404."""
        response = self.client.get('/api/recipes/does-not-exist')
        data = response.get_json()

        self.assertEqual(response.status_code, 404)
        self.assertEqual(data.get('error'), 'Recipe not found')
        self.assertEqual(data.get('message'), 'Recipe not found')

#=================================================================================
#    test recipe input validation
#=================================================================================
    def test_create_recipe_rejects_missing_title(self):
        """POST /api/recipes/create without a title should return 400,
        not a 500 from the database's NOT NULL constraint."""
        headers = self.get_auth_header()
        response = self.client.post('/api/recipes/create',
                                     data=json.dumps({"description": "No title here"}),
                                     headers=headers,
                                     content_type='application/json')

        self.assertEqual(response.status_code, 400)
        self.assertIn('title', response.get_json().get('message'))

    def test_create_recipe_rejects_non_string_title(self):
        """A non-string title should be rejected, not stored as-is."""
        headers = self.get_auth_header()
        response = self.client.post('/api/recipes/create',
                                     data=json.dumps({"title": 12345}),
                                     headers=headers,
                                     content_type='application/json')

        self.assertEqual(response.status_code, 400)

    def test_create_recipe_rejects_title_too_long(self):
        """A title over the DB column's 150-char limit should be rejected
        here (400) instead of failing at the database layer."""
        headers = self.get_auth_header()
        response = self.client.post('/api/recipes/create',
                                     data=json.dumps({"title": "x" * 151}),
                                     headers=headers,
                                     content_type='application/json')

        self.assertEqual(response.status_code, 400)

    def test_create_recipe_rejects_negative_servings(self):
        """servings must be a positive number."""
        headers = self.get_auth_header()
        response = self.client.post('/api/recipes/create',
                                     data=json.dumps({"title": "Bad Servings", "servings": -1}),
                                     headers=headers,
                                     content_type='application/json')

        self.assertEqual(response.status_code, 400)

    def test_create_recipe_rejects_ingredient_missing_name(self):
        """An ingredient without a name should be rejected here (400),
        not reach Ingredient.name's NOT NULL constraint and 500."""
        headers = self.get_auth_header()
        payload = {
            "title": "Nameless Ingredient",
            "parts": [{
                "title": "Part 1",
                "ingredients": [{"amount": 5, "unit": "g"}]
            }]
        }

        response = self.client.post('/api/recipes/create',
                                     data=json.dumps(payload),
                                     headers=headers,
                                     content_type='application/json')

        self.assertEqual(response.status_code, 400)

    def test_create_recipe_allows_explicit_null_parts(self):
        """`"parts": null` used to crash with a 500 (iterating None) -
        it should be treated the same as omitting `parts` entirely."""
        headers = self.get_auth_header()
        response = self.client.post('/api/recipes/create',
                                     data=json.dumps({"title": "Null Parts", "parts": None}),
                                     headers=headers,
                                     content_type='application/json')

        data = response.get_json()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(data['parts'], [])

    def test_update_recipe_rejects_ingredient_missing_name(self):
        """PUT /api/recipes/<id> should reject a nameless ingredient the
        same way create does."""
        headers = self.get_auth_header()
        create_res = self.client.post('/api/recipes/create',
                                       data=json.dumps({"title": "Original"}),
                                       headers=headers,
                                       content_type='application/json')
        recipe_id = create_res.get_json()['id']

        payload = {
            "parts": [{
                "title": "Part 1",
                "ingredients": [{"amount": 5, "unit": "g"}]
            }]
        }

        response = self.client.put(f'/api/recipes/{recipe_id}',
                                    data=json.dumps(payload),
                                    headers=headers,
                                    content_type='application/json')

        self.assertEqual(response.status_code, 400)

    def test_update_recipe_allows_explicit_null_parts(self):
        """`"parts": null` on update should leave existing parts
        untouched instead of crashing with a 500."""
        headers = self.get_auth_header()
        initial_payload = {
            "title": "Has Parts",
            "parts": [{"title": "Part 1", "ingredients": [{"name": "Salt", "amount": 5, "unit": "g"}]}]
        }
        create_res = self.client.post('/api/recipes/create',
                                       data=json.dumps(initial_payload),
                                       headers=headers,
                                       content_type='application/json')
        recipe_id = create_res.get_json()['id']

        response = self.client.put(f'/api/recipes/{recipe_id}',
                                    data=json.dumps({"title": "Still Has Parts", "parts": None}),
                                    headers=headers,
                                    content_type='application/json')

        data = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data['parts']), 1)
        self.assertEqual(data['parts'][0]['ingredients'][0]['name'], "Salt")

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
#    test recipe size limits
#=================================================================================
    def test_create_recipe_rejects_too_many_parts(self):
        """POST /api/recipes/create with over 50 parts should be rejected
        before touching the database."""
        headers = self.get_auth_header()
        payload = {
            "title": "Too Many Parts",
            "parts": [{"title": f"Part {i}"} for i in range(51)]
        }

        response = self.client.post('/api/recipes/create',
                                     data=json.dumps(payload),
                                     headers=headers,
                                     content_type='application/json')

        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.get_json())

    def test_create_recipe_rejects_too_many_ingredients(self):
        """POST /api/recipes/create with over 50 ingredients in one part
        should be rejected before touching the database."""
        headers = self.get_auth_header()
        payload = {
            "title": "Too Many Ingredients",
            "parts": [{
                "title": "Overloaded Part",
                "ingredients": [{"name": f"Ingredient {i}"} for i in range(51)]
            }]
        }

        response = self.client.post('/api/recipes/create',
                                     data=json.dumps(payload),
                                     headers=headers,
                                     content_type='application/json')

        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.get_json())

    def test_create_recipe_rejects_oversized_payload(self):
        """A request body over MAX_CONTENT_LENGTH is rejected (413) by
        Werkzeug before the route even runs."""
        headers = self.get_auth_header()
        payload = {
            "title": "Huge Payload",
            "description": "x" * (2 * 1024 * 1024)  # 2 MB, over the 1 MB cap
        }

        response = self.client.post('/api/recipes/create',
                                     data=json.dumps(payload),
                                     headers=headers,
                                     content_type='application/json')

        self.assertEqual(response.status_code, 413)

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

#=================================================================================
#    test error response shape
#=================================================================================
    def test_delete_nonexistent_recipe_returns_404_with_both_keys(self):
        """A NotFoundError raised from the controller should be caught by
        the centralized handler and carry both 'error' and 'message'."""
        headers = self.get_auth_header()

        response = self.client.delete('/api/recipes/does-not-exist', headers=headers)
        data = response.get_json()

        self.assertEqual(response.status_code, 404)
        self.assertEqual(data.get('error'), 'Recipe not found')
        self.assertEqual(data.get('message'), 'Recipe not found')

if __name__ == '__main__':
    unittest.main()