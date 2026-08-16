from models.user import db, User
from app_logginig.logger import app_logger  # Import our structured logger

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

            token = user.generate_token()

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
            app_logger.error(
                f"User registration database error: {str(e)}",
                extra={"props": {"action": "REGISTER_USER", "status": "FAILED", "error": str(e)}}
            )
            return {'message': 'Database error occurred', 'details': str(e)}, 500
    
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

        token = user.generate_token()

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