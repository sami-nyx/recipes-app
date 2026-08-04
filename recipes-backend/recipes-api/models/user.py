import uuid
import jwt
from datetime import datetime, timedelta, timezone
from flask import current_app
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
bcrypt = Bcrypt()

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    avatar_url = db.Column(db.String(255), nullable=True)
    bio = db.Column(db.Text, nullable=True)

    def set_password(self, password: str):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password: str) -> bool:
        return bcrypt.check_password_hash(self.password_hash, password)
    def generate_token(self, expires_in_hours=24) -> str:
        """Generates a signed JWT access token for this user."""
        payload = {
            'sub': self.id,
            'username': self.username,
            'email': self.email,
            'iat': datetime.now(timezone.utc),
            'exp': datetime.now(timezone.utc) + timedelta(hours=expires_in_hours)
        }
        secret = current_app.config.get('SECRET_KEY', 'dev-secret-key')
        return jwt.encode(payload, secret, algorithm='HS256')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'username': self.username,
            'email': self.email,
            'avatarUrl': self.avatar_url,
            'bio': self.bio
        }