"""
Configuration for INSIDERS Dubai Commercial Proposal Generator
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent

# On Windows use LOCALAPPDATA, on Linux (Railway) use BASE_DIR/instance
if os.name == 'nt':
    _DB_DIR = Path(os.environ.get('LOCALAPPDATA', str(BASE_DIR))) / 'insiders_dubai'
else:
    _DB_DIR = BASE_DIR / 'instance'
_DB_DIR.mkdir(parents=True, exist_ok=True)
_DB_PATH = _DB_DIR / 'insiders.db'

class Config:
    """Base configuration"""
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = False
    TESTING = False

    # Database
    INSTANCE_PATH = BASE_DIR / 'instance'
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        f"sqlite:///{_DB_PATH.as_posix()}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # File uploads
    UPLOAD_FOLDER = BASE_DIR / 'uploads'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    
    # API Keys
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')
    
    # Default currencies
    DEFAULT_CURRENCY = 'USD'
    BASE_CURRENCY = 'USD'
    CURRENCIES = {
        'USD': {'name': 'US Dollar', 'rate': 1.0, 'active': True},
        'AED': {'name': 'UAE Dirham', 'rate': 3.67, 'active': True},
        'EUR': {'name': 'Euro', 'rate': 0.93, 'active': True},
        'GBP': {'name': 'British Pound', 'rate': 0.81, 'active': True},
    }

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

# Config selector
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
