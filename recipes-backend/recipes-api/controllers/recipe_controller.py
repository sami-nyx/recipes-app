from models.recipe import Recipe, RecipePart, Ingredient
from models.user import db
from app_logginig.logger import app_logger  # Import our structured logger

class RecipeController:

    @classmethod
    def get_recipes(cls, args=None):
        """Fetch all recipes ordered by creation date (newest first)."""
        try:
            recipes = Recipe.query.order_by(Recipe.created_at.desc()).all()
            app_logger.info(
                "Fetched all recipes list",
                extra={"props": {"action": "GET_RECIPES_LIST", "count": len(recipes), "status": "SUCCESS"}}
            )
            return [recipe.to_dict() for recipe in recipes], 200
        except Exception as e:
            app_logger.error(
                f"Error fetching recipes: {str(e)}",
                extra={"props": {"action": "GET_RECIPES_LIST", "status": "FAILED", "error": str(e)}}
            )
            return {"error": "Failed to fetch recipes"}, 500

    @classmethod
    def get_recipe_by_id(cls, recipe_id):
        """Fetch a single recipe by its UUID."""
        try:
            recipe = Recipe.query.get(recipe_id)
            if not recipe:
                app_logger.warning(
                    f"Recipe not found: {recipe_id}",
                    extra={"props": {"action": "GET_RECIPE", "recipe_id": recipe_id, "status": "NOT_FOUND"}}
                )
                return {"error": "Recipe not found"}, 404
            
            app_logger.info(
                f"Fetched recipe {recipe_id}",
                extra={"props": {"action": "GET_RECIPE", "recipe_id": recipe_id, "status": "SUCCESS"}}
            )
            return recipe.to_dict(), 200
        except Exception as e:
            app_logger.error(
                f"Error fetching recipe {recipe_id}: {str(e)}",
                extra={"props": {"action": "GET_RECIPE", "recipe_id": recipe_id, "status": "FAILED", "error": str(e)}}
            )
            return {"error": "Failed to fetch recipe"}, 500

    @classmethod
    def create_recipe(cls, data, current_user_id):
        try:
            new_recipe = Recipe(
                title=data.get('title'),
                description=data.get('description'),
                image_url=data.get('imageUrl'),
                prep_time_minutes=data.get('prepTimeMinutes', 0),
                cook_time_minutes=data.get('cookTimeMinutes', 0),
                servings=data.get('servings', 1),
                total_weight_grams=data.get('totalWeightGrams', 0.0),
                cost_per_100g=data.get('costPer100g', 0.0),
                calories_per_100g=data.get('caloriesPer100g', 0.0),
                author_id=current_user_id
            )

            for part_data in data.get('parts', []):
                part = RecipePart(
                    title=part_data.get('title', 'Main Assembly'),
                    instructions=part_data.get('instructions', [])
                )
                for ing_data in part_data.get('ingredients', []):
                    ing = Ingredient(
                        name=ing_data.get('name'),
                        amount=ing_data.get('amount', 0),
                        unit=ing_data.get('unit', 'g'),
                        cost_per_100g=ing_data.get('costPer100g'),
                        calories_per_100g=ing_data.get('caloriesPer100g')
                    )
                    part.ingredients.append(ing)
                new_recipe.parts.append(part)

            db.session.add(new_recipe)
            db.session.commit()

            app_logger.info(
                f"Recipe created successfully: {new_recipe.id}",
                extra={
                    "props": {
                        "action": "CREATE_RECIPE",
                        "user_id": current_user_id,
                        "recipe_id": new_recipe.id,
                        "title": new_recipe.title,
                        "status": "SUCCESS"
                    }
                }
            )
            return new_recipe.to_dict(), 201

        except Exception as e:
            db.session.rollback()
            app_logger.error(
                f"Failed to create recipe: {str(e)}",
                extra={
                    "props": {
                        "action": "CREATE_RECIPE",
                        "user_id": current_user_id,
                        "status": "FAILED",
                        "error": str(e)
                    }
                }
            )
            return {"error": "Failed to create recipe"}, 500

    @classmethod
    def update_recipe(cls, recipe_id, data, current_user_id):
        recipe = db.session.get(Recipe, recipe_id)
        if not recipe:
            return {"error": "Recipe not found"}, 404

        if str(recipe.author_id) != str(current_user_id):
            app_logger.warning(
                f"Unauthorized update attempt on recipe {recipe_id} by user {current_user_id}",
                extra={"props": {"action": "UPDATE_RECIPE", "recipe_id": recipe_id, "user_id": current_user_id, "status": "UNAUTHORIZED"}}
            )
            return {"error": "Unauthorized to update this recipe"}, 403

        try:
            recipe.title = data.get('title', recipe.title)
            recipe.description = data.get('description', recipe.description)
            recipe.image_url = data.get('imageUrl', recipe.image_url)
            recipe.prep_time_minutes = data.get('prepTimeMinutes', recipe.prep_time_minutes)
            recipe.cook_time_minutes = data.get('cookTimeMinutes', recipe.cook_time_minutes)
            recipe.servings = data.get('servings', recipe.servings)
            recipe.total_weight_grams = data.get('totalWeightGrams', recipe.total_weight_grams)
            recipe.cost_per_100g = data.get('costPer100g', recipe.cost_per_100g)
            recipe.calories_per_100g = data.get('caloriesPer100g', recipe.calories_per_100g)

            if 'parts' in data:
                recipe.parts.clear()
                for part_data in data['parts']:
                    part = RecipePart(
                        title=part_data.get('title', 'Main Assembly'),
                        instructions=part_data.get('instructions', [])
                    )
                    for ing_data in part_data.get('ingredients', []):
                        ing = Ingredient(
                            name=ing_data.get('name'),
                            amount=ing_data.get('amount'),
                            unit=ing_data.get('unit'),
                            cost_per_100g=ing_data.get('costPer100g'),
                            calories_per_100g=ing_data.get('caloriesPer100g')
                        )
                        part.ingredients.append(ing)
                    recipe.parts.append(part)

            db.session.commit()
            
            app_logger.info(
                f"Recipe updated successfully: {recipe_id}",
                extra={"props": {"action": "UPDATE_RECIPE", "recipe_id": recipe_id, "user_id": current_user_id, "status": "SUCCESS"}}
            )
            return recipe.to_dict(), 200

        except Exception as e:
            db.session.rollback()
            app_logger.error(
                f"Failed to update recipe {recipe_id}: {str(e)}",
                extra={"props": {"action": "UPDATE_RECIPE", "recipe_id": recipe_id, "user_id": current_user_id, "status": "FAILED", "error": str(e)}}
            )
            return {"error": "Failed to update recipe"}, 500

    @classmethod
    def delete_recipe(cls, recipe_id, current_user_id):
        recipe = db.session.get(Recipe, recipe_id)
        if not recipe:
            return {"error": "Recipe not found"}, 404

        if str(recipe.author_id) != str(current_user_id):
            app_logger.warning(
                f"Unauthorized delete attempt on recipe {recipe_id} by user {current_user_id}",
                extra={"props": {"action": "DELETE_RECIPE", "recipe_id": recipe_id, "user_id": current_user_id, "status": "UNAUTHORIZED"}}
            )
            return {"error": "Unauthorized to delete this recipe"}, 403

        try:
            db.session.delete(recipe)
            db.session.commit()
            
            app_logger.info(
                f"Recipe deleted successfully: {recipe_id}",
                extra={"props": {"action": "DELETE_RECIPE", "recipe_id": recipe_id, "user_id": current_user_id, "status": "SUCCESS"}}
            )
            return {"message": "Recipe deleted successfully"}, 200

        except Exception as e:
            db.session.rollback()
            app_logger.error(
                f"Failed to delete recipe {recipe_id}: {str(e)}",
                extra={"props": {"action": "DELETE_RECIPE", "recipe_id": recipe_id, "user_id": current_user_id, "status": "FAILED", "error": str(e)}}
            )
            return {"error": "Failed to delete recipe"}, 500