import os

from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from prometheus_flask_exporter import PrometheusMetrics

from models.user import db, bcrypt, TokenBlocklist
from views.user_views import user_bp
from views.recipe_views import recipes_bp
from views.system_views import system_bp

metrics = None
jwt = JWTManager()

@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    jti = jwt_payload['jti']

    token = db.session.scalar(
        db.select(TokenBlocklist).where(
            TokenBlocklist.jti == jti
        )
    )

    return token is not None

def get_required_env(name: str) -> str:
    value = os.getenv(name)

    if value is None or not value.strip():
        raise RuntimeError(
            f"Required environment variable '{name}' is not set"
        )

    return value

def configure_app(app):
    """Configure application from required environment variables."""

    # Security
    jwt_secret = get_required_env('JWT_SECRET_KEY')

    app.config['JWT_SECRET_KEY'] = jwt_secret
    app.config['SECRET_KEY'] = jwt_secret

    # Database
    db_scheme = get_required_env('DB_SCHEME')
    db_user = get_required_env('DB_USER_NAME')
    db_pass = get_required_env('DB_PASSWORD')
    db_host = get_required_env('DB_HOST')
    db_port = get_required_env('DB_PORT')
    db_name = get_required_env('DB_NAME')

    app.config['SQLALCHEMY_DATABASE_URI'] = (
        f"{db_scheme}://"
        f"{db_user}:{db_pass}@"
        f"{db_host}:{db_port}/"
        f"{db_name}"
    )

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Server
    app.config['PORT'] = int(get_required_env('PORT'))

    # CORS
    app.config['CORS_ORIGIN'] = get_required_env('CORS_ORIGIN')
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

    if not app.config.get('TESTING', False):

        app_version = get_required_env('APP_VERSION')
        metrics = PrometheusMetrics(app)
        metrics.info(
            'recipes_api_info',
            'Recipes API Metrics',
             version=app_version
        )


def register_blueprints(app):
    app.register_blueprint(user_bp)
    app.register_blueprint(recipes_bp)
    app.register_blueprint(system_bp)

def create_app(config_override=None):
    """Application Factory Pattern."""

    app = Flask(__name__)

    if config_override:
        # Test/custom configuration supplied explicitly
        app.config.update(config_override)
    else:
        # Normal production/development startup
        configure_app(app)

    init_extensions(app)
    register_blueprints(app)

    return app



if __name__ == '__main__':
    port = int(get_required_env('PORT'))
    app = create_app()

    app.run(
        host='0.0.0.0',
        port=port,
        debug=False
    )