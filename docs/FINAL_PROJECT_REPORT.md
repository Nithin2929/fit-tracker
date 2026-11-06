# FitTrack Final Project Report

**Project:** Fitness and Wellness Tracking Database System  
**Report date:** 3 November 2026  
**Implementation:** Python, Flask, MySQL, HTML, CSS, and JavaScript

## Executive summary

FitTrack is a web application for recording and reviewing personal workouts,
food intake, and daily health metrics. Flask serves the interface and
application logic; the configured Aiven Cloud MySQL database stores the
accounts and fitness records. The project includes account authentication,
per-user record management, summary pages, SQL-backed reports, and analytics
endpoints.

The application and its offline checks are implemented. Live Aiven
integration and the rollback-only load benchmark require an explicitly
configured development or staging database; their results are not represented
as completed in this report.

## 1. Goals and scope

The system brings fitness and wellness records into one relational application
and demonstrates entity relationships, normalization, constraints, SQL
aggregation, transactions, and progress reporting. Its core modules are:

- User accounts and profiles.
- Workout sessions.
- Nutrition logs with calories and macronutrients.
- Daily health metrics, including weight, height, steps, and recorded calories.
- Dashboard and date-filtered progress reports.

Optional schema migrations define multi-exercise workouts, timestamped
nutrition records, and time-based heart-rate readings. They are separate from
the core schema and must be applied explicitly before those database features
are available.

## 2. Architecture and technology

The browser sends requests to a Flask application. Flask validates input,
enforces authentication and per-user access, runs parameterized SQL through
MySQL Connector/Python, and renders HTML or returns JSON. MySQL stores the
application data. The application requires an Aiven Cloud MySQL connection
using CA-verified TLS; it has no local database fallback.

The user interface uses Jinja templates, HTML, CSS, and vanilla JavaScript.
The backend uses Python and Flask. Environment variables, loaded from a
developer-managed `.env` file, provide connection configuration. Waitress is
the documented production WSGI server.

## 3. Relational data model

The core schema has four tables:

- `users`: account and profile fields; email is unique and the password is
  stored as a one-way hash.
- `workouts`: a user's exercise label, duration, calories, and date.
- `nutrition_logs`: a user's food, meal type, calories, macronutrients, and log
  date.
- `health_metrics`: a user's daily weight, height, steps, and recorded
  calories.

Each fitness table references `users`. The health table enforces one record per
user per date. The optional exercise migration adds an exercise catalogue and
a workout-to-exercise junction table. Database design, data dictionary,
normalization, logic-flow, and physical-schema documents are maintained under
`docs/`.

## 4. Validation and integrity

The schema defines primary keys, foreign keys, unique constraints, indexes,
and range checks for important user-entered measurements. Personal reads and
mutations are scoped to the authenticated user's identifier. Queries use
parameter placeholders.

Write helpers commit successful changes and roll back failed work. An explicit
transaction helper supports multi-row operations. The database connection
verifies both the certificate chain and server hostname. The application
rejects local database hosts rather than silently switching storage.

## 5. Application functions and analytics

The web application includes registration, login, logout, profiles, dashboard
summaries, and create/read/update/delete flows for workouts, nutrition, and
health metrics. BMI is derived from weight and height rather than stored as
duplicated data.

The reports use SQL aggregation for daily, weekly, and monthly summaries.
Analytics include workout totals and frequency, food and macro summaries,
weight/BMI/steps series, recorded calorie balance, optional heart-rate
summaries, and optional strength performance. The
`/api/analytics/protein-strength` endpoint compares weekly recorded protein
with strength-training volume. This is a descriptive comparison, not evidence
of causation or medical advice.

The calorie-balance calculation is explicitly a recorded-data comparison. It
does not estimate unlogged activity or personal energy expenditure.

## 6. Security and privacy

- Passwords are stored as hashes, not plaintext.
- Private pages and analytics APIs require a logged-in session.
- CSRF protection applies to form submissions.
- SQL values are parameterized.
- User-specific queries use the authenticated user's ID.
- Session cookies and response security headers have secure defaults.
- Raw database error details are not returned to the browser.
- Database credentials and certificates are kept outside source control.

## 7. Verification status

The offline test suite checks configuration validation, database TLS settings,
page rendering, route protection, CSRF rejection, helper functions, and
analytics transformations. The latest run completed 35 tests: 33 passed, 2
Aiven-only tests were skipped, and none failed. A separate read-only
connectivity check succeeded over verified TLS against MySQL 8.4.11. Run the
offline suite from the project root:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

The opt-in Aiven tests exercise schema queries and user isolation using
transactions that are rolled back. Both live tests passed against the
configured development/staging Aiven database. The load test inserted 600
synthetic workouts and 600 synthetic nutrition records inside a transaction,
then ran the 90-day analytics summary three times. The slowest run took
**2.709 seconds**, below the configured **5-second** per-run target. The
transaction was rolled back. This is a result from one database environment,
not a general capacity guarantee. To repeat the test, set
`RUN_LIVE_DB_TESTS=1`; adjust the threshold with
`FITTRACK_STRESS_MAX_QUERY_SECONDS`.

The public home page was inspected in a desktop browser and at a 390-pixel
mobile viewport. The responsive navigation opened correctly, and the mobile
document width did not exceed the viewport. The shared browser currently has
no signed-in session, so private dashboard and record-management pages were
not visually verified.

## 8. Setup and operation

1. Install the packages in `requirements.txt` in a virtual environment.
2. Copy `.env.example` to `.env` and set the Aiven connection values.
3. Download the Aiven CA certificate to the configured certificate path.
4. Review and apply `database/aiven_init.sql` to the intended database.
5. Apply optional migrations only when those features have been reviewed and
   approved.
6. Run `python check_db.py` to verify the configured connection.
7. Run `python run.py` for local development, or use the documented Waitress
   command for deployment.
8. Run offline tests before enabling the opt-in live tests.

Refer to `README.md` for detailed environment setup, database initialization,
and operational instructions.

## 9. Limitations and next steps

- Visually inspect authenticated pages at desktop and mobile sizes using an
  authorized test account.
- Apply optional migrations only after reviewing their compatibility with the
  target schema.
- Review deployment secrets, HTTPS, backups, and monitoring before production
  use.
- Treat fitness and nutrition analytics as informational records, not
  professional medical guidance.

## Conclusion

FitTrack provides a functional full-stack foundation with a relational MySQL
schema, authenticated record management, integrity controls, reporting,
automated offline tests, and a passing rollback-only load check. Remaining
completion work is limited to authenticated UI review and deployment-specific
readiness checks.
