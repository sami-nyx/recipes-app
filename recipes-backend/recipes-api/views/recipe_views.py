from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from controllers.recipe_controller import RecipeController
from models.recipe import Recipe

recipes_bp = Blueprint('recipes_bp', __name__, url_prefix='/api/recipes')

@recipes_bp.route('/create', methods=['POST'])
@jwt_required()
def create_recipe():
    data = request.get_json() or {}
    current_user_id = get_jwt_identity()
    response_body, status_code = RecipeController.create_recipe(data, current_user_id)
    return jsonify(response_body), status_code

@recipes_bp.route('', methods=['GET'])
def get_recipes():
    try:
        response_body, status_code = RecipeController.get_recipes(request.args)
        return jsonify(response_body), status_code
    except Exception as e:
        print(f"Error fetching recipes: {e}")
        return jsonify([]), 200


# --- UPDATE / EDIT RECIPE ROUTE ---
@recipes_bp.route('/<string:recipe_id>', methods=['PUT'])
@jwt_required()
def update_recipe(recipe_id):
    
    data = request.get_json() or {}
    current_user_id = get_jwt_identity()
    
    response_body, status_code = RecipeController.update_recipe(recipe_id, data, current_user_id)
    return jsonify(response_body), status_code

@recipes_bp.route('/<string:recipe_id>', methods=['DELETE'])
@jwt_required()
def delete_recipe(recipe_id):
    current_user_id = get_jwt_identity()
    response_body, status_code = RecipeController.delete_recipe(recipe_id, current_user_id)
    return jsonify(response_body), status_code