"""Application configuration.

Values are read from environment variables, with safe local defaults.
Copy .env.example to .env and fill in your real MySQL password before using
the database pages.
"""

import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuration used by the Flask application."""

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-secret-change-me")

    DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT = int(os.getenv("DB_PORT", "3306"))
    DB_NAME = os.getenv("DB_NAME", "fitness_wellness_db")
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
