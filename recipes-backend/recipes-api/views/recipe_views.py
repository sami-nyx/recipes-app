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
    # No try/except here on purpose: any failure (an ApiError the
    # controller raises, or a genuine DB error) is caught once, centrally,
    # by the app-level error handlers in app.py - not re-caught per view.
    response_body, status_code, meta = RecipeController.get_recipes(request.args)
    response = jsonify(response_body)

    response.headers['X-Total-Count'] = str(meta['total'])
    response.headers['X-Page'] = str(meta['page'])
    response.headers['X-Page-Size'] = str(meta['pageSize'])

    return response, status_code

@recipes_bp.route('/<string:recipe_id>', methods=['GET'])
def get_recipe(recipe_id):
    response_body, status_code = RecipeController.get_recipe_by_id(recipe_id)
    return jsonify(response_body), status_code

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