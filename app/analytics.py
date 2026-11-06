"""Analytics for the signed-in user, built from real MySQL rows.

Every function takes ``user_id`` and filters with ``WHERE user_id = %s``.
Optional tables (exercises, heart rate, nutrition timestamps) are only queried
when ``app.schema`` reports that they exist, so the module works before and
after the draft migrations are approved.

Calorie balance is a *recorded* balance:

    recorded balance = recorded intake - recorded expenditure

Expenditure uses one source per day to avoid double counting: the daily
``health_metrics.calories_burned`` total when a health record exists for that
day, otherwise the sum of that day's ``workouts.calories_burned``. It is not a
medical measurement, and it does not estimate unrecorded activity.
"""

from datetime import date, timedelta

from app.db import fetch_all, fetch_one
from app.schema import has_exercises, has_heart_rate


def _number(value, default=0.0):
    """Convert MySQL Decimal/None into a JSON-safe float."""

    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def macro_ratios(protein_g, carbohydrates_g, fat_g):
    """Return Atwater-based macro ratios as percentages of macro energy.

    The denominator is macro-derived energy (4/4/9 kcal per gram), not the
    stored ``calories`` value, because labels, fibre, and alcohol can make the
    two differ. When no macro energy is recorded every ratio is 0.
    """

    protein_kcal = _number(protein_g) * 4
    carbohydrate_kcal = _number(carbohydrates_g) * 4
    fat_kcal = _number(fat_g) * 9
    total = protein_kcal + carbohydrate_kcal + fat_kcal
    if total <= 0:
        return {
            "protein_pct": 0.0,
            "carbohydrates_pct": 0.0,
            "fat_pct": 0.0,
            "macro_kcal": 0.0,
        }
    return {
        "protein_pct": round(protein_kcal / total * 100, 1),
        "carbohydrates_pct": round(carbohydrate_kcal / total * 100, 1),
        "fat_pct": round(fat_kcal / total * 100, 1),
        "macro_kcal": round(total, 1),
    }


def _date_labels(days):
    today = date.today()
    return [today - timedelta(days=offset) for offset in range(days - 1, -1, -1)]


def workout_analytics(user_id):
    """Totals, weekly/monthly progress, weekday frequency, and top exercises."""

    totals = fetch_one(
        """
        SELECT COUNT(*) AS total_workouts,
               COALESCE(SUM(duration_minutes), 0) AS total_minutes,
               COALESCE(AVG(duration_minutes), 0) AS average_minutes,
               COALESCE(SUM(calories_burned), 0) AS total_calories,
               MIN(workout_date) AS first_date,
               MAX(workout_date) AS last_date
        FROM workouts
        WHERE user_id = %s
        """,
        (user_id,),
    ) or {}

    weekly_start = date.today() - timedelta(days=83)
    weekly = fetch_all(
        """
        SELECT DATE_SUB(workout_date, INTERVAL WEEKDAY(workout_date) DAY)
                   AS week_start,
               COUNT(*) AS workouts,
               COALESCE(SUM(duration_minutes), 0) AS minutes,
               COALESCE(SUM(calories_burned), 0) AS calories
        FROM workouts
        WHERE user_id = %s AND workout_date >= %s
        GROUP BY week_start
        ORDER BY week_start
        """,
        (user_id, weekly_start),
    )
    for row in weekly:
        row["week_start"] = row["week_start"].isoformat()
        row["workouts"] = int(_number(row["workouts"]))
        row["minutes"] = int(_number(row["minutes"]))
        row["calories"] = int(_number(row["calories"]))

    monthly = fetch_all(
        """
        SELECT DATE_FORMAT(workout_date, '%%Y-%%m') AS month,
               COUNT(*) AS workouts,
               COALESCE(SUM(duration_minutes), 0) AS minutes,
               COALESCE(SUM(calories_burned), 0) AS calories
        FROM workouts
        WHERE user_id = %s AND workout_date >= %s
        GROUP BY month
        ORDER BY month
        """,
        (user_id, date.today() - timedelta(days=365)),
    )

    weekday_rows = fetch_all(
        """
        SELECT WEEKDAY(workout_date) AS weekday_index, COUNT(*) AS workouts
        FROM workouts
        WHERE user_id = %s AND workout_date >= %s
        GROUP BY weekday_index
        """,
        (user_id, date.today() - timedelta(days=90)),
    )
    weekday_counts = [0] * 7
    for row in weekday_rows:
        index = int(row["weekday_index"])
        if 0 <= index < 7:
            weekday_counts[index] = int(row["workouts"])

    top_exercises = fetch_all(
        """
        SELECT exercise_name,
               COUNT(*) AS sessions,
               COALESCE(SUM(duration_minutes), 0) AS minutes,
               COALESCE(SUM(calories_burned), 0) AS calories
        FROM workouts
        WHERE user_id = %s
        GROUP BY exercise_name
        ORDER BY sessions DESC, exercise_name ASC
        LIMIT 8
        """,
        (user_id,),
    )

    result = {
        "total_workouts": int(_number(totals.get("total_workouts"))),
        "total_minutes": int(_number(totals.get("total_minutes"))),
        "average_minutes": round(_number(totals.get("average_minutes")), 1),
        "total_calories": int(_number(totals.get("total_calories"))),
        "first_date": (
            totals["first_date"].isoformat() if totals.get("first_date") else None
        ),
        "last_date": (
            totals["last_date"].isoformat() if totals.get("last_date") else None
        ),
        "weekly": weekly,
        "monthly": monthly,
        "weekday_counts": weekday_counts,
        "top_exercises": top_exercises,
        "exercise_analytics": {},
        "category_summary": [],
        "performance_summary": [],
    }

    if has_exercises():
        result["exercise_analytics"] = exercise_analytics(user_id)

    return result


def exercise_analytics(user_id):
    """Strength/cardio summaries and per-exercise performance (post-migration)."""

    categories = fetch_all(
        """
        SELECT exercises.exercise_type AS category,
               COUNT(*) AS entries,
               COALESCE(SUM(workout_exercises.duration_minutes), 0) AS minutes,
               COALESCE(SUM(workout_exercises.calories_burned), 0) AS calories
        FROM workout_exercises
        JOIN workouts ON workouts.workout_id = workout_exercises.workout_id
        JOIN exercises ON exercises.exercise_id = workout_exercises.exercise_id
        WHERE workouts.user_id = %s
        GROUP BY exercises.exercise_type
        ORDER BY entries DESC
        """,
        (user_id,),
    )

    performance = fetch_all(
        """
        SELECT exercises.exercise_name,
               exercises.muscle_group,
               exercises.exercise_type,
               COUNT(*) AS entries,
               COALESCE(SUM(workout_exercises.sets), 0) AS total_sets,
               COALESCE(SUM(workout_exercises.repetitions), 0) AS total_repetitions,
               COALESCE(MAX(workout_exercises.weight_kg), 0) AS max_weight_kg,
               COALESCE(SUM(workout_exercises.sets *
                            workout_exercises.repetitions *
                            workout_exercises.weight_kg), 0) AS volume_kg,
               COALESCE(SUM(workout_exercises.calories_burned), 0) AS calories
        FROM workout_exercises
        JOIN workouts ON workouts.workout_id = workout_exercises.workout_id
        JOIN exercises ON exercises.exercise_id = workout_exercises.exercise_id
        WHERE workouts.user_id = %s
        GROUP BY exercises.exercise_id, exercises.exercise_name,
                 exercises.muscle_group, exercises.exercise_type
        ORDER BY volume_kg DESC, entries DESC
        LIMIT 12
        """,
        (user_id,),
    )

    for row in performance:
        row["max_weight_kg"] = _number(row["max_weight_kg"])
        row["volume_kg"] = _number(row["volume_kg"])
        row["total_sets"] = int(_number(row["total_sets"]))
        row["total_repetitions"] = int(_number(row["total_repetitions"]))
        row["calories"] = int(_number(row["calories"]))

    return {"categories": categories, "performance": performance}


def protein_strength_analytics(user_id, days=90):
    """Compare weekly recorded protein with strength-training volume.

    Protein intake and strength work are aggregated independently before they
    are joined, preventing a many-to-many join from multiplying either total.
    This is descriptive only and does not imply a causal relationship.
    """

    if not has_exercises():
        return {
            "available": False,
            "days": days,
            "weeks": [],
            "note": "Apply the exercises migration to enable strength trends.",
        }

    start = date.today() - timedelta(days=days - 1)
    rows = fetch_all(
        """
        WITH protein_weekly AS (
            SELECT DATE_SUB(log_date, INTERVAL WEEKDAY(log_date) DAY) AS week_start,
                   ROUND(
                       SUM(protein) /
                       NULLIF(COUNT(DISTINCT log_date), 0),
                       1
                   ) AS average_daily_protein_g,
                   COUNT(DISTINCT log_date) AS protein_logged_days
            FROM nutrition_logs
            WHERE user_id = %s
              AND log_date BETWEEN %s AND %s
              AND protein IS NOT NULL
            GROUP BY week_start
        ),
        strength_weekly AS (
            SELECT DATE_SUB(workouts.workout_date,
                            INTERVAL WEEKDAY(workouts.workout_date) DAY)
                       AS week_start,
                   COUNT(DISTINCT workouts.workout_id) AS strength_sessions,
                   ROUND(
                       COALESCE(
                           SUM(
                               CASE
                                   WHEN workout_exercises.sets IS NOT NULL
                                    AND workout_exercises.repetitions IS NOT NULL
                                    AND workout_exercises.weight_kg IS NOT NULL
                                   THEN workout_exercises.sets
                                      * workout_exercises.repetitions
                                      * workout_exercises.weight_kg
                                   ELSE 0
                               END
                           ),
                           0
                       ),
                       1
                   ) AS strength_volume_kg,
                   MAX(workout_exercises.weight_kg) AS max_load_kg
            FROM workouts
            JOIN workout_exercises
              ON workout_exercises.workout_id = workouts.workout_id
            JOIN exercises
              ON exercises.exercise_id = workout_exercises.exercise_id
            WHERE workouts.user_id = %s
              AND workouts.workout_date BETWEEN %s AND %s
              AND exercises.exercise_type = 'Strength'
            GROUP BY week_start
        ),
        week_keys AS (
            SELECT week_start FROM protein_weekly
            UNION
            SELECT week_start FROM strength_weekly
        )
        SELECT week_keys.week_start,
               protein_weekly.average_daily_protein_g,
               COALESCE(protein_weekly.protein_logged_days, 0)
                   AS protein_logged_days,
               COALESCE(strength_weekly.strength_sessions, 0)
                   AS strength_sessions,
               COALESCE(strength_weekly.strength_volume_kg, 0)
                   AS strength_volume_kg,
               strength_weekly.max_load_kg
        FROM week_keys
        LEFT JOIN protein_weekly USING (week_start)
        LEFT JOIN strength_weekly USING (week_start)
        ORDER BY week_keys.week_start
        """,
        (user_id, start, date.today(), user_id, start, date.today()),
    )

    weeks = []
    for row in rows:
        weeks.append(
            {
                "week_start": row["week_start"].isoformat(),
                "average_daily_protein_g": (
                    _number(row["average_daily_protein_g"])
                    if row["average_daily_protein_g"] is not None
                    else None
                ),
                "protein_logged_days": int(_number(row["protein_logged_days"])),
                "strength_sessions": int(_number(row["strength_sessions"])),
                "strength_volume_kg": _number(row["strength_volume_kg"]),
                "max_load_kg": (
                    _number(row["max_load_kg"])
                    if row["max_load_kg"] is not None
                    else None
                ),
            }
        )

    return {
        "available": True,
        "days": days,
        "weeks": weeks,
        "note": (
            "Weekly recorded protein and strength-training volume are "
            "descriptive trends, not evidence that protein caused strength changes."
        ),
    }


def nutrition_analytics(user_id, days=30):
    """Intake totals, averages, macro ratios, and daily/weekly series."""

    start = date.today() - timedelta(days=days - 1)
    totals = fetch_one(
        """
        SELECT COALESCE(SUM(calories), 0) AS calories,
               COALESCE(SUM(protein), 0) AS protein,
               COALESCE(SUM(carbohydrates), 0) AS carbohydrates,
               COALESCE(SUM(fat), 0) AS fat,
               COUNT(DISTINCT log_date) AS logged_days,
               COUNT(*) AS entries
        FROM nutrition_logs
        WHERE user_id = %s AND log_date BETWEEN %s AND %s
        """,
        (user_id, start, date.today()),
    ) or {}

    logged_days = int(_number(totals.get("logged_days")))
    calorie_total = _number(totals.get("calories"))
    protein_total = _number(totals.get("protein"))
    carbohydrate_total = _number(totals.get("carbohydrates"))
    fat_total = _number(totals.get("fat"))

    ratios = macro_ratios(protein_total, carbohydrate_total, fat_total)

    daily = fetch_all(
        """
        SELECT log_date AS day,
               COALESCE(SUM(calories), 0) AS calories,
               COALESCE(SUM(protein), 0) AS protein,
               COALESCE(SUM(carbohydrates), 0) AS carbohydrates,
               COALESCE(SUM(fat), 0) AS fat
        FROM nutrition_logs
        WHERE user_id = %s AND log_date BETWEEN %s AND %s
        GROUP BY log_date
        ORDER BY log_date
        """,
        (user_id, start, date.today()),
    )
    for row in daily:
        row["day"] = row["day"].isoformat()
        for key in ("calories", "protein", "carbohydrates", "fat"):
            row[key] = _number(row[key])

    weekly = fetch_all(
        """
        SELECT DATE_SUB(log_date, INTERVAL WEEKDAY(log_date) DAY) AS week_start,
               COALESCE(SUM(calories), 0) AS calories,
               COALESCE(SUM(protein), 0) AS protein,
               COALESCE(SUM(carbohydrates), 0) AS carbohydrates,
               COALESCE(SUM(fat), 0) AS fat
        FROM nutrition_logs
        WHERE user_id = %s AND log_date >= %s
        GROUP BY week_start
        ORDER BY week_start
        """,
        (user_id, date.today() - timedelta(days=83)),
    )
    for row in weekly:
        row["week_start"] = row["week_start"].isoformat()
        for key in ("calories", "protein", "carbohydrates", "fat"):
            row[key] = _number(row[key])

    meals = fetch_all(
        """
        SELECT meal_type, COUNT(*) AS entries,
               COALESCE(SUM(calories), 0) AS calories
        FROM nutrition_logs
        WHERE user_id = %s AND log_date BETWEEN %s AND %s
        GROUP BY meal_type
        ORDER BY calories DESC
        """,
        (user_id, start, date.today()),
    )

    return {
        "calories": round(calorie_total, 1),
        "protein": round(protein_total, 1),
        "carbohydrates": round(carbohydrate_total, 1),
        "fat": round(fat_total, 1),
        "entries": int(_number(totals.get("entries"))),
        "logged_days": logged_days,
        "average_calories": round(calorie_total / logged_days, 1) if logged_days else 0.0,
        "average_protein": round(protein_total / logged_days, 1) if logged_days else 0.0,
        "ratios": ratios,
        "daily": daily,
        "weekly": weekly,
        "meals": meals,
        "window_days": days,
    }


def health_analytics(user_id, days=90):
    """Latest health record, weight/BMI/steps trends, and weight change."""

    latest = fetch_one(
        """
        SELECT metric_id, weight, height, steps, calories_burned, recorded_date
        FROM health_metrics
        WHERE user_id = %s
        ORDER BY recorded_date DESC, metric_id DESC
        LIMIT 1
        """,
        (user_id,),
    )

    start = date.today() - timedelta(days=days - 1)
    history = fetch_all(
        """
        SELECT recorded_date AS day, weight, height, steps, calories_burned
        FROM health_metrics
        WHERE user_id = %s AND recorded_date BETWEEN %s AND %s
        ORDER BY recorded_date
        """,
        (user_id, start, date.today()),
    )

    weight_series = []
    bmi_series = []
    for row in history:
        weight = _number(row["weight"])
        height = _number(row["height"])
        bmi = round(weight / ((height / 100) ** 2), 1) if weight > 0 and height > 0 else 0
        weight_series.append({"day": row["day"].isoformat(), "weight": weight})
        bmi_series.append({"day": row["day"].isoformat(), "bmi": bmi})

    weight_change = None
    if len(history) >= 2:
        weight_change = round(
            _number(history[-1]["weight"]) - _number(history[0]["weight"]), 2
        )

    weekly_steps = fetch_all(
        """
        SELECT DATE_SUB(recorded_date, INTERVAL WEEKDAY(recorded_date) DAY)
                   AS week_start,
               ROUND(AVG(steps), 0) AS average_steps,
               COALESCE(SUM(calories_burned), 0) AS calories
        FROM health_metrics
        WHERE user_id = %s AND recorded_date >= %s
        GROUP BY week_start
        ORDER BY week_start
        """,
        (user_id, date.today() - timedelta(days=83)),
    )
    for row in weekly_steps:
        row["week_start"] = row["week_start"].isoformat()
        row["average_steps"] = int(_number(row["average_steps"]))

    return {
        "latest": latest,
        "weight_series": weight_series,
        "bmi_series": bmi_series,
        "weekly_steps": weekly_steps,
        "weight_change": weight_change,
        "record_count": len(history),
    }


def calorie_balance(user_id, days=30):
    """Daily recorded intake minus recorded expenditure, with one source per day."""

    start = date.today() - timedelta(days=days - 1)
    end = date.today()
    rows = fetch_all(
        """
        WITH recorded_dates AS (
            SELECT log_date AS day FROM nutrition_logs
            WHERE user_id = %s AND log_date BETWEEN %s AND %s
            UNION
            SELECT workout_date FROM workouts
            WHERE user_id = %s AND workout_date BETWEEN %s AND %s
            UNION
            SELECT recorded_date FROM health_metrics
            WHERE user_id = %s AND recorded_date BETWEEN %s AND %s
        ),
        intake AS (
            SELECT log_date AS day, COALESCE(SUM(calories), 0) AS calories
            FROM nutrition_logs
            WHERE user_id = %s AND log_date BETWEEN %s AND %s
            GROUP BY log_date
        ),
        workout_out AS (
            SELECT workout_date AS day, COALESCE(SUM(calories_burned), 0) AS calories
            FROM workouts
            WHERE user_id = %s AND workout_date BETWEEN %s AND %s
            GROUP BY workout_date
        ),
        health_out AS (
            SELECT recorded_date AS day, COALESCE(SUM(calories_burned), 0) AS calories
            FROM health_metrics
            WHERE user_id = %s AND recorded_date BETWEEN %s AND %s
            GROUP BY recorded_date
        )
        SELECT recorded_dates.day,
               COALESCE(intake.calories, 0) AS intake,
               COALESCE(health_out.calories, workout_out.calories, 0) AS expenditure,
               COALESCE(health_out.calories, 0) AS activity_calories,
               COALESCE(workout_out.calories, 0) AS workout_calories,
               COALESCE(intake.calories, 0)
                   - COALESCE(health_out.calories, workout_out.calories, 0) AS balance
        FROM recorded_dates
        LEFT JOIN intake ON intake.day = recorded_dates.day
        LEFT JOIN workout_out ON workout_out.day = recorded_dates.day
        LEFT JOIN health_out ON health_out.day = recorded_dates.day
        ORDER BY recorded_dates.day
        """,
        (
            user_id, start, end,
            user_id, start, end,
            user_id, start, end,
            user_id, start, end,
            user_id, start, end,
            user_id, start, end,
        ),
    )
    for row in rows:
        row["day"] = row["day"].isoformat()
        for key in ("intake", "expenditure", "activity_calories",
                    "workout_calories", "balance"):
            row[key] = _number(row[key])

    return {
        "rows": rows,
        "total_intake": round(sum(row["intake"] for row in rows), 1),
        "total_expenditure": round(sum(row["expenditure"] for row in rows), 1),
        "total_balance": round(sum(row["balance"] for row in rows), 1),
        "days": days,
    }


def heart_rate_analytics(user_id, days=30):
    """Zone distribution and time-in-zone for recorded samples (post-migration)."""

    if not has_heart_rate():
        return {"available": False, "samples": 0, "zones": [], "recent": []}

    start = date.today() - timedelta(days=days - 1)
    rows = fetch_all(
        """
        SELECT zones.zone_id, zones.zone_name,
               zones.minimum_percentage, zones.maximum_percentage,
               COUNT(samples.sample_id) AS samples,
               ROUND(AVG(samples.heart_rate_bpm), 1) AS average_bpm,
               MIN(samples.heart_rate_bpm) AS minimum_bpm,
               MAX(samples.heart_rate_bpm) AS maximum_bpm
        FROM heart_rate_zones AS zones
        LEFT JOIN heart_rate_samples AS samples
               ON samples.zone_id = zones.zone_id
              AND samples.user_id = %s
              AND samples.recorded_at >= %s
        GROUP BY zones.zone_id, zones.zone_name,
                 zones.minimum_percentage, zones.maximum_percentage
        ORDER BY zones.minimum_percentage
        """,
        (user_id, start),
    )

    recent = fetch_all(
        """
        SELECT samples.sample_id, samples.heart_rate_bpm, samples.recorded_at,
               zones.zone_name
        FROM heart_rate_samples AS samples
        LEFT JOIN heart_rate_zones AS zones ON zones.zone_id = samples.zone_id
        WHERE samples.user_id = %s AND samples.recorded_at >= %s
        ORDER BY samples.recorded_at DESC
        LIMIT 25
        """,
        (user_id, start),
    )

    total = sum(int(_number(row["samples"])) for row in rows)
    return {
        "available": True,
        "samples": total,
        "zones": rows,
        "recent": recent,
    }


def _fill_daily_series(rows, key, days):
    labels = [day.isoformat() for day in _date_labels(days)]
    values = {row["day"]: row.get(key, 0) for row in rows}
    return labels, [round(_number(values.get(label)), 1) for label in labels]


def dashboard_charts(user_id, days=30, workouts=None, nutrition=None,
                     health=None, balance=None):
    """Six DB-driven chart payloads for the dashboard.

    Each chart has ``labels`` and one or more ``series``. Empty datasets are
    returned as empty arrays so the frontend can show a friendly message.
    Callers that already computed an analytics block can pass it in to avoid
    running the same aggregate queries twice.
    """

    workouts = workouts if workouts is not None else workout_analytics(user_id)
    nutrition = (
        nutrition if nutrition is not None
        else nutrition_analytics(user_id, days=days)
    )
    health = health if health is not None else health_analytics(user_id)
    balance = balance if balance is not None else calorie_balance(user_id, days=days)

    weekly = workouts["weekly"][-8:]
    weekly_labels = [row["week_start"] for row in weekly]
    weekly_counts = [row["workouts"] for row in weekly]

    consumed_labels, consumed_values = _fill_daily_series(
        nutrition["daily"], "calories", min(days, 14)
    )
    burned_labels, burned_values = _fill_daily_series(
        balance["rows"], "expenditure", min(days, 14)
    )

    weight_labels = [row["day"] for row in health["weight_series"]]
    weight_values = [row["weight"] for row in health["weight_series"]]

    ratios = nutrition["ratios"]

    return {
        "weekly_workouts": {
            "type": "bar",
            "labels": weekly_labels,
            "series": [{"name": "Workouts", "values": weekly_counts}],
            "has_data": any(weekly_counts),
        },
        "daily_calories_in": {
            "type": "line",
            "labels": consumed_labels,
            "series": [{"name": "Calories eaten", "values": consumed_values}],
            "has_data": any(value > 0 for value in consumed_values),
        },
        "daily_calories_out": {
            "type": "line",
            "labels": burned_labels,
            "series": [{"name": "Recorded calories burned", "values": burned_values}],
            "has_data": any(value > 0 for value in burned_values),
        },
        "weight_progress": {
            "type": "line",
            "labels": weight_labels,
            "series": [{"name": "Weight (kg)", "values": weight_values}],
            "has_data": len(weight_values) > 0,
        },
        "nutrition_macros": {
            "type": "bar",
            "labels": ["Protein", "Carbohydrates", "Fat"],
            "series": [{
                "name": "Grams",
                "values": [nutrition["protein"], nutrition["carbohydrates"],
                           nutrition["fat"]],
            }],
            "ratios": [ratios["protein_pct"], ratios["carbohydrates_pct"],
                       ratios["fat_pct"]],
            "has_data": ratios["macro_kcal"] > 0,
        },
        "workout_frequency": {
            "type": "bar",
            "labels": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
            "series": [{"name": "Sessions", "values": workouts["weekday_counts"]}],
            "has_data": any(workouts["weekday_counts"]),
        },
    }


def analytics_summary(user_id, days=30):
    """Full analytics payload used by the reports page and JSON endpoint."""

    workouts = workout_analytics(user_id)
    nutrition = nutrition_analytics(user_id, days=days)
    health = health_analytics(user_id)
    balance = calorie_balance(user_id, days=days)
    heart_rate = heart_rate_analytics(user_id, days=days)
    protein_strength = protein_strength_analytics(user_id, days=days)

    return {
        "workouts": workouts,
        "nutrition": nutrition,
        "health": health,
        "calorie_balance": balance,
        "heart_rate": heart_rate,
        "protein_strength": protein_strength,
        "chart_data": dashboard_charts(
            user_id,
            days=days,
            workouts=workouts,
            nutrition=nutrition,
            health=health,
            balance=balance,
        ),
    }
