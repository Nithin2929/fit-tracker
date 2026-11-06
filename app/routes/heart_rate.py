"""Time-based heart-rate samples and heart-rate zone summaries.

The `heart_rate_zones` and `heart_rate_samples` tables are proposed by
`database/migration_heart_rate.sql` and are not in the live Aiven database yet.
Every route checks `app.schema.has_heart_rate()` and shows a migration notice
instead of failing.

Zone resolution:

    estimated_max_hr = 220 - age      (fallback 190 when date_of_birth is NULL)
    percentage       = bpm / estimated_max_hr * 100

The zone whose [minimum_percentage, maximum_percentage) contains the percentage
is stored in `heart_rate_samples.zone_id`. It is nullable: a reading below the
first zone, or exactly at 100%, is stored without a guessed zone.
"""

from datetime import date, datetime

from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for

from app.db import execute, fetch_all, fetch_one
from app.schema import has_heart_rate, migration_notice
from app.utils import login_required, parse_datetime, parse_int, validate_csrf

heart_rate_bp = Blueprint("heart_rate", __name__, url_prefix="/heart-rate")


def estimated_max_hr(date_of_birth):
    """Return an estimated maximum heart rate using the 220 - age rule."""

    if not date_of_birth:
        return 190
    today = date.today()
    age = today.year - date_of_birth.year - (
        (today.month, today.day) < (date_of_birth.month, date_of_birth.day)
    )
    age = max(10, min(100, age))
    return 220 - age


def resolve_zone(heart_rate_bpm, date_of_birth, zones):
    """Return the matching zone dictionary, or None when no zone applies."""

    maximum = estimated_max_hr(date_of_birth)
    if maximum <= 0:
        return None
    percentage = float(heart_rate_bpm) / maximum * 100
    for zone in zones:
        minimum = float(zone["minimum_percentage"])
        upper = float(zone["maximum_percentage"])
        if minimum <= percentage < upper:
            return zone
    return None


def _read_sample_form():
    """Read and validate a heart-rate sample form."""

    form = {
        "heart_rate_bpm": request.form.get("heart_rate_bpm", "").strip(),
        "recorded_at": request.form.get("recorded_at", "").strip(),
    }
    errors = []

    heart_rate = None
    try:
        heart_rate = parse_int(form["heart_rate_bpm"], "Heart rate", 20, 250)
    except ValueError as error:
        errors.append(str(error))

    recorded_at = None
    try:
        recorded_at = parse_datetime(form["recorded_at"], "Recorded at")
    except ValueError as error:
        errors.append(str(error))

    if recorded_at and recorded_at > datetime.now():
        errors.append("Recorded at cannot be in the future.")
        recorded_at = None

    return form, errors, heart_rate, recorded_at


@heart_rate_bp.route("/")
@login_required
def index():
    """Show the signed-in user's recent heart-rate samples and zone summary."""

    if not has_heart_rate():
        return render_template(
            "heart_rate/index.html",
            available=False,
            notice=migration_notice("heart_rate"),
            samples=[],
            zones=[],
            summary=None,
        )

    user_id = g.user["user_id"]
    zones = fetch_all(
        """
        SELECT zone_id, zone_name, minimum_percentage, maximum_percentage
        FROM heart_rate_zones
        ORDER BY minimum_percentage
        """
    )

    samples = fetch_all(
        """
        SELECT samples.sample_id, samples.heart_rate_bpm, samples.recorded_at,
               zones.zone_name, zones.minimum_percentage, zones.maximum_percentage
        FROM heart_rate_samples AS samples
        LEFT JOIN heart_rate_zones AS zones ON zones.zone_id = samples.zone_id
        WHERE samples.user_id = %s
        ORDER BY samples.recorded_at DESC, samples.sample_id DESC
        LIMIT 50
        """,
        (user_id,),
    )

    summary = fetch_one(
        """
        SELECT COUNT(*) AS samples,
               ROUND(AVG(heart_rate_bpm), 1) AS average_bpm,
               MIN(heart_rate_bpm) AS minimum_bpm,
               MAX(heart_rate_bpm) AS maximum_bpm,
               MAX(recorded_at) AS latest_at
        FROM heart_rate_samples
        WHERE user_id = %s
        """,
        (user_id,),
    )

    return render_template(
        "heart_rate/index.html",
        available=True,
        notice=None,
        samples=samples,
        zones=zones,
        summary=summary,
        estimated_max=estimated_max_hr(g.user.get("date_of_birth")),
    )


@heart_rate_bp.route("/new", methods=["GET", "POST"])
@login_required
def create():
    """Store one time-stamped heart-rate sample."""

    if not has_heart_rate():
        flash(migration_notice("heart_rate"), "warning")
        return redirect(url_for("heart_rate.index"))

    form = {
        "heart_rate_bpm": "",
        "recorded_at": datetime.now().strftime("%Y-%m-%dT%H:%M"),
    }

    if request.method == "POST":
        validate_csrf()
        form, errors, heart_rate, recorded_at = _read_sample_form()

        if errors:
            for message in errors:
                flash(message, "error")
        else:
            zones = fetch_all(
                """
                SELECT zone_id, zone_name, minimum_percentage, maximum_percentage
                FROM heart_rate_zones
                ORDER BY minimum_percentage
                """
            )
            zone = resolve_zone(heart_rate, g.user.get("date_of_birth"), zones)
            execute(
                """
                INSERT INTO heart_rate_samples
                    (user_id, zone_id, heart_rate_bpm, recorded_at)
                VALUES (%s, %s, %s, %s)
                """,
                (
                    g.user["user_id"],
                    zone["zone_id"] if zone else None,
                    heart_rate,
                    recorded_at,
                ),
            )
            zone_label = zone["zone_name"] if zone else "no matching zone"
            flash(f"Heart-rate sample saved ({zone_label}).", "success")
            return redirect(url_for("heart_rate.index"))

    return render_template(
        "heart_rate/form.html",
        form=form,
        estimated_max=estimated_max_hr(g.user.get("date_of_birth")),
    )


@heart_rate_bp.route("/<int:sample_id>/delete", methods=["POST"])
@login_required
def delete(sample_id):
    """Delete one of the signed-in user's own samples."""

    if not has_heart_rate():
        flash(migration_notice("heart_rate"), "warning")
        return redirect(url_for("heart_rate.index"))

    validate_csrf()
    _, rowcount = execute(
        "DELETE FROM heart_rate_samples WHERE sample_id = %s AND user_id = %s",
        (sample_id, g.user["user_id"]),
    )
    if rowcount == 0:
        abort(404)
    flash("Heart-rate sample deleted.", "success")
    return redirect(url_for("heart_rate.index"))
