"""MySQL connection helpers.

A new connection is opened for each request and closed automatically when the
request finishes. This keeps the example simple and avoids sharing one
connection between users.
"""

import mysql.connector
from flask import current_app, g


def get_db():
    """Return the MySQL connection for the current request."""

    if "db" not in g:
        g.db = mysql.connector.connect(
            host=current_app.config["DB_HOST"],
            port=current_app.config["DB_PORT"],
            user=current_app.config["DB_USER"],
            password=current_app.config["DB_PASSWORD"],
            database=current_app.config["DB_NAME"],
            charset="utf8mb4",
            autocommit=False,
        )
    return g.db


def close_db(error=None):
    """Close the connection at the end of the request."""

    db = g.pop("db", None)
    if db is not None and db.is_connected():
        db.close()


def init_app(app):
    """Register database cleanup with the Flask application."""

    app.teardown_appcontext(close_db)
