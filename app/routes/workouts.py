"""Workout tracking: list, add, edit, and delete a user's own workouts.

Two data models are supported at the same time:

* **Before the draft migration** the workout is one row with a free-text
  ``exercise_name`` (the original, live behaviour).
* **After `database/migration_exercises.sql` is approved and applied**, each
  workout can also store several catalogue exercises in ``workout_exercises``.

The workout row and all of its exercise rows are written inside one database
transaction, so a failure rolls back the whole session instead of leaving a
header without its exercises.
"""

from datetime import date

from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for

from app.db import execute, fetch_all, fetch_one, transaction
from app.schema import has_exercises
from app.utils import (
    login_required,
    parse_date,
    parse_decimal,
    parse_int,
    validate_csrf,
)

workouts_bp = Blueprint("workouts", __name__, url_prefix="/workouts")

MAX_EXERCISE_ROWS = 10


def _exercise_options():
    """Return the catalogue for the form, or an empty list pre-migration."""

    if not has_exercises():
        return []
    return fetch_all(
        """
        SELECT exercise_id, exercise_name, muscle_group, exercise_type
        FROM exercises
        ORDER BY exercise_type, exercise_name
        """
    )


def _read_exercise_rows():
    """Read the optional multi-exercise rows from the workout form.

    Returns ``(rows, errors)``. Rows are only read when the exercise tables
    exist, so a pre-migration database keeps the original single-exercise
    behaviour without any errors.
    """

    if not has_exercises():
        return [], []

    exercise_ids = request.form.getlist("exercise_id")
    sets_values = request.form.getlist("sets")
    repetition_values = request.form.getlist("repetitions")
    weight_values = request.form.getlist("weight_kg")
    duration_values = request.form.getlist("exercise_duration_minutes")
    calorie_values = request.form.getlist("exercise_calories_burned")

    def value_at(values, index):
        return values[index].strip() if index < len(values) else ""

    candidates = []
    for index, raw_id in enumerate(exercise_ids):
        raw_id = raw_id.strip()
        other_values = [
            value_at(sets_values, index),
            value_at(repetition_values, index),
            value_at(weight_values, index),
            value_at(duration_values, index),
            value_at(calorie_values, index),
        ]
        if not raw_id:
            if any(other_values):
                return [], ["Choose an exercise for every row you fill in."]
            continue
        candidates.append((raw_id, other_values))

    if not candidates:
        return [], []
    if len(candidates) > MAX_EXERCISE_ROWS:
        return [], [f"Add at most {MAX_EXERCISE_ROWS} exercises to one workout."]

    unique_ids = sorted({int(item[0]) for item in candidates if item[0].isdigit()})
    known = {}
    if unique_ids:
        placeholders = ", ".join(["%s"] * len(unique_ids))
        rows = fetch_all(
            f"""
            SELECT exercise_id, exercise_name
            FROM exercises
            WHERE exercise_id IN ({placeholders})
            """,
            tuple(unique_ids),
        )
        known = {row["exercise_id"]: row["exercise_name"] for row in rows}

    errors = []
    exercise_rows = []
    for order, (raw_id, values) in enumerate(candidates, start=1):
        if not raw_id.isdigit() or int(raw_id) not in known:
            errors.append(f"Exercise row {order}: choose a valid catalogue exercise.")
            continue

        sets = repetitions = weight = duration = calories = None
        try:
            sets = parse_int(
                values[0], f"Exercise row {order} sets", 1, 100, required=False
            )
            repetitions = parse_int(
                values[1],
                f"Exercise row {order} repetitions",
                1,
                1000,
                required=False,
            )
            weight = parse_decimal(
                values[2], f"Exercise row {order} weight", 0, 1000, required=False
            )
            duration = parse_int(
                values[3],
                f"Exercise row {order} duration",
                1,
                1440,
                required=False,
            )
            calories = parse_int(
                values[4],
                f"Exercise row {order} calories",
                0,
                10000,
                required=False,
            )
        except ValueError as error:
            errors.append(str(error))
            continue

        exercise_rows.append(
            {
                "exercise_id": int(raw_id),
                "exercise_name": known[int(raw_id)],
                "exercise_order": order,
                "sets": sets,
                "repetitions": repetitions,
                "weight_kg": weight,
                "duration_minutes": duration,
                "calories_burned": calories,
            }
        )

    return exercise_rows, errors


def _read_workout_form(require_name=True):
    """Read and validate the workout form fields."""

    form = {
        "exercise_name": request.form.get("exercise_name", "").strip(),
        "duration_minutes": request.form.get("duration_minutes", "").strip(),
        "calories_burned": request.form.get("calories_burned", "").strip(),
        "workout_date": request.form.get("workout_date", "").strip(),
    }
    errors = []

    if require_name:
        if not form["exercise_name"]:
            errors.append("Exercise name is required.")
        elif len(form["exercise_name"]) > 100:
            errors.append("Exercise name must be 100 characters or fewer.")
    elif len(form["exercise_name"]) > 100:
        errors.append("Exercise name must be 100 characters or fewer.")

    duration = None
    try:
        duration = parse_int(form["duration_minutes"], "Duration", 1, 1440)
    except ValueError as error:
        errors.append(str(error))

    calories = None
    if form["calories_burned"]:
        try:
            calories = parse_int(form["calories_burned"], "Calories burned", 0, 10000)
        except ValueError as error:
            errors.append(str(error))

    workout_date = None
    try:
        workout_date = parse_date(form["workout_date"], "Workout date")
    except ValueError as error:
        errors.append(str(error))

    return form, errors, duration, calories, workout_date


def _insert_exercise_rows(cursor, workout_id, exercise_rows):
    """Insert junction rows inside an existing transaction."""

    for row in exercise_rows:
        cursor.execute(
            """
            INSERT INTO workout_exercises
                (workout_id, exercise_id, exercise_order, sets, repetitions,
                 weight_kg, duration_minutes, calories_burned)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                workout_id,
                row["exercise_id"],
                row["exercise_order"],
                row["sets"],
                row["repetitions"],
                row["weight_kg"],
                row["duration_minutes"],
                row["calories_burned"],
            ),
        )


@workouts_bp.route("/")
@login_required
def index():
    """List only the signed-in user's workouts."""

    user_id = g.user["user_id"]

    if has_exercises():
        workouts = fetch_all(
            """
            SELECT workouts.workout_id,
                   workouts.exercise_name,
                   workouts.duration_minutes,
                   workouts.calories_burned,
                   workouts.workout_date,
                   COUNT(workout_exercises.workout_exercise_id) AS exercise_count,
                   GROUP_CONCAT(exercises.exercise_name
                                ORDER BY workout_exercises.exercise_order
                                SEPARATOR ', ') AS exercise_list
            FROM workouts
            LEFT JOIN workout_exercises
                   ON workout_exercises.workout_id = workouts.workout_id
            LEFT JOIN exercises
                   ON exercises.exercise_id = workout_exercises.exercise_id
            WHERE workouts.user_id = %s
            GROUP BY workouts.workout_id, workouts.exercise_name,
                     workouts.duration_minutes, workouts.calories_burned,
                     workouts.workout_date
            ORDER BY workouts.workout_date DESC, workouts.workout_id DESC
            """,
            (user_id,),
        )
    else:
        workouts = fetch_all(
            """
            SELECT workout_id, exercise_name, duration_minutes,
                   calories_burned, workout_date
            FROM workouts
            WHERE user_id = %s
            ORDER BY workout_date DESC, workout_id DESC
            """,
            (user_id,),
        )

    totals = {
        "count": len(workouts),
        "minutes": sum(row["duration_minutes"] or 0 for row in workouts),
        "calories": sum(row["calories_burned"] or 0 for row in workouts),
    }
    return render_template(
        "workouts/index.html",
        workouts=workouts,
        totals=totals,
        exercise_feature=has_exercises(),
    )


@workouts_bp.route("/new", methods=["GET", "POST"])
@login_required
def create():
    """Add a workout for the signed-in user."""

    form = {
        "exercise_name": "",
        "duration_minutes": "",
        "calories_burned": "",
        "workout_date": date.today().isoformat(),
    }
    exercise_feature = has_exercises()

    if request.method == "POST":
        validate_csrf()
        exercise_rows, exercise_errors = _read_exercise_rows()
        form, errors, duration, calories, workout_date = _read_workout_form(
            require_name=not exercise_rows
        )
        errors = exercise_errors + errors

        if errors:
            for message in errors:
                flash(message, "error")
        else:
            legacy_name = (
                form["exercise_name"]
                or (exercise_rows[0]["exercise_name"] if exercise_rows else "")
            )
            if exercise_rows:
                # One transaction: the workout header and every exercise line
                # commit together, or none of them are saved.
                with transaction() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO workouts
                            (user_id, exercise_name, duration_minutes,
                             calories_burned, workout_date)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (
                            g.user["user_id"],
                            legacy_name,
                            duration,
                            calories,
                            workout_date,
                        ),
                    )
                    _insert_exercise_rows(cursor, cursor.lastrowid, exercise_rows)
            else:
                execute(
                    """
                    INSERT INTO workouts
                        (user_id, exercise_name, duration_minutes,
                         calories_burned, workout_date)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        g.user["user_id"],
                        legacy_name,
                        duration,
                        calories,
                        workout_date,
                    ),
                )
            flash("Workout added.", "success")
            return redirect(url_for("workouts.index"))

    return render_template(
        "workouts/form.html",
        form=form,
        mode="add",
        workout=None,
        workout_exercises=[],
        exercise_options=_exercise_options() if exercise_feature else [],
        exercise_feature=exercise_feature,
        max_exercise_rows=MAX_EXERCISE_ROWS,
    )


@workouts_bp.route("/<int:workout_id>/edit", methods=["GET", "POST"])
@login_required
def edit(workout_id):
    """Edit a workout only when it belongs to the signed-in user."""

    workout = fetch_one(
        """
        SELECT workout_id, exercise_name, duration_minutes,
               calories_burned, workout_date
        FROM workouts
        WHERE workout_id = %s AND user_id = %s
        """,
        (workout_id, g.user["user_id"]),
    )
    if workout is None:
        abort(404)

    exercise_feature = has_exercises()
    exercise_options = _exercise_options() if exercise_feature else []
    workout_exercises = []
    if exercise_feature:
        workout_exercises = fetch_all(
            """
            SELECT workout_exercise_id, exercise_id, exercise_order, sets,
                   repetitions, weight_kg, duration_minutes, calories_burned
            FROM workout_exercises
            WHERE workout_id = %s
            ORDER BY exercise_order
            """,
            (workout_id,),
        )

    form = {
        "exercise_name": workout["exercise_name"],
        "duration_minutes": workout["duration_minutes"],
        "calories_burned": (
            workout["calories_burned"]
            if workout["calories_burned"] is not None
            else ""
        ),
        "workout_date": workout["workout_date"].isoformat(),
    }

    if request.method == "POST":
        validate_csrf()
        exercise_rows, exercise_errors = _read_exercise_rows()
        form, errors, duration, calories, workout_date = _read_workout_form(
            require_name=not exercise_rows
        )
        errors = exercise_errors + errors

        if errors:
            for message in errors:
                flash(message, "error")
        else:
            legacy_name = (
                form["exercise_name"]
                or (exercise_rows[0]["exercise_name"] if exercise_rows else workout[
                    "exercise_name"
                ])
            )
            if exercise_feature:
                # Replace the exercise lines and update the header atomically.
                with transaction() as cursor:
                    cursor.execute(
                        """
                        UPDATE workouts
                        SET exercise_name = %s,
                            duration_minutes = %s,
                            calories_burned = %s,
                            workout_date = %s
                        WHERE workout_id = %s AND user_id = %s
                        """,
                        (
                            legacy_name,
                            duration,
                            calories,
                            workout_date,
                            workout_id,
                            g.user["user_id"],
                        ),
                    )
                    if cursor.rowcount == 0:
                        abort(404)
                    cursor.execute(
                        "DELETE FROM workout_exercises WHERE workout_id = %s",
                        (workout_id,),
                    )
                    _insert_exercise_rows(cursor, workout_id, exercise_rows)
            else:
                _, rowcount = execute(
                    """
                    UPDATE workouts
                    SET exercise_name = %s,
                        duration_minutes = %s,
                        calories_burned = %s,
                        workout_date = %s
                    WHERE workout_id = %s AND user_id = %s
                    """,
                    (
                        legacy_name,
                        duration,
                        calories,
                        workout_date,
                        workout_id,
                        g.user["user_id"],
                    ),
                )
                if rowcount == 0:
                    abort(404)
            flash("Workout updated.", "success")
            return redirect(url_for("workouts.index"))

    return render_template(
        "workouts/form.html",
        form=form,
        mode="edit",
        workout=workout,
        workout_exercises=workout_exercises,
        exercise_options=exercise_options,
        exercise_feature=exercise_feature,
        max_exercise_rows=MAX_EXERCISE_ROWS,
    )


@workouts_bp.route("/<int:workout_id>/delete", methods=["POST"])
@login_required
def delete(workout_id):
    """Delete a workout only when it belongs to the signed-in user.

    ``workout_exercises`` uses ON DELETE CASCADE, so its lines are removed with
    the workout by the database.
    """

    validate_csrf()
    _, rowcount = execute(
        "DELETE FROM workouts WHERE workout_id = %s AND user_id = %s",
        (workout_id, g.user["user_id"]),
    )
    if rowcount == 0:
        abort(404)
    flash("Workout deleted.", "success")
    return redirect(url_for("workouts.index"))
