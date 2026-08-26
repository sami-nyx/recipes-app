from flask import Blueprint, current_app, jsonify
from sqlalchemy import text

from extensions import db
from app_logging import app_logger


system_bp = Blueprint(
    'system_bp',
    __name__,
    url_prefix='/system'
)


def _check_database():
    """Returns "ok" if a trivial query succeeds, "unreachable" otherwise.

    Deliberately returns a category, not the exception itself - these
    endpoints sit on the public internet (the Ingress uses a catch-all
    "/" path), so the real error goes to the log, not the response body.
    """
    try:
        db.session.execute(text("SELECT 1"))
        return "ok"
    except Exception as e:
        app_logger.warning(
            "Database check failed",
            extra={"props": {"action": "SYSTEM_CHECK", "check": "database", "error": str(e)}}
        )
        return "unreachable"


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
        "status": "healthy",
        "version": current_app.config.get('APP_VERSION')
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
    database_status = _check_database()

    if database_status == "ok":
        return jsonify({
            "status": "ready",
            "checks": {"database": database_status}
        }), 200

    return jsonify({
        "status": "not_ready",
        "checks": {"database": database_status}
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
    database_status = _check_database()

    if database_status == "ok":
        return jsonify({
            "status": "started",
            "checks": {"database": database_status}
        }), 200

    return jsonify({
        "status": "starting",
        "checks": {"database": database_status}
    }), 503
