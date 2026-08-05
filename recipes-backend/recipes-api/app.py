import os
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager  #1

from models.user import db, bcrypt
from views.user_views import user_bp
from views.recipe_views import recipes_bp


def create_app(config_override=None):
    app = Flask(__name__)
    
    # Secret Keys & App Config
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'super-secret-dev-key-123')
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', app.config['SECRET_KEY'])

    # Enable CORS for Angular frontend
    CORS(app, resources={r"/api/*": {"origins": "http://localhost:4200"}})

    # Default PostgreSQL DB Config
    db_user = os.getenv('DB_USER_NAME', 'recipes_user')
    db_pass = os.getenv('DB_PASSWORD', 'recipes_password')
    db_name = os.getenv('DB_NAME', 'recipes_db')
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')

    app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Apply configuration overrides (e.g., in-memory SQLite for testing)
    if config_override:
        app.config.update(config_override)

    # Initialize Extensions AFTER config is finalized
    db.init_app(app)
    bcrypt.init_app(app)
    JWTManager(app)

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