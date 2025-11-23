"""
Test configuration
"""
import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


@pytest.fixture(scope='session')
def app():
    """Create application for testing"""
    from app import create_app
    from config.config import TestingConfig
    
    app = create_app(TestingConfig)
    return app


@pytest.fixture(scope='session')
def client(app):
    """Create test client"""
    return app.test_client()
