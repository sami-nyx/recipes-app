import unittest
from app import create_app  # Or your app factory / app instance
from models.user import db
from models.recipe import Recipe, RecipePart, Ingredient

class BaseTestCase(unittest.TestCase):

    def setUp(self):
        """Executed before each test."""
        self.app = create_app()  # If using factory pattern, or import 'app' directly
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['JWT_SECRET_KEY'] = 'super-secret-test-key-must-be-at-least-32-bytes-long!'
        self.app.config['SECRET_KEY'] = 'super-secret-test-key-must-be-at-least-32-bytes-long!'

        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        """Executed after each test."""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()