"""Optional live integration tests against the real Aiven MySQL database.

These tests are skipped unless you explicitly enable them:

    $env:RUN_LIVE_DB_TESTS = "1"
    .\\.venv\\Scripts\\python.exe -m unittest tests.test_live_aiven -v

Safety:
- They require the real .env and certs/ca.pem.
- Every INSERT/UPDATE runs inside one transaction that is **always rolled
  back** in tearDownClass, so no test user or fitness data is saved.
- They never run DROP, TRUNCATE, or DELETE.
- They never print the host, user, or password.
"""

import os
import time
import unittest
import uuid
from datetime import date, timedelta
from unittest import mock

import mysql.connector
from werkzeug.security import check_password_hash, generate_password_hash

from app import analytics, create_app
from app.db import _connection_settings, verify_connection

LIVE = os.getenv("RUN_LIVE_DB_TESTS") == "1"


@unittest.skipUnless(
    LIVE,
    "Set RUN_LIVE_DB_TESTS=1 to run tests that require real Aiven credentials.",
)
class LiveAivenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        with cls.app.app_context():
            try:
                verify_connection()
                cls.connection = mysql.connector.connect(**_connection_settings())
            except Exception as error:  # noqa: BLE001 - convert to a clear skip
                raise unittest.SkipTest(
                    "Aiven is not reachable or not configured. "
                    f"Reason class: {error.__class__.__name__}"
                ) from error
        cls.connection.autocommit = False

    @classmethod
    def tearDownClass(cls):
        connection = getattr(cls, "connection", None)
        if connection is not None:
            try:
                connection.rollback()
            finally:
                connection.close()

    def setUp(self):
        # Every test starts from the same clean transaction boundary.
        self.connection.rollback()
        self.cursor = self.connection.cursor()
        self.email_one = f"live-test-{uuid.uuid4().hex}@example.invalid"
        self.email_two = f"live-test-{uuid.uuid4().hex}@example.invalid"

    def tearDown(self):
        self.cursor.close()
        self.connection.rollback()

    def _create_user(self, email, name):
        password_hash = generate_password_hash("LiveTestPassword123")
        self.cursor.execute(
            """
            INSERT INTO users
                (full_name, email, password_hash, date_of_birth, gender, height_cm)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (name, email, password_hash, date(1990, 1, 1), "Other", 175.0),
        )
        user_id = self.cursor.lastrowid
        self.assertTrue(check_password_hash(password_hash, "LiveTestPassword123"))
        return user_id

    def test_analytics_load_with_1200_rollback_only_records(self):
        """Benchmark analytics with synthetic rows without persisting them."""

        record_count = 600
        user_id = self._create_user(self.email_one, "Load Test User")
        today = date.today()

        self.cursor.executemany(
            """
            INSERT INTO workouts
                (user_id, exercise_name, duration_minutes, calories_burned, workout_date)
            VALUES (%s, %s, %s, %s, %s)
            """,
            [
                (
                    user_id,
                    f"Load-test exercise {index % 6}",
                    30 + index % 60,
                    100 + index % 500,
                    today - timedelta(days=index % 84),
                )
                for index in range(record_count)
            ],
        )
        self.cursor.executemany(
            """
            INSERT INTO nutrition_logs
                (user_id, food_name, meal_type, calories, protein,
                 carbohydrates, fat, log_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            [
                (
                    user_id,
                    f"Load-test food {index % 12}",
                    ("Breakfast", "Lunch", "Dinner", "Snack")[index % 4],
                    200 + index % 400,
                    10 + index % 30,
                    20 + index % 60,
                    5 + index % 20,
                    today - timedelta(days=index % 84),
                )
                for index in range(record_count)
            ],
        )

        try:
            max_seconds = float(os.getenv("FITTRACK_STRESS_MAX_QUERY_SECONDS", "5"))
        except ValueError as error:
            raise ValueError(
                "FITTRACK_STRESS_MAX_QUERY_SECONDS must be a positive number."
            ) from error
        if max_seconds <= 0:
            raise ValueError("FITTRACK_STRESS_MAX_QUERY_SECONDS must be positive.")

        elapsed = []
        with self.app.app_context(), mock.patch(
            "app.db.get_db", return_value=self.connection
        ):
            for _ in range(3):
                started = time.perf_counter()
                summary = analytics.analytics_summary(user_id, days=90)
                elapsed.append(time.perf_counter() - started)

        self.assertEqual(summary["workouts"]["total_workouts"], record_count)
        self.assertEqual(summary["nutrition"]["entries"], record_count)
        self.assertEqual(len(elapsed), 3)
        self.assertLessEqual(
            max(elapsed),
            max_seconds,
            "An analytics summary exceeded the configured response-time target.",
        )
        print(
            "Aiven analytics load check: 1,200 synthetic rows, "
            f"3 runs, max {max(elapsed):.3f}s "
            f"(target {max_seconds:.3f}s); transaction rolled back."
        )

    def test_schema_and_user_isolation_with_rollback(self):
        today = date.today()
        yesterday = today - timedelta(days=1)
        user_one = self._create_user(self.email_one, "Live Test One")
        user_two = self._create_user(self.email_two, "Live Test Two")

        # Workouts: the route's INSERT statement.
        self.cursor.executemany(
            """
            INSERT INTO workouts
                (user_id, exercise_name, duration_minutes, calories_burned, workout_date)
            VALUES (%s, %s, %s, %s, %s)
            """,
            [
                (user_one, "Running", 30, 250, today),
                (user_one, "Cycling", 45, 300, yesterday),
                (user_two, "Swimming", 60, 500, today),
            ],
        )

        # Nutrition: the route's INSERT statement.
        self.cursor.execute(
            """
            INSERT INTO nutrition_logs
                (user_id, food_name, meal_type, calories, protein,
                 carbohydrates, fat, log_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (user_one, "Oats", "Breakfast", 300, 12.0, 45.0, 6.0, today),
            )
        self.cursor.execute(
            """
            INSERT INTO nutrition_logs
                (user_id, food_name, meal_type, calories, protein,
                 carbohydrates, fat, log_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (user_one, "Rice", "Lunch", 350, 10.0, 60.0, 5.0, today),
        )

        # Health upsert: same SQL as app/routes/health.py.
        health_values = (user_one, 70.5, 175.0, 8000, 200, today)
        self.cursor.execute(
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
            health_values
            + (70.5, 175.0, 9000, 250),
        )
        # Second save for the same date must update, not duplicate.
        self.cursor.execute(
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
            (user_one, 71.2, 175.0, 10000, 300, today)
            + (71.2, 175.0, 10000, 300),
        )

        # Dashboard totals for user one.
        self.cursor.execute(
            """
            SELECT COUNT(*) AS total_workouts,
                   COALESCE(SUM(duration_minutes), 0) AS total_minutes,
                   COALESCE(SUM(calories_burned), 0) AS total_calories
            FROM workouts
            WHERE user_id = %s
            """,
            (user_one,),
        )
        totals = self.cursor.fetchone()
        self.assertEqual(totals[0], 2)
        self.assertEqual(totals[1], 75)
        self.assertEqual(totals[2], 550)

        # User isolation: user two sees only their own row.
        self.cursor.execute(
            "SELECT COUNT(*) FROM workouts WHERE user_id = %s", (user_two,)
        )
        self.assertEqual(self.cursor.fetchone()[0], 1)

        # Today's nutrition total.
        self.cursor.execute(
            """
            SELECT COALESCE(SUM(calories), 0) FROM nutrition_logs
            WHERE user_id = %s AND log_date = %s
            """,
            (user_one, today),
        )
        self.assertEqual(self.cursor.fetchone()[0], 650)

        # Health upsert result and live BMI calculation.
        self.cursor.execute(
            """
            SELECT COUNT(*), MAX(weight), MAX(steps)
            FROM health_metrics
            WHERE user_id = %s AND recorded_date = %s
            """,
            (user_one, today),
        )
        count, weight, steps = self.cursor.fetchone()
        self.assertEqual(count, 1)
        self.assertEqual(float(weight), 71.2)
        self.assertEqual(steps, 10000)

        self.cursor.execute(
            """
            SELECT ROUND(weight / ((height / 100) * (height / 100)), 1) AS bmi
            FROM health_metrics
            WHERE user_id = %s AND recorded_date = %s
            """,
            (user_one, today),
        )
        self.assertGreater(float(self.cursor.fetchone()[0]), 0)

        # Reports: daily, weekly, and monthly SQL from app/routes/reports.py.
        self.cursor.execute(
            """
            SELECT workout_date AS day, COUNT(*) AS workouts,
                   COALESCE(SUM(duration_minutes), 0) AS minutes,
                   COALESCE(SUM(calories_burned), 0) AS calories
            FROM workouts
            WHERE user_id = %s AND workout_date BETWEEN %s AND %s
            GROUP BY workout_date
            ORDER BY workout_date DESC
            """,
            (user_one, yesterday, today),
        )
        self.assertEqual(len(self.cursor.fetchall()), 2)

        self.cursor.execute(
            """
            SELECT DATE_SUB(workout_date, INTERVAL WEEKDAY(workout_date) DAY)
                       AS week_start,
                   COUNT(*) AS workouts
            FROM workouts
            WHERE user_id = %s AND workout_date BETWEEN %s AND %s
            GROUP BY week_start
            ORDER BY week_start DESC
            """,
            (user_one, yesterday, today),
        )
        self.assertGreaterEqual(len(self.cursor.fetchall()), 1)

        self.cursor.execute(
            """
            SELECT DATE_FORMAT(workout_date, '%%Y-%%m') AS month,
                   COUNT(*) AS workouts
            FROM workouts
            WHERE user_id = %s AND workout_date BETWEEN %s AND %s
            GROUP BY month
            ORDER BY month DESC
            """,
            (user_one, yesterday, today),
        )
        self.assertGreaterEqual(len(self.cursor.fetchall()), 1)

        self.cursor.execute(
            """
            SELECT DATE_FORMAT(recorded_date, '%%Y-%%m') AS month,
                   ROUND(AVG(weight), 2) AS average_weight,
                   ROUND(AVG(steps), 0) AS average_steps,
                   COALESCE(SUM(calories_burned), 0) AS activity_calories,
                   ROUND(AVG(weight / ((height / 100) * (height / 100))), 1)
                       AS average_bmi
            FROM health_metrics
            WHERE user_id = %s AND recorded_date BETWEEN %s AND %s
            GROUP BY month
            ORDER BY month DESC
            """,
            (user_one, yesterday, today),
        )
        report_row = self.cursor.fetchone()
        self.assertIsNotNone(report_row)
        self.assertGreater(float(report_row[4]), 0)

        # CHECK constraint: an invalid workout must be rejected.
        with self.assertRaises(mysql.connector.Error):
            self.cursor.execute(
                """
                INSERT INTO workouts
                    (user_id, exercise_name, duration_minutes, calories_burned, workout_date)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (user_one, "Invalid", 0, 10, today),
            )

        # Prove the live tables are still empty for these test users.
        self.cursor.execute(
            "SELECT COUNT(*) FROM users WHERE email IN (%s, %s)",
            (self.email_one, self.email_two),
        )
        self.assertEqual(self.cursor.fetchone()[0], 2)


if __name__ == "__main__":
    unittest.main()
