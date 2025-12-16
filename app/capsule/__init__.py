# Time Capsule Blueprint
from flask import Blueprint

capsule_bp = Blueprint('capsule', __name__, url_prefix='/capsule')

from . import routes
