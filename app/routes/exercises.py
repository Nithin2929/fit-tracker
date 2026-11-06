"""Exercise catalogue management.

The `exercises` and `workout_exercises` tables are proposed by
`database/migration_exercises.sql` and are **not** in the live Aiven database
yet. Every route in this module checks `app.schema.has_exercises()` first and
shows a clear "migration required" notice instead of failing, so the rest of
the application keeps working before the migration is approved.
"""

from mysql.connector import IntegrityError

from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for

from app.db import execute, fetch_all, fetch_one
from app.schema import has_exercises, migration_notice
from app.utils import login_required, parse_choice, validate_csrf

exercises_bp = Blueprint("exercises", __name__, url_prefix="/exercises")

EXERCISE_TYPES = ("Strength", "Cardio", "Flexibility", "Balance", "Other")


def _require_feature():
    """Return True when the exercise tables exist."""

    return has_exercises()


def _read_exercise_form():
    """Read and validate the exercise catalogue form."""

    form = {
        "exercise_name": request.form.get("exercise_name", "").strip(),
        "muscle_group": request.form.get("muscle_group", "").strip(),
        "exercise_type": request.form.get("exercise_type", "").strip(),
        "description": request.form.get("description", "").strip(),
    }
    errors = []

    if not form["exercise_name"]:
        errors.append("Exercise name is required.")
    elif len(form["exercise_name"]) > 100:
        errors.append("Exercise name must be 100 characters or fewer.")

    if len(form["muscle_group"]) > 50:
        errors.append("Muscle group must be 50 characters or fewer.")

    if len(form["description"]) > 500:
        errors.append("Description must be 500 characters or fewer.")

    exercise_type = "Other"
    if form["exercise_type"]:
        try:
            exercise_type = parse_choice(
                form["exercise_type"], "Exercise type", EXERCISE_TYPES
            )
        except ValueError as error:
            errors.append(str(error))

    return form, errors, exercise_type


@exercises_bp.route("/")
@login_required
def index():
    """List the shared exercise catalogue with usage counts."""

    if not _require_feature():
        return render_template(
            "exercises/index.html",
            available=False,
            notice=migration_notice("exercises"),
            exercises=[],
        )

    exercises = fetch_all(
        """
        SELECT exercises.exercise_id,
               exercises.exercise_name,
               exercises.muscle_group,
               exercises.exercise_type,
               exercises.description,
               COUNT(workout_exercises.workout_exercise_id) AS times_used
        FROM exercises
        LEFT JOIN workout_exercises
               ON workout_exercises.exercise_id = exercises.exercise_id
        GROUP BY exercises.exercise_id, exercises.exercise_name,
                 exercises.muscle_group, exercises.exercise_type,
                 exercises.description
        ORDER BY exercises.exercise_type, exercises.exercise_name
        """
    )

    return render_template(
        "exercises/index.html",
        available=True,
        notice=None,
        exercises=exercises,
    )


@exercises_bp.route("/new", methods=["GET", "POST"])
@login_required
def create():
    """Add an exercise to the shared catalogue."""

    if not _require_feature():
        flash(migration_notice("exercises"), "warning")
        return redirect(url_for("exercises.index"))

    form = {
        "exercise_name": "",
        "muscle_group": "",
        "exercise_type": "Strength",
        "description": "",
    }

    if request.method == "POST":
        validate_csrf()
        form, errors, exercise_type = _read_exercise_form()

        if errors:
            for message in errors:
                flash(message, "error")
        else:
            try:
                execute(
                    """
                    INSERT INTO exercises
                        (exercise_name, muscle_group, exercise_type, description)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (
                        form["exercise_name"],
                        form["muscle_group"] or None,
                        exercise_type,
                        form["description"] or None,
                    ),
                )
            except IntegrityError:
                flash(
                    "An exercise with that name already exists in the catalogue.",
                    "error",
                )
            else:
                flash("Exercise added to the catalogue.", "success")
                return redirect(url_for("exercises.index"))

    return render_template(
        "exercises/form.html",
        form=form,
        mode="add",
        exercise=None,
        exercise_types=EXERCISE_TYPES,
    )


@exercises_bp.route("/<int:exercise_id>/edit", methods=["GET", "POST"])
@login_required
def edit(exercise_id):
    """Edit a shared catalogue exercise."""

    if not _require_feature():
        flash(migration_notice("exercises"), "warning")
        return redirect(url_for("exercises.index"))

    exercise = fetch_one(
        """
        SELECT exercise_id, exercise_name, muscle_group, exercise_type, description
        FROM exercises
        WHERE exercise_id = %s
        """,
        (exercise_id,),
    )
    if exercise is None:
        abort(404)

    form = {
        "exercise_name": exercise["exercise_name"],
        "muscle_group": exercise["muscle_group"] or "",
        "exercise_type": exercise["exercise_type"],
        "description": exercise["description"] or "",
    }

    if request.method == "POST":
        validate_csrf()
        form, errors, exercise_type = _read_exercise_form()

        if errors:
            for message in errors:
                flash(message, "error")
        else:
            try:
                _, rowcount = execute(
                    """
                    UPDATE exercises
                    SET exercise_name = %s,
                        muscle_group = %s,
                        exercise_type = %s,
                        description = %s
                    WHERE exercise_id = %s
                    """,
                    (
                        form["exercise_name"],
                        form["muscle_group"] or None,
                        exercise_type,
                        form["description"] or None,
                        exercise_id,
                    ),
                )
            except IntegrityError:
                flash(
                    "Another exercise already uses that name.",
                    "error",
                )
            else:
                if rowcount == 0:
                    abort(404)
                flash("Exercise updated.", "success")
                return redirect(url_for("exercises.index"))

    return render_template(
        "exercises/form.html",
        form=form,
        mode="edit",
        exercise=exercise,
        exercise_types=EXERCISE_TYPES,
    )


@exercises_bp.route("/<int:exercise_id>/delete", methods=["POST"])
@login_required
def delete(exercise_id):
    """Delete an unused catalogue exercise.

    The foreign key uses ON DELETE RESTRICT, so an exercise that appears in any
    workout cannot be deleted. That preserves the meaning of past sessions.
    """

    if not _require_feature():
        flash(migration_notice("exercises"), "warning")
        return redirect(url_for("exercises.index"))

    validate_csrf()
    try:
        _, rowcount = execute(
            "DELETE FROM exercises WHERE exercise_id = %s",
            (exercise_id,),
        )
    except IntegrityError:
        flash(
            "This exercise is used by existing workouts and cannot be deleted. "
            "Keep it in the catalogue so past sessions stay meaningful.",
            "error",
        )
        return redirect(url_for("exercises.index"))

    if rowcount == 0:
        abort(404)

    flash("Exercise deleted.", "success")
    return redirect(url_for("exercises.index"))
