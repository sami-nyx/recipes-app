from flask import Blueprint, request, jsonify
from controllers.user_controller import UserController

user_bp = Blueprint('user_bp', __name__, url_prefix='/api/users')
@user_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    response_body, status_code = UserController.register_user(data)
    return jsonify(response_body), status_code

@user_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    response_body, status_code = UserController.login_user(data)
    return jsonify(response_body), status_code  
# 💡 GET endpoint for public author/user data by ID
@user_bp.route('/author/<string:author_id>', methods=['GET'])
def get_author(author_id):
    response_body, status_code = UserController.get_author_by_id(author_id)
    return jsonify(response_body), status_code