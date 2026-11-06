#!/usr/bin/env python3
"""Generate a deterministic, realistic FitTrack sample dataset.

WHY THIS EXISTS
    The mentor requires at least 1,000 records suitable for analytics testing.
    The live Aiven database must never be filled with synthetic rows, so this
    script:

    * writes a SQL file by default (``database/sample_data.sql``); it does NOT
      touch any database unless you explicitly ask it to,
    * can optionally insert into a **separate** test database with ``--execute``,
    * refuses to execute when the target name does not look like a test database
      or when it matches the configured production ``DB_NAME``.

USAGE
    # 1. Generate the SQL file only (safe, default)
    python database/generate_sample_data.py

    # 2. Deterministic output and a custom path
    python database/generate_sample_data.py --seed 20261103 \
        --output database/sample_data.sql

    # 3. Insert into an explicitly configured test database
    #    TEST_DB_HOST / TEST_DB_PORT / TEST_DB_USER / TEST_DB_PASSWORD /
    #    TEST_DB_NAME / TEST_DB_SSL_CA
    python database/generate_sample_data.py --execute

DEMO LOGIN
    Every generated account uses the password ``DemoPass123!``.
    Emails look like ``demo01@fittrack.test``.

The generated IDs start far above typical live values (users 1001+,
workouts 5001+, ...) so a test database can also receive them safely.
"""

import argparse
import hashlib
import os
import random
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - python-dotenv is in requirements.txt
    load_dotenv = None

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if load_dotenv:
    load_dotenv(PROJECT_ROOT / ".env")

DEFAULT_SEED = 20261103
DEFAULT_OUTPUT = PROJECT_ROOT / "database" / "sample_data.sql"
DEMO_PASSWORD = "DemoPass123!"
DEMO_SALT = "fittrack-demo-salt"

COUNT_USERS = 30
COUNT_EXERCISES = 24
WORKOUTS_PER_USER = 24
NUTRITION_PER_USER = 40
HEALTH_DAYS_PER_USER = 30
HEART_RATE_PER_USER = 12

USER_IDS = list(range(1001, 1001 + COUNT_USERS))
EXERCISE_IDS = list(range(101, 101 + COUNT_EXERCISES))
WORKOUT_IDS = list(range(5001, 5001 + COUNT_USERS * WORKOUTS_PER_USER))
NUTRITION_IDS = list(range(6001, 6001 + COUNT_USERS * NUTRITION_PER_USER))
HEALTH_IDS = list(range(7001, 7001 + COUNT_USERS * HEALTH_DAYS_PER_USER))
SAMPLE_IDS = list(range(9001, 9001 + COUNT_USERS * HEART_RATE_PER_USER))

FIRST_NAMES = [
    "Aarav", "Aditi", "Arjun", "Ananya", "Bhavya", "Chirag", "Devika", "Dhruv",
    "Esha", "Farhan", "Gaurav", "Isha", "Jeevan", "Kavya", "Kiran", "Lakshmi",
    "Manav", "Meera", "Naveen", "Nisha", "Omkar", "Pooja", "Rahul", "Riya",
    "Sanjay", "Sneha", "Tanvi", "Uday", "Varun", "Zoya",
]
LAST_NAMES = [
    "Sharma", "Patel", "Nair", "Rao", "Iyer", "Menon", "Gupta", "Verma",
    "Reddy", "Kulkarni", "Joshi", "Das", "Bose", "Kapoor", "Mehta", "Pillai",
    "Shetty", "Chawla", "Bhat", "Sinha",
]
GENDERS = ["Male", "Female", "Other", "Prefer not to say"]
GENDER_WEIGHTS = [46, 46, 4, 4]

EXERCISES = [
    ("Running", "Full body", "Cardio", "Steady or interval running outdoors or on a treadmill."),
    ("Walking", "Full body", "Cardio", "Low-impact walking session."),
    ("Cycling", "Legs", "Cardio", "Indoor or outdoor cycling session."),
    ("Swimming", "Full body", "Cardio", "Pool or open-water swimming."),
    ("Rowing", "Full body", "Cardio", "Rowing machine or on-water rowing."),
    ("Jump Rope", "Full body", "Cardio", "Skipping rope for conditioning."),
    ("Squat", "Legs", "Strength", "Bodyweight or loaded squat."),
    ("Deadlift", "Posterior chain", "Strength", "Hip-hinge barbell or dumbbell lift."),
    ("Bench Press", "Chest", "Strength", "Flat, incline, or dumbbell press."),
    ("Overhead Press", "Shoulders", "Strength", "Standing or seated vertical press."),
    ("Barbell Row", "Back", "Strength", "Bent-over row for upper-body pulling."),
    ("Pull-up", "Back", "Strength", "Bodyweight vertical pull."),
    ("Push-up", "Chest", "Strength", "Bodyweight horizontal push."),
    ("Lunge", "Legs", "Strength", "Forward, reverse, or walking lunge."),
    ("Plank", "Core", "Strength", "Isometric core hold."),
    ("Bicep Curl", "Arms", "Strength", "Dumbbell or cable curl."),
    ("Tricep Dip", "Arms", "Strength", "Parallel-bar or bench dip."),
    ("Hip Thrust", "Glutes", "Strength", "Barbell or bodyweight hip extension."),
    ("Yoga", "Full body", "Flexibility", "Mobility and flexibility practice."),
    ("Stretching", "Full body", "Flexibility", "Guided static or dynamic stretching."),
    ("Balance Drill", "Full body", "Balance", "Single-leg or stability exercises."),
    ("Burpee", "Full body", "Cardio", "Full-body conditioning movement."),
    ("Kettlebell Swing", "Posterior chain", "Strength", "Explosive hip-hinge swing."),
    ("Mountain Climber", "Core", "Cardio", "Dynamic plank conditioning."),
]

FOODS = [
    ("Oatmeal with milk", "Breakfast", 350, 12.0, 55.0, 8.0),
    ("Greek yoghurt and berries", "Breakfast", 220, 18.0, 22.0, 6.0),
    ("Vegetable poha", "Breakfast", 280, 8.0, 45.0, 7.0),
    ("Egg white omelette", "Breakfast", 190, 24.0, 4.0, 8.0),
    ("Banana and peanut butter toast", "Breakfast", 330, 10.0, 42.0, 13.0),
    ("Grilled chicken salad", "Lunch", 420, 38.0, 24.0, 18.0),
    ("Dal rice with vegetables", "Lunch", 520, 20.0, 82.0, 11.0),
    ("Paneer wrap", "Lunch", 480, 26.0, 48.0, 20.0),
    ("Rajma chawal", "Lunch", 540, 21.0, 88.0, 10.0),
    ("Tuna sandwich", "Lunch", 390, 28.0, 40.0, 12.0),
    ("Grilled salmon with quinoa", "Dinner", 610, 42.0, 52.0, 24.0),
    ("Chicken curry with roti", "Dinner", 650, 38.0, 62.0, 26.0),
    ("Vegetable pasta", "Dinner", 520, 17.0, 84.0, 13.0),
    ("Tofu stir-fry", "Dinner", 430, 26.0, 38.0, 19.0),
    ("Lentil soup with bread", "Dinner", 360, 19.0, 55.0, 8.0),
    ("Apple", "Snack", 95, 0.5, 25.0, 0.3),
    ("Mixed nuts", "Snack", 180, 5.0, 6.0, 16.0),
    ("Protein shake", "Snack", 160, 25.0, 8.0, 3.0),
    ("Roasted chickpeas", "Snack", 140, 7.0, 20.0, 4.0),
    ("Dark chocolate", "Snack", 170, 2.0, 17.0, 11.0),
]

HEALTH_NOTES = []


def deterministic_hash(password, salt, iterations=260000):
    """Build a deterministic Werkzeug-compatible PBKDF2 hash string."""

    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations
    ).hex()
    return f"pbkdf2:sha256:{iterations}${salt}${digest}"


def sql_value(value):
    """Quote a Python value for a MySQL INSERT statement."""

    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, datetime):
        return "'" + value.strftime("%Y-%m-%d %H:%M:%S") + "'"
    if isinstance(value, date):
        return "'" + value.isoformat() + "'"
    text = str(value).replace("\\", "\\\\").replace("'", "''")
    return "'" + text + "'"


def insert_block(table, columns, rows, batch_size=100):
    """Return one or more multi-row INSERT statements."""

    statements = []
    rows = list(rows)
    for start in range(0, len(rows), batch_size):
        batch = rows[start:start + batch_size]
        values = ",\n".join(
            "(" + ", ".join(sql_value(value) for value in row) + ")" for row in batch
        )
        statements.append(
            f"INSERT INTO {table} ({', '.join(columns)}) VALUES\n{values};"
        )
    return "\n\n".join(statements)


def build_dataset(seed=DEFAULT_SEED):
    """Build every row in memory and return a dict of table -> rows."""

    rng = random.Random(seed)
    today = date.today()
    password_hash = deterministic_hash(DEMO_PASSWORD, DEMO_SALT)

    users = []
    profiles = {}
    for offset, user_id in enumerate(USER_IDS):
        age = rng.randint(18, 55)
        birthday = today - timedelta(days=age * 365 + rng.randint(0, 364))
        height = round(rng.uniform(150, 193), 1)
        gender = rng.choices(GENDERS, weights=GENDER_WEIGHTS, k=1)[0]
        full_name = f"{FIRST_NAMES[offset % len(FIRST_NAMES)]} {LAST_NAMES[offset % len(LAST_NAMES)]}"
        users.append(
            (
                user_id,
                full_name,
                f"demo{offset + 1:02d}@fittrack.test",
                password_hash,
                birthday,
                gender,
                height,
            )
        )
        profiles[user_id] = {
            "height": height,
            "weight": round(rng.uniform(52, 96), 1),
            "age": age,
            "birthday": birthday,
        }

    exercises = [(exercise_id,) + item for exercise_id, item in zip(EXERCISE_IDS, EXERCISES)]

    workouts = []
    workout_exercises = []
    workout_plan = {}
    workout_id = WORKOUT_IDS[0]
    junction_id = 8001
    for user_id in USER_IDS:
        for _ in range(WORKOUTS_PER_USER):
            day = today - timedelta(days=rng.randint(0, 119))
            count = rng.choices([1, 2, 3], weights=[35, 45, 20], k=1)[0]
            chosen = rng.sample(EXERCISES, k=count)
            total_duration = 0
            total_calories = 0
            lines = []
            for order, (name, muscle, kind, _description) in enumerate(chosen, start=1):
                if kind == "Strength":
                    sets = rng.randint(2, 5)
                    reps = rng.randint(6, 15)
                    weight = round(rng.uniform(5, 80) if muscle not in ("Chest", "Legs", "Back", "Posterior chain")
                                   else rng.uniform(20, 140), 1)
                    minutes = rng.randint(5, 15)
                    calories = rng.randint(30, 120)
                elif kind == "Cardio":
                    sets = reps = weight = None
                    minutes = rng.randint(10, 40)
                    calories = rng.randint(60, 380)
                elif kind == "Flexibility":
                    sets = reps = weight = None
                    minutes = rng.randint(10, 25)
                    calories = rng.randint(20, 80)
                else:
                    sets = rng.randint(1, 3)
                    reps = rng.randint(5, 12)
                    weight = None
                    minutes = rng.randint(5, 12)
                    calories = rng.randint(15, 60)
                lines.append(
                    (workout_id, name, order, sets, reps, weight, minutes, calories)
                )
                total_duration += minutes
                total_calories += calories

            legacy_name = " + ".join(item[0] for item in chosen)[:100]
            workouts.append(
                (workout_id, user_id, legacy_name, total_duration, total_calories, day)
            )
            workout_plan[workout_id] = lines
            for line in lines:
                workout_exercises.append((junction_id,) + line)
                junction_id += 1
            workout_id += 1

    nutrition = []
    nutrition_id = NUTRITION_IDS[0]
    for user_id in USER_IDS:
        used_days = sorted(
            rng.sample(range(0, 75), k=min(25, 75)), reverse=True
        )
        for index in range(NUTRITION_PER_USER):
            day = today - timedelta(days=used_days[index % len(used_days)])
            name, meal, calories, protein, carbs, fat = rng.choice(FOODS)
            variation = rng.uniform(0.85, 1.2)
            nutrition.append(
                (
                    nutrition_id,
                    user_id,
                    name,
                    meal,
                    int(round(calories * variation)),
                    round(protein * variation, 1),
                    round(carbs * variation, 1),
                    round(fat * variation, 1),
                    day,
                )
            )
            nutrition_id += 1

    health = []
    health_id = HEALTH_IDS[0]
    for user_id in USER_IDS:
        profile = profiles[user_id]
        current_weight = profile["weight"]
        days = sorted(rng.sample(range(0, 90), k=HEALTH_DAYS_PER_USER), reverse=True)
        for day_offset in days:
            day = today - timedelta(days=day_offset)
            current_weight = round(
                max(40.0, min(160.0, current_weight + rng.uniform(-0.35, 0.25))), 1
            )
            health.append(
                (
                    health_id,
                    user_id,
                    current_weight,
                    profile["height"],
                    rng.randint(1800, 18000),
                    rng.randint(120, 900),
                    day,
                )
            )
            health_id += 1

    heart_rate = []
    sample_id = SAMPLE_IDS[0]
    zone_bounds = [
        ("Zone 1", 0.0, 50.0),
        ("Zone 2", 50.0, 60.0),
        ("Zone 3", 60.0, 70.0),
        ("Zone 4", 70.0, 80.0),
        ("Zone 5", 80.0, 100.0),
    ]
    for user_id in USER_IDS:
        max_hr = 220 - profiles[user_id]["age"]
        for _ in range(HEART_RATE_PER_USER):
            bpm = rng.randint(62, 182)
            percentage = bpm / max_hr * 100
            zone_name = None
            for name, minimum, maximum in zone_bounds:
                if minimum <= percentage < maximum:
                    zone_name = name
                    break
            day = today - timedelta(days=rng.randint(0, 29))
            recorded_at = datetime(
                day.year, day.month, day.day, rng.randint(6, 21), rng.randint(0, 59)
            )
            heart_rate.append((sample_id, user_id, zone_name, bpm, recorded_at))
            sample_id += 1

    return {
        "users": users,
        "exercises": exercises,
        "workouts": workouts,
        "workout_exercises": workout_exercises,
        "nutrition_logs": nutrition,
        "health_metrics": health,
        "heart_rate_samples": heart_rate,
        "workout_plan": workout_plan,
    }


def render_sql(data, seed=DEFAULT_SEED):
    """Render the full SQL file with a test-database safety guard."""

    total = sum(
        len(data[key])
        for key in (
            "users",
            "exercises",
            "workouts",
            "workout_exercises",
            "nutrition_logs",
            "health_metrics",
            "heart_rate_samples",
        )
    )
    counts = {
        key: len(data[key])
        for key in (
            "users",
            "exercises",
            "workouts",
            "workout_exercises",
            "nutrition_logs",
            "health_metrics",
            "heart_rate_samples",
        )
    }

    parts = [
        "-- ============================================================================",
        "-- FitTrack - generated sample dataset",
        f"-- File: database/sample_data.sql",
        f"-- Seed: {seed}",
        f"-- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"-- Total records: {total}",
        "--",
        "-- PRE-REQUISITES",
        "--   1. A SEPARATE test/sample/dev database.",
        "--   2. Run database/aiven_init.sql and the three approved migrations there.",
        "--   3. Never run this file against the production Aiven database.",
        "--",
        "-- SAFETY",
        "--   The guard procedure below refuses to continue unless DATABASE()",
        "--   contains test, sample, or dev. No DROP/TRUNCATE/DELETE is present.",
        "--",
        "-- COUNTS",
    ]
    parts.extend(f"--   {key}: {value}" for key, value in counts.items())
    parts.extend(
        [
            "--",
            "-- DEMO LOGIN",
            f"--   password: {DEMO_PASSWORD}",
            "--   users: demo01@fittrack.test ... demo%02d@fittrack.test" % COUNT_USERS,
            "--",
            "-- GENERATED BY",
            "--   python database/generate_sample_data.py",
            "-- ============================================================================",
            "",
            "DELIMITER $$",
            "DROP PROCEDURE IF EXISTS fittrack_assert_test_database$$",
            "CREATE PROCEDURE fittrack_assert_test_database()",
            "BEGIN",
            "    IF DATABASE() NOT LIKE '%test%'",
            "       AND DATABASE() NOT LIKE '%sample%'",
            "       AND DATABASE() NOT LIKE '%dev%' THEN",
            "        SIGNAL SQLSTATE '45000'",
            "            SET MESSAGE_TEXT = 'FitTrack sample data refused: target database name must contain test, sample, or dev.';",
            "    END IF;",
            "END$$",
            "DELIMITER ;",
            "",
            "CALL fittrack_assert_test_database();",
            "DROP PROCEDURE fittrack_assert_test_database;",
            "",
            "-- ----------------------------------------------------------------------------",
            "-- Users",
            "-- ----------------------------------------------------------------------------",
            insert_block(
                "users",
                [
                    "user_id", "full_name", "email", "password_hash",
                    "date_of_birth", "gender", "height_cm",
                ],
                data["users"],
            ),
            "",
            "-- ----------------------------------------------------------------------------",
            "-- Exercise catalogue (requires migration_exercises.sql)",
            "-- ----------------------------------------------------------------------------",
            insert_block(
                "exercises",
                [
                    "exercise_id", "exercise_name", "muscle_group",
                    "exercise_type", "description",
                ],
                data["exercises"],
            ),
            "",
            "-- ----------------------------------------------------------------------------",
            "-- Workout sessions",
            "-- ----------------------------------------------------------------------------",
            insert_block(
                "workouts",
                [
                    "workout_id", "user_id", "exercise_name", "duration_minutes",
                    "calories_burned", "workout_date",
                ],
                data["workouts"],
            ),
            "",
            "-- ----------------------------------------------------------------------------",
            "-- Workout -> exercise junction (requires migration_exercises.sql)",
            "-- ----------------------------------------------------------------------------",
            insert_block(
                "workout_exercises",
                [
                    "workout_exercise_id", "workout_id", "exercise_id",
                    "exercise_order", "sets", "repetitions", "weight_kg",
                    "duration_minutes", "calories_burned",
                ],
                [
                    (
                        row[0], row[1], _exercise_id_for(row[2]), row[3],
                        row[4], row[5], row[6], row[7], row[8],
                    )
                    for row in data["workout_exercises"]
                ],
            ),
            "",
            "-- ----------------------------------------------------------------------------",
            "-- Nutrition logs",
            "-- ----------------------------------------------------------------------------",
            insert_block(
                "nutrition_logs",
                [
                    "nutrition_id", "user_id", "food_name", "meal_type",
                    "calories", "protein", "carbohydrates", "fat", "log_date",
                ],
                data["nutrition_logs"],
            ),
            "",
            "-- ----------------------------------------------------------------------------",
            "-- Health metrics (one record per user per day)",
            "-- ----------------------------------------------------------------------------",
            insert_block(
                "health_metrics",
                [
                    "metric_id", "user_id", "weight", "height", "steps",
                    "calories_burned", "recorded_date",
                ],
                data["health_metrics"],
            ),
            "",
            "-- ----------------------------------------------------------------------------",
            "-- Heart-rate samples (requires migration_heart_rate.sql)",
            "-- Zone names are resolved with a scalar subquery so the file works even",
            "-- if the seeded zone IDs are not 1..5 in the test database.",
            "-- ----------------------------------------------------------------------------",
        ]
    )

    sample_columns = (
        "sample_id", "user_id", "zone_id", "heart_rate_bpm", "recorded_at"
    )
    sample_rows = []
    for sample_id, user_id, zone_name, bpm, recorded_at in data["heart_rate_samples"]:
        zone_expression = (
            f"(SELECT zone_id FROM heart_rate_zones WHERE zone_name = {sql_value(zone_name)})"
            if zone_name else "NULL"
        )
        sample_rows.append(
            "(" + ", ".join(
                [
                    str(sample_id), str(user_id), zone_expression,
                    str(bpm), sql_value(recorded_at),
                ]
            ) + ")"
        )
    for start in range(0, len(sample_rows), 100):
        batch = sample_rows[start:start + 100]
        parts.append(
            f"INSERT INTO heart_rate_samples ({', '.join(sample_columns)}) VALUES\n"
            + ",\n".join(batch)
            + ";"
        )

    parts.extend(
        [
            "",
            "-- ----------------------------------------------------------------------------",
            "-- Verification summary (read-only)",
            "-- ----------------------------------------------------------------------------",
            "SELECT 'users' AS table_name, COUNT(*) AS rows_loaded FROM users",
            "UNION ALL SELECT 'exercises', COUNT(*) FROM exercises",
            "UNION ALL SELECT 'workouts', COUNT(*) FROM workouts",
            "UNION ALL SELECT 'workout_exercises', COUNT(*) FROM workout_exercises",
            "UNION ALL SELECT 'nutrition_logs', COUNT(*) FROM nutrition_logs",
            "UNION ALL SELECT 'health_metrics', COUNT(*) FROM health_metrics",
            "UNION ALL SELECT 'heart_rate_samples', COUNT(*) FROM heart_rate_samples;",
            "",
            "-- Expected total: %d records. Run database/verify_sample_data.sql next." % total,
            "",
        ]
    )
    return "\n".join(parts)


def _exercise_id_for(name):
    """Map an exercise name to its deterministic generated ID."""

    for index, item in enumerate(EXERCISES):
        if item[0] == name:
            return EXERCISE_IDS[index]
    raise KeyError(name)


def execute_into_test_database(data):
    """Insert the dataset into an explicitly configured test database.

    This path is never used by default and refuses anything that does not look
    like a test database.
    """

    import mysql.connector

    production_name = (os.getenv("DB_NAME") or "").strip()
    test_name = (os.getenv("TEST_DB_NAME") or "").strip()
    if not test_name:
        raise SystemExit(
            "TEST_DB_NAME is not set. Set the TEST_DB_* variables for a separate "
            "test database before using --execute."
        )
    lowered = test_name.lower()
    if not any(marker in lowered for marker in ("test", "sample", "dev")):
        raise SystemExit(
            f"Refusing to execute: TEST_DB_NAME={test_name!r} does not contain "
            "test, sample, or dev."
        )
    if production_name and test_name == production_name:
        raise SystemExit(
            "Refusing to execute: TEST_DB_NAME matches the production DB_NAME."
        )

    required = ["TEST_DB_HOST", "TEST_DB_USER", "TEST_DB_PASSWORD"]
    missing = [name for name in required if not (os.getenv(name) or "").strip()]
    if missing:
        raise SystemExit("Missing test database variables: " + ", ".join(missing))

    settings = {
        "host": os.environ["TEST_DB_HOST"],
        "port": int(os.getenv("TEST_DB_PORT") or 3306),
        "user": os.environ["TEST_DB_USER"],
        "password": os.environ["TEST_DB_PASSWORD"],
        "database": test_name,
        "charset": "utf8mb4",
        "use_unicode": True,
    }
    ca = (os.getenv("TEST_DB_SSL_CA") or "").strip()
    if ca:
        settings.update(
            {"ssl_ca": ca, "ssl_verify_cert": True, "ssl_verify_identity": True}
        )

    connection = mysql.connector.connect(**settings)
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT DATABASE()")
        active = cursor.fetchone()[0]
        if active != test_name:
            raise SystemExit("Connected database does not match TEST_DB_NAME.")

        cursor.execute("SELECT zone_id, zone_name FROM heart_rate_zones")
        zones = {name: zone_id for zone_id, name in cursor.fetchall()}

        statements = [
            (
                "INSERT INTO users (user_id, full_name, email, password_hash, "
                "date_of_birth, gender, height_cm) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                data["users"],
            ),
            (
                "INSERT INTO exercises (exercise_id, exercise_name, muscle_group, "
                "exercise_type, description) VALUES (%s, %s, %s, %s, %s)",
                data["exercises"],
            ),
            (
                "INSERT INTO workouts (workout_id, user_id, exercise_name, "
                "duration_minutes, calories_burned, workout_date) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                data["workouts"],
            ),
            (
                "INSERT INTO nutrition_logs (nutrition_id, user_id, food_name, "
                "meal_type, calories, protein, carbohydrates, fat, log_date) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                data["nutrition_logs"],
            ),
            (
                "INSERT INTO health_metrics (metric_id, user_id, weight, height, "
                "steps, calories_burned, recorded_date) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                data["health_metrics"],
            ),
        ]
        for statement, rows in statements:
            cursor.executemany(statement, rows)

        junction_rows = [
            (
                row[0], row[1], _exercise_id_for(row[2]), row[3], row[4],
                row[5], row[6], row[7], row[8],
            )
            for row in data["workout_exercises"]
        ]
        cursor.executemany(
            "INSERT INTO workout_exercises (workout_exercise_id, workout_id, "
            "exercise_id, exercise_order, sets, repetitions, weight_kg, "
            "duration_minutes, calories_burned) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
            junction_rows,
        )

        sample_rows = [
            (sample_id, user_id, zones.get(zone_name), bpm, recorded_at)
            for sample_id, user_id, zone_name, bpm, recorded_at
            in data["heart_rate_samples"]
        ]
        cursor.executemany(
            "INSERT INTO heart_rate_samples (sample_id, user_id, zone_id, "
            "heart_rate_bpm, recorded_at) VALUES (%s, %s, %s, %s, %s)",
            sample_rows,
        )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Insert into TEST_DB_* instead of only writing the SQL file.",
    )
    args = parser.parse_args(argv)

    data = build_dataset(seed=args.seed)
    counts = {key: len(value) for key, value in data.items() if isinstance(value, list)}
    total = sum(counts.values())

    if args.execute:
        execute_into_test_database(data)
        print(f"Inserted {total} records into the configured test database.")
        return 0

    sql = render_sql(data, seed=args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(sql, encoding="utf-8")
    print(f"Wrote {args.output} with {total} records.")
    for key, value in counts.items():
        print(f"  {key}: {value}")
    print("No database was modified. This file targets a separate test database.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

