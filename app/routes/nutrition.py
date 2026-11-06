"""Nutrition tracking: food logs with calories and macronutrients."""

from datetime import date

from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for

from app.db import execute, fetch_all, fetch_one
from app.utils import (
    login_required,
    parse_choice,
    parse_date,
    parse_decimal,
    parse_int,
    validate_csrf,
)

nutrition_bp = Blueprint("nutrition", __name__, url_prefix="/nutrition")

MEAL_TYPES = ("Breakfast", "Lunch", "Dinner", "Snack")


@nutrition_bp.route("/")
@login_required
def index():
    """List only the signed-in user's food records."""

    logs = fetch_all(
        """
        SELECT nutrition_id, food_name, meal_type, calories, protein,
               carbohydrates, fat, log_date
        FROM nutrition_logs
        WHERE user_id = %s
        ORDER BY log_date DESC, nutrition_id DESC
        """,
        (g.user["user_id"],),
    )
    totals = {
        "count": len(logs),
        "calories": sum(row["calories"] or 0 for row in logs),
        "protein": sum(float(row["protein"] or 0) for row in logs),
        "carbohydrates": sum(float(row["carbohydrates"] or 0) for row in logs),
        "fat": sum(float(row["fat"] or 0) for row in logs),
    }
    return render_template(
        "nutrition/index.html", logs=logs, totals=totals, meal_types=MEAL_TYPES
    )


def _read_nutrition_form():
    """Read and validate the nutrition form fields."""

    form = {
        "food_name": request.form.get("food_name", "").strip(),
        "meal_type": request.form.get("meal_type", "").strip(),
        "calories": request.form.get("calories", "").strip(),
        "protein": request.form.get("protein", "").strip(),
        "carbohydrates": request.form.get("carbohydrates", "").strip(),
        "fat": request.form.get("fat", "").strip(),
        "log_date": request.form.get("log_date", "").strip(),
    }
    errors = []

    if not form["food_name"]:
        errors.append("Food name is required.")
    elif len(form["food_name"]) > 120:
        errors.append("Food name must be 120 characters or fewer.")

    meal_type = None
    try:
        meal_type = parse_choice(form["meal_type"], "Meal type", MEAL_TYPES)
    except ValueError as error:
        errors.append(str(error))

    calories = None
    try:
        calories = parse_int(form["calories"], "Calories", 0, 10000)
    except ValueError as error:
        errors.append(str(error))

    protein = None
    if form["protein"]:
        try:
            protein = parse_decimal(form["protein"], "Protein", 0, 1000)
        except ValueError as error:
            errors.append(str(error))

    carbohydrates = None
    if form["carbohydrates"]:
        try:
            carbohydrates = parse_decimal(form["carbohydrates"], "Carbohydrates", 0, 1000)
        except ValueError as error:
            errors.append(str(error))

    fat = None
    if form["fat"]:
        try:
            fat = parse_decimal(form["fat"], "Fat", 0, 1000)
        except ValueError as error:
            errors.append(str(error))

    log_date = None
    try:
        log_date = parse_date(form["log_date"], "Log date")
    except ValueError as error:
        errors.append(str(error))

    return form, errors, meal_type, calories, protein, carbohydrates, fat, log_date


@nutrition_bp.route("/new", methods=["GET", "POST"])
@login_required
def create():
    """Add a food record for the signed-in user."""

    form = {
        "food_name": "",
        "meal_type": "",
        "calories": "",
        "protein": "",
        "carbohydrates": "",
        "fat": "",
        "log_date": date.today().isoformat(),
    }

    if request.method == "POST":
        validate_csrf()
        (
            form,
            errors,
            meal_type,
            calories,
            protein,
            carbohydrates,
            fat,
            log_date,
        ) = _read_nutrition_form()

        if errors:
            for message in errors:
                flash(message, "error")
        else:
            execute(
                """
                INSERT INTO nutrition_logs
                    (user_id, food_name, meal_type, calories, protein,
                     carbohydrates, fat, log_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    g.user["user_id"],
                    form["food_name"],
                    meal_type,
                    calories,
                    protein,
                    carbohydrates,
                    fat,
                    log_date,
                ),
            )
            flash("Nutrition record added.", "success")
            return redirect(url_for("nutrition.index"))

    return render_template(
        "nutrition/form.html",
        form=form,
        mode="add",
        log=None,
        meal_types=MEAL_TYPES,
    )


@nutrition_bp.route("/<int:nutrition_id>/edit", methods=["GET", "POST"])
@login_required
def edit(nutrition_id):
    """Edit a food record only when it belongs to the signed-in user."""

    log = fetch_one(
        """
        SELECT nutrition_id, food_name, meal_type, calories, protein,
               carbohydrates, fat, log_date
        FROM nutrition_logs
        WHERE nutrition_id = %s AND user_id = %s
        """,
        (nutrition_id, g.user["user_id"]),
    )
    if log is None:
        abort(404)

    form = {
        "food_name": log["food_name"],
        "meal_type": log["meal_type"],
        "calories": log["calories"],
        "protein": log["protein"] if log["protein"] is not None else "",
        "carbohydrates": log["carbohydrates"] if log["carbohydrates"] is not None else "",
        "fat": log["fat"] if log["fat"] is not None else "",
        "log_date": log["log_date"].isoformat(),
    }

    if request.method == "POST":
        validate_csrf()
        (
            form,
            errors,
            meal_type,
            calories,
            protein,
            carbohydrates,
            fat,
            log_date,
        ) = _read_nutrition_form()

        if errors:
            for message in errors:
                flash(message, "error")
        else:
            _, rowcount = execute(
                """
                UPDATE nutrition_logs
                SET food_name = %s,
                    meal_type = %s,
                    calories = %s,
                    protein = %s,
                    carbohydrates = %s,
                    fat = %s,
                    log_date = %s
                WHERE nutrition_id = %s AND user_id = %s
                """,
                (
                    form["food_name"],
                    meal_type,
                    calories,
                    protein,
                    carbohydrates,
                    fat,
                    log_date,
                    nutrition_id,
                    g.user["user_id"],
                ),
            )
            if rowcount == 0:
                abort(404)
            flash("Nutrition record updated.", "success")
            return redirect(url_for("nutrition.index"))

    return render_template(
        "nutrition/form.html",
        form=form,
        mode="edit",
        log=log,
        meal_types=MEAL_TYPES,
    )


@nutrition_bp.route("/<int:nutrition_id>/delete", methods=["POST"])
@login_required
def delete(nutrition_id):
    """Delete a food record only when it belongs to the signed-in user."""

    validate_csrf()
    _, rowcount = execute(
        "DELETE FROM nutrition_logs WHERE nutrition_id = %s AND user_id = %s",
        (nutrition_id, g.user["user_id"]),
    )
    if rowcount == 0:
        abort(404)
    flash("Nutrition record deleted.", "success")
    return redirect(url_for("nutrition.index"))
