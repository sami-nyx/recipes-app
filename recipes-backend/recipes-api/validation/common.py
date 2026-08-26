"""Small, dependency-free input-validation helpers.

Shared by resource-specific validators (see `validation/recipes.py`) so
each one only has to declare *which* fields it needs and with what
constraints, not re-implement the same type/length checks. Every
function raises `BadRequestError` on the spot - matching the "raise a
typed exception, let app.py's centralized handler turn it into a
response" idiom the rest of the app already uses (see exceptions.py)
- rather than returning a schema library is deliberately *not* used
here (see recipes-api-enhancements.md item 4): the app has no such
dependency today, and adding one is a separate decision from closing
the actual gap, which is that recipe input wasn't being checked at all.
"""

from exceptions import BadRequestError


def require_string(data, field, action, *, max_length=None):
    """`field` must be present and a non-blank string; returns it stripped.

    Used for fields the database itself requires (`NOT NULL`) - e.g.
    Recipe.title, Ingredient.name - where a missing/blank value would
    otherwise reach the database and fail there instead of here.
    """
    value = data.get(field)

    if not isinstance(value, str) or not value.strip():
        raise BadRequestError(
            f'{field} is required',
            action=action, status="BAD_REQUEST", missing_field=field
        )

    value = value.strip()

    if max_length is not None and len(value) > max_length:
        raise BadRequestError(
            f'{field} cannot exceed {max_length} characters',
            action=action, status="BAD_REQUEST", field=field
        )

    return value


def optional_string(data, field, action, *, max_length=None):
    """If present and non-null, `field` must be a string.

    Absent, or explicitly `null`, is treated as "not provided" and
    returns None without error - the caller/model default applies.
    """
    if field not in data or data[field] is None:
        return None

    value = data[field]

    if not isinstance(value, str):
        raise BadRequestError(
            f'{field} must be a string',
            action=action, status="BAD_REQUEST", field=field
        )

    value = value.strip()

    if max_length is not None and len(value) > max_length:
        raise BadRequestError(
            f'{field} cannot exceed {max_length} characters',
            action=action, status="BAD_REQUEST", field=field
        )

    return value


def optional_number(data, field, action, *, minimum=None):
    """If present and non-null, `field` must be an int/float (not bool -
    `isinstance(True, int)` is True in Python, so booleans are excluded
    explicitly) and >= `minimum` when one is given.
    """
    if field not in data or data[field] is None:
        return None

    value = data[field]

    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise BadRequestError(
            f'{field} must be a number',
            action=action, status="BAD_REQUEST", field=field
        )

    if minimum is not None and value < minimum:
        raise BadRequestError(
            f'{field} cannot be less than {minimum}',
            action=action, status="BAD_REQUEST", field=field
        )

    return value


def optional_string_list(data, field, action):
    """If present and non-null, `field` must be a list of strings."""
    if field not in data or data[field] is None:
        return None

    value = data[field]

    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise BadRequestError(
            f'{field} must be a list of strings',
            action=action, status="BAD_REQUEST", field=field
        )

    return value
