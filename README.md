# FitTrack — Fitness & Wellness Tracking Database System

A Flask + **Aiven Cloud MySQL** web application for tracking user profiles,
workouts, nutrition, weight, BMI, steps, calories, and fitness reports.

> **Database rule:** FitTrack uses only the online Aiven MySQL database. There is
> no SQLite file, no local MySQL connection, no JSON/CSV database, and no
> automatic local fallback. If Aiven is unavailable, the app shows a clear
> database error instead of switching databases.

---

## 1. Architecture

```text
User Browser
    |
HTML / CSS / JavaScript
    |
Python Flask Backend
    |
Aiven MySQL Connection (TLS + CA verification)
    |
Aiven Cloud MySQL Database
    |
Database Response
    |
Flask Backend
    |
User Interface
```

---

## 2. Tech stack

| Layer | Technology |
|---|---|
| Frontend | HTML5, CSS3, vanilla JavaScript |
| Backend | Python 3.12+, Flask |
| Database | Aiven Cloud MySQL 8.x, InnoDB, `utf8mb4` |
| DB driver | `mysql-connector-python` |
| Configuration | `python-dotenv` + environment variables |
| Passwords | Werkzeug secure password hashing (scrypt) |
| Production server | Waitress |

---

## 3. What is implemented

| Module | Routes | Status |
|---|---|---|
| Public Home | `/` | Working |
| Database check | `/db-check` | Working |
| Registration / login / logout | `/register`, `/login`, `/logout` | Working |
| Profile | `/profile` | Working |
| Dashboard | `/dashboard` | Live Aiven MySQL data |
| Workouts | `/workouts`, `/workouts/new`, edit/delete | Full CRUD |
| Nutrition | `/nutrition`, `/nutrition/new`, edit/delete | Full CRUD |
| Health metrics + BMI | `/health`, `/health/new`, edit/delete | Full CRUD |
| Reports | `/reports` | Daily, weekly, monthly, calorie, weight, BMI |

Every personal query filters by the logged-in user's `user_id`. Users cannot
read, edit, or delete another user's records by changing a URL.

---

## 4. Project structure

```text
D:\ictproject\fitnesstrack\
├── app\
│   ├── __init__.py          # Flask app factory, error handlers, user loading
│   ├── db.py                # Aiven MySQL connection + safe query helpers
│   ├── utils.py             # login guard, CSRF, validation, BMI helpers
│   ├── routes\
│   │   ├── main.py          # Home + /db-check
│   │   ├── auth.py          # register, login, logout, profile
│   │   ├── dashboard.py     # live summary cards
│   │   ├── workouts.py      # workout CRUD
│   │   ├── nutrition.py     # nutrition CRUD
│   │   ├── health.py        # health metrics + BMI
│   │   └── reports.py       # SQL reports
│   ├── templates\           # existing design + new app pages
│   └── static\              # existing CSS/JS + app-page styles
├── database\
│   ├── aiven_init.sql       # safe Aiven schema initialization
│   ├── step3_tables.sql     # add child tables to an existing Aiven database
│   ├── step3_sample_data.sql# OPTIONAL manual demo data
│   ├── step3_verify.sql     # read-only verification queries
│   └── app_user.sql         # Aiven user guidance
├── certs\                   # put Aiven ca.pem here (gitignored)
├── tests\
│   ├── test_smoke.py        # offline tests (no database needed)
│   └── test_live_aiven.py   # optional live test; writes only inside a rollback
├── config.py                # strict environment-variable configuration
├── check_db.py              # standalone Aiven connectivity test
├── run.py                   # startup validation + dev server
├── requirements.txt
├── .env.example             # safe placeholders only
└── README.md
```

---

## 5. Aiven MySQL setup (console)

1. Sign in at <https://console.aiven.io/>.
2. Create or open a **MySQL** service and wait until it is running.
3. Open the service's **Overview** / **Connection information** page.
4. Copy these values:
   - **Host**
   - **Port**
   - **User**
   - **Password**
   - **Database name** (Aiven may provide `defaultdb`)
5. Create or select the database named `fitness_wellness_db`. You can do this
   with your Aiven admin user in the Aiven Query editor:

   ```sql
   CREATE DATABASE IF NOT EXISTS fitness_wellness_db
       CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```

   This project uses `fitness_wellness_db` as its database name. The schema
   scripts and `DB_NAME` in `.env` must all point at the same database.
6. Create a dedicated application user (Aiven console → **Users** → **Add
   user**) with read/write access to that database. Use that user in `.env`, not
   the administrator account.
7. Download the **CA certificate** (`ca.pem`) and save it as:

   ```text
   D:\ictproject\fitnesstrack\certs\ca.pem
   ```

   The app requires TLS and verifies both the certificate and the hostname.

> Aiven connection details are credentials. Never put them in HTML, JavaScript,
> a GitHub commit, a screenshot, or an error message.

---

## 6. Environment configuration

Create your local file:

```powershell
Copy-Item .env.example .env
notepad .env
```

Fill in every value:

```dotenv
SECRET_KEY=replace-with-a-long-random-string

DB_HOST=your-aiven-host
DB_PORT=your-aiven-port
DB_USER=your-aiven-app-user
DB_PASSWORD=your-aiven-app-password
DB_NAME=fitness_wellness_db
DB_SSL_CA=certs/ca.pem

FLASK_DEBUG=false
SESSION_COOKIE_SECURE=false
```

Generate a strong Flask secret:

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

Notes:

- `.env` is ignored by Git. `.env.example` contains placeholders only.
- `config.py` has **no localhost, root, empty-password, or SQLite defaults**.
- The app refuses to start if a required value is missing, still contains a
  placeholder, or points `DB_HOST` at localhost/127.0.0.1.
- Set `SESSION_COOKIE_SECURE=true` only when the site is served over HTTPS.

---

## 7. Install

From VS Code's terminal, in `D:\ictproject\fitnesstrack`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell blocks activation, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

---

## 8. Initialize the Aiven database

The application does **not** run `CREATE DATABASE` and does not create a local
database. Initialize the online database manually.

### Option A — Aiven Query editor

1. Open your MySQL service in the Aiven console.
2. Open the **Query editor** (or connect with the Aiven CLI/mysql client).
3. Select `fitness_wellness_db`.
4. Paste and run the contents of `database\aiven_init.sql`.

### Option B — mysql client

```powershell
mysql --host YOUR_AIVEN_HOST --port YOUR_AIVEN_PORT `
      --user YOUR_AIVEN_USER --password `
      --ssl-ca certs\ca.pem `
      fitness_wellness_db < database\aiven_init.sql
```

The script:

- creates `users`, `workouts`, `nutrition_logs`, `health_metrics`;
- uses `CREATE TABLE IF NOT EXISTS`, so it is safe to run again;
- never drops, truncates, or deletes data;
- preserves primary keys, foreign keys, the email unique constraint, and the
  `health_metrics` unique constraint on `(user_id, recorded_date)`.

If the database does not exist, MySQL returns `Unknown database`. Create or
select it in Aiven first; the app will not create a local substitute.

### Optional demo data

`database\step3_sample_data.sql` is a **manual demo script only**. The Flask app
never loads it and never invents dashboard data. Register a real account first,
then run the script once if you want sample rows for a demonstration.

### Verify the schema

```powershell
mysql ... fitness_wellness_db < database\step3_verify.sql
```

---

## 9. Test the Aiven connection

```powershell
python check_db.py
```

Expected successful output includes:

```text
Configuration loaded: all required variables are present.
Target database: fitness_wellness_db
SELECT 1 succeeded.
SELECT DATABASE() -> fitness_wellness_db
SUCCESS: connected to the online Aiven MySQL database.
```

If it fails, it prints a clear configuration/connection message and exits with a
non-zero code. It never substitutes a local database.

You can also run the Flask app and open:

```text
http://127.0.0.1:5000/db-check
```

A successful JSON response looks like:

```json
{"status": "ok", "database": "fitness_wellness_db", "ssl_verified": true}
```

---

## 10. Run the application

Development:

```powershell
.\.venv\Scripts\Activate.ps1
python run.py
```

`run.py`:

1. loads `.env`;
2. validates all Aiven settings;
3. verifies the live Aiven connection and TLS;
4. only then starts the Flask development server.

Open <http://127.0.0.1:5000>.

### Production

Do not use `python run.py` (Flask's development server) in production and do not
enable debug mode. Verify the database first, then run Waitress:

```powershell
python check_db.py
waitress-serve --listen=0.0.0.0:8000 --call app:create_app
```

Set `FLASK_DEBUG=false` and `SESSION_COOKIE_SECURE=true` in the production
environment, and put the app behind HTTPS.

---

## 11. Routes and security

| Route | Access | Purpose |
|---|---|---|
| `/` | Public | Home page |
| `/register`, `/login` | Public | Create account / sign in |
| `/logout` | POST + login | End session |
| `/profile` | Login | Update own profile |
| `/dashboard` | Login | Live summary |
| `/workouts` | Login | Own workout CRUD |
| `/nutrition` | Login | Own nutrition CRUD |
| `/health` | Login | Own health metrics + BMI |
| `/reports` | Login | Own reports |
| `/db-check` | Public | Safe connectivity JSON |
| `/api/analytics/protein-strength` | Login | Weekly recorded protein and strength trends |

Security measures:

- Passwords are hashed with Werkzeug; plaintext passwords are never stored.
- All SQL uses `%s` placeholders, never string concatenation.
- Every personal `SELECT`/`UPDATE`/`DELETE` includes `user_id = %s`.
- Login is required for all private pages.
- CSRF tokens protect every POST form.
- Session cookies are HTTP-only and same-site; the secret key comes from `.env`.
- Raw MySQL errors are logged on the server and replaced with friendly pages.
- TLS certificate and hostname verification are always enabled.
- The protein/strength trend API aggregates each source before joining and is descriptive, not causal.

---

## 12. Database schema

```text
users 1 ───< workouts
users 1 ───< nutrition_logs
users 1 ───< health_metrics
```

| Table | Key | Important rule |
|---|---|---|
| `users` | `user_id` | `email` is unique; `password_hash` only |
| `workouts` | `workout_id` | `user_id` FK; duration 1–1440 minutes |
| `nutrition_logs` | `nutrition_id` | meal type is Breakfast/Lunch/Dinner/Snack |
| `health_metrics` | `metric_id` | unique `(user_id, recorded_date)` |

BMI is calculated in SQL/Python, not stored:

```text
BMI = weight_kg / (height_m × height_m)
```

---

## 13. Troubleshooting

| Message / symptom | Meaning | Fix |
|---|---|---|
| `DB_HOST is missing` or other `* is missing` | `.env` is incomplete | Fill every value from Aiven |
| `DB_HOST still contains the .env.example placeholder` | Placeholder not replaced | Put the real Aiven hostname |
| `DB_HOST points to a local database` | Local MySQL was configured | Use the Aiven hostname only |
| `DB_SSL_CA file was not found` | `ca.pem` is missing | Download it from Aiven to `certs/ca.pem` |
| `Access denied for user` | Wrong user/password or no database access | Recheck the Aiven user's password and permissions |
| `Unknown database` | `fitness_wellness_db` does not exist | Create/select it in Aiven |
| SSL / certificate error | Wrong or missing CA file | Download the current `ca.pem`; never disable verification |
| Connection timed out | Network/firewall or Aiven service down | Check internet, Aiven service status, and allowed IPs |
| `Duplicate entry` on health date | One health row per user per day | Edit the existing date instead |
| `No module named flask` | Dependencies not installed | Activate `.venv`, then `pip install -r requirements.txt` |

Server logs contain debugging details. Passwords are never logged.

---

## 14. Testing

Offline tests that do **not** need Aiven credentials:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

This covers configuration validation, TLS flags, template rendering, CSRF
rejection, route protection, analytics transformations, BMI/date/number
helpers, and the absence of SQLite/local-database code. Aiven integration
tests are skipped unless explicitly enabled.

Live checks that **do** need your real Aiven `.env` and `certs/ca.pem`:

```powershell
python check_db.py
python run.py
```

Optional live database integration test:

```powershell
$env:RUN_LIVE_DB_TESTS = "1"
.\.venv\Scripts\python.exe -m unittest tests.test_live_aiven -v
```

These tests insert temporary records, run analytics and report queries, check
user isolation and the `ON DUPLICATE KEY UPDATE` rule, and then **roll the
transactions back**. The analytics load test inserts 600 synthetic workouts
and 600 synthetic nutrition records (1,200 total), runs the 90-day analytics
summary three times, and enforces a 5-second maximum per run by default.
Override the threshold with `FITTRACK_STRESS_MAX_QUERY_SECONDS`. Run this
write-and-rollback test against a development or staging database, not a
production workload. Tests never run `DROP`, `TRUNCATE`, or `DELETE`.

The final project report is available as
[`docs/FINAL_PROJECT_REPORT.md`](docs/FINAL_PROJECT_REPORT.md) and
[`docs/FINAL_PROJECT_REPORT.docx`](docs/FINAL_PROJECT_REPORT.docx). Regenerate
the Word document after editing the report with:

```powershell
.\.venv\Scripts\python.exe tools\export_final_report.py
```

Finally, open `http://127.0.0.1:5000/db-check`, register an account in the
browser, and test each CRUD page. Live credentials remain private to your
machine.

---

## 15. Migration notes

- `config.py` previously defaulted to local MySQL. All local defaults were
  removed; every value now comes from `.env`.
- `app/db.py` now uses Aiven TLS settings (`ssl_ca`, `ssl_verify_cert`,
  `ssl_verify_identity`) and wraps errors safely.
- Dashboard placeholder cards and “coming soon” pages were replaced by real
  Aiven-backed pages while keeping the original visual design.
- Historical files in `database\archive\` and `docs\archive\` are reference only
  and are not executed by the application.

---

## 16. Author

College industry project — Fitness & Wellness Tracking Database System.
