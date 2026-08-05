import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from models.user import db, bcrypt, User  # Import models so db.create_all() registers them
from models.recipe import Recipe
from views.user_views import user_bp
from views.recipe_views import recipes_bp


def create_app(config_override=None):
    app = Flask(__name__)
    
  # 32+ character fallback key
    FALLBACK_KEY = 'recipes-dev-secret-key-must-be-at-least-32-bytes'

    # Read environment variables
    secret_key = os.getenv('SECRET_KEY') or os.getenv('JWT_SECRET_KEY') or FALLBACK_KEY
    
    # Ensure BOTH configs use the exact same key string
    app.config['SECRET_KEY'] = secret_key
    app.config['JWT_SECRET_KEY'] = secret_key
    # Enable CORS for Angular frontend
    CORS(
        app, 
        resources={r"/api/*": {"origins": "*"}},
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    )

    # PostgreSQL DB Config
    db_user = os.getenv('DB_USER_NAME', 'recipes_user')
    db_pass = os.getenv('DB_PASSWORD', 'recipes_password')
    db_name = os.getenv('DB_NAME', 'recipes_db')
    db_host = os.getenv('DB_HOST', 'postgres')  # Defaults to 'postgres' service name in Docker Compose
    db_port = os.getenv('DB_PORT', '5432')

    app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Apply configuration overrides (e.g., in-memory SQLite for testing)
    if config_override:
        app.config.update(config_override)

    # Initialize Extensions AFTER config is finalized
    db.init_app(app)
    bcrypt.init_app(app)
    
    jwt = JWTManager(app)

    # --- JWT DEBUG CALLBACKS ---
    @jwt.invalid_token_loader
    def custom_invalid_token_callback(error_string):
        print(f"--> [JWT ERROR] Invalid Token: {error_string}")
        return jsonify({
            "message": "Signature verification failed or token malformed. Please log out and log in again.",
            "error": error_string
        }), 422

    @jwt.unauthorized_loader
    def custom_missing_token_callback(error_string):
        print(f"--> [JWT ERROR] Missing Authorization Header: {error_string}")
        return jsonify({
            "message": "Request is missing the Authorization header (Bearer <token>).",
            "error": error_string
        }), 422

    @jwt.expired_token_loader
    def custom_expired_token_callback(jwt_header, jwt_payload):
        print(f"--> [JWT ERROR] Expired Token for subject: {jwt_payload.get('sub')}")
        return jsonify({
            "message": "Token has expired. Please log in again.",
            "error": "token_expired"
        }), 401

    # Register Blueprints / Views
    app.register_blueprint(user_bp)
    app.register_blueprint(recipes_bp)

    return app


app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("Connected to PostgreSQL & initialized tables.")

    app.run(host='0.0.0.0', port=5000, debug=True)