"""Application configuration for FitTrack.

Every database value comes from environment variables. There are deliberately
no localhost, root, empty-password, or SQLite fallbacks: if a value is missing
the application tells you exactly what to fix instead of quietly connecting to
a different database.

The real values live in ``.env`` (never committed). ``.env.example`` is the
safe template that can be committed.
"""

import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the project root, even when the app is started from another
# working directory.
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


class ConfigurationError(Exception):
    """Raised when the Aiven MySQL configuration is incomplete or unsafe."""


def _env(name):
    """Read a trimmed environment variable, returning None when empty."""

    value = os.getenv(name)
    if value is None:
        return None
    value = value.strip()
    return value or None


def _env_bool(name, default=False):
    """Read a boolean environment variable such as true/false/1/0."""

    value = _env(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def _optional_int(value):
    """Convert a string to int, returning None when it is not a number."""

    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _resolve_path(value):
    """Resolve a relative certificate path against the project root."""

    if value is None:
        return None
    path = Path(value)
    if not path.is_absolute():
        path = BASE_DIR / path
    return str(path)


class Config:
    """Flask configuration sourced from environment variables only."""

    # Flask session signing key. Must be a long random value.
    SECRET_KEY = _env("SECRET_KEY")

    # Aiven MySQL connection details.
    DB_HOST = _env("DB_HOST")
    DB_PORT = _optional_int(_env("DB_PORT"))
    DB_USER = _env("DB_USER")
    DB_PASSWORD = _env("DB_PASSWORD")
    DB_NAME = _env("DB_NAME")
    DB_SSL_CA = _resolve_path(_env("DB_SSL_CA"))

    # Cookies are HTTP-only and same-site by default. Set
    # SESSION_COOKIE_SECURE=true when the app is served over HTTPS.
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = _env_bool("SESSION_COOKIE_SECURE", False)
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)

    # Never enable debug automatically. Set FLASK_DEBUG=true only in local
    # development.
    DEBUG = _env_bool("FLASK_DEBUG", False)
    TESTING = False

    # Database connection timeout in seconds.
    DB_CONNECT_TIMEOUT = _optional_int(_env("DB_CONNECT_TIMEOUT")) or 10

    # Development web server address. This is the browser URL, not a database
    # host. A local web server is fine; the database itself must be Aiven.
    APP_HOST = _env("APP_HOST") or "127.0.0.1"
    APP_PORT = _optional_int(_env("APP_PORT")) or 5000


# Values shipped in .env.example. If one of these is still present, the user
# has not finished configuring the project.
_PLACEHOLDER_VALUES = {
    "your-aiven-host",
    "your-aiven-port",
    "your-aiven-user",
    "your-aiven-username",
    "your-aiven-password",
    "your-flask-secret-key",
    "replace-with-a-long-random-string",
    "replace-with-secure-secret",
    "replace-with-the-password-from-database-app_user.sql",
    "changeme",
    "change-me",
}

_LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1", "0.0.0.0"}


def is_local_host(host):
    """Return True when a hostname points at the local machine."""

    if not host:
        return False
    normalised = host.strip().lower()
    if normalised in _LOCAL_HOSTS:
        return True
    return normalised.startswith("127.")


def _looks_like_placeholder(value):
    if not value:
        return False
    lowered = value.strip().lower()
    return (
        lowered in _PLACEHOLDER_VALUES
        or lowered.startswith("your-")
        or lowered.startswith("replace-with")
    )


def validate_config(app):
    """Validate the Aiven configuration and raise a clear error if invalid.

    Called before the database is used and during application startup. The
    returned error text is safe to show to the developer: it never contains a
    password or a full connection string.
    """

    problems = []

    required = {
        "SECRET_KEY": "Flask session signing key",
        "DB_HOST": "Aiven MySQL hostname",
        "DB_PORT": "Aiven MySQL port",
        "DB_USER": "Aiven MySQL username",
        "DB_PASSWORD": "Aiven MySQL password",
        "DB_NAME": "Aiven database name",
        "DB_SSL_CA": "Aiven CA certificate path",
    }

    for key, label in required.items():
        value = app.config.get(key)
        if value in (None, ""):
            problems.append(f"{key} is missing ({label}).")

    secret_key = app.config.get("SECRET_KEY")
    if secret_key and (len(secret_key) < 32 or _looks_like_placeholder(secret_key)):
        problems.append(
            "SECRET_KEY must be a long random value (at least 32 characters). "
            "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
        )

    host = app.config.get("DB_HOST")
    if host:
        if _looks_like_placeholder(host):
            problems.append("DB_HOST still contains the .env.example placeholder.")
        if is_local_host(host):
            problems.append(
                "DB_HOST points to a local database. FitTrack must use only the "
                "Aiven Cloud MySQL hostname."
            )

    port = app.config.get("DB_PORT")
    if port is not None and not (1 <= port <= 65535):
        problems.append("DB_PORT must be a number between 1 and 65535.")

    database = app.config.get("DB_NAME")
    if database and _looks_like_placeholder(database):
        problems.append("DB_NAME still contains a placeholder value.")

    for key in ("DB_USER", "DB_PASSWORD"):
        value = app.config.get(key)
        if value and _looks_like_placeholder(value):
            problems.append(f"{key} still contains the .env.example placeholder.")

    ssl_ca = app.config.get("DB_SSL_CA")
    if ssl_ca and not Path(ssl_ca).is_file():
        problems.append(
            f"DB_SSL_CA file was not found at: {ssl_ca}. "
            "Download the Aiven CA certificate (ca.pem) from the Aiven console "
            "and save it at that path."
        )

    if problems:
        raise ConfigurationError(
            "FitTrack cannot start because the Aiven MySQL configuration is "
            "incomplete:\n\n- " + "\n- ".join(problems) + "\n\n"
            "Copy .env.example to .env and fill in every value from the Aiven "
            "console. See README.md for step-by-step instructions."
        )

    return True
