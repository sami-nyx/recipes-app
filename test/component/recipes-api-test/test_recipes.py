# test/backend/recipes-api-test/test_recipes.py


# ============================================================
# Test Helpers
# ============================================================

def build_recipe_payload(title="Integration Test Pasta"):
    return {
        "title": title,
        "description": "JSON API test dish",
        "prepTimeMinutes": 5,
        "cookTimeMinutes": 10,
        "servings": 2,
        "totalWeightGrams": 500,
        "costPer100g": 2.5,
        "caloriesPer100g": 180,
        "parts": [
            {
                "title": "Main",
                "instructions": [
                    "Boil pasta",
                    "Mix with sauce"
                ],
                "ingredients": [
                    {
                        "name": "Pasta",
                        "amount": 300,
                        "unit": "g",
                        "costPer100g": 1.5,
                        "caloriesPer100g": 350
                    },
                    {
                        "name": "Tomato Sauce",
                        "amount": 200,
                        "unit": "g",
                        "costPer100g": 2.0,
                        "caloriesPer100g": 80
                    }
                ]
            }
        ]
    }


def create_recipe(
    base_url,
    api_session,
    auth_headers,
    title="Integration Test Pasta"
):
    payload = build_recipe_payload(title)

    response = api_session.post(
        f"{base_url}/api/recipes/create",
        json=payload,
        headers=auth_headers
    )

    assert response.status_code == 201, response.text

    return response.json()


# ============================================================
# Recipe lifecycle - create and update
# ============================================================

def test_recipe_lifecycle(
    base_url,
    api_session,
    auth_headers
):
    created_recipe = create_recipe(
        base_url,
        api_session,
        auth_headers
    )

    recipe_id = created_recipe["id"]

    assert created_recipe["title"] == "Integration Test Pasta"
    assert created_recipe["servings"] == 2
    assert len(created_recipe["parts"]) == 1
    assert len(created_recipe["parts"][0]["ingredients"]) == 2

    update_payload = {
        "title": "Updated Integration Test Pasta",
        "description": "Updated via HTTP PUT",
        "prepTimeMinutes": 7,
        "cookTimeMinutes": 12,
        "servings": 3,
        "parts": [
            {
                "title": "Updated Main",
                "instructions": [
                    "Boil pasta",
                    "Add sauce",
                    "Serve"
                ],
                "ingredients": [
                    {
                        "name": "Pasta",
                        "amount": 350,
                        "unit": "g",
                        "costPer100g": 1.5,
                        "caloriesPer100g": 350
                    },
                    {
                        "name": "Tomato Sauce",
                        "amount": 200,
                        "unit": "g",
                        "costPer100g": 2.0,
                        "caloriesPer100g": 80
                    },
                    {
                        "name": "Cheese",
                        "amount": 50,
                        "unit": "g",
                        "costPer100g": 4.0,
                        "caloriesPer100g": 400
                    }
                ]
            }
        ]
    }

    update_res = api_session.put(
        f"{base_url}/api/recipes/{recipe_id}",
        json=update_payload,
        headers=auth_headers
    )

    assert update_res.status_code == 200, update_res.text

    updated_recipe = update_res.json()

    assert (
        updated_recipe["title"]
        == "Updated Integration Test Pasta"
    )

    assert updated_recipe["servings"] == 3
    assert len(updated_recipe["parts"]) == 1
    assert len(updated_recipe["parts"][0]["ingredients"]) == 3


# ============================================================
# Recipe list - public read
# ============================================================

def test_get_recipes(
    base_url,
    api_session,
    auth_headers
):
    created_recipe = create_recipe(
        base_url,
        api_session,
        auth_headers,
        title="Recipe List Test"
    )

    response = api_session.get(
        f"{base_url}/api/recipes"
    )

    assert response.status_code == 200, response.text

    recipes = response.json()

    assert isinstance(recipes, list)

    recipe_ids = [
        recipe["id"]
        for recipe in recipes
    ]

    assert created_recipe["id"] in recipe_ids


# ============================================================
# Recipe creation - authentication is required
# ============================================================

def test_unauthorized_recipe_creation(
    base_url,
    api_session
):
    response = api_session.post(
        f"{base_url}/api/recipes/create",
        json={
            "title": "Unauthorized"
        }
    )

    assert response.status_code == 401, response.text


# ============================================================
# Recipe update - authentication is required
# ============================================================

def test_unauthorized_recipe_update(
    base_url,
    api_session,
    auth_headers
):
    created_recipe = create_recipe(
        base_url,
        api_session,
        auth_headers,
        title="Unauthorized Update Test"
    )

    response = api_session.put(
        f"{base_url}/api/recipes/{created_recipe['id']}",
        json={
            "title": "Should Not Work"
        }
    )

    assert response.status_code == 401, response.text


# ============================================================
# Recipe delete - authentication is required
# ============================================================

def test_unauthorized_recipe_delete(
    base_url,
    api_session,
    auth_headers
):
    created_recipe = create_recipe(
        base_url,
        api_session,
        auth_headers,
        title="Unauthorized Delete Test"
    )

    response = api_session.delete(
        f"{base_url}/api/recipes/{created_recipe['id']}"
    )

    assert response.status_code == 401, response.text


# ============================================================
# Recipe ownership - another user cannot update recipe
# ============================================================

def test_user_cannot_update_another_users_recipe(
    base_url,
    api_session,
    auth_headers,
    second_auth_headers
):
    created_recipe = create_recipe(
        base_url,
        api_session,
        auth_headers,
        title="Ownership Update Test"
    )

    response = api_session.put(
        f"{base_url}/api/recipes/{created_recipe['id']}",
        json={
            "title": "Unauthorized Owner Change"
        },
        headers=second_auth_headers
    )

    assert response.status_code == 403, response.text


# ============================================================
# Recipe ownership - another user cannot delete recipe
# ============================================================

def test_user_cannot_delete_another_users_recipe(
    base_url,
    api_session,
    auth_headers,
    second_auth_headers
):
    created_recipe = create_recipe(
        base_url,
        api_session,
        auth_headers,
        title="Ownership Delete Test"
    )

    response = api_session.delete(
        f"{base_url}/api/recipes/{created_recipe['id']}",
        headers=second_auth_headers
    )

    assert response.status_code == 403, response.text


# ============================================================
# Recipe delete - owner can delete recipe
# ============================================================

def test_owner_can_delete_recipe(
    base_url,
    api_session,
    auth_headers
):
    created_recipe = create_recipe(
        base_url,
        api_session,
        auth_headers,
        title="Delete Recipe Test"
    )

    recipe_id = created_recipe["id"]

    delete_res = api_session.delete(
        f"{base_url}/api/recipes/{recipe_id}",
        headers=auth_headers
    )

    assert delete_res.status_code == 200, delete_res.text

    assert (
        delete_res.json()["message"]
        == "Recipe deleted successfully"
    )