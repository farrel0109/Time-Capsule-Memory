# Children Blueprint
from flask import Blueprint

children_bp = Blueprint('children', __name__, url_prefix='/children')

from . import routes
