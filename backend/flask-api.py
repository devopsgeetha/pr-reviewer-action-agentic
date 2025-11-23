"""
Example Flask API with API Key Authentication
Compatible with Flask 3.0+
"""
from flask import Flask, request, jsonify
from functools import wraps
import secrets
import hashlib
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'

# In-memory store for API keys (use database in production)
API_KEYS = {}


class APIKey:
    """API Key model"""
    
    def __init__(self, name, secret=None):
        self.name = name
        self.secret = secret or secrets.token_urlsafe(32)
        self.hash = hashlib.sha256(self.secret.encode()).hexdigest()
        self.created_at = datetime.utcnow()
        self.is_active = True
    
    def verify(self, key):
        """Verify if provided key matches"""
        return hashlib.sha256(key.encode()).hexdigest() == self.hash


class APIKeyManager:
    """Manage API Keys"""
    
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize with Flask app"""
        self.app = app
    
    def create(self, name):
        """Create a new API key"""
        api_key = APIKey(name)
        API_KEYS[api_key.hash] = api_key
        return api_key
    
    def verify(self, key):
        """Verify an API key"""
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        api_key = API_KEYS.get(key_hash)
        return api_key and api_key.is_active
    
    def revoke(self, key):
        """Revoke an API key"""
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        if key_hash in API_KEYS:
            API_KEYS[key_hash].is_active = False
            return True
        return False


# Initialize API Key Manager
mgr = APIKeyManager(app)


def require_api_key(f):
    """Decorator to require API key authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check for API key in header
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            return jsonify({'error': 'API key is required'}), 401
        
        if not mgr.verify(api_key):
            return jsonify({'error': 'Invalid API key'}), 403
        
        return f(*args, **kwargs)
    
    return decorated_function


# Example routes
@app.route('/public')
def public():
    """Public endpoint - no auth required"""
    return jsonify({'message': 'This is a public endpoint'})


@app.route('/protected')
@require_api_key
def protected():
    """Protected endpoint - requires API key"""
    return jsonify({'message': 'This is a protected endpoint'})


@app.route('/api/keys', methods=['POST'])
def create_key():
    """Create a new API key"""
    data = request.get_json()
    name = data.get('name', 'default')
    
    api_key = mgr.create(name)
    
    return jsonify({
        'name': api_key.name,
        'key': api_key.secret,  # Only shown once!
        'created_at': api_key.created_at.isoformat(),
        'message': 'Store this key securely - it will not be shown again'
    }), 201


if __name__ == '__main__':
    # Create a sample API key
    my_key = mgr.create('MY_FIRST_KEY')
    print('\n' + '='*60)
    print('Sample API Key Created:')
    print(f'Name: {my_key.name}')
    print(f'Key: {my_key.secret}')
    print('='*60)
    print('\nTest the API:')
    print(f'  Public:    curl http://localhost:5000/public')
    print(f'  Protected: curl -H "X-API-Key: {my_key.secret}" http://localhost:5000/protected')
    print(f'  Create Key: curl -X POST http://localhost:5000/api/keys -H "Content-Type: application/json" -d \'{{"name":"test"}}\'')
    print('='*60 + '\n')
    
    app.run(debug=True, port=5000)