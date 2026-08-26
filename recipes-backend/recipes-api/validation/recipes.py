"""Input validation for recipe create/update payloads.

Pulled out of RecipeController so "is this payload shaped correctly"
lives separately from "how do we persist it" - see
recipes-api-enhancements.md item 4. `RecipeController` calls
`validate_recipe_payload()` once, up front, before touching the
database; every check below only ever raises `BadRequestError` (400)
or returns.
"""

from exceptions import BadRequestError
from validation.common import (
    optional_number,
    optional_string,
    optional_string_list,
    require_string,
)

ACTION = "VALIDATE_RECIPE"

# Same ceiling this used to enforce inline in recipe_controller.py - kept
# here instead so the size limit lives next to the rest of the shape
# validation for `parts`/`ingredients`.
MAX_PARTS_PER_RECIPE = 50
MAX_INGREDIENTS_PER_PART = 50

# Mirrors the column lengths in models/recipe.py - kept in sync deliberately
# so a too-long value is rejected here (400, clear message) instead of
# reaching Postgres and failing there (500, opaque, and - for sqlite,
# used in tests - not enforced at all, so the bug would only show up
# in Postgres/production).
TITLE_MAX_LENGTH = 150
IMAGE_URL_MAX_LENGTH = 500
INGREDIENT_NAME_MAX_LENGTH = 150
UNIT_MAX_LENGTH = 50


def validate_recipe_payload(data, *, partial=False):
    """Validate a recipe create (`partial=False`) or update
    (`partial=True`) payload. Raises `BadRequestError` on the first
    invalid field; returns None if the payload is well-formed.

    `partial=True` (update) treats every field, including `title`, as
    optional - the controller only overwrites fields that are actually
    present in `data` - but still validates any field that *is* present.
    `partial=False` (create) additionally requires `title`, matching
    the database's `NOT NULL` constraint on `Recipe.title`.
    """
    if not isinstance(data, dict):
        raise BadRequestError('Request body must be a JSON object', action=ACTION, status="BAD_REQUEST")

    if partial:
        if 'title' in data:
            require_string(data, 'title', ACTION, max_length=TITLE_MAX_LENGTH)
    else:
        require_string(data, 'title', ACTION, max_length=TITLE_MAX_LENGTH)

    optional_string(data, 'description', ACTION)
    optional_string(data, 'imageUrl', ACTION, max_length=IMAGE_URL_MAX_LENGTH)
    optional_number(data, 'prepTimeMinutes', ACTION, minimum=0)
    optional_number(data, 'cookTimeMinutes', ACTION, minimum=0)
    optional_number(data, 'servings', ACTION, minimum=1)
    optional_number(data, 'totalWeightGrams', ACTION, minimum=0)
    optional_number(data, 'costPer100g', ACTION, minimum=0)
    optional_number(data, 'caloriesPer100g', ACTION, minimum=0)

    if 'parts' in data and data['parts'] is not None:
        validate_parts(data['parts'])


def validate_parts(parts_data):
    """Validate the `parts` array of a recipe payload (and each part's
    nested `ingredients`)."""
    if not isinstance(parts_data, list):
        raise BadRequestError('parts must be a list', action=ACTION, status="BAD_REQUEST")

    if len(parts_data) > MAX_PARTS_PER_RECIPE:
        raise BadRequestError(
            f"A recipe can have at most {MAX_PARTS_PER_RECIPE} parts",
            action=ACTION, status="BAD_REQUEST"
        )

    for part_data in parts_data:
        if not isinstance(part_data, dict):
            raise BadRequestError('Each part must be an object', action=ACTION, status="BAD_REQUEST")

        optional_string(part_data, 'title', ACTION, max_length=TITLE_MAX_LENGTH)
        optional_string_list(part_data, 'instructions', ACTION)

        ingredients = part_data.get('ingredients') or []

        if not isinstance(ingredients, list):
            raise BadRequestError('ingredients must be a list', action=ACTION, status="BAD_REQUEST")

        if len(ingredients) > MAX_INGREDIENTS_PER_PART:
            raise BadRequestError(
                f"A part can have at most {MAX_INGREDIENTS_PER_PART} ingredients",
                action=ACTION, status="BAD_REQUEST"
            )

        for ing_data in ingredients:
            if not isinstance(ing_data, dict):
                raise BadRequestError('Each ingredient must be an object', action=ACTION, status="BAD_REQUEST")

            require_string(ing_data, 'name', ACTION, max_length=INGREDIENT_NAME_MAX_LENGTH)
            optional_number(ing_data, 'amount', ACTION, minimum=0)
            optional_string(ing_data, 'unit', ACTION, max_length=UNIT_MAX_LENGTH)
            optional_number(ing_data, 'costPer100g', ACTION, minimum=0)
            optional_number(ing_data, 'caloriesPer100g', ACTION, minimum=0)
