"""Flask extension singletons.

Instantiated here (not in `models/` or `app.py`) so any module can import
them without pulling in the rest of the app, and without `models/` owning
app-wide objects it doesn't otherwise need. Each extension is bound to the
Flask app later via its own `init_app()` call in `app.py`.
"""

from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
bcrypt = Bcrypt()
jwt = JWTManager()

# Per-IP request throttling (currently applied to login/register - see
# views/user_views.py). Uses in-memory storage: correct for today's
# single-replica deployment, but each pod would count independently if
# ever scaled to multiple replicas - a shared backend (e.g. Redis) would
# be needed at that point for the limit to still mean what it says.
limiter = Limiter(key_func=get_remote_address)
