"""Read-only detection of optional schema features.

FitTrack runs against the live Aiven database. The Milestone 2 migrations are
draft-only until they are approved, so the application must work both before
and after they are applied. This module answers one question per request:
"which optional tables/columns exist right now?"

It only reads ``information_schema``. It never creates or alters anything.
"""

from flask import g

from app.db import fetch_all


def _columns():
    """Return ``{table: {column, ...}}`` for the active database."""

    rows = fetch_all(
        """
        SELECT TABLE_NAME, COLUMN_NAME
        FROM information_schema.columns
        WHERE table_schema = DATABASE()
        """
    )
    tables = {}
    for row in rows:
        table = row["TABLE_NAME"].lower()
        tables.setdefault(table, set()).add(row["COLUMN_NAME"].lower())
    return tables


def capabilities():
    """Return a cached capability map for the current request."""

    cached = getattr(g, "_schema_capabilities", None)
    if cached is not None:
        return cached

    columns = _columns()
    capabilities_map = {
        "exercises": {"exercises", "workout_exercises"} <= set(columns),
        "heart_rate": {"heart_rate_zones", "heart_rate_samples"} <= set(columns),
        "nutrition_time": "logged_at" in columns.get("nutrition_logs", set()),
    }
    capabilities_map["analytics"] = True
    g._schema_capabilities = capabilities_map
    return capabilities_map


def has_exercises():
    return capabilities()["exercises"]


def has_heart_rate():
    return capabilities()["heart_rate"]


def has_nutrition_time():
    return capabilities()["nutrition_time"]


def migration_notice(feature):
    """Return a short user-facing explanation for a missing feature."""

    notices = {
        "exercises": (
            "The exercises and workout_exercises tables are not in the database "
            "yet. Run database/migration_exercises.sql after approval to enable "
            "multi-exercise workouts."
        ),
        "heart_rate": (
            "The heart-rate tables are not in the database yet. Run "
            "database/migration_heart_rate.sql after approval to store "
            "time-based heart-rate samples and zones."
        ),
        "nutrition_time": (
            "Meal timestamps are optional and not enabled. Run "
            "database/migration_nutrition_time.sql after approval to add "
            "nutrition_logs.logged_at."
        ),
    }
    return notices.get(feature, "This optional feature is not enabled.")
