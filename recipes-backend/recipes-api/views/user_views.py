from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity,
    get_jwt
)

from controllers.user_controller import UserController
from extensions import limiter


user_bp = Blueprint(
    'user_bp',
    __name__,
    url_prefix='/api/users'
)


# ============================================================
# Register
# ============================================================

@user_bp.route('/register', methods=['POST'])
@limiter.limit("5 per hour")
def register():
    data = request.get_json(silent=True) or {}

    response_body, status_code = UserController.register_user(data)

    return jsonify(response_body), status_code


# ============================================================
# Login
# ============================================================

@user_bp.route('/login', methods=['POST'])
@limiter.limit("10 per minute")
def login():
    data = request.get_json(silent=True) or {}

    response_body, status_code = UserController.login_user(data)

    return jsonify(response_body), status_code


# ============================================================
# Logout
# ============================================================

@user_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    user_id = get_jwt_identity()
    jti = get_jwt()['jti']

    response_body, status_code = UserController.logout_user(
        user_id=user_id,
        jti=jti
    )

    return jsonify(response_body), status_code


# ============================================================
# Public author profile
# ============================================================

@user_bp.route('/author/<string:author_id>', methods=['GET'])
def get_author(author_id):
    response_body, status_code = (
        UserController.get_author_by_id(author_id)
    )

    return jsonify(response_body), status_code


# ============================================================
# Update user
# ============================================================

@user_bp.route('/<string:user_id>', methods=['PATCH'])
@jwt_required()
def update_user(user_id):
    authenticated_user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}

    response_body, status_code = UserController.update_user(
        user_id=user_id,
        authenticated_user_id=authenticated_user_id,
        data=data
    )

    return jsonify(response_body), status_code


# ============================================================
# Delete user
# ============================================================

@user_bp.route('/<string:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    authenticated_user_id = get_jwt_identity()
    jti = get_jwt()['jti']

    response_body, status_code = UserController.delete_user(
        user_id=user_id,
        authenticated_user_id=authenticated_user_id,
        jti=jti
    )

    return jsonify(response_body), status_code