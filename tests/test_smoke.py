"""Offline tests for FitTrack.

These tests never contact Aiven MySQL and never need real credentials. They
verify the parts that can be checked without a live database:

- The public pages and templates render.
- Anonymous users are redirected away from protected pages.
- CSRF protection rejects a POST without a token.
- Configuration validation refuses missing values, placeholders and local hosts.
- The database layer always enables TLS certificate and hostname verification.
- The source tree contains no SQLite/local-database fallback.

The live Aiven connection is verified separately with ``python check_db.py``.
"""

import os
import re
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest import mock

from flask import Flask

from app import create_app
from app.db import (
    DatabaseConfigurationError,
    _connection_settings,
    verify_connection,
)
from app.utils import (
    bmi_category,
    calculate_bmi,
    display_date,
    display_number,
    parse_choice,
    parse_date,
    parse_decimal,
    parse_int,
    safe_next_url,
)
from config import (
    Config,
    ConfigurationError,
    _looks_like_placeholder,
    is_local_host,
    validate_config,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _write_temp_ca():
    """Create a temporary file so DB_SSL_CA passes the existence check."""

    handle = tempfile.NamedTemporaryFile(
        mode="w", suffix=".pem", delete=False, encoding="utf-8"
    )
    handle.write("-----BEGIN CERTIFICATE-----\nTEST ONLY\n-----END CERTIFICATE-----\n")
    handle.close()
    return handle.name


def _valid_config(ca_path):
    """Return a complete, non-placeholder configuration dictionary."""

    return {
        "SECRET_KEY": "t" * 64,
        "DB_HOST": "fitness-project.aivencloud.com",
        "DB_PORT": 23456,
        "DB_USER": "avnadmin",
        "DB_PASSWORD": "a-real-looking-test-secret",
        "DB_NAME": "fitness_wellness_db",
        "DB_SSL_CA": ca_path,
        "DB_CONNECT_TIMEOUT": 10,
    }


class ConfigValidationTests(unittest.TestCase):
    def setUp(self):
        self.ca_path = _write_temp_ca()
        self.addCleanup(os.unlink, self.ca_path)

    def _make_app(self, **overrides):
        app = Flask(__name__)
        app.config.update(_valid_config(self.ca_path))
        app.config.update(overrides)
        return app

    def test_valid_aiven_configuration_passes(self):
        app = self._make_app()
        self.assertTrue(validate_config(app))

    def test_missing_values_are_rejected(self):
        app = self._make_app(DB_HOST=None, DB_PASSWORD=None)
        with self.assertRaises(ConfigurationError) as caught:
            validate_config(app)
        message = str(caught.exception)
        self.assertIn("DB_HOST is missing", message)
        self.assertIn("DB_PASSWORD is missing", message)

    def test_localhost_is_rejected(self):
        for host in ("localhost", "127.0.0.1", "127.0.1.1", "::1", "0.0.0.0"):
            with self.subTest(host=host):
                app = self._make_app(DB_HOST=host)
                with self.assertRaises(ConfigurationError):
                    validate_config(app)

    def test_placeholder_values_are_rejected(self):
        app = self._make_app(
            DB_HOST="your-aiven-host",
            DB_USER="your-aiven-username",
            DB_PASSWORD="replace-with-a-long-random-string",
        )
        with self.assertRaises(ConfigurationError) as caught:
            validate_config(app)
        message = str(caught.exception)
        self.assertIn("placeholder", message)

    def test_short_secret_key_is_rejected(self):
        app = self._make_app(SECRET_KEY="too-short")
        with self.assertRaises(ConfigurationError):
            validate_config(app)

    def test_missing_ca_file_is_rejected(self):
        app = self._make_app(DB_SSL_CA=str(PROJECT_ROOT / "certs" / "does-not-exist.pem"))
        with self.assertRaises(ConfigurationError) as caught:
            validate_config(app)
        self.assertIn("DB_SSL_CA file was not found", str(caught.exception))

    def test_port_must_be_in_range(self):
        app = self._make_app(DB_PORT=70000)
        with self.assertRaises(ConfigurationError):
            validate_config(app)

    def test_is_local_host_helper(self):
        self.assertTrue(is_local_host("localhost"))
        self.assertTrue(is_local_host("127.0.0.1"))
        self.assertFalse(is_local_host("fitness-project.aivencloud.com"))
        self.assertFalse(is_local_host(None))


class DatabaseSettingsTests(unittest.TestCase):
    def setUp(self):
        self.ca_path = _write_temp_ca()
        self.addCleanup(os.unlink, self.ca_path)

    def test_tls_verification_is_always_enabled(self):
        app = Flask(__name__)
        app.config.update(_valid_config(self.ca_path))

        with app.app_context():
            settings = _connection_settings()

        self.assertTrue(settings["ssl_verify_cert"])
        self.assertTrue(settings["ssl_verify_identity"])
        self.assertFalse(settings["ssl_disabled"])
        self.assertEqual(settings["ssl_ca"], self.ca_path)
        self.assertEqual(settings["charset"], "utf8mb4")

    def test_database_layer_refuses_localhost(self):
        app = Flask(__name__)
        app.config.update(_valid_config(self.ca_path))
        app.config["DB_HOST"] = "localhost"

        with app.app_context():
            with self.assertRaises(DatabaseConfigurationError):
                _connection_settings()

    def test_verify_connection_reads_the_right_columns(self):
        class FakeCursor:
            def __init__(self):
                self.rows = [
                    {"ok": 1},
                    {
                        "active_database": "fitness_wellness_db",
                        "server_version": "8.0.36",
                    },
                    {"Variable_name": "Ssl_cipher", "Value": "TLS_AES_256_GCM_SHA384"},
                ]
                self.index = 0

            def execute(self, sql, params=None):
                return None

            def fetchone(self):
                row = self.rows[self.index]
                self.index += 1
                return row

        @contextmanager
        def fake_cursor(dictionary=True, commit=False):
            yield FakeCursor()

        app = Flask(__name__)
        app.config.update(_valid_config(self.ca_path))

        with app.app_context(), mock.patch("app.db.get_cursor", fake_cursor):
            details = verify_connection()

        self.assertEqual(details["database"], "fitness_wellness_db")
        self.assertEqual(details["server_version"], "8.0.36")
        self.assertEqual(details["ssl_cipher"], "TLS_AES_256_GCM_SHA384")


class PageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config.update(TESTING=True)
        # Force the database check to fail before any network connection is
        # attempted, so this suite stays completely offline even when the local
        # .env happens to contain working Aiven credentials.
        cls.app.config["DB_SSL_CA"] = str(
            PROJECT_ROOT / "certs" / "offline-tests-no-ca.pem"
        )
        cls.client = cls.app.test_client()

    def test_home_page_renders_without_a_database(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("FitTrack", body)
        self.assertIn("Preview", body)

    def test_login_page_renders_without_a_database(self):
        response = self.client.get("/login")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Log in to FitTrack", response.get_data(as_text=True))

    def test_register_page_renders_without_a_database(self):
        response = self.client.get("/register")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Create your FitTrack account", response.get_data(as_text=True))

    def test_unknown_page_returns_friendly_404(self):
        response = self.client.get("/this-page-does-not-exist")
        self.assertEqual(response.status_code, 404)
        self.assertIn("Page not found", response.get_data(as_text=True))

    def test_protected_pages_redirect_anonymous_users(self):
        for path in ("/dashboard", "/workouts/", "/nutrition/", "/health/", "/reports/", "/profile"):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 302)
                self.assertIn("/login", response.headers["Location"])

    def test_protected_analytics_api_returns_json_401(self):
        response = self.client.get("/api/analytics/protein-strength")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.get_json(), {"error": "authentication_required"})

    def test_login_post_without_csrf_is_rejected(self):
        response = self.client.post(
            "/login", data={"email": "a@example.com", "password": "password123"}
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("form expired", response.get_data(as_text=True))

    def test_logout_requires_csrf(self):
        response = self.client.post("/logout")
        self.assertEqual(response.status_code, 400)

    def test_health_check_route_is_not_public_data(self):
        # /db-check needs a live database; without valid Aiven settings it must
        # fail safely rather than expose credentials.
        response = self.client.get("/db-check")
        self.assertIn(response.status_code, (500, 503))
        body = response.get_data(as_text=True)
        # Variable *names* are fine in a help message, but real configured
        # secret *values* must never be reflected back to the browser.
        for value in (Config.DB_PASSWORD, Config.DB_USER, Config.DB_HOST):
            if value and not _looks_like_placeholder(str(value)):
                self.assertFalse(
                    str(value) in body,
                    "A configured credential value leaked into the response.",
                )

    def test_db_check_returns_safe_json(self):
        fake_details = {
            "database": "fitness_wellness_db",
            "server_version": "8.0.36",
            "ssl_cipher": "TLS_AES_256_GCM_SHA384",
        }
        with mock.patch("app.routes.main.verify_connection", return_value=fake_details):
            response = self.client.get("/db-check")

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["database"], "fitness_wellness_db")
        self.assertTrue(payload["ssl_verified"])
        self.assertNotIn("host", payload)

    def test_all_templates_compile(self):
        with self.app.app_context():
            for name in self.app.jinja_env.list_templates():
                with self.subTest(template=name):
                    self.app.jinja_env.get_template(name)

    def test_security_headers_are_present(self):
        response = self.client.get("/")
        self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(response.headers["X-Frame-Options"], "DENY")
        self.assertIn("Referrer-Policy", response.headers)


class UtilityTests(unittest.TestCase):
    def test_bmi_calculation_and_categories(self):
        self.assertEqual(calculate_bmi(70, 175), 22.9)
        self.assertIsNone(calculate_bmi(0, 175))
        self.assertIsNone(calculate_bmi(None, 175))
        self.assertEqual(bmi_category(17), "Underweight")
        self.assertEqual(bmi_category(22), "Normal")
        self.assertEqual(bmi_category(27), "Overweight")
        self.assertEqual(bmi_category(31), "Obese")
        self.assertEqual(bmi_category(None), "Not available")

    def test_parse_helpers(self):
        self.assertEqual(parse_int("45", "Duration", 1, 1440), 45)
        self.assertIsNone(parse_int("", "Optional", required=False))
        self.assertEqual(str(parse_decimal("12.5", "Protein", 0, 1000)), "12.5")
        self.assertEqual(parse_choice("Lunch", "Meal", ("Lunch", "Dinner")), "Lunch")
        self.assertEqual(str(parse_date("2026-01-02", "Date")), "2026-01-02")

        with self.assertRaises(ValueError):
            parse_int("0", "Duration", 1, 1440)
        with self.assertRaises(ValueError):
            parse_choice("Brunch", "Meal", ("Lunch", "Dinner"))
        with self.assertRaises(ValueError):
            parse_date("02/01/2026", "Date")

    def test_safe_next_url_blocks_external_redirects(self):
        self.assertEqual(safe_next_url("/reports/", "/dashboard"), "/reports/")
        for unsafe in (
            "https://evil.example",
            "http://evil.example/path",
            "//evil.example",
            "/\\evil.example",
            "\\\\evil.example",
            "/path\r\nLocation: https://evil.example",
            "javascript:alert(1)",
            None,
            "",
        ):
            with self.subTest(target=unsafe):
                self.assertEqual(safe_next_url(unsafe, "/dashboard"), "/dashboard")

    def test_display_helpers(self):
        self.assertEqual(display_date(None), "—")
        self.assertEqual(display_date("2026-01-02"), "2026-01-02")
        self.assertEqual(display_number(None), "—")
        self.assertEqual(display_number(12.0), "12")
        self.assertEqual(display_number(12.34), "12.3")


class NoLocalDatabaseTests(unittest.TestCase):
    def test_no_sqlite_imports_in_application_code(self):
        roots = [PROJECT_ROOT / "app", PROJECT_ROOT / "config.py", PROJECT_ROOT / "run.py"]
        pattern = re.compile(r"\bimport\s+sqlite3\b|\bsqlite3\.connect\b")
        offenders = []
        for root in roots:
            files = root.rglob("*.py") if root.is_dir() else [root]
            for path in files:
                text = path.read_text(encoding="utf-8")
                if pattern.search(text):
                    offenders.append(str(path))
        self.assertEqual(offenders, [], f"SQLite usage found in: {offenders}")

    def test_no_hardcoded_local_database_host_in_code(self):
        # Look at actual string literals, not comments. Localhost may appear in a
        # comment explaining that it is forbidden.
        pattern = re.compile(r"[\"'](?:localhost|127\.0\.0\.1)[\"']")
        offenders = []
        for path in (PROJECT_ROOT / "app").rglob("*.py"):
            if pattern.search(path.read_text(encoding="utf-8")):
                offenders.append(str(path))
        self.assertEqual(offenders, [], f"Hardcoded local DB host found in: {offenders}")

    def test_env_example_contains_only_placeholders(self):
        text = (PROJECT_ROOT / ".env.example").read_text(encoding="utf-8")
        self.assertIn("your-aiven-host", text)
        self.assertNotRegex(text, r"DB_PASSWORD=\s*(?!your-aiven-password)")

    def test_env_file_is_gitignored(self):
        ignore = (PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertRegex(ignore, r"(?m)^\.env$")
        self.assertIn("certs/*.pem", ignore)


if __name__ == "__main__":
    unittest.main()
