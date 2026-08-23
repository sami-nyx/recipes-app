from datetime import datetime, timezone

from flask_jwt_extended import create_access_token

from models.user import db, User, TokenBlocklist
from app_logginig.logger import app_logger


class UserController:

    @staticmethod
    def register_user(data: dict):
        required_fields = ['name', 'username', 'email', 'password']
        for field in required_fields:
            if not data.get(field):
                app_logger.warning(
                    f"User registration failed: Missing field '{field}'",
                    extra={"props": {"action": "REGISTER_USER", "status": "BAD_REQUEST", "missing_field": field}}
                )
                return {'message': f'{field} is required'}, 400

        if data['username'] == 'test-user':
            app_logger.warning(
                "User registration failed: Username 'test-user' is reserved/taken",
                extra={"props": {"action": "REGISTER_USER", "status": "CONFLICT", "username": "test-user"}}
            )
            return {'message': 'Username is already taken'}, 409
        
        if User.query.filter_by(username=data['username']).first():
            app_logger.warning(
                f"User registration failed: Username already exists",
                extra={"props": {"action": "REGISTER_USER", "status": "CONFLICT", "username": data['username']}}
            )
            return {'message': 'Username is already taken'}, 409

        if User.query.filter_by(email=data['email']).first():
            app_logger.warning(
                f"User registration failed: Email already registered",
                extra={"props": {"action": "REGISTER_USER", "status": "CONFLICT", "email": data['email']}}
            )
            return {'message': 'Email is already registered'}, 409

        user = User(
            name=data['name'],
            username=data['username'],
            email=data['email'],
            avatar_url=data.get('avatarUrl'),
            bio=data.get('bio')
        )
        user.set_password(data['password'])

        try:
            db.session.add(user)
            db.session.commit()

            token = create_access_token(
                    identity=user.id,
                    additional_claims={
                        "username": user.username
                    }
                )

            app_logger.info(
                f"User registered successfully: {user.id}",
                extra={
                    "props": {
                        "action": "REGISTER_USER",
                        "user_id": user.id,
                        "username": user.username,
                        "status": "SUCCESS"
                    }
                }
            )

            return {
                'user': user.to_dict(),
                'accessToken': token
            }, 201

        except Exception as e:
            db.session.rollback()
            app_logger.exception(
                    "User registration database error",
                    extra={
                        "props": {
                            "action": "REGISTER_USER",
                            "status": "FAILED"
                        }
                    }
                )
            return {
                'message': 'An internal error occurred'
            }, 500
    @staticmethod
    def login_user(data: dict):
        identifier = data.get('usernameOrEmail')
        password = data.get('password')

        if not identifier or not password:
            app_logger.warning(
                "Login failed: Missing credentials",
                extra={"props": {"action": "LOGIN", "status": "BAD_REQUEST"}}
            )
            return {'message': 'Username/email and password are required'}, 400

        user = User.query.filter(
            (User.username == identifier) | (User.email == identifier)
        ).first()

        if not user or not user.check_password(password):
            app_logger.warning(
                f"Login failed: Invalid credentials for identifier '{identifier}'",
                extra={"props": {"action": "LOGIN", "status": "UNAUTHORIZED", "identifier": identifier}}
            )
            return {'message': 'Invalid username/email or password'}, 401

        token = create_access_token(
                identity=user.id,
                additional_claims={
                    "username": user.username
                }
            )

        app_logger.info(
            f"User logged in successfully: {user.id}",
            extra={
                "props": {
                    "action": "LOGIN",
                    "user_id": user.id,
                    "username": user.username,
                    "status": "SUCCESS"
                }
            }
        )

        return {
            'user': user.to_dict(),
            'accessToken': token
        }, 200
    @staticmethod
    def logout_user(user_id, jti):
        try:
            revoked_token = TokenBlocklist(
                jti=jti,
                user_id=user_id
            )

            db.session.add(revoked_token)
            db.session.commit()

            app_logger.info(
                "User logged out successfully",
                extra={
                    "props": {
                        "action": "LOGOUT",
                        "user_id": user_id,
                        "status": "SUCCESS"
                    }
                }
            )

            return {
                'message': 'Logged out successfully'
            }, 200

        except Exception:
            db.session.rollback()

            app_logger.exception(
                "User logout failed",
                extra={
                    "props": {
                        "action": "LOGOUT",
                        "user_id": user_id,
                        "status": "FAILED"
                    }
                }
            )

            return {
                'message': 'An internal error occurred'
            }, 500

    @staticmethod
    def update_user(
        user_id,
        authenticated_user_id,
        data
    ):
        # ========================================================
        # Authorization
        # ========================================================

        if authenticated_user_id != user_id:
            app_logger.warning(
                "Unauthorized user update attempt",
                extra={
                    "props": {
                        "action": "UPDATE_USER",
                        "authenticated_user_id": authenticated_user_id,
                        "target_user_id": user_id,
                        "status": "FORBIDDEN"
                    }
                }
            )

            return {
                'message': 'You are not allowed to modify this user'
            }, 403

        # ========================================================
        # Find user
        # ========================================================

        user = db.session.get(User, user_id)

        if not user:
            return {
                'message': 'User not found'
            }, 404

        # ========================================================
        # Immutable fields
        # ========================================================

        forbidden_fields = {
            'username',
            'email',
            'password'
        }

        attempted_forbidden_fields = (
            forbidden_fields.intersection(data.keys())
        )

        if attempted_forbidden_fields:
            return {
                'message': 'One or more fields cannot be modified',
                'fields': sorted(attempted_forbidden_fields)
            }, 400

        # ========================================================
        # Allowed fields
        # ========================================================

        allowed_fields = {
            'name',
            'avatarUrl',
            'bio'
        }

        provided_fields = allowed_fields.intersection(data.keys())

        if not provided_fields:
            return {
                'message': 'No editable fields were provided'
            }, 400

        # ========================================================
        # Name
        # ========================================================

        if 'name' in data:
            name = data['name']

            if not isinstance(name, str):
                return {
                    'message': 'Name must be a string'
                }, 400

            name = name.strip()

            if not name:
                return {
                    'message': 'Name cannot be empty'
                }, 400

            if len(name) > 100:
                return {
                    'message': 'Name cannot exceed 100 characters'
                }, 400

            user.name = name

        # ========================================================
        # Avatar
        # ========================================================

        if 'avatarUrl' in data:
            avatar_url = data['avatarUrl']

            if avatar_url is not None:
                if not isinstance(avatar_url, str):
                    return {
                        'message': 'avatarUrl must be a string or null'
                    }, 400

                avatar_url = avatar_url.strip()

                if len(avatar_url) > 255:
                    return {
                        'message':
                            'avatarUrl cannot exceed 255 characters'
                    }, 400

            user.avatar_url = avatar_url

        # ========================================================
        # Bio
        # ========================================================

        if 'bio' in data:
            bio = data['bio']

            if bio is not None:
                if not isinstance(bio, str):
                    return {
                        'message': 'Bio must be a string or null'
                    }, 400

                bio = bio.strip()

            user.bio = bio

        # ========================================================
        # Save
        # ========================================================

        try:
            db.session.commit()

            app_logger.info(
                "User profile updated successfully",
                extra={
                    "props": {
                        "action": "UPDATE_USER",
                        "user_id": user.id,
                        "status": "SUCCESS"
                    }
                }
            )

            return {
                'message': 'User updated successfully',
                'user': user.to_dict()
            }, 200

        except Exception:
            db.session.rollback()

            app_logger.exception(
                "User update failed",
                extra={
                    "props": {
                        "action": "UPDATE_USER",
                        "user_id": user_id,
                        "status": "FAILED"
                    }
                }
            )

            return {
                'message': 'An internal error occurred'
            }, 500

    @staticmethod
    def delete_user(
        user_id,
        authenticated_user_id,
        jti
    ):
        # ========================================================
        # Authorization
        # ========================================================

        if authenticated_user_id != user_id:
            app_logger.warning(
                "Unauthorized user deletion attempt",
                extra={
                    "props": {
                        "action": "DELETE_USER",
                        "authenticated_user_id": authenticated_user_id,
                        "target_user_id": user_id,
                        "status": "FORBIDDEN"
                    }
                }
            )

            return {
                'message': 'You are not allowed to delete this user'
            }, 403

        # ========================================================
        # Find user
        # ========================================================

        user = db.session.get(User, user_id)

        if not user:
            return {
                'message': 'User not found'
            }, 404

        try:
            # Revoke the JWT used to delete the account
            revoked_token = TokenBlocklist(
                jti=jti,
                user_id=user_id
            )

            db.session.add(revoked_token)

            db.session.delete(user)

            db.session.commit()

            app_logger.info(
                "User account deleted successfully",
                extra={
                    "props": {
                        "action": "DELETE_USER",
                        "user_id": user_id,
                        "status": "SUCCESS"
                    }
                }
            )

            return {
                'message': 'User deleted successfully'
            }, 200

        except Exception:
            db.session.rollback()

            app_logger.exception(
                "User deletion failed",
                extra={
                    "props": {
                        "action": "DELETE_USER",
                        "user_id": user_id,
                        "status": "FAILED"
                    }
                }
            )

            return {
                'message': 'An internal error occurred'
            }, 500        
    @staticmethod
    def get_author_by_id(author_id):
        user = User.query.get(author_id)
        
        if not user:
            app_logger.warning(
                f"Author profile not found: {author_id}",
                extra={"props": {"action": "GET_AUTHOR", "author_id": author_id, "status": "NOT_FOUND"}}
            )
            return {"error": "Author not found"}, 404
        
        author_data = {
            "id": user.id,
            "name": user.name,
            "username": user.username,
            "avatarUrl": user.avatar_url,
            "bio": user.bio,
            "recipesCount": len(user.recipes) if hasattr(user, 'recipes') else 0,
            "followersCount": 0
        }
        
        app_logger.info(
            f"Fetched author profile: {author_id}",
            extra={"props": {"action": "GET_AUTHOR", "author_id": author_id, "status": "SUCCESS"}}
        )
        return author_data, 200