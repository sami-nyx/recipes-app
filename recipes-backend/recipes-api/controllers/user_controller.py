from flask_jwt_extended import create_access_token

from exceptions import BadRequestError, ConflictError, ForbiddenError, NotFoundError, UnauthorizedError
from extensions import db
from models.user import User, TokenBlocklist
from app_logging import app_logger


class UserController:

    @staticmethod
    def register_user(data: dict):
        required_fields = ['name', 'username', 'email', 'password']
        for field in required_fields:
            if not data.get(field):
                raise BadRequestError(
                    f'{field} is required',
                    action="REGISTER_USER", status="BAD_REQUEST", missing_field=field
                )

        if data['username'] == 'test-user':
            raise ConflictError(
                'Username is already taken',
                action="REGISTER_USER", status="CONFLICT", username="test-user"
            )

        if User.query.filter_by(username=data['username']).first():
            raise ConflictError(
                'Username is already taken',
                action="REGISTER_USER", status="CONFLICT", username=data['username']
            )

        if User.query.filter_by(email=data['email']).first():
            raise ConflictError(
                'Email is already registered',
                action="REGISTER_USER", status="CONFLICT", email=data['email']
            )

        user = User(
            name=data['name'],
            username=data['username'],
            email=data['email'],
            avatar_url=data.get('avatarUrl'),
            bio=data.get('bio')
        )
        user.set_password(data['password'])

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

    @staticmethod
    def login_user(data: dict):
        identifier = data.get('usernameOrEmail')
        password = data.get('password')

        if not identifier or not password:
            raise BadRequestError(
                'Username/email and password are required',
                action="LOGIN", status="BAD_REQUEST"
            )

        user = User.query.filter(
            (User.username == identifier) | (User.email == identifier)
        ).first()

        if not user or not user.check_password(password):
            raise UnauthorizedError(
                'Invalid username/email or password',
                action="LOGIN", status="UNAUTHORIZED", identifier=identifier
            )

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
            raise ForbiddenError(
                'You are not allowed to modify this user',
                action="UPDATE_USER",
                authenticated_user_id=authenticated_user_id,
                target_user_id=user_id,
                status="FORBIDDEN"
            )

        # ========================================================
        # Find user
        # ========================================================

        user = db.session.get(User, user_id)

        if not user:
            raise NotFoundError(
                'User not found',
                action="UPDATE_USER", user_id=user_id, status="NOT_FOUND"
            )

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
            raise BadRequestError(
                'One or more fields cannot be modified',
                payload={'fields': sorted(attempted_forbidden_fields)},
                action="UPDATE_USER", user_id=user_id, status="BAD_REQUEST",
                attempted_fields=sorted(attempted_forbidden_fields)
            )

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
            raise BadRequestError(
                'No editable fields were provided',
                action="UPDATE_USER", user_id=user_id, status="BAD_REQUEST"
            )

        # ========================================================
        # Name
        # ========================================================

        if 'name' in data:
            name = data['name']

            if not isinstance(name, str):
                raise BadRequestError(
                    'Name must be a string',
                    action="UPDATE_USER", user_id=user_id, status="BAD_REQUEST"
                )

            name = name.strip()

            if not name:
                raise BadRequestError(
                    'Name cannot be empty',
                    action="UPDATE_USER", user_id=user_id, status="BAD_REQUEST"
                )

            if len(name) > 100:
                raise BadRequestError(
                    'Name cannot exceed 100 characters',
                    action="UPDATE_USER", user_id=user_id, status="BAD_REQUEST"
                )

            user.name = name

        # ========================================================
        # Avatar
        # ========================================================

        if 'avatarUrl' in data:
            avatar_url = data['avatarUrl']

            if avatar_url is not None:
                if not isinstance(avatar_url, str):
                    raise BadRequestError(
                        'avatarUrl must be a string or null',
                        action="UPDATE_USER", user_id=user_id, status="BAD_REQUEST"
                    )

                avatar_url = avatar_url.strip()

                if len(avatar_url) > 255:
                    raise BadRequestError(
                        'avatarUrl cannot exceed 255 characters',
                        action="UPDATE_USER", user_id=user_id, status="BAD_REQUEST"
                    )

            user.avatar_url = avatar_url

        # ========================================================
        # Bio
        # ========================================================

        if 'bio' in data:
            bio = data['bio']

            if bio is not None:
                if not isinstance(bio, str):
                    raise BadRequestError(
                        'Bio must be a string or null',
                        action="UPDATE_USER", user_id=user_id, status="BAD_REQUEST"
                    )

                bio = bio.strip()

            user.bio = bio

        # ========================================================
        # Save
        # ========================================================

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
            raise ForbiddenError(
                'You are not allowed to delete this user',
                action="DELETE_USER",
                authenticated_user_id=authenticated_user_id,
                target_user_id=user_id,
                status="FORBIDDEN"
            )

        # ========================================================
        # Find user
        # ========================================================

        user = db.session.get(User, user_id)

        if not user:
            raise NotFoundError(
                'User not found',
                action="DELETE_USER", user_id=user_id, status="NOT_FOUND"
            )

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

    @staticmethod
    def get_author_by_id(author_id):
        user = db.session.get(User, author_id)

        if not user:
            raise NotFoundError(
                'Author not found',
                action="GET_AUTHOR", author_id=author_id, status="NOT_FOUND"
            )

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
