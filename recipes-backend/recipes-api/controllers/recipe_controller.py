from models.recipe import Recipe, RecipePart, Ingredient
from models.user import db

class RecipeController:

    @classmethod
    def get_recipes(cls, args=None):
        """Fetch all recipes ordered by creation date (newest first)."""
        try:
            # Query all recipes ordered by creation date descending
            recipes = Recipe.query.order_by(Recipe.created_at.desc()).all()
            return [recipe.to_dict() for recipe in recipes], 200
        except Exception as e:
            print(f"Error fetching recipes in controller: {e}")
            return {"error": "Failed to fetch recipes"}, 500

    @classmethod
    def get_recipe_by_id(cls, recipe_id):
        """Fetch a single recipe by its UUID."""
        try:
            recipe = Recipe.query.get(recipe_id)
            if not recipe:
                return {"error": "Recipe not found"}, 404
            return recipe.to_dict(), 200
        except Exception as e:
            print(f"Error fetching recipe {recipe_id}: {e}")
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

            # Handle parts & ingredients if present in payload
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

            return new_recipe.to_dict(), 201

        except Exception as e:
            db.session.rollback()
            print(f"Error creating recipe: {e}")
            return {"error": "Failed to create recipe"}, 500

    @classmethod
    def update_recipe(cls, recipe_id, data, current_user_id):
        recipe = db.session.get(Recipe, recipe_id)
        if not recipe:
            return {"error": "Recipe not found"}, 404

        if str(recipe.author_id) != str(current_user_id):
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
            return recipe.to_dict(), 200

        except Exception as e:
            db.session.rollback()
            print(f"Error updating recipe {recipe_id}: {e}")
            return {"error": "Failed to update recipe"}, 500


    @classmethod
    def delete_recipe(cls, recipe_id, current_user_id):
        # 1. Fetch recipe using modern SQLAlchemy 2.0 syntax
        recipe = db.session.get(Recipe, recipe_id)
        if not recipe:
            return {"error": "Recipe not found"}, 404

        # 2. Authorization check: Ensure only the author can delete
        if str(recipe.author_id) != str(current_user_id):
            return {"error": "Unauthorized to delete this recipe"}, 403

        try:
            # 3. Delete from DB (cascade rules will automatically clean up parts and ingredients)
            db.session.delete(recipe)
            db.session.commit()
            return {"message": "Recipe deleted successfully"}, 200

        except Exception as e:
            db.session.rollback()
            print(f"Error deleting recipe {recipe_id}: {e}")
            return {"error": "Failed to delete recipe"}, 500