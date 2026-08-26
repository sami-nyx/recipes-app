"""Application configuration, loaded from required environment variables.

Extracted from the application factory in `app.py` so config loading,
extension wiring, and blueprint registration each live in their own module.
Every value is validated eagerly by `load_config()` so a missing or blank
environment variable fails fast at startup, not on first request.
"""

import os


def get_required_env(name: str) -> str:
    value = os.getenv(name)

    if value is None or not value.strip():
        raise RuntimeError(
            f"Required environment variable '{name}' is not set"
        )

    return value


def load_config() -> dict:
    """Build the Flask config dict for normal (non-test) startup.

    Order matches the original inline `configure_app()` exactly: which
    variable's error surfaces first if several are missing is unchanged.
    """

    # Security
    # JWT_SECRET_KEY and SECRET_KEY are deliberately separate secrets:
    # one signs auth tokens, the other backs Flask's general-purpose
    # signing (sessions, CSRF, itsdangerous). They should never share a
    # value, so a compromise of one signing context can't be used to
    # forge tokens in the other.
    jwt_secret = get_required_env('JWT_SECRET_KEY')
    secret_key = get_required_env('SECRET_KEY')

    flask_env = get_required_env('FLASK_ENV')

    # Database
    db_scheme = get_required_env('DB_SCHEME')
    db_user = get_required_env('DB_USER_NAME')
    db_pass = get_required_env('DB_PASSWORD')
    db_host = get_required_env('DB_HOST')
    db_port = get_required_env('DB_PORT')
    db_name = get_required_env('DB_NAME')

    # Server
    port = int(get_required_env('PORT'))

    # CORS
    cors_origin = get_required_env('CORS_ORIGIN')

    # Surfaced on /system/health so a deployed build is checkable without
    # needing kubectl - see views/system_views.py.
    app_version = get_required_env('APP_VERSION')

    return {
        'JWT_SECRET_KEY': jwt_secret,
        'SECRET_KEY': secret_key,

        'FLASK_ENV': flask_env,

        'SQLALCHEMY_DATABASE_URI': (
            f"{db_scheme}://"
            f"{db_user}:{db_pass}@"
            f"{db_host}:{db_port}/"
            f"{db_name}"
        ),
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,

        # pool_pre_ping: check a pooled connection is actually alive before
        # handing it to a request, transparently reconnecting if not -
        # otherwise a DB restart/failover surfaces as a random request
        # failure instead of being invisibly retried.
        # pool_recycle: proactively refresh connections older than this so
        # nothing upstream (DB, proxy) gets a chance to silently kill one
        # out from under us first.
        'SQLALCHEMY_ENGINE_OPTIONS': {
            'pool_pre_ping': True,
            'pool_recycle': 1800,
        },

        'PORT': port,

        'CORS_ORIGIN': cors_origin,

        'APP_VERSION': app_version,

        # Reject oversized request bodies (413) before Werkzeug even
        # finishes buffering them. No endpoint here accepts file uploads;
        # 1 MB is generous for a recipe payload's text/JSON.
        'MAX_CONTENT_LENGTH': 1 * 1024 * 1024,
    }
