"""Reports built from real Aiven MySQL data for the signed-in user."""

from datetime import date, timedelta

from flask import Blueprint, flash, g, render_template, request

from app.db import fetch_all
from app.analytics import analytics_summary
from app.schema import capabilities
from app.utils import bmi_category, login_required, parse_date

reports_bp = Blueprint("reports", __name__, url_prefix="/reports")


def _date_range():
    """Read the optional start/end filter, with a safe 30-day default."""

    today = date.today()
    start_default = today - timedelta(days=29)
    start_raw = request.args.get("start", "").strip()
    end_raw = request.args.get("end", "").strip()

    try:
        start = parse_date(start_raw, "Start date") if start_raw else start_default
        end = parse_date(end_raw, "End date") if end_raw else today
    except ValueError as error:
        flash(str(error), "error")
        start, end = start_default, today

    if end < start:
        flash("The end date was before the start date, so the range was reset.", "warning")
        start, end = start_default, today

    if (end - start).days > 366:
        flash("Please choose a range of 366 days or fewer.", "warning")
        start = end - timedelta(days=29)

    return start, end


@reports_bp.route("/")
@login_required
def index():
    """Show daily, weekly, monthly, calorie, weight, and BMI reports."""

    user_id = g.user["user_id"]
    start, end = _date_range()

    workouts_by_day = fetch_all(
        """
        SELECT workout_date AS day,
               COUNT(*) AS workouts,
               COALESCE(SUM(duration_minutes), 0) AS minutes,
               COALESCE(SUM(calories_burned), 0) AS calories
        FROM workouts
        WHERE user_id = %s AND workout_date BETWEEN %s AND %s
        GROUP BY workout_date
        ORDER BY workout_date DESC
        """,
        (user_id, start, end),
    )

    nutrition_by_day = fetch_all(
        """
        SELECT log_date AS day,
               COALESCE(SUM(calories), 0) AS calories,
               COALESCE(SUM(protein), 0) AS protein,
               COALESCE(SUM(carbohydrates), 0) AS carbohydrates,
               COALESCE(SUM(fat), 0) AS fat
        FROM nutrition_logs
        WHERE user_id = %s AND log_date BETWEEN %s AND %s
        GROUP BY log_date
        ORDER BY log_date DESC
        """,
        (user_id, start, end),
    )

    health_by_day = fetch_all(
        """
        SELECT recorded_date AS day, weight, height, steps, calories_burned,
               ROUND(weight / ((height / 100) * (height / 100)), 1) AS bmi
        FROM health_metrics
        WHERE user_id = %s AND recorded_date BETWEEN %s AND %s
        ORDER BY recorded_date DESC
        """,
        (user_id, start, end),
    )

    weekly_workouts = fetch_all(
        """
        SELECT DATE_SUB(workout_date, INTERVAL WEEKDAY(workout_date) DAY) AS week_start,
               COUNT(*) AS workouts,
               COALESCE(SUM(duration_minutes), 0) AS minutes,
               COALESCE(SUM(calories_burned), 0) AS calories
        FROM workouts
        WHERE user_id = %s AND workout_date BETWEEN %s AND %s
        GROUP BY week_start
        ORDER BY week_start DESC
        """,
        (user_id, start, end),
    )

    monthly_workouts = fetch_all(
        """
        SELECT DATE_FORMAT(workout_date, '%%Y-%%m') AS month,
               COUNT(*) AS workouts,
               COALESCE(SUM(duration_minutes), 0) AS minutes,
               COALESCE(SUM(calories_burned), 0) AS calories
        FROM workouts
        WHERE user_id = %s AND workout_date BETWEEN %s AND %s
        GROUP BY month
        ORDER BY month DESC
        """,
        (user_id, start, end),
    )

    monthly_nutrition = fetch_all(
        """
        SELECT DATE_FORMAT(log_date, '%%Y-%%m') AS month,
               COALESCE(SUM(calories), 0) AS calories
        FROM nutrition_logs
        WHERE user_id = %s AND log_date BETWEEN %s AND %s
        GROUP BY month
        ORDER BY month DESC
        """,
        (user_id, start, end),
    )

    monthly_health = fetch_all(
        """
        SELECT DATE_FORMAT(recorded_date, '%%Y-%%m') AS month,
               ROUND(AVG(weight), 2) AS average_weight,
               ROUND(AVG(steps), 0) AS average_steps,
               COALESCE(SUM(calories_burned), 0) AS activity_calories,
               ROUND(AVG(weight / ((height / 100) * (height / 100))), 1) AS average_bmi
        FROM health_metrics
        WHERE user_id = %s AND recorded_date BETWEEN %s AND %s
        GROUP BY month
        ORDER BY month DESC
        """,
        (user_id, start, end),
    )

    # Merge the three per-day result sets into one table. Python is used only
    # for presentation; every number comes from Aiven MySQL.
    daily = {}
    for row in workouts_by_day:
        entry = daily.setdefault(row["day"], _empty_day(row["day"]))
        entry["workouts"] = row["workouts"]
        entry["minutes"] = row["minutes"]
        entry["workout_calories"] = row["calories"]

    for row in nutrition_by_day:
        entry = daily.setdefault(row["day"], _empty_day(row["day"]))
        entry["food_calories"] = row["calories"]
        entry["protein"] = row["protein"]
        entry["carbohydrates"] = row["carbohydrates"]
        entry["fat"] = row["fat"]

    for row in health_by_day:
        entry = daily.setdefault(row["day"], _empty_day(row["day"]))
        entry["steps"] = row["steps"]
        entry["weight"] = row["weight"]
        entry["height"] = row["height"]
        entry["bmi"] = row["bmi"]
        entry["bmi_label"] = bmi_category(row["bmi"])
        entry["activity_calories"] = row["calories_burned"]

    daily_rows = [daily[key] for key in sorted(daily.keys(), reverse=True)]
    for row in daily_rows:
        row["total_calories_out"] = (
            (row["workout_calories"] or 0) + (row["activity_calories"] or 0)
        )

    monthly = {}
    for row in monthly_workouts:
        entry = monthly.setdefault(row["month"], _empty_month(row["month"]))
        entry["workouts"] = row["workouts"]
        entry["minutes"] = row["minutes"]
        entry["workout_calories"] = row["calories"]
    for row in monthly_nutrition:
        entry = monthly.setdefault(row["month"], _empty_month(row["month"]))
        entry["food_calories"] = row["calories"]
    for row in monthly_health:
        entry = monthly.setdefault(row["month"], _empty_month(row["month"]))
        entry["average_weight"] = row["average_weight"]
        entry["average_steps"] = row["average_steps"]
        entry["activity_calories"] = row["activity_calories"]
        entry["average_bmi"] = row["average_bmi"]
        entry["bmi_label"] = bmi_category(row["average_bmi"])
    monthly_rows = [monthly[key] for key in sorted(monthly.keys(), reverse=True)]

    # Range totals and weight change (oldest to newest inside the range).
    ranges = {
        "workouts": sum(row["workouts"] or 0 for row in workouts_by_day),
        "minutes": sum(row["minutes"] or 0 for row in workouts_by_day),
        "workout_calories": sum(row["calories"] or 0 for row in workouts_by_day),
        "food_calories": sum(row["calories"] or 0 for row in nutrition_by_day),
    }
    weight_change = None
    if len(health_by_day) >= 2:
        newest = health_by_day[0]["weight"]
        oldest = health_by_day[-1]["weight"]
        weight_change = round(float(newest) - float(oldest), 2)

    analytics = analytics_summary(user_id, days=min((end - start).days + 1, 365))

    return render_template(
        "reports/index.html",
        start=start,
        end=end,
        daily_rows=daily_rows,
        weekly_workouts=weekly_workouts,
        monthly_rows=monthly_rows,
        nutrition_by_day=nutrition_by_day,
        health_by_day=health_by_day,
        ranges=ranges,
        weight_change=weight_change,
        analytics=analytics,
        chart_data=analytics["chart_data"],
        capabilities=capabilities(),
    )


def _empty_day(day):
    return {
        "day": day,
        "workouts": 0,
        "minutes": 0,
        "workout_calories": 0,
        "food_calories": 0,
        "protein": 0,
        "carbohydrates": 0,
        "fat": 0,
        "steps": 0,
        "weight": None,
        "height": None,
        "bmi": None,
        "bmi_label": "Not available",
        "activity_calories": 0,
        "total_calories_out": 0,
    }


def _empty_month(month):
    return {
        "month": month,
        "workouts": 0,
        "minutes": 0,
        "workout_calories": 0,
        "food_calories": 0,
        "average_weight": None,
        "average_steps": 0,
        "activity_calories": 0,
        "average_bmi": None,
        "bmi_label": "Not available",
    }
