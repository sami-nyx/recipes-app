import os
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from prometheus_flask_exporter import PrometheusMetrics

from models.user import db, bcrypt
from views.user_views import user_bp
from views.recipe_views import recipes_bp
from views.system_views import system_bp

# Global placeholder for metrics if needed across blueprints
metrics = None

def configure_app(app):
    """Handles application configurations and environment variables."""
    # 1. Secret Key Configuration
    FALLBACK_KEY = 'recipes-dev-secret-key-must-be-at-least-32-bytes'
    secret_key = os.getenv('SECRET_KEY') or os.getenv('JWT_SECRET_KEY') or FALLBACK_KEY
    app.config['SECRET_KEY'] = secret_key
    app.config['JWT_SECRET_KEY'] = secret_key

    # 2. Database Configuration
    db_scheme = os.getenv('DB_SCHEME', 'postgresql+psycopg2')
    db_user   = os.getenv('DB_USER_NAME', 'recipes_user')
    db_pass   = os.getenv('DB_PASSWORD', 'recipes_password')
    db_host   = os.getenv('DB_HOST', 'localhost')
    db_port   = os.getenv('DB_PORT', '5432')
    db_name   = os.getenv('DB_NAME', 'recipes_db')

    app.config['SQLALCHEMY_DATABASE_URI'] = f"{db_scheme}://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

def init_extensions(app):
    """Initializes all Flask extensions and third-party integrations."""
    global metrics

    # CORS
    CORS(
        app, 
        resources={r"/api/*": {"origins": "*"}},
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    )

    # Core Database & Security Extensions
    db.init_app(app)
    bcrypt.init_app(app)
    JWTManager(app)

    # Prometheus Metrics 
    metrics = PrometheusMetrics(app)
    metrics.info('recipe_app_info', 'Recipe Application Metrics', version='1.0.0')

def register_blueprints(app):
    """Registers all application blueprints/views."""
    app.register_blueprint(user_bp)
    app.register_blueprint(recipes_bp)
    app.register_blueprint(system_bp)

def create_app(config_override=None):
    """Application Factory Pattern."""
    app = Flask(__name__)

    # Load configurations
    configure_app(app)

    # Apply testing or custom overrides if passed
    if config_override:
        app.config.update(config_override)

    # Initialize extensions and blueprints
    init_extensions(app)
    register_blueprints(app)

    return app

# Instantiate the application
app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("Connected to PostgreSQL & initialized tables.")

    # Main API server port using env var with fallback to 5000
    app_port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=app_port, debug=False)