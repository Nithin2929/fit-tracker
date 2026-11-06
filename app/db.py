"""Aiven Cloud MySQL connection and query helpers.

Design rules:
- The only database is the Aiven MySQL database configured in .env.
- TLS certificate verification is always enabled.
- There is no localhost, SQLite, or fallback connection anywhere in this file.
- One connection is opened per request and closed when the request ends.
  Every SQL operation in that request reuses the same connection.
"""

from contextlib import contextmanager

import mysql.connector
from flask import current_app, g
from mysql.connector import Error, IntegrityError

from config import ConfigurationError, is_local_host, validate_config


class DatabaseError(Exception):
    """Base class for safe, user-facing database errors."""


class DatabaseConfigurationError(DatabaseError):
    """The environment variables are missing or unsafe."""


class DatabaseConnectionError(DatabaseError):
    """The Aiven server could not be reached or rejected the connection."""


class DatabaseQueryError(DatabaseError):
    """A SQL statement could not be completed."""


def _connection_settings():
    """Build the mysql.connector settings for Aiven MySQL."""

    try:
        validate_config(current_app)
    except ConfigurationError as error:
        raise DatabaseConfigurationError(str(error)) from error

    settings = {
        "host": current_app.config["DB_HOST"],
        "port": current_app.config["DB_PORT"],
        "user": current_app.config["DB_USER"],
        "password": current_app.config["DB_PASSWORD"],
        "database": current_app.config["DB_NAME"],
        "charset": "utf8mb4",
        "use_unicode": True,
        "autocommit": False,
        "connection_timeout": current_app.config.get("DB_CONNECT_TIMEOUT", 10),
        # Aiven requires TLS. We verify both the certificate chain and that the
        # certificate matches the hostname. Never disable these in production.
        "ssl_ca": current_app.config["DB_SSL_CA"],
        "ssl_verify_cert": True,
        "ssl_verify_identity": True,
        "ssl_disabled": False,
    }

    # Defence in depth: even if a future edit accidentally puts a local host in
    # .env, refuse to open the connection.
    if is_local_host(settings["host"]):
        raise DatabaseConfigurationError(
            "Refusing to connect to a local database. "
            "FitTrack must use the Aiven Cloud MySQL hostname."
        )

    return settings


def get_db():
    """Return the Aiven MySQL connection for the current request."""

    if "db" not in g:
        try:
            g.db = mysql.connector.connect(**_connection_settings())
        except DatabaseError:
            raise
        except Error as error:
            # Log only the error type. The connector message can contain the
            # hostname and username, but never log the password.
            current_app.logger.error(
                "Aiven MySQL connection failed: %s", error.__class__.__name__
            )
            raise DatabaseConnectionError(
                "FitTrack could not connect to Aiven Cloud MySQL. "
                "Check your internet connection and the DB_* values in .env. "
                "The application will not fall back to a local database."
            ) from error

    return g.db


def close_db(error=None):
    """Close the request connection and return it to the operating system."""

    db = g.pop("db", None)
    if db is None:
        return
    try:
        if db.is_connected():
            db.close()
    except Error:
        # A broken connection is already unusable; nothing else to do.
        pass


def init_app(app):
    """Register database cleanup with the Flask application."""

    app.teardown_appcontext(close_db)


@contextmanager
def get_cursor(dictionary=True, commit=False):
    """Yield a cursor and always close it.

    When ``commit`` is True the transaction is committed on success and rolled
    back on any exception. This keeps every route short and safe.
    """

    db = get_db()
    cursor = db.cursor(dictionary=dictionary)
    try:
        yield cursor
        if commit:
            db.commit()
    except Exception:
        if commit:
            try:
                db.rollback()
            except Error:
                pass
        raise
    finally:
        try:
            cursor.close()
        except Error:
            pass


@contextmanager
def transaction(dictionary=False):
    """Yield a cursor inside one explicit database transaction.

    The transaction commits only when the block finishes successfully. Any
    exception rolls back **every** statement in the block, which is what makes
    multi-row operations such as "workout + its exercises" atomic.
    """

    db = get_db()
    cursor = db.cursor(dictionary=dictionary)
    try:
        yield cursor
        db.commit()
    except Exception:
        try:
            db.rollback()
        except Error:
            pass
        raise
    finally:
        try:
            cursor.close()
        except Error:
            pass


def fetch_one(sql, params=()):
    """Run a SELECT and return one row as a dictionary, or None."""

    try:
        with get_cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchone()
    except Error as error:
        current_app.logger.error("SELECT failed: %s", error.__class__.__name__)
        raise DatabaseQueryError("The database query could not be completed.") from error


def fetch_all(sql, params=()):
    """Run a SELECT and return a list of dictionaries."""

    try:
        with get_cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchall()
    except Error as error:
        current_app.logger.error("SELECT failed: %s", error.__class__.__name__)
        raise DatabaseQueryError("The database query could not be completed.") from error


def execute(sql, params=()):
    """Run an INSERT, UPDATE, or DELETE and commit it.

    Returns ``(lastrowid, rowcount)``.
    """

    try:
        with get_cursor(commit=True) as cursor:
            cursor.execute(sql, params)
            return cursor.lastrowid, cursor.rowcount
    except IntegrityError:
        # Let the route show a friendly duplicate/foreign-key message instead of
        # turning it into a generic database failure.
        current_app.logger.warning("WRITE rejected by a database constraint.")
        raise
    except Error as error:
        current_app.logger.error("WRITE failed: %s", error.__class__.__name__)
        raise DatabaseQueryError("The database change could not be saved.") from error


def verify_connection():
    """Verify that the configured Aiven database is reachable and encrypted.

    Returns a dictionary with the database name, server version and TLS cipher.
    Raises DatabaseError on failure. Used by the /db-check route and check_db.py.
    """

    try:
        with get_cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()

            cursor.execute(
                "SELECT DATABASE() AS active_database, VERSION() AS server_version"
            )
            row = cursor.fetchone()
            database_name = row["active_database"]
            server_version = row["server_version"]

            ssl_cipher = None
            try:
                cursor.execute("SHOW STATUS LIKE 'Ssl_cipher'")
                status_row = cursor.fetchone()
                if status_row:
                    ssl_cipher = status_row.get("Value")
            except Error:
                # Some managed users cannot read status variables. The TLS
                # handshake above still used the CA certificate.
                ssl_cipher = None

        return {
            "database": database_name,
            "server_version": server_version,
            "ssl_cipher": ssl_cipher,
        }
    except DatabaseError:
        raise
    except Error as error:
        current_app.logger.error(
            "Aiven MySQL verification failed: %s", error.__class__.__name__
        )
        raise DatabaseConnectionError(
            "The Aiven MySQL database could not be verified. "
            "Check the DB_* values and the CA certificate in .env."
        ) from error
