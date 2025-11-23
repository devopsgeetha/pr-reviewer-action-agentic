"""API Blueprint initialization."""

from flask import Blueprint

api_bp = Blueprint("api", __name__)


def register_routes() -> None:
    """Import route handlers to attach them to the blueprint."""
    from app.api import routes  # noqa: F401
