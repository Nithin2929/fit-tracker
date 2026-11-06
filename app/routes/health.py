"""Health metrics: weight, height, steps, calories burned, and BMI."""

from datetime import date

from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for
from mysql.connector import IntegrityError

from app.db import DatabaseQueryError, execute, fetch_all, fetch_one
from app.utils import (
    bmi_category,
    login_required,
    parse_date,
    parse_decimal,
    parse_int,
    validate_csrf,
)

health_bp = Blueprint("health", __name__, url_prefix="/health")


@health_bp.route("/")
@login_required
def index():
    """List only the signed-in user's health records with calculated BMI."""

    metrics = fetch_all(
        """
        SELECT metric_id, weight, height, steps, calories_burned, recorded_date,
               ROUND(weight / ((height / 100) * (height / 100)), 1) AS bmi
        FROM health_metrics
        WHERE user_id = %s
        ORDER BY recorded_date DESC, metric_id DESC
        """,
        (g.user["user_id"],),
    )
    for row in metrics:
        row["bmi_label"] = bmi_category(row["bmi"])

    latest = metrics[0] if metrics else None
    return render_template("health/index.html", metrics=metrics, latest=latest)


def _read_health_form():
    """Read and validate the health metrics form fields."""

    form = {
        "weight": request.form.get("weight", "").strip(),
        "height": request.form.get("height", "").strip(),
        "steps": request.form.get("steps", "").strip(),
        "calories_burned": request.form.get("calories_burned", "").strip(),
        "recorded_date": request.form.get("recorded_date", "").strip(),
    }
    errors = []

    weight = None
    try:
        weight = parse_decimal(form["weight"], "Weight", 0.1, 499.99, required=True)
    except ValueError as error:
        errors.append(str(error))

    height = None
    try:
        height = parse_decimal(form["height"], "Height", 0.1, 299.99, required=True)
    except ValueError as error:
        errors.append(str(error))

    steps = 0
    if form["steps"]:
        try:
            steps = parse_int(form["steps"], "Steps", 0, 200000)
        except ValueError as error:
            errors.append(str(error))

    calories_burned = 0
    if form["calories_burned"]:
        try:
            calories_burned = parse_int(
                form["calories_burned"], "Calories burned", 0, 10000
            )
        except ValueError as error:
            errors.append(str(error))

    recorded_date = None
    try:
        recorded_date = parse_date(form["recorded_date"], "Recorded date")
    except ValueError as error:
        errors.append(str(error))

    return form, errors, weight, height, steps, calories_burned, recorded_date


@health_bp.route("/new", methods=["GET", "POST"])
@login_required
def create():
    """Add a daily health record, updating the same date instead of duplicating."""

    form = {
        "weight": "",
        "height": "",
        "steps": "",
        "calories_burned": "",
        "recorded_date": date.today().isoformat(),
    }

    if request.method == "POST":
        validate_csrf()
        (
            form,
            errors,
            weight,
            height,
            steps,
            calories_burned,
            recorded_date,
        ) = _read_health_form()

        if errors:
            for message in errors:
                flash(message, "error")
        else:
            execute(
                """
                INSERT INTO health_metrics
                    (user_id, weight, height, steps, calories_burned, recorded_date)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    weight = %s,
                    height = %s,
                    steps = %s,
                    calories_burned = %s
                """,
                (
                    g.user["user_id"],
                    weight,
                    height,
                    steps,
                    calories_burned,
                    recorded_date,
                    weight,
                    height,
                    steps,
                    calories_burned,
                ),
            )
            flash(
                "Health metrics saved. If a record already existed for that date, "
                "it was updated.",
                "success",
            )
            return redirect(url_for("health.index"))

    return render_template("health/form.html", form=form, mode="add", metric=None)


@health_bp.route("/<int:metric_id>/edit", methods=["GET", "POST"])
@login_required
def edit(metric_id):
    """Edit a health record only when it belongs to the signed-in user."""

    metric = fetch_one(
        """
        SELECT metric_id, weight, height, steps, calories_burned, recorded_date
        FROM health_metrics
        WHERE metric_id = %s AND user_id = %s
        """,
        (metric_id, g.user["user_id"]),
    )
    if metric is None:
        abort(404)

    form = {
        "weight": metric["weight"],
        "height": metric["height"],
        "steps": metric["steps"],
        "calories_burned": metric["calories_burned"],
        "recorded_date": metric["recorded_date"].isoformat(),
    }

    if request.method == "POST":
        validate_csrf()
        (
            form,
            errors,
            weight,
            height,
            steps,
            calories_burned,
            recorded_date,
        ) = _read_health_form()

        if errors:
            for message in errors:
                flash(message, "error")
        else:
            try:
                _, rowcount = execute(
                    """
                    UPDATE health_metrics
                    SET weight = %s,
                        height = %s,
                        steps = %s,
                        calories_burned = %s,
                        recorded_date = %s
                    WHERE metric_id = %s AND user_id = %s
                    """,
                    (
                        weight,
                        height,
                        steps,
                        calories_burned,
                        recorded_date,
                        metric_id,
                        g.user["user_id"],
                    ),
                )
                if rowcount == 0:
                    abort(404)
                flash("Health metrics updated.", "success")
                return redirect(url_for("health.index"))
            except IntegrityError:
                flash(
                    "A health record already exists for that date. Edit that "
                    "record instead.",
                    "error",
                )
            except DatabaseQueryError:
                flash("The health record could not be saved. Please try again.", "error")

    return render_template(
        "health/form.html", form=form, mode="edit", metric=metric
    )


@health_bp.route("/<int:metric_id>/delete", methods=["POST"])
@login_required
def delete(metric_id):
    """Delete a health record only when it belongs to the signed-in user."""

    validate_csrf()
    _, rowcount = execute(
        "DELETE FROM health_metrics WHERE metric_id = %s AND user_id = %s",
        (metric_id, g.user["user_id"]),
    )
    if rowcount == 0:
        abort(404)
    flash("Health record deleted.", "success")
    return redirect(url_for("health.index"))
