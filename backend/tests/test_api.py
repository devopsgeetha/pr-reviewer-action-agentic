"""
Unit tests for API routes
"""
import pytest
from unittest.mock import patch, MagicMock
from app import create_app
from config.config import TestingConfig


@pytest.fixture
def app():
    """Create test app"""
    app = create_app(TestingConfig)
    return app


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


class TestAPIRoutes:
    """Test API routes"""
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get('/health')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'healthy'
    
    def test_get_reviews(self, client):
        """Test get all reviews - should return empty list when DB not available"""
        response = client.get('/api/reviews')
        if response.status_code != 200:
            print(f"Error response: {response.get_json()}")
        assert response.status_code == 200
        data = response.get_json()
        assert 'reviews' in data
        assert isinstance(data['reviews'], list)
    
    def test_analyze_code_no_code(self, client):
        """Test analyze endpoint without code"""
        response = client.post(
            '/api/analyze',
            json={}
        )
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    def test_get_settings(self, client):
        """Test get settings"""
        response = client.get('/api/settings')
        assert response.status_code == 200
        data = response.get_json()
        assert 'model' in data
        assert 'temperature' in data
