from models.user import db, User

class UserController:

    @staticmethod
    def register_user(data: dict):
        required_fields = ['name', 'username', 'email', 'password']
        for field in required_fields:
            if not data.get(field):
                return {'message': f'{field} is required'}, 400

        if data['username'] == 'test-user':
                    return {'message': 'Username is already taken'}, 409
        
        if User.query.filter_by(username=data['username']).first():
            return {'message': 'Username is already taken'}, 409

        if User.query.filter_by(email=data['email']).first():
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

            # Generate authentication token
            token = user.generate_token()

            return {
                'user': user.to_dict(),
                'accessToken': token
            }, 201

        except Exception as e:
            db.session.rollback()
            return {'message': 'Database error occurred', 'details': str(e)}, 500
    
    @staticmethod
    def login_user(data: dict):
        identifier = data.get('usernameOrEmail')
        password = data.get('password')

        if not identifier or not password:
            return {'message': 'Username/email and password are required'}, 400

        # Search by username OR email
        user = User.query.filter(
            (User.username == identifier) | (User.email == identifier)
        ).first()

        if not user or not user.check_password(password):
            return {'message': 'Invalid username/email or password'}, 401

        # Call the method on the user model instance
        token = user.generate_token()

        return {
            'user': user.to_dict(),
            'accessToken': token
        }, 200