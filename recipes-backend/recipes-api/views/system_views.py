from flask import Blueprint, jsonify
from sqlalchemy import text

from models.user import db


system_bp = Blueprint(
    'system_bp',
    __name__,
    url_prefix='/system'
)


# ============================================================
# Liveness Probe
# ============================================================

@system_bp.route('/health', methods=['GET'])
def health():
    """
    Liveness probe.

    Indicates that the Flask application process is alive.
    This should NOT depend on external services such as PostgreSQL.
    """
    return jsonify({
        "status": "healthy"
    }), 200


# ============================================================
# Readiness Probe
# ============================================================

@system_bp.route('/ready', methods=['GET'])
def ready():
    """
    Readiness probe.

    Indicates whether this pod can currently serve application traffic.
    PostgreSQL connectivity is required for the API to function.
    """

    try:
        db.session.execute(text("SELECT 1"))

        return jsonify({
            "status": "ready"
        }), 200

    except Exception:
        return jsonify({
            "status": "not_ready"
        }), 503


# ============================================================
# Startup Probe
# ============================================================

@system_bp.route('/startup', methods=['GET'])
def startup():
    """
    Startup probe.

    Indicates that the application has successfully initialized.
    PostgreSQL connectivity is checked because the API is not useful
    until its database is reachable.
    """

    try:
        db.session.execute(text("SELECT 1"))

        return jsonify({
            "status": "started"
        }), 200

    except Exception:
        return jsonify({
            "status": "starting"
        }), 503