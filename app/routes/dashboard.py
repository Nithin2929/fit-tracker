"""Authenticated dashboard with live Aiven MySQL data."""

from datetime import date

from flask import Blueprint, g, render_template

from app.db import fetch_all, fetch_one
from app.analytics import analytics_summary
from app.schema import capabilities
from app.utils import bmi_category, calculate_bmi, login_required

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard")
@login_required
def index():
    """Show the signed-in user's real totals and latest measurements."""

    user_id = g.user["user_id"]

    workout_totals = fetch_one(
        """
        SELECT COUNT(*) AS total_workouts,
               COALESCE(SUM(duration_minutes), 0) AS total_minutes,
               COALESCE(SUM(calories_burned), 0) AS total_calories
        FROM workouts
        WHERE user_id = %s
        """,
        (user_id,),
    )

    today_nutrition = fetch_one(
        """
        SELECT COALESCE(SUM(calories), 0) AS calories,
               COALESCE(SUM(protein), 0) AS protein,
               COALESCE(SUM(carbohydrates), 0) AS carbohydrates,
               COALESCE(SUM(fat), 0) AS fat
        FROM nutrition_logs
        WHERE user_id = %s AND log_date = %s
        """,
        (user_id, date.today()),
    )

    latest_health = fetch_one(
        """
        SELECT metric_id, weight, height, steps, calories_burned, recorded_date
        FROM health_metrics
        WHERE user_id = %s
        ORDER BY recorded_date DESC, metric_id DESC
        LIMIT 1
        """,
        (user_id,),
    )

    today_health = fetch_one(
        """
        SELECT steps, calories_burned
        FROM health_metrics
        WHERE user_id = %s AND recorded_date = %s
        """,
        (user_id, date.today()),
    )

    recent_workouts = fetch_all(
        """
        SELECT workout_id, exercise_name, duration_minutes, calories_burned, workout_date
        FROM workouts
        WHERE user_id = %s
        ORDER BY workout_date DESC, workout_id DESC
        LIMIT 5
        """,
        (user_id,),
    )

    recent_nutrition = fetch_all(
        """
        SELECT nutrition_id, food_name, meal_type, calories, log_date
        FROM nutrition_logs
        WHERE user_id = %s
        ORDER BY log_date DESC, nutrition_id DESC
        LIMIT 5
        """,
        (user_id,),
    )

    bmi = None
    bmi_label = "Not available"
    if latest_health:
        bmi = calculate_bmi(latest_health["weight"], latest_health["height"])
        bmi_label = bmi_category(bmi)

    analytics = analytics_summary(user_id, days=30)

    return render_template(
        "dashboard.html",
        workout_totals=workout_totals,
        today_nutrition=today_nutrition,
        latest_health=latest_health,
        today_health=today_health,
        recent_workouts=recent_workouts,
        recent_nutrition=recent_nutrition,
        bmi=bmi,
        bmi_label=bmi_label,
        analytics=analytics,
        chart_data=analytics["chart_data"],
        capabilities=capabilities(),
    )
