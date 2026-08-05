import os
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager 

from models.user import db, bcrypt
from views.user_views import user_bp
from views.recipe_views import recipes_bp   #axaxaxxxx

def create_app():
    app = Flask(__name__)
    
    # Secret Keys & App Config
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'super-secret-dev-key-123')
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', app.config['SECRET_KEY']) # <--- Added JWT secret key

    # Enable CORS for Angular frontend
    CORS(app, resources={r"/api/*": {"origins": "http://localhost:4200"}})

    # DB Config
    db_user = os.getenv('DB_USER_NAME', 'recipes_user')
    db_pass = os.getenv('DB_PASSWORD', 'recipes_password')
    db_name = os.getenv('DB_NAME', 'recipes_db')
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')

    app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize Extensions
    db.init_app(app)
    bcrypt.init_app(app)
    JWTManager(app) # <--- Initialize JWT extension

    # Register Blueprints / Views
    app.register_blueprint(user_bp)
    app.register_blueprint(recipes_bp) # <--- Register recipes_bp here!

    return app


app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("Connected to PostgreSQL & initialized tables.")

    app.run(host='0.0.0.0', port=5000, debug=True)