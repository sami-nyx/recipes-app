import unittest

from app import create_app
from extensions import db
from models.recipe import Recipe, RecipePart, Ingredient


class BaseTestCase(unittest.TestCase):

    def setUp(self):
        """Executed before each test."""

        self.app = create_app({
            'TESTING': True,

            'FLASK_ENV': 'development',
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'SQLALCHEMY_TRACK_MODIFICATIONS': False,

            'JWT_SECRET_KEY':
                'super-secret-test-key-must-be-at-least-32-bytes-long!',

            'SECRET_KEY':
                'super-secret-test-key-must-be-at-least-32-bytes-long!',

            'CORS_ORIGIN': 'http://localhost:4200',

            'MAX_CONTENT_LENGTH': 1 * 1024 * 1024
        })

        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        """Executed after each test."""

        with self.app.app_context():
            db.session.remove()
            db.drop_all()