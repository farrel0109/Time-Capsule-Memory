# BabyGrow - Flask Application Factory
import os
from flask import Flask
from .config import config


def create_app(config_name=None):
    """Application factory for creating Flask app instance."""
    
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    app = Flask(__name__,
                template_folder='../templates',
                static_folder='../static')
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Ensure upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Initialize extensions
    from .extensions import close_db, init_db
    app.teardown_appcontext(close_db)
    
    # Initialize database
    with app.app_context():
        init_db()
    
    # Register blueprints
    from .auth import auth_bp
    from .children import children_bp
    from .health import health_bp
    from .capsule import capsule_bp
    from .main import main_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(children_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(capsule_bp)
    
    return app
