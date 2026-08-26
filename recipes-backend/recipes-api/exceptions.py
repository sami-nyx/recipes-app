"""Typed exceptions for expected, business-logic error conditions.

Controllers raise these instead of hand-building an ({...}, status_code)
tuple and duplicating try/except/rollback/log boilerplate at every call
site. The handlers registered in app.py (`register_error_handlers`) catch
them exactly once, log them, and shape the JSON response - so every error
across the whole API comes out the same way.

Anything that ISN'T one of these (a real database failure, a bug) is left
to raise naturally and is caught by the generic Exception handler instead,
which rolls back the session and returns a generic 500 without leaking
internals.
"""


class ApiError(Exception):
    """Base class for a deliberately-raised, expected API error.

    `payload` is merged into the JSON response body alongside "error"/
    "message" (e.g. the {'fields': [...]} list on a rejected update).
    `extra_props` is forwarded to the structured logger only, not the
    response - it's the same "action"/"status"/entity-id context that
    used to be logged at each call site, preserved even though the
    actual logging call now happens once, centrally.
    """

    status_code = 500

    def __init__(self, message: str, payload: dict = None, **extra_props):
        super().__init__(message)
        self.message = message
        self.payload = payload or {}
        self.extra_props = extra_props


class BadRequestError(ApiError):
    status_code = 400


class UnauthorizedError(ApiError):
    status_code = 401


class ForbiddenError(ApiError):
    status_code = 403


class NotFoundError(ApiError):
    status_code = 404


class ConflictError(ApiError):
    status_code = 409
