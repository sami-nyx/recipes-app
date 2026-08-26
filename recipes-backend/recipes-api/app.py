from flask import Flask, jsonify
from flask_cors import CORS
from prometheus_flask_exporter import PrometheusMetrics
from werkzeug.exceptions import HTTPException

from app_logging import app_logger
from config import load_config, get_required_env
from exceptions import ApiError
from extensions import db, bcrypt, jwt, limiter
from models.user import TokenBlocklist
from views.user_views import user_bp
from views.recipe_views import recipes_bp
from views.system_views import system_bp

metrics = None

@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    jti = jwt_payload['jti']

    token = db.session.scalar(
        db.select(TokenBlocklist).where(
            TokenBlocklist.jti == jti
        )
    )

    return token is not None

def init_extensions(app):
    """Initialize Flask extensions."""
    global metrics
    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": app.config['CORS_ORIGIN']
            }
        },
        allow_headers=[
            "Content-Type",
            "Authorization"
        ],
        methods=[
            "GET",
            "POST",
            "PUT",
            "PATCH",
            "DELETE",
            "OPTIONS"
        ]
    )
    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)

    # Disabled under TESTING (the suite hits /register and /login many
    # times across the run) and under FLASK_ENV=development (a developer
    # iterating against a local docker-compose stack hits the same routes
    # repeatedly by hand - re-submitting a form, retrying after a 409,
    # etc). Neither is "real traffic" the limiter is meant to protect
    # against; it stays fully enforced everywhere else, including staging.
    flask_env = (app.config.get('FLASK_ENV') or '').lower()
    app.config['RATELIMIT_ENABLED'] = not (
        app.config.get('TESTING', False) or flask_env == 'development'
    )
    limiter.init_app(app)

    if not app.config.get('TESTING', False):

        metrics = PrometheusMetrics(app)
        metrics.info(
            'recipes_api_info',
            'Recipes API Metrics',
             version=app.config['APP_VERSION']
        )


def register_blueprints(app):
    app.register_blueprint(user_bp)
    app.register_blueprint(recipes_bp)
    app.register_blueprint(system_bp)

def register_error_handlers(app):
    """One place that turns any exception into a JSON response.

    Controllers raise ApiError subclasses (see exceptions.py) instead of
    hand-building an ({...}, status) tuple - this is where that gets
    turned into an actual response, replacing what used to be a
    try/except/rollback/log block duplicated in nearly every controller
    method.
    """

    @app.errorhandler(ApiError)
    def handle_api_error(error):
        app_logger.warning(
            error.message,
            extra={"props": {**error.extra_props, "status_code": error.status_code}}
        )
        body = {"error": error.message, "message": error.message, **error.payload}
        return jsonify(body), error.status_code

    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        # Werkzeug's own exceptions (404 on an unmatched route, 405, 413
        # from MAX_CONTENT_LENGTH, ...) - preserve their status/message
        # instead of falling through to the generic 500 handler below.
        return jsonify({"error": error.description, "message": error.description}), error.code

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        # Anything else: a real bug or DB failure. Roll back so a failed
        # request can't leave a half-committed session behind, log the
        # full traceback for us, and never leak internals to the client.
        db.session.rollback()
        app_logger.exception(
            "Unhandled exception",
            extra={"props": {"error": str(error)}}
        )
        message = "An internal error occurred"
        return jsonify({"error": message, "message": message}), 500

def create_app(config_override=None):
    """Application Factory Pattern."""

    app = Flask(__name__)

    if config_override:
        # Test/custom configuration supplied explicitly
        app.config.update(config_override)
    else:
        # Normal production/development startup
        app.config.update(load_config())

    init_extensions(app)
    register_blueprints(app)
    register_error_handlers(app)
    if app.config.get('FLASK_ENV').lower() == 'development' or app.config.get('FLASK_ENV').lower() == 'test' :
        with app.app_context():
            db.create_all()
    return app



if __name__ == '__main__':
    port = int(get_required_env('PORT'))
    app = create_app()

    app.run(
        host='0.0.0.0',
        port=port,
        debug=False
    )