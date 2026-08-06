import uuid
from datetime import datetime, timezone
from models.user import db  # Importing shared db instance from user.py

def generate_uuid():
    return str(uuid.uuid4())

class Recipe(db.Model):
    __tablename__ = 'recipes'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(500), nullable=True)
    prep_time_minutes = db.Column(db.Integer, default=0)
    cook_time_minutes = db.Column(db.Integer, default=0)
    servings = db.Column(db.Integer, default=1)
    total_weight_grams = db.Column(db.Float, default=0.0)
    cost_per_100g = db.Column(db.Float, default=0.0)
    calories_per_100g = db.Column(db.Float, default=0.0)
    favs_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    author_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    author = db.relationship('User', backref=db.backref('recipes', lazy=True))

    # Relationship to Recipe Parts (cascade delete cleans up parts when recipe is deleted)
    parts = db.relationship('RecipePart', backref='recipe', cascade="all, delete-orphan", lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description or '',
            'imageUrl': self.image_url or '',
            'prepTimeMinutes': self.prep_time_minutes,
            'cookTimeMinutes': self.cook_time_minutes,
            'servings': self.servings,
            'totalWeightGrams': self.total_weight_grams,
            'costPer100g': self.cost_per_100g,
            'caloriesPer100g': self.calories_per_100g,
            'favsCount': self.favs_count,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'author': self.author.to_dict() if self.author and hasattr(self.author, 'to_dict') else None,
            'parts': [part.to_dict() for part in self.parts]
        }


class RecipePart(db.Model):
    __tablename__ = 'recipe_parts'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    recipe_id = db.Column(db.String(36), db.ForeignKey('recipes.id'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    instructions = db.Column(db.JSON, default=list)  # Stores array of strings

    ingredients = db.relationship('Ingredient', backref='part', cascade="all, delete-orphan", lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'instructions': self.instructions or [],
            'ingredients': [ing.to_dict() for ing in self.ingredients]
        }


class Ingredient(db.Model):
    __tablename__ = 'ingredients'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    part_id = db.Column(db.String(36), db.ForeignKey('recipe_parts.id'), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    amount = db.Column(db.Float, nullable=False, default=0.0)
    unit = db.Column(db.String(50), nullable=False, default='g')
    cost_per_100g = db.Column(db.Float, default=0.0)
    calories_per_100g = db.Column(db.Float, default=0.0)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'amount': self.amount,
            'unit': self.unit,
            'costPer100g': self.cost_per_100g,
            'caloriesPer100g': self.calories_per_100g
        }