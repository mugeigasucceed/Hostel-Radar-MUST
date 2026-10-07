"""
Configuration file for Room Radar Flask application.
Manages development, testing, and production settings.
"""

import os
from datetime import timedelta

class Config:
    """Base configuration - shared by all environments."""
    
    # Security - CRITICAL: Change this in production!
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-change-in-production'
    
    # Session and cookie security
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_SECURE = True  # Only send over HTTPS
    SESSION_COOKIE_HTTPONLY = True  # Not accessible via JavaScript
    SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection
    REMEMBER_COOKIE_SECURE = True
    REMEMBER_COOKIE_HTTPONLY = True
    
    # Database
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False  # Set to True for SQL query logging in dev
    
    # File uploads
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB max file size
    UPLOAD_FOLDER = 'static/uploads'
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}
    
    # WTForms CSRF protection
    WTF_CSRF_TIME_LIMIT = None  # CSRF token valid for session duration
    WTF_CSRF_SSL_STRICT = False  # Allow HTTP in development
    
    # Rate limiting
    RATELIMIT_STORAGE_URL = 'memory://'
    
    # Pagination
    ITEMS_PER_PAGE = 12
    

class DevelopmentConfig(Config):
    """Development environment configuration."""
    DEBUG = True
    TESTING = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///room_radar_dev.db'
    SESSION_COOKIE_SECURE = False  # Allow HTTP in development
    WTF_CSRF_SSL_STRICT = False  # Allow HTTP in development
    

class ProductionConfig(Config):
    """Production environment configuration."""
    DEBUG = False
    TESTING = False
    # Use PostgreSQL in production
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://user:password@localhost/room_radar'
    SESSION_COOKIE_SECURE = True  # HTTPS only
    WTF_CSRF_SSL_STRICT = True  # Strict CSRF checking
    

class TestingConfig(Config):
    """Testing environment configuration."""
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'  # In-memory database for tests
    WTF_CSRF_ENABLED = False  # Disable CSRF for testing
    PRESERVE_CONTEXT_ON_EXCEPTION = False
    

# Configuration selector
def get_config():
    """Return appropriate config based on environment."""
    env = os.environ.get('FLASK_ENV', 'development')
    
    if env == 'production':
        return ProductionConfig
    elif env == 'testing':
        return TestingConfig
    else:
        return DevelopmentConfig
