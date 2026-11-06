"""Read-only JSON analytics endpoints.

These endpoints exist so the dashboard charts retrieve their data from Flask
and MySQL instead of embedding hardcoded numbers in JavaScript. They return
only the signed-in user's records.

Authentication is session-based, exactly like the HTML pages. Anonymous
requests receive HTTP 401 with a JSON body instead of an HTML redirect.
"""

from datetime import date, datetime
from decimal import Decimal
from functools import wraps

from flask import Blueprint, g, jsonify, request

from app import analytics
from app.schema import capabilities
from app.utils import login_required  # noqa: F401  (documented import intent)

api_bp = Blueprint("api", __name__, url_prefix="/api")

BALANCE_NOTE = (
    "Recorded calorie balance = recorded intake - recorded expenditure. "
    "Expenditure uses the daily health_metrics value when present, otherwise "
    "the sum of that day's workouts. It is a simplified record, not a medical "
    "or physiological measurement."
)


def api_login_required(view):
    """Return JSON 401 instead of an HTML redirect for anonymous API calls."""

    @wraps(view)
    def wrapped(*args, **kwargs):
        if getattr(g, "user", None) is None:
            return jsonify({"error": "authentication_required"}), 401
        return view(*args, **kwargs)

    return wrapped


def _json_safe(value):
    """Recursively convert MySQL types into JSON-serializable values."""

    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, datetime):
        return value.isoformat(sep=" ")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


def _days(default=30):
    """Read a bounded ?days= window."""

    try:
        days = int(request.args.get("days", default))
    except (TypeError, ValueError):
        days = default
    return max(1, min(days, 365))


def _user_id():
    return g.user["user_id"]


@api_bp.route("/schema")
@api_login_required
def schema_status():
    """Report which optional migrations the live database currently satisfies."""

    return jsonify(_json_safe({"capabilities": capabilities()}))


@api_bp.route("/analytics/summary")
@api_login_required
def analytics_summary():
    """Full analytics payload used by charts, reports and API clients."""

    days = _days()
    payload = analytics.analytics_summary(_user_id(), days=days)
    payload["meta"] = {
        "window_days": days,
        "calorie_balance_note": BALANCE_NOTE,
        "capabilities": capabilities(),
    }
    return jsonify(_json_safe(payload))


@api_bp.route("/analytics/charts")
@api_login_required
def analytics_charts():
    """The six dashboard chart payloads only."""

    days = _days()
    payload = analytics.analytics_summary(_user_id(), days=days)
    return jsonify(
        _json_safe(
            {
                "days": days,
                "charts": payload["chart_data"],
                "capabilities": capabilities(),
            }
        )
    )


@api_bp.route("/analytics/workouts")
@api_login_required
def analytics_workouts():
    return jsonify(_json_safe(analytics.workout_analytics(_user_id())))


@api_bp.route("/analytics/nutrition")
@api_login_required
def analytics_nutrition():
    return jsonify(_json_safe(analytics.nutrition_analytics(_user_id(), _days())))


@api_bp.route("/analytics/health")
@api_login_required
def analytics_health():
    return jsonify(_json_safe(analytics.health_analytics(_user_id())))


@api_bp.route("/analytics/calorie-balance")
@api_login_required
def analytics_calorie_balance():
    days = _days()
    payload = analytics.calorie_balance(_user_id(), days=days)
    payload["note"] = BALANCE_NOTE
    return jsonify(_json_safe(payload))


@api_bp.route("/analytics/heart-rate")
@api_login_required
def analytics_heart_rate():
    return jsonify(
        _json_safe(analytics.heart_rate_analytics(_user_id(), _days()))
    )


@api_bp.route("/analytics/protein-strength")
@api_login_required
def analytics_protein_strength():
    """Compare recorded weekly protein intake with strength training."""

    return jsonify(
        _json_safe(analytics.protein_strength_analytics(_user_id(), _days(90)))
    )


@api_bp.route("/exercises")
@api_login_required
def exercises():
    """Return the exercise catalogue, or an unavailable marker pre-migration."""

    from app.db import fetch_all

    if not capabilities()["exercises"]:
        return jsonify(
            {
                "available": False,
                "message": "Run database/migration_exercises.sql after approval.",
                "exercises": [],
            }
        )

    rows = fetch_all(
        """
        SELECT exercise_id, exercise_name, muscle_group, exercise_type, description
        FROM exercises
        ORDER BY exercise_name
        """
    )
    return jsonify({"available": True, "exercises": _json_safe(rows)})
