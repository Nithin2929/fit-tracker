"""Fitness & Wellness Tracking application package.

This module creates the Flask application and registers the route modules.
"""

from flask import Flask

from config import Config


def create_app():
    """Create and configure the Flask application."""

    app = Flask(__name__)
    app.config.from_object(Config)

    # Database helpers are registered here so every request can use get_db().
    from app.db import init_app as init_db

    init_db(app)

    # The Home page route lives in app/routes/main.py.
    from app.routes.main import main_bp

    app.register_blueprint(main_bp)

    return app
