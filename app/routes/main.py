"""Public pages and a small database health check."""

from flask import Blueprint, abort, jsonify, render_template
from mysql.connector import Error

from app.db import get_db

main_bp = Blueprint("main", __name__)

# Pages that are intentionally built in later frontend steps.
COMING_SOON_PAGES = {
    "register": (
        "Create your account",
        "The registration form, validation and password hashing are the next "
        "frontend step.",
    ),
    "login": (
        "Log in",
        "The login form and session handling arrive after registration is "
        "working.",
    ),
    "dashboard": (
        "Your dashboard",
        "Calorie, step, workout and BMI cards will be filled with live MySQL "
        "data here.",
    ),
    "workouts": (
        "Workout tracking",
        "The workout form, history table and calorie totals are built in the "
        "workout step.",
    ),
    "nutrition": (
        "Nutrition tracking",
        "Daily meals, macronutrients and calorie intake will be logged on this "
        "page.",
    ),
    "health": (
        "Health metrics",
        "Weight, height, steps and automatic BMI calculations are added in the "
        "health step.",
    ),
    "reports": (
        "Progress reports",
        "Daily, weekly and monthly reports with SQL joins and aggregate "
        "functions are added near the end of the build.",
    ),
}


@main_bp.route("/")
def home():
    """Show the public Home page."""

    return render_template("home.html")


@main_bp.route("/coming-soon/<page>")
def coming_soon(page):
    """Show a friendly placeholder for pages that are not built yet."""

    details = COMING_SOON_PAGES.get(page)
    if details is None:
        abort(404)

    page_title, page_summary = details
    return render_template(
        "coming_soon.html",
        page_title=page_title,
        page_summary=page_summary,
    )


@main_bp.route("/db-check")
def db_check():
    """Return JSON showing whether Flask can reach MySQL.

    This is a development helper. Open http://127.0.0.1:5000/db-check after
    filling in your .env file.
    """

    try:
        connection = get_db()
        cursor = connection.cursor()
        cursor.execute("SELECT DATABASE(), VERSION()")
        database_name, mysql_version = cursor.fetchone()
        cursor.close()

        return jsonify(
            status="ok",
            database=database_name,
            mysql_version=mysql_version,
        )
    except Error as error:
        return (
            jsonify(
                status="error",
                message=str(error),
                hint="Check DB_HOST, DB_PORT, DB_NAME, DB_USER and DB_PASSWORD in .env.",
            ),
            500,
        )
