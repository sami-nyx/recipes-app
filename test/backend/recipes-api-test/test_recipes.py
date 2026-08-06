# test/backend/recipes-api-test/test_recipes.py

def test_recipe_lifecycle(base_url, api_session, auth_headers):
    # 1. Create Recipe
    new_recipe = {
        "title": "Integration Test Pasta",
        "description": "JSON API test dish",
        "ingredients": ["pasta", "sauce"],
        "instructions": ["boil", "mix"],
        "prepTimeMinutes": 5,
        "cookTimeMinutes": 10,
        "servings": 2
    }

    create_res = api_session.post(
        f"{base_url}/api/recipes/create",
        json=new_recipe,
        headers=auth_headers
    )
    assert create_res.status_code == 201
    created_recipe = create_res.json()
    recipe_id = created_recipe["id"]

    # 2. Update Recipe
    update_payload = {
        "title": "Updated Integration Test Pasta",
        "description": "Updated via HTTP PUT",
        "ingredients": ["pasta", "sauce", "cheese"],
        "instructions": ["boil", "mix", "serve"],
        "prepTimeMinutes": 5,
        "cookTimeMinutes": 12,
        "servings": 3
    }

    update_res = api_session.put(
        f"{base_url}/api/recipes/{recipe_id}",
        json=update_payload,
        headers=auth_headers
    )
    assert update_res.status_code == 200
    assert update_res.json()["title"] == "Updated Integration Test Pasta"

def test_unauthorized_recipe_creation(base_url, api_session):
    res = api_session.post(f"{base_url}/api/recipes/create", json={"title": "Unauthorized"})
    assert res.status_code == 401