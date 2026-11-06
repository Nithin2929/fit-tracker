"""Fitness & Wellness Tracking application package.

This module creates the Flask application, registers the blueprints, loads the
logged-in user, and turns database failures into friendly error pages.
"""

import logging

from flask import Flask, g, render_template, session
from mysql.connector import Error

from app.db import (
    DatabaseConfigurationError,
    DatabaseConnectionError,
    DatabaseError,
    DatabaseQueryError,
    fetch_one,
)
from app.utils import register_template_helpers
from config import Config


def create_app():
    """Create and configure the Flask application."""

    app = Flask(__name__)
    app.config.from_object(Config)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    app.logger.setLevel(logging.INFO)

    # Database helpers and cleanup.
    from app.db import init_app as init_db

    init_db(app)

    # Shared Jinja filters and the CSRF helper.
    register_template_helpers(app)

    # Route modules.
    from app.routes.api import api_bp
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.exercises import exercises_bp
    from app.routes.health import health_bp
    from app.routes.heart_rate import heart_rate_bp
    from app.routes.main import main_bp
    from app.routes.nutrition import nutrition_bp
    from app.routes.reports import reports_bp
    from app.routes.workouts import workouts_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(workouts_bp)
    app.register_blueprint(exercises_bp)
    app.register_blueprint(nutrition_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(heart_rate_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(api_bp)

    @app.before_request
    def load_logged_in_user():
        """Load the current user from the session before each request.

        No database call is made for anonymous visitors, so the public Home
        page keeps working even before Aiven is configured.
        """

        user_id = session.get("user_id")
        g.user = None
        if user_id is None:
            return

        user = fetch_one(
            """
            SELECT user_id, full_name, email, date_of_birth, gender,
                   height_cm, created_at
            FROM users
            WHERE user_id = %s
            """,
            (user_id,),
        )
        if user is None:
            # The account was removed while the session was still active.
            session.clear()
            return
        g.user = user

    @app.context_processor
    def inject_current_user():
        return {"current_user": getattr(g, "user", None)}

    @app.after_request
    def add_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "geolocation=(), microphone=()")
        return response

    @app.errorhandler(DatabaseConfigurationError)
    def handle_configuration_error(error):
        app.logger.error("Database configuration error: %s", error)
        return (
            render_template(
                "error.html",
                code=500,
                title="Aiven MySQL is not configured",
                message=str(error),
                hint="Copy .env.example to .env, fill in the Aiven details, "
                "download ca.pem, and restart the application.",
            ),
            500,
        )

    @app.errorhandler(DatabaseConnectionError)
    def handle_connection_error(error):
        app.logger.error("Database connection error: %s", error)
        return (
            render_template(
                "error.html",
                code=503,
                title="Aiven MySQL is unavailable",
                message=str(error),
                hint="Check your internet connection, the Aiven service status, "
                "your DB_* values, and the CA certificate path.",
            ),
            503,
        )

    @app.errorhandler(DatabaseQueryError)
    def handle_query_error(error):
        app.logger.error("Database query error: %s", error)
        return (
            render_template(
                "error.html",
                code=503,
                title="The database request failed",
                message=str(error),
                hint="Please try again. If the problem continues, check the "
                "Aiven service and the application log.",
            ),
            503,
        )

    @app.errorhandler(Error)
    def handle_mysql_error(error):
        # Never show the raw MySQL message. It can contain SQL, table names, or
        # connection details that should not reach the browser.
        app.logger.error("Unhandled MySQL error: %s", error.__class__.__name__)
        return (
            render_template(
                "error.html",
                code=503,
                title="The database request failed",
                message="The database could not complete this request.",
                hint="Please try again. Details were written to the server log.",
            ),
            503,
        )

    @app.errorhandler(400)
    def handle_bad_request(error):
        return (
            render_template(
                "error.html",
                code=400,
                title="That request was not valid",
                message=getattr(error, "description", "Please check the form and try again."),
                hint="Go back, refresh the page, and submit the form again.",
            ),
            400,
        )

    @app.errorhandler(404)
    def handle_not_found(error):
        return (
            render_template(
                "error.html",
                code=404,
                title="Page not found",
                message="The page you asked for does not exist.",
                hint="Use the navigation above to return to a real page.",
            ),
            404,
        )

    @app.errorhandler(500)
    def handle_server_error(error):
        app.logger.exception("Unhandled application error")
        return (
            render_template(
                "error.html",
                code=500,
                title="Something went wrong",
                message="The application hit an unexpected error.",
                hint="Please try again. Details were written to the server log.",
            ),
            500,
        )

    return app
