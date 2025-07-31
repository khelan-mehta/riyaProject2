"""
Configuration file for Vehicle Parking App
Contains all application settings and constants
"""

import os

class Config:
    """Base configuration class"""
    
    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database Configuration
    DATABASE_NAME = 'parking_app.db'
    DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), DATABASE_NAME)
    
    # Application Settings
    APP_NAME = 'Vehicle Parking App'
    APP_VERSION = '1.0.0'
    
    # Admin Configuration
    DEFAULT_ADMIN_USERNAME = 'admin'
    DEFAULT_ADMIN_PASSWORD = 'admin123'
    DEFAULT_ADMIN_EMAIL = 'admin@parking.com'
    
    # Parking Configuration
    MIN_PARKING_SPOTS = 1
    MAX_PARKING_SPOTS = 500
    MIN_HOURLY_RATE = 0.01
    MAX_HOURLY_RATE = 999.99
    
    # Session Configuration
    SESSION_TIMEOUT = 3600  # 1 hour in seconds
    
    # Pagination
    ITEMS_PER_PAGE = 10
    
    # File Upload (if needed in future)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Security Settings
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    DEVELOPMENT = True
    
class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    DEVELOPMENT = False
    
    # Override with environment variables in production
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-must-set-a-secret-key'

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DATABASE_NAME = 'test_parking_app.db'
    WTF_CSRF_ENABLED = False

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

# Application Constants
class Constants:
    """Application constants"""
    
    # Parking Spot Status
    SPOT_AVAILABLE = 'A'
    SPOT_OCCUPIED = 'O'
    
    # Reservation Status
    RESERVATION_ACTIVE = 'active'
    RESERVATION_COMPLETED = 'completed'
    RESERVATION_CANCELLED = 'cancelled'
    
    # User Roles
    ROLE_ADMIN = 1
    ROLE_USER = 0
    
    # Flash Message Categories
    MESSAGE_SUCCESS = 'success'
    MESSAGE_ERROR = 'error'
    MESSAGE_WARNING = 'warning'
    MESSAGE_INFO = 'info'
    
    # Parking Lot Validation
    LOCATION_NAME_MAX_LENGTH = 100
    ADDRESS_MAX_LENGTH = 255
    PIN_CODE_LENGTH = 6
    
    # User Validation
    USERNAME_MIN_LENGTH = 3
    USERNAME_MAX_LENGTH = 20
    PASSWORD_MIN_LENGTH = 6
    
    # Time Formats
    DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
    DATE_FORMAT = '%Y-%m-%d'
    TIME_FORMAT = '%H:%M:%S'