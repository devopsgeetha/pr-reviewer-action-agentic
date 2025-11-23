"""
Entry point for the Flask application
"""
from app import create_app
from config.config import Config

app = create_app(Config)

if __name__ == '__main__':
    app.run(
        host=app.config.get('HOST', '0.0.0.0'),
        port=app.config.get('PORT', 5000),
        debug=app.config.get('DEBUG', True)
    )
