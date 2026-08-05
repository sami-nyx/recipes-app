import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from models.user import db, bcrypt, User  
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
    db_scheme = os.getenv('DB_SCHEME', 'postgresql+psycopg2')
    db_user   = os.getenv('DB_USER_NAME', 'recipes_user')
    db_pass   = os.getenv('DB_PASSWORD', 'recipes_password')
    db_host   = os.getenv('DB_HOST', 'localhost')
    db_port   = os.getenv('DB_PORT', '5432')
    db_name   = os.getenv('DB_NAME', 'recipes_db')

    app.config['SQLALCHEMY_DATABASE_URI'] = f"{db_scheme}://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Apply configuration overrides (e.g., in-memory SQLite for testing)
    if config_override:
        app.config.update(config_override)

    # Initialize Extensions AFTER config is finalized
    db.init_app(app)
    bcrypt.init_app(app)
    
    jwt = JWTManager(app)

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