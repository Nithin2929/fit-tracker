"""Public pages and the Aiven MySQL connectivity check."""

from flask import Blueprint, abort, jsonify, render_template

from app.db import DatabaseError, verify_connection

main_bp = Blueprint("main", __name__)

# Kept for older bookmarks. The real pages are now built and linked in the
# navigation; these friendly placeholders remain harmless.
COMING_SOON_PAGES = {
    "register": ("Create your account", "Registration is available from the Get started button."),
    "login": ("Log in", "Use the Log in button in the navigation."),
    "dashboard": ("Your dashboard", "Open Dashboard after logging in."),
    "workouts": ("Workout tracking", "Open Workouts after logging in."),
    "nutrition": ("Nutrition tracking", "Open Nutrition after logging in."),
    "health": ("Health metrics", "Open Health after logging in."),
    "reports": ("Progress reports", "Open Reports after logging in."),
}


@main_bp.route("/")
def home():
    """Show the public Home page."""

    return render_template("home.html")


@main_bp.route("/coming-soon/<page>")
def coming_soon(page):
    """Show a friendly placeholder for an old link."""

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
    """Return JSON proving that Flask can reach the configured Aiven MySQL.

    This is a development/operations helper. It deliberately returns only safe
    information: never the host, username, password, or CA path.
    """

    try:
        details = verify_connection()
    except DatabaseError as error:
        return (
            jsonify(
                status="error",
                message=str(error),
                hint="Check DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD "
                "and DB_SSL_CA in .env, then verify the Aiven service is running.",
            ),
            503,
        )

    return jsonify(
        status="ok",
        database=details["database"],
        server_version=details["server_version"],
        ssl_cipher=details["ssl_cipher"],
        ssl_verified=bool(details["ssl_cipher"]),
    )
