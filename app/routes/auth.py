"""User registration, login, logout, and profile management."""

import re
from datetime import date

from flask import (
    Blueprint,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from mysql.connector import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from app.db import DatabaseQueryError, execute, fetch_one
from app.utils import (
    login_required,
    parse_date,
    parse_decimal,
    safe_next_url,
    validate_csrf,
)

auth_bp = Blueprint("auth", __name__)

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
GENDERS = ("Male", "Female", "Other", "Prefer not to say")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """Create an account with a securely hashed password."""

    if getattr(g, "user", None):
        return redirect(url_for("dashboard.index"))

    form = {
        "full_name": "",
        "email": "",
        "date_of_birth": "",
        "gender": "",
        "height_cm": "",
    }
    errors = []

    if request.method == "POST":
        validate_csrf()
        form["full_name"] = request.form.get("full_name", "").strip()
        form["email"] = request.form.get("email", "").strip().lower()
        form["date_of_birth"] = request.form.get("date_of_birth", "").strip()
        form["gender"] = request.form.get("gender", "").strip()
        form["height_cm"] = request.form.get("height_cm", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if len(form["full_name"]) < 2 or len(form["full_name"]) > 100:
            errors.append("Full name must be between 2 and 100 characters.")
        if not EMAIL_PATTERN.match(form["email"]) or len(form["email"]) > 150:
            errors.append("Enter a valid email address.")
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long.")
        if password != confirm:
            errors.append("The two passwords do not match.")

        date_of_birth = None
        if form["date_of_birth"]:
            try:
                date_of_birth = parse_date(form["date_of_birth"], "Date of birth")
                if date_of_birth > date.today():
                    errors.append("Date of birth cannot be in the future.")
            except ValueError as error:
                errors.append(str(error))

        height_cm = None
        if form["height_cm"]:
            try:
                height_cm = parse_decimal(
                    form["height_cm"], "Height", minimum=1, maximum=299
                )
            except ValueError as error:
                errors.append(str(error))

        gender = form["gender"] or None
        if gender is not None and gender not in GENDERS:
            errors.append("Choose a valid gender option.")

        if not errors:
            try:
                execute(
                    """
                    INSERT INTO users
                        (full_name, email, password_hash, date_of_birth, gender, height_cm)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        form["full_name"],
                        form["email"],
                        generate_password_hash(password),
                        date_of_birth,
                        gender,
                        height_cm,
                    ),
                )
                user = fetch_one(
                    "SELECT user_id FROM users WHERE email = %s", (form["email"],)
                )
                session.clear()
                session["user_id"] = user["user_id"]
                session.permanent = True
                flash("Your FitTrack account is ready.", "success")
                return redirect(url_for("dashboard.index"))
            except IntegrityError:
                errors.append("An account with that email address already exists.")
            except DatabaseQueryError:
                errors.append("The account could not be created. Please try again.")

        for message in errors:
            flash(message, "error")

    return render_template("auth/register.html", form=form, errors=errors)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Check the email and password, then start a fresh session."""

    if getattr(g, "user", None):
        return redirect(url_for("dashboard.index"))

    email = ""
    next_url = request.values.get("next", "")

    if request.method == "POST":
        validate_csrf()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Enter both your email address and password.", "error")
        else:
            user = fetch_one(
                """
                SELECT user_id, full_name, password_hash
                FROM users
                WHERE email = %s
                """,
                (email,),
            )
            if user is None or not check_password_hash(user["password_hash"], password):
                # The same message for both cases avoids revealing which emails
                # have accounts.
                flash("Email address or password is incorrect.", "error")
            else:
                session.clear()
                session["user_id"] = user["user_id"]
                session.permanent = True
                flash(f"Welcome back, {user['full_name']}.", "success")
                return redirect(
                    safe_next_url(next_url, url_for("dashboard.index"))
                )

    return render_template("auth/login.html", email=email, next_url=next_url)


@auth_bp.route("/logout", methods=["POST"])
def logout():
    """End the session. Logout is POST-only so a link cannot log users out."""

    validate_csrf()
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("main.home"))


@auth_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    """Show and update the authenticated user's own profile."""

    user = fetch_one(
        """
        SELECT user_id, full_name, email, date_of_birth, gender,
               height_cm, created_at
        FROM users
        WHERE user_id = %s
        """,
        (g.user["user_id"],),
    )
    if user is None:
        session.clear()
        flash("Your account could not be found. Please log in again.", "error")
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        validate_csrf()
        full_name = request.form.get("full_name", "").strip()
        date_of_birth_raw = request.form.get("date_of_birth", "").strip()
        gender = request.form.get("gender", "").strip() or None
        height_raw = request.form.get("height_cm", "").strip()
        errors = []

        if len(full_name) < 2 or len(full_name) > 100:
            errors.append("Full name must be between 2 and 100 characters.")

        date_of_birth = None
        if date_of_birth_raw:
            try:
                date_of_birth = parse_date(date_of_birth_raw, "Date of birth")
                if date_of_birth > date.today():
                    errors.append("Date of birth cannot be in the future.")
            except ValueError as error:
                errors.append(str(error))

        height_cm = None
        if height_raw:
            try:
                height_cm = parse_decimal(height_raw, "Height", minimum=1, maximum=299)
            except ValueError as error:
                errors.append(str(error))

        if gender is not None and gender not in GENDERS:
            errors.append("Choose a valid gender option.")

        if errors:
            for message in errors:
                flash(message, "error")
            user.update(
                {
                    "full_name": full_name,
                    "date_of_birth": date_of_birth_raw,
                    "gender": gender or "",
                    "height_cm": height_raw,
                }
            )
        else:
            execute(
                """
                UPDATE users
                SET full_name = %s, date_of_birth = %s, gender = %s, height_cm = %s
                WHERE user_id = %s
                """,
                (
                    full_name,
                    date_of_birth,
                    gender,
                    height_cm,
                    g.user["user_id"],
                ),
            )
            flash("Profile updated.", "success")
            return redirect(url_for("auth.profile"))

    return render_template("auth/profile.html", user=user, genders=GENDERS)
