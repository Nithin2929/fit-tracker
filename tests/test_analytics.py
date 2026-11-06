"""Offline tests for database-backed analytics transformations."""

import unittest
from datetime import date
from decimal import Decimal
from unittest import mock

from app import analytics


class ProteinStrengthAnalyticsTests(unittest.TestCase):
    def test_reports_weekly_protein_and_strength_trends(self):
        rows = [
            {
                "week_start": date(2026, 10, 26),
                "average_daily_protein_g": Decimal("92.5"),
                "protein_logged_days": 4,
                "strength_sessions": 2,
                "strength_volume_kg": Decimal("4200.0"),
                "max_load_kg": Decimal("80.00"),
            },
            {
                "week_start": date(2026, 11, 2),
                "average_daily_protein_g": None,
                "protein_logged_days": 0,
                "strength_sessions": 0,
                "strength_volume_kg": Decimal("0.0"),
                "max_load_kg": None,
            },
        ]
        with (
            mock.patch("app.analytics.has_exercises", return_value=True),
            mock.patch("app.analytics.fetch_all", return_value=rows) as fetch_all,
        ):
            result = analytics.protein_strength_analytics(17, days=30)

        self.assertTrue(result["available"])
        self.assertEqual(result["days"], 30)
        self.assertEqual(result["weeks"][0]["week_start"], "2026-10-26")
        self.assertEqual(result["weeks"][0]["average_daily_protein_g"], 92.5)
        self.assertEqual(result["weeks"][0]["protein_logged_days"], 4)
        self.assertEqual(result["weeks"][0]["strength_sessions"], 2)
        self.assertEqual(result["weeks"][0]["strength_volume_kg"], 4200.0)
        self.assertEqual(result["weeks"][0]["max_load_kg"], 80.0)
        self.assertIsNone(result["weeks"][1]["average_daily_protein_g"])
        self.assertIsNone(result["weeks"][1]["max_load_kg"])

        query, params = fetch_all.call_args.args
        self.assertIn("JOIN workout_exercises", query)
        self.assertIn("JOIN exercises", query)
        self.assertIn("UNION", query)
        self.assertIn("WHERE workouts.user_id = %s", query)
        self.assertEqual(params[0], 17)
        self.assertEqual(params[3], 17)

    def test_returns_unavailable_without_exercises_migration(self):
        with (
            mock.patch("app.analytics.has_exercises", return_value=False),
            mock.patch("app.analytics.fetch_all") as fetch_all,
        ):
            result = analytics.protein_strength_analytics(17)

        self.assertFalse(result["available"])
        self.assertEqual(result["weeks"], [])
        fetch_all.assert_not_called()


if __name__ == "__main__":
    unittest.main()
