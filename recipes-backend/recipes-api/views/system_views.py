
from flask import Blueprint


system_bp = Blueprint('system_bp', __name__, url_prefix='/system')

@system_bp.route('/health', methods=['GET'])
def health_check():
    return {'status': 'healthy'}, 200