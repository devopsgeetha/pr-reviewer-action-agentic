"""
Application factory and initialization
"""
from flask import Flask
from flask_cors import CORS
from flask_pymongo import PyMongo
from config.config import Config

mongo = PyMongo()


def create_app(config_class=Config):
    """Create and configure the Flask application"""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    CORS(app)

    # Only initialize MongoDB if URI is provided
    if app.config.get("MONGO_URI"):
        mongo.init_app(app)

    # Register blueprints
    from app.api import api_bp, register_routes

    register_routes()
    app.register_blueprint(api_bp, url_prefix="/api")

    # Health check endpoint
    @app.route("/health")
    def health():
        return {"status": "healthy", "service": "PR Reviewer Bot"}, 200

    return app
