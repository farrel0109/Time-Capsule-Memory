# BabyGrow Configuration
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('FLASK_SECRET', 'dev-secret-key-change-in-production')
    
    # Database
    DB_TYPE = os.environ.get('DB_TYPE', 'sqlite').lower()
    DATABASE_DIR = os.path.join(BASE_DIR, 'database')
    DATABASE_PATH = os.path.join(DATABASE_DIR, 'babygrow.db')
    
    # MySQL settings (if DB_TYPE=mysql)
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT', '3306'))
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASS = os.environ.get('MYSQL_PASS', '')
    MYSQL_DB = os.environ.get('MYSQL_DB', 'babygrow_db')
    
    # Upload settings
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'mp3', 'wav', 'mp4', 'webm'}
    
    # Session
    SESSION_COOKIE_SECURE = False  # Set True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SESSION_COOKIE_SECURE = True


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DB_TYPE = 'sqlite'
    DATABASE_PATH = ':memory:'


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
