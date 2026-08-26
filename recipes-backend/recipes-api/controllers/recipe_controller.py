from sqlalchemy.orm import selectinload

from exceptions import ForbiddenError, NotFoundError
from extensions import db
from models.recipe import Recipe, RecipePart, Ingredient
from app_logging import app_logger  # Import our structured logger
from validation.recipes import validate_recipe_payload

# Pagination defaults. MAX_PAGE_SIZE exists specifically so a client can't
# request pageSize=999999 and defeat the point of paginating at all.
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# Sorting is applied server-side, before pagination - recipes are
# paginated, so sorting only what's already been fetched would silently
# give a wrong answer past page 1 (e.g. the actual cheapest recipe could
# be sitting on page 3). "Lowest first" for prepTime/calories/cost is a
# deliberate default (quickest/lightest/cheapest surfaces first) - not an
# arbitrary column-order choice.
DEFAULT_SORT = 'newest'
SORT_OPTIONS = {
    'newest': Recipe.created_at.desc(),
    'prepTime': Recipe.prep_time_minutes.asc(),
    'calories': Recipe.calories_per_100g.asc(),
    'cost': Recipe.cost_per_100g.asc(),
}


def _parse_positive_int(raw, default):
    """Best-effort int parse that never raises - falls back to `default`
    for anything missing, non-numeric, or <= 0."""
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return default
    return value if value > 0 else default


def _parse_pagination(args):
    """Read page/pageSize from query args, defensively.

    Works whether `args` is a real Flask/Werkzeug MultiDict, a plain dict,
    or None - doesn't rely on MultiDict-specific `type=` conversion.
    """
    args = args or {}

    page = _parse_positive_int(args.get('page'), 1)
    page_size = _parse_positive_int(args.get('pageSize'), DEFAULT_PAGE_SIZE)
    page_size = min(page_size, MAX_PAGE_SIZE)

    return page, page_size


def _parse_sort(args):
    """Read `sort` from query args - any value outside SORT_OPTIONS
    (missing, misspelled, tampered-with) falls back to DEFAULT_SORT
    rather than erroring, matching _parse_pagination's leniency."""
    args = args or {}
    sort = args.get('sort')
    return sort if sort in SORT_OPTIONS else DEFAULT_SORT


class RecipeController:

    @classmethod
    def get_recipes(cls, args=None):
        """Fetch one page of recipes, ordered by `sort` (newest first by
        default).

        Returns a (body, status_code, meta) tuple. `meta` carries
        pagination info for the view to expose as response headers.
        Any DB failure propagates to the app-level error handler instead
        of being caught here.
        """
        page, page_size = _parse_pagination(args)
        sort = _parse_sort(args)

        total = Recipe.query.count()

        recipes = (
            Recipe.query
            .options(
                selectinload(Recipe.author),
                selectinload(Recipe.parts).selectinload(RecipePart.ingredients)
            )
            .order_by(SORT_OPTIONS[sort])
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        app_logger.info(
            "Fetched recipes page",
            extra={
                "props": {
                    "action": "GET_RECIPES_LIST",
                    "page": page,
                    "page_size": page_size,
                    "sort": sort,
                    "count": len(recipes),
                    "total": total,
                    "status": "SUCCESS"
                }
            }
        )

        meta = {"total": total, "page": page, "pageSize": page_size}
        return [recipe.to_dict() for recipe in recipes], 200, meta

    @classmethod
    def get_recipe_by_id(cls, recipe_id):
        """Fetch a single recipe by its UUID."""
        recipe = db.session.get(Recipe, recipe_id)

        if not recipe:
            raise NotFoundError(
                'Recipe not found',
                action="GET_RECIPE", recipe_id=recipe_id, status="NOT_FOUND"
            )

        app_logger.info(
            f"Fetched recipe {recipe_id}",
            extra={"props": {"action": "GET_RECIPE", "recipe_id": recipe_id, "status": "SUCCESS"}}
        )
        return recipe.to_dict(), 200

    @classmethod
    def create_recipe(cls, data, current_user_id):
        validate_recipe_payload(data, partial=False)

        # `.get('parts') or []`, not `.get('parts', [])`: a payload with
        # an explicit `"parts": null` still has the key present, so the
        # default above would never kick in and `new_recipe.parts.append`
        # below would be iterating `None`.
        parts_data = data.get('parts') or []

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

        for part_data in parts_data:
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

    @classmethod
    def update_recipe(cls, recipe_id, data, current_user_id):
        recipe = db.session.get(Recipe, recipe_id)
        if not recipe:
            raise NotFoundError(
                'Recipe not found',
                action="UPDATE_RECIPE", recipe_id=recipe_id, status="NOT_FOUND"
            )

        if str(recipe.author_id) != str(current_user_id):
            raise ForbiddenError(
                'Unauthorized to update this recipe',
                action="UPDATE_RECIPE", recipe_id=recipe_id,
                user_id=current_user_id, status="UNAUTHORIZED"
            )

        validate_recipe_payload(data, partial=True)

        recipe.title = data.get('title', recipe.title)
        recipe.description = data.get('description', recipe.description)
        recipe.image_url = data.get('imageUrl', recipe.image_url)
        recipe.prep_time_minutes = data.get('prepTimeMinutes', recipe.prep_time_minutes)
        recipe.cook_time_minutes = data.get('cookTimeMinutes', recipe.cook_time_minutes)
        recipe.servings = data.get('servings', recipe.servings)
        recipe.total_weight_grams = data.get('totalWeightGrams', recipe.total_weight_grams)
        recipe.cost_per_100g = data.get('costPer100g', recipe.cost_per_100g)
        recipe.calories_per_100g = data.get('caloriesPer100g', recipe.calories_per_100g)

        # `data['parts']` may be `None` here (an explicit `"parts": null`
        # passed validation above as "not provided") - only rebuild parts
        # when it's an actual list, otherwise leave the existing ones alone.
        if 'parts' in data and data['parts'] is not None:
            recipe.parts.clear()
            for part_data in data['parts']:
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
                recipe.parts.append(part)

        db.session.commit()

        app_logger.info(
            f"Recipe updated successfully: {recipe_id}",
            extra={"props": {"action": "UPDATE_RECIPE", "recipe_id": recipe_id, "user_id": current_user_id, "status": "SUCCESS"}}
        )
        return recipe.to_dict(), 200

    @classmethod
    def delete_recipe(cls, recipe_id, current_user_id):
        recipe = db.session.get(Recipe, recipe_id)
        if not recipe:
            raise NotFoundError(
                'Recipe not found',
                action="DELETE_RECIPE", recipe_id=recipe_id, status="NOT_FOUND"
            )

        if str(recipe.author_id) != str(current_user_id):
            raise ForbiddenError(
                'Unauthorized to delete this recipe',
                action="DELETE_RECIPE", recipe_id=recipe_id,
                user_id=current_user_id, status="UNAUTHORIZED"
            )

        db.session.delete(recipe)
        db.session.commit()

        app_logger.info(
            f"Recipe deleted successfully: {recipe_id}",
            extra={"props": {"action": "DELETE_RECIPE", "recipe_id": recipe_id, "user_id": current_user_id, "status": "SUCCESS"}}
        )
        return {"message": "Recipe deleted successfully"}, 200
