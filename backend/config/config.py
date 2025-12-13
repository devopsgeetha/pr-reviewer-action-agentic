"""
Configuration settings for the application
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration"""
    
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Server
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5000))
    
    # Database
    MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/pr_reviewer')
    MONGO_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/pr_reviewer')  # Flask-PyMongo expects MONGO_URI
    MONGODB_DB_NAME = os.getenv('MONGODB_DB_NAME', 'pr_reviewer')
    
    # OpenAI
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4-turbo-preview')
    OPENAI_TEMPERATURE = float(os.getenv('OPENAI_TEMPERATURE', 0.5))
    MAX_TOKENS = int(os.getenv('MAX_TOKENS', 8000))
    
    # GitHub
    GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
    GITHUB_WEBHOOK_SECRET = os.getenv('GITHUB_WEBHOOK_SECRET')
    
    # GitLab
    GITLAB_TOKEN = os.getenv('GITLAB_TOKEN')
    GITLAB_WEBHOOK_SECRET = os.getenv('GITLAB_WEBHOOK_SECRET')
    
    # Redis
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # AWS
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    MONGODB_DB_NAME = 'pr_reviewer_test'
    # Disable MongoDB for testing
    MONGO_URI = None
    MONGODB_URI = None


config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
