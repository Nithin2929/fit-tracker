# Fitness & Wellness Tracking Database System
## Complete Project Requirement Audit and Gap Analysis

**Project:** FitTrack — Fitness & Wellness Tracking Database System  
**Audit date:** 2026-11-02  
**Auditor role:** DBMS project reviewer / MySQL architect / technical auditor  
**Mode:** Read-only audit. No project file was modified. No table was created or altered. No row was inserted, updated, or deleted.  
**Database audited:** Aiven Cloud MySQL `fitness_wellness_db` (server `8.4.11`)  
**Report file:** `Fitness_Wellness_Project_Requirement_Audit.md`

> **Historical snapshot:** This audit describes the repository as inspected on
> 2026-11-02. Project files and implementation changed afterward, so its score
> and gap list are not the current completion status. See
> [`docs/FINAL_PROJECT_REPORT.md`](docs/FINAL_PROJECT_REPORT.md) for the later
> report and current verification limits.

> **Honest answer up front:** The project is a working Flask + Aiven MySQL application with a clean four-table schema, real constraints, indexes, TLS, parameterized queries, and a proper connection/transaction layer. It is **not yet complete against the mentor's four milestones**. The biggest gaps are: no ER diagram, no Data Dictionary, no Normalization Report, no Logic Flow Diagram, no `exercises` / `workout_exercises` normalization (one workout cannot hold many exercises), no heart-rate or time-based metrics, no 1,000+ dataset, no dummy-data generator, no visual charts, no `HAVING` query, no strength-vs-protein correlation, no caloric-deficit report, no performance testing, and no final PDF/DOCX report. The live database currently has **1 user and 0 fitness records**. Overall requirement completion is **47.7%**.

---

# 1. Project Inspection Summary

## 1.1 Files inspected (evidence inventory)

### Python application

| File | Purpose | Evidence it provides |
|---|---|---|
| `run.py` | App entry point | Starts the Flask app via the application factory. |
| `config.py` | Environment configuration | Strict env validation, no SQLite/local fallback, TLS settings, secret handling. |
| `check_db.py` | Connectivity checker | Separate live database connectivity check. |
| `app/__init__.py` | Application factory | Blueprint registration, user loading, error handling. |
| `app/db.py` | Database layer | Aiven TLS connection, per-request connection, `autocommit=False`, commit/rollback helper, parameterized `fetch_one` / `fetch_all` / `execute`. |
| `app/utils.py` | Shared helpers | Login guard, CSRF, date/int/decimal parsing, BMI calculation, safe redirects, template filters. |
| `app/routes/main.py` | Public pages | Home page and `/db-check` live connectivity endpoint. |
| `app/routes/auth.py` | Authentication | Register, login, logout, profile update; password hashing; unique-email handling. |
| `app/routes/dashboard.py` | Dashboard | Live aggregate totals and latest measurements for the signed-in user. |
| `app/routes/workouts.py` | Workout CRUD | List/add/edit/delete with `WHERE user_id = %s` ownership filtering. |
| `app/routes/nutrition.py` | Nutrition CRUD | List/add/edit/delete meals with calories, protein, carbohydrates, fat. |
| `app/routes/health.py` | Health CRUD | List/add/edit/delete daily weight, height, steps, calories; BMI calculated. |
| `app/routes/reports.py` | Reports | Daily, weekly, monthly, calorie, weight and BMI aggregate queries. |
| `app/routes/__init__.py` | Blueprint exports | Route registration support. |
| `tests/test_smoke.py` | Offline tests | 30 tests for pages, CSRF, config, TLS, BMI, parsers, no-SQLite rule. |
| `tests/test_live_aiven.py` | Live integration tests | Rollback-only live tests; skipped unless `RUN_LIVE_DB_TESTS=1`. |

### SQL and database scripts

| File | Purpose | Evidence it provides |
|---|---|---|
| `database/aiven_init.sql` | Current DDL | Creates `users`, `workouts`, `nutrition_logs`, `health_metrics` with PK/FK/UNIQUE/CHECK/DEFAULT and indexes. |
| `database/step3_tables.sql` | Child-table DDL | Alternative DDL for the three child tables (assumes `users` exists). |
| `database/step3_sample_data.sql` | Manual sample data | Adds 3 workouts, 4 nutrition rows, 3 health rows for the first user only. |
| `database/step3_verify.sql` | Read-only verification | Metadata, JOIN, subquery and aggregate examples. |
| `database/app_user.sql` | DB account notes | Aiven user/grant guidance; no live account created by the app. |
| `database/archive/*.sql` | Obsolete reference | Five-table designs and sample data that do **not** match the live schema. |

### Templates, static assets, configuration and documentation

| Area | Files inspected |
|---|---|
| Templates | `base.html`, `home.html`, `dashboard.html`, `auth/{register,login,profile}.html`, `workouts/{index,form}.html`, `nutrition/{index,form}.html`, `health/{index,form}.html`, `reports/index.html`, `error.html`, `coming_soon.html` |
| Static | `app/static/js/main.js`, `app/static/css/style.css`, `app/static/images/favicon.svg` |
| Config | `requirements.txt`, `.env.example`, `.gitignore`, `certs/README.md` |
| Documentation | `README.md`, `docs/STEP3_TABLES.md`, `docs/archive/DATABASE_DESIGN_v1.md`, `docs/archive/STEP1_DATABASE_auto.md`, `docs/archive/PHASE1_SETUP_v1.md` |

> `.env` and `certs/ca.pem` exist locally but are gitignored. Their contents were **not** read into this report and no credential value is disclosed.

## 1.2 Live Aiven database inventory (read-only)

| Item | Verified result |
|---|---|
| Server version | MySQL `8.4.11` |
| Active database | `fitness_wellness_db` |
| Storage engine | InnoDB for all four tables |
| Character set / collation | `utf8mb4` / `utf8mb4_unicode_ci` |
| Tables | `health_metrics`, `nutrition_logs`, `users`, `workouts` |
| Users | **1** (real account, `user_id = 5`, created 2026-11-02) |
| Workouts | **0** |
| Nutrition logs | **0** |
| Health metric records | **0** |
| Foreign keys | 3, all to `users.user_id`, `ON DELETE CASCADE ON UPDATE CASCADE` |
| CHECK constraints | 11 |
| Indexes | Primary keys, `uq_users_email`, `idx_workouts_user_date`, `idx_nutrition_user_date`, `uq_health_user_date` |
| TLS | `/db-check` reports `ssl_verified: true`, cipher `TLS_AES_128_GCM_SHA256` |
| Write operations during audit | **None** |

Actual `SELECT COUNT(*)` results override stale InnoDB `TABLE_ROWS` estimates, which showed non-zero estimates while the tables are empty.

## 1.3 Executed evidence

- **Offline tests:** `python -m unittest discover -s tests -v` → **31 tests run, OK, 1 skipped** (the skipped test is the live Aiven test, disabled unless `RUN_LIVE_DB_TESTS=1`).
- **Public pages:** `/`, `/login`, `/register`, `/db-check` return HTTP 200.
- **Protected pages:** `/dashboard`, `/workouts/`, `/nutrition/`, `/health/`, `/reports/`, `/profile` return HTTP 302 to `/login`.
- **`/db-check` JSON:** database `fitness_wellness_db`, server `8.4.11`, TLS verified, status `ok`.
- **Representative SQL executed read-only:** daily workout aggregate, daily nutrition aggregate, daily health select, weekly workout aggregate, monthly health aggregate, INNER JOIN, LEFT JOIN summary, correlated subquery, dashboard totals. All executed successfully; data-dependent queries returned 0 rows, the user-level join summary returned 1 row.
- **`EXPLAIN`:** `workouts` and `nutrition_logs` use their composite `(user_id, date)` range indexes; `health_metrics` uses `uq_health_user_date`; email login benefits from the unique email index.
- **No 1,000+ row dataset, no measured query timings, and no stress/load test results were found.**

## 1.4 Application functionality check (inspected vs tested)

This audit was read-only. Read paths were exercised; write paths were inspected in code but **not executed**.

| Function | Status | Evidence / note |
|---|---|---|
| User registration | Inspected, not live-tested | `app/routes/auth.py` validates, hashes password, inserts with parameterized SQL. A write would have been required to test. |
| User login | Inspected, not live-tested | `check_password_hash` + session setup in `auth.py`; no live credentials were used. |
| Password hashing | PASS (inspection) | Werkzeug `generate_password_hash` / `check_password_hash`; no plaintext passwords stored. |
| Profile management | Inspected, not live-tested | `auth.py` profile route updates name, DOB, gender, height. |
| Workout create/retrieve/update/delete | Read paths not authenticated; writes inspected only | `workouts.py` uses a single free-text `exercise_name`; no multi-exercise support. |
| Exercise management | FAIL | No exercises module, table, CRUD, or template exists. |
| Nutrition create/retrieve/update/delete | Writes inspected only | `nutrition.py` stores one food item per row with calories and three macros. |
| Health metric create/retrieve/update/delete | Writes inspected only | `health.py` upserts one record per user per day; BMI is computed. |
| Dashboard | Inspected; empty-data render not authenticated | `dashboard.py` reads live totals from Aiven. |
| Reports | Query layer executed read-only | `reports.py` queries ran; the authenticated HTML page was not rendered because no login was performed. |
| Aiven-only database use | PASS | `config.py` / `app/db.py` have no SQLite/local fallback; tests enforce this. |
| Hardcoded credentials | PASS (none found) | Values come from environment variables; `.env.example` contains placeholders only. |
| Fake/hardcoded dashboard data | PASS (none found) | Dashboard values come from SQL queries. |
| User ownership checks | PASS (inspection) | Every user-data query filters by `g.user["user_id"]`; detail routes also verify ownership. |

## 1.5 Repository state

The working tree contains the completed Aiven migration and is **uncommitted**. This audit did not stage, commit, modify, or delete any project file; the only new file is this report.

---

# 2. Requirement-by-Requirement Matrix

**Status definitions:** PASS = implemented and evidenced; PARTIAL = partly implemented or incomplete evidence; FAIL = missing or clearly not implemented; NOT VERIFIED = insufficient evidence; NOT APPLICABLE = genuinely does not apply.

> **Note on data-count rows:** Where a row asks to determine a record count, PASS means the count was positively established, not that data exists. Data availability itself is assessed separately (M3-16, M3-17, M3-65, M4-25 to M4-35).

## 2.1 Milestone 1 — Entity Identification & Logic Mapping (43 requirements)

| ID | Milestone | Mentor Requirement | Status | Evidence | Missing Work | Recommended Action |
|---|---|---|---|---|---|---|
| M1-01 | M1 | Users entity exists | PASS | Live `users` table: `user_id` PK, `full_name`, `email`, `password_hash`, `date_of_birth`, `gender`, `height_cm`, timestamps. | None. | Keep. Document in data dictionary. |
| M1-02 | M1 | Activities entity exists | PARTIAL | Activity is represented only as `workouts.exercise_name`; no standalone activities table or activity-type lookup. | Dedicated activity classification. | Add an `activities` or `exercise_categories` lookup, or document that a workout row is the activity. |
| M1-03 | M1 | Workouts entity exists | PASS | Live `workouts` table with `workout_id` PK and `user_id` FK. | None. | Keep. |
| M1-04 | M1 | Exercises entity exists | FAIL | No `exercises` table, route, template, or model. `exercise_name` is free text. | Exercise catalog with attributes. | Create `exercises` and `workout_exercises` (see Appendix B). |
| M1-05 | M1 | Nutrition entity exists | PARTIAL | Nutrition is stored only as `nutrition_logs`; no `foods` reference table. | Food/nutrition reference entity. | Add `foods` or document that a log row is the nutrition record. |
| M1-06 | M1 | Nutrition logs entity exists | PASS | Live `nutrition_logs` table with `nutrition_id` PK and `user_id` FK. | None. | Keep. |
| M1-07 | M1 | BioMetrics / health metrics entity exists | PASS | Live `health_metrics` table with `metric_id` PK and `user_id` FK. | None. | Keep. |
| M1-08 | M1 | User profile information represented | PASS | `users.full_name`, `email`, `date_of_birth`, `gender`, `height_cm`. | None. | Document fields and types. |
| M1-09 | M1 | Workout activities represented | PASS | `workouts.exercise_name`, `duration_minutes`, `calories_burned`, `workout_date`. | None. | Keep. |
| M1-10 | M1 | Exercise details represented | PARTIAL | Only the exercise name is stored; no sets, reps, weight, distance, or muscle group. | Detailed exercise attributes. | Add via `exercises` + `workout_exercises`. |
| M1-11 | M1 | Workout performance represented | PARTIAL | Duration and calories only; no sets/reps/load/distance/pace/1RM. | Performance attributes. | Add performance columns to `workout_exercises`. |
| M1-12 | M1 | Food intake represented | PASS | `nutrition_logs.food_name`, `meal_type`, `log_date`. | None. | Keep. |
| M1-13 | M1 | Nutritional values represented (calories/carbs/fats) | PASS | `nutrition_logs.calories`, `carbohydrates`, `fat`. | None. | Keep. |
| M1-14 | M1 | Protein represented | PASS | `nutrition_logs.protein DECIMAL(6,1)`. | None. | Keep. |
| M1-15 | M1 | Weight represented | PASS | `health_metrics.weight DECIMAL(5,2)` and `users.height_cm`. | None. | Keep; resolve height duplication (M2-34). |
| M1-16 | M1 | BMI represented | PASS | BMI is derived in SQL: `weight / ((height/100)^2)` in `health.py` and `reports.py`; also `calculate_bmi()` in `utils.py`. | BMI is not stored, which is acceptable; document the derivation. | Document the formula and rounding in the data dictionary. |
| M1-17 | M1 | Steps represented | PASS | `health_metrics.steps INT UNSIGNED DEFAULT 0`. | None. | Keep. |
| M1-18 | M1 | Heart rate represented | FAIL | No heart-rate column, table, or input field anywhere. | Heart-rate attributes. | Add heart-rate fields or a `heart_rate_samples` table (Appendix B). |
| M1-19 | M1 | Heart rate zones represented | FAIL | No zone definition, storage, or documentation. | Zone model. | Add zone boundaries and per-zone time, or document as out of scope. |
| M1-20 | M1 | Time-based health measurements represented | FAIL | `health_metrics.recorded_date` is DATE only; no DATETIME/timestamp per sample, no continuous data. | Time-of-day / interval measurements. | Add `recorded_at DATETIME` or a separate samples table. |
| M1-21 | M1 | Entity attributes and data types documented | PARTIAL | Types exist in DDL; `README.md` and `docs/STEP3_TABLES.md` describe some columns, but there is no current comprehensive data dictionary. | Complete attribute/type documentation. | Create `docs/DATA_DICTIONARY.md` (Appendix C). |
| M1-22 | M1 | One User to Many Workouts | PASS | `workouts.user_id` FK to `users.user_id`; multiple workouts allowed per user. | None. | Keep. |
| M1-23 | M1 | One Workout to Many Exercises | FAIL | No junction table; one workout row holds one `exercise_name`. | `workout_exercises` relationship. | Create `workout_exercises` with FKs to `workouts` and `exercises`. |
| M1-24 | M1 | One User to Many Nutrition Logs | PASS | `nutrition_logs.user_id` FK; no daily uniqueness rule, so many rows per user/day are allowed. | None. | Keep. |
| M1-25 | M1 | One User to Many Health Metric Records | PASS | `health_metrics.user_id` FK; `UNIQUE(user_id, recorded_date)` allows many records over time. | None. | Keep. |
| M1-26 | M1 | Multiple exercises in one workout | FAIL | Not supported; `exercise_name` is a single value. | Junction/collection model. | Implement `workout_exercises` and update workout forms/routes. |
| M1-27 | M1 | Multiple workouts per user | PASS | FK allows many `workouts` rows per `user_id`; list query orders by date. | None. | Keep. |
| M1-28 | M1 | Multiple nutrition logs per user | PASS | FK allows many rows; daily aggregate query groups by `log_date`. | None. | Keep. |
| M1-29 | M1 | Multiple health metric records per user | PASS | One per day is allowed, so a user accumulates many records over time. | None. | Keep; document the one-per-day rule. |
| M1-30 | M1 | Comprehensive Data Dictionary | FAIL | No current data dictionary file. Archive design is for a different schema. | Full data dictionary. | Create `docs/DATA_DICTIONARY.md`. |
| M1-31 | M1 | High-level Logic Flow Diagram | FAIL | No logic-flow diagram or Mermaid/drawio file. README has an architecture ASCII sketch only. | Logic flow diagram. | Create `docs/LOGIC_FLOW.md` with a diagram (Appendix C). |
| M1-32 | M1 | Clear separation of Users, Activities, Nutrition, BioMetrics | PARTIAL | Users, nutrition, and health are separate tables; activities and workouts are the same table. | Separate activity concept. | Add activity classification or explicitly document the merge. |
| M1-33 | M1 | Documented explanation of module interaction | PARTIAL | `README.md` explains architecture and module pages; no formal interaction/data-flow document. | Interaction documentation. | Add module-interaction section to design docs. |
| M1-34 | M1 | Real-time or time-based health metrics supported | FAIL | Only DATE-level snapshots; no real-time ingestion or time series. | Time-based sampling. | Add timestamped samples or mark out of scope with mentor approval. |
| M1-35 | M1 | Heart rate zones and macronutrient ratios implemented or documented | FAIL | No HR zones; macros stored as absolute grams with no ratio calculation or documentation. | Zone + ratio logic/docs. | Add ratio queries and document; add HR zones only if in scope. |
| M1-36 | M1 | Deliverable: Data Dictionary | FAIL | File absent. | `docs/DATA_DICTIONARY.md`. | Create it. |
| M1-37 | M1 | Deliverable: Logic Flow Diagram | FAIL | File absent. | `docs/LOGIC_FLOW.md`. | Create it. |
| M1-38 | M1 | Deliverable: Entity identification | PARTIAL | Entities are implicit in DDL; no formal entity list document. | Formal entity list. | Add to design document. |
| M1-39 | M1 | Deliverable: Attribute identification | PARTIAL | Attributes exist in DDL and partial docs; no complete formal list. | Formal attribute list. | Add to data dictionary. |
| M1-40 | M1 | Deliverable: Primary key identification | PARTIAL | PKs exist in DDL (`user_id`, `workout_id`, `nutrition_id`, `metric_id`); not formally documented. | PK documentation. | Add to data dictionary and schema reference. |
| M1-41 | M1 | Deliverable: Foreign key identification | PARTIAL | Three FKs exist in DDL; not formally documented as a deliverable. | FK documentation. | Add to schema reference. |
| M1-42 | M1 | Deliverable: Relationship mapping | PARTIAL | Relationships enforced by FKs; no relationship-map deliverable. | Relationship map. | Add to design document. |
| M1-43 | M1 | Deliverable: Cardinality | FAIL | Cardinality is not documented anywhere current. | Cardinality notation. | Document 1:N and missing M:N in the ER deliverable. |

**Milestone 1 result:** 18 PASS, 12 PARTIAL, 13 FAIL, 0 NOT VERIFIED, 0 NOT APPLICABLE (43 total).

## 2.2 Milestone 2 — ER Diagramming & Schema Normalization (40 requirements)

| ID | Milestone | Mentor Requirement | Status | Evidence | Missing Work | Recommended Action |
|---|---|---|---|---|---|---|
| M2-01 | M2 | ER diagram exists | FAIL | No `.drawio`, `.mmd`, image, PDF, or diagram file anywhere in the project. | ER diagram deliverable. | Create `docs/ER_DIAGRAM.md` plus an exported PNG/drawio using Crow's Foot. |
| M2-02 | M2 | All relevant entities represented in ER diagram | FAIL | No diagram exists. | Entities: users, workouts, exercises, workout_exercises, nutrition_logs, health_metrics. | Draw all six entities after schema fix. |
| M2-03 | M2 | Primary keys shown | FAIL | No diagram. | PK notation. | Show PKs in the ER diagram and schema table. |
| M2-04 | M2 | Foreign keys shown | FAIL | No diagram. | FK notation. | Show FK links. |
| M2-05 | M2 | Relationships represented | FAIL | No diagram. | Relationship lines. | Draw all 1:N and M:N relationships. |
| M2-06 | M2 | Cardinality clearly indicated | FAIL | No diagram; not documented elsewhere. | Cardinality labels. | Use Crow's Foot with 1 and N markers. |
| M2-07 | M2 | Crow's Foot notation used | FAIL | No diagram. | Crow's Foot symbols. | Use standard Crow's Foot. |
| M2-08 | M2 | Diagram matches actual database | FAIL | No current diagram. `docs/archive/DATABASE_DESIGN_v1.md` shows a five-table design (`daily_wellness`, `goals`, `progress`) that does not match the live four-table schema. | Accurate current diagram. | Draw from the live schema, not from archive docs. |
| M2-09 | M2 | 1NF: every field holds a single atomic value | PASS | All live columns are scalar (`VARCHAR`, `INT`, `DECIMAL`, `DATE`, `ENUM`, `TIMESTAMP`); no arrays or JSON. | None. | Keep. |
| M2-10 | M2 | 1NF: no repeating groups | PASS | No repeating column groups such as `exercise1`, `exercise2`; child rows are separate records. | None. | Keep. |
| M2-11 | M2 | 1NF: no multiple exercises in one comma-separated column | PASS | `workouts.exercise_name` stores one name per row; no comma-separated lists were found. | Note: this satisfies 1NF literally but fails the many-exercises model (M1-23). | Add the junction table rather than comma lists. |
| M2-12 | M2 | 1NF: no multiple food items in one field | PASS | `nutrition_logs.food_name` is one food item per row; multiple items are multiple rows. | None. | Keep. |
| M2-13 | M2 | 2NF satisfied | PASS | Every table uses a single-column surrogate PK (`user_id`, `workout_id`, `nutrition_id`, `metric_id`); there are no composite keys and therefore no partial dependencies. | None. | Keep; re-check after adding `workout_exercises` (composite key needs justification). |
| M2-14 | M2 | 3NF satisfied | PARTIAL | No non-key-to-non-key dependency exists inside a table, so formal 3NF holds. However, `height` is duplicated in `users.height_cm` and `health_metrics.height`, and `exercise_name` / `food_name` are free-text values that would normally be lookup entities. | Remove/derive the duplicated height and normalize exercise/food reference data. | Keep one source of height; add `exercises` (and optionally `foods`). |
| M2-15 | M2 | PRIMARY KEY constraints exist | PASS | Live PKs: `users.user_id`, `workouts.workout_id`, `nutrition_logs.nutrition_id`, `health_metrics.metric_id`. | None. | Keep. |
| M2-16 | M2 | FOREIGN KEY constraints exist | PASS | Live FKs: `fk_workouts_user`, `fk_nutrition_user`, `fk_health_user`, all to `users.user_id`. | None. | Add `workout_exercises` FKs when the table is created. |
| M2-17 | M2 | NOT NULL constraints exist | PASS | Verified on `users.full_name/email/password_hash`, all PKs/FKs, `workouts.exercise_name/duration_minutes/workout_date`, `nutrition_logs.food_name/meal_type/calories/log_date`, `health_metrics.weight/height/recorded_date`. | None. | Keep. |
| M2-18 | M2 | UNIQUE constraints exist | PASS | `uq_users_email` on `users.email`; `uq_health_user_date` on `(user_id, recorded_date)`. | None. | Keep. |
| M2-19 | M2 | CHECK constraints exist | PASS | 11 live CHECK constraints across `users`, `workouts`, `nutrition_logs`, `health_metrics`. | None. | Keep. |
| M2-20 | M2 | DEFAULT constraints exist | PASS | `health_metrics.steps DEFAULT 0`, `calories_burned DEFAULT 0`; `users.created_at DEFAULT CURRENT_TIMESTAMP`; `updated_at` auto-update. | None. | Keep. |
| M2-21 | M2 | Database prevents negative weight | PASS | `chk_health_weight CHECK (weight > 0 AND weight < 500)`; weight is also `DECIMAL(5,2) NOT NULL`. | None. | Keep. |
| M2-22 | M2 | Database prevents negative calories | PASS | `calories` / `calories_burned` are `INT UNSIGNED`; CHECK upper bounds exist. Unsigned blocks negatives at the type level. | None. | Keep. |
| M2-23 | M2 | Database prevents negative steps | PASS | `health_metrics.steps INT UNSIGNED DEFAULT 0`. | None. | Keep. |
| M2-24 | M2 | Database prevents invalid nutritional values | PASS | `chk_nutrition_protein`, `chk_nutrition_carbohydrates`, `chk_nutrition_fat` enforce 0–1000; `calories` is unsigned with `<= 10000`. | None. | Keep. |
| M2-25 | M2 | Database prevents duplicate user emails | PASS | `CONSTRAINT uq_users_email UNIQUE (email)` is live. | None. | Keep. |
| M2-26 | M2 | Database prevents invalid references to users | PASS | All three FKs reference `users.user_id`; an unknown user_id is rejected. | None. | Keep. |
| M2-27 | M2 | Database prevents invalid references to workouts or exercises | PARTIAL | No table references `workouts` or `exercises`, because neither a child table nor an exercises table exists. The requirement cannot be fully enforced without `workout_exercises`. | Child-table FKs. | Create `workout_exercises` with FKs to both parents. |
| M2-28 | M2 | Constraints exist in the database, not only in Python | PASS | PK/FK/UNIQUE/CHECK/DEFAULT are all visible in live `information_schema`; not merely route validation. | None. | Keep; avoid moving these rules into Python only. |
| M2-29 | M2 | CHECK constraints actually enforced by the MySQL version | PARTIAL | Server is MySQL `8.4.11`, which enforces CHECK constraints. Enforcement was **inspected, not executed** because the audit forbade writes. | A safe rollback test of a negative insert. | Run a transaction + negative insert + `ROLLBACK` as a post-approval validation. |
| M2-30 | M2 | Foreign key relationships implemented | PASS | Three FKs confirmed live with `REFERENCED_TABLE_NAME = users`. | None. | Keep. |
| M2-31 | M2 | Appropriate ON DELETE behavior | PASS | All FKs use `ON DELETE CASCADE`; deleting a user removes their child records. Behavior was inspected, not live-deleted. | Document the cascade policy. | Add to schema documentation; live-test with rollback only. |
| M2-32 | M2 | Appropriate ON UPDATE behavior | PASS | All FKs use `ON UPDATE CASCADE`. | None. | Keep. |
| M2-33 | M2 | Prevention of orphan records | PASS | Child rows require an existing `users.user_id`; deleting a user cascades. | None. | Keep; same policy for the new junction table. |
| M2-34 | M2 | Consistency between related tables | PARTIAL | Height exists in both `users.height_cm` and `health_metrics.height`; a profile update does not retroactively change historical records, so values can diverge. | A single source of truth or a documented snapshot policy. | Keep `users.height_cm` as current profile and document `health_metrics.height` as a historical snapshot, or remove one. |
| M2-35 | M2 | Deliverable: ER Diagram | FAIL | File absent. | ER diagram file. | Create it. |
| M2-36 | M2 | Deliverable: Crow's Foot notation | FAIL | Absent. | Crow's Foot version. | Create it. |
| M2-37 | M2 | Deliverable: Normalization Report | FAIL | No normalization report file. | 1NF/2NF/3NF analysis. | Create `docs/NORMALIZATION_REPORT.md`. |
| M2-38 | M2 | Deliverable: Physical Schema Blueprint | FAIL | DDL exists, but no blueprint document mapping logical to physical schema. | Physical schema document. | Create `docs/PHYSICAL_SCHEMA.md`. |
| M2-39 | M2 | Deliverable: PK/FK documentation | FAIL | Not documented as a deliverable; only visible in DDL. | PK/FK table. | Add to schema reference. |
| M2-40 | M2 | Deliverable: Constraint documentation | PARTIAL | Constraints are in `database/aiven_init.sql`; `docs/STEP3_TABLES.md` partially describes them. No consolidated constraint table. | Consolidated constraint list. | Add a constraint table to the schema reference. |

**Milestone 2 result:** 22 PASS, 5 PARTIAL, 13 FAIL, 0 NOT VERIFIED, 0 NOT APPLICABLE (40 total).

## 2.3 Milestone 3 — Relational Implementation & Query Engineering (74 requirements)

### 2.3.1 Implementation and data availability (M3-01 to M3-17)

| ID | Milestone | Mentor Requirement | Status | Evidence | Missing Work | Recommended Action |
|---|---|---|---|---|---|---|
| M3-01 | M3 | Database implemented using MySQL | PASS | Live Aiven MySQL `8.4.11`, `fitness_wellness_db`, four InnoDB tables. | None. | Keep. |
| M3-02 | M3 | Database creation scripts | PARTIAL | `database/aiven_init.sql` uses `USE fitness_wellness_db`; there is no `CREATE DATABASE` because Aiven provisions it. Database existence was confirmed live. | A documented provisioning step. | Document the Aiven console database-creation step in setup docs. |
| M3-03 | M3 | Table creation scripts | PASS | `database/aiven_init.sql` and `database/step3_tables.sql`. | None. | Keep; make one canonical script. |
| M3-04 | M3 | Column definitions | PASS | Verified live columns and types match the scripts. | None. | Keep. |
| M3-05 | M3 | Primary keys implemented | PASS | Four live PKs confirmed. | None. | Keep. |
| M3-06 | M3 | Foreign keys implemented | PASS | Three live FKs confirmed. | None. | Add junction FKs when created. |
| M3-07 | M3 | Constraints implemented | PASS | 11 CHECK constraints, 2 UNIQUE constraints, NOT NULL and DEFAULT columns confirmed. | None. | Keep. |
| M3-08 | M3 | Indexes implemented | PASS | Live indexes: composite user/date on `workouts`, `nutrition_logs`, `health_metrics`; unique email. | None. | Keep and document. |
| M3-09 | M3 | Relationships implemented | PASS | User to workouts/nutrition/health FKs are live. | Workout to exercises relationship. | Add `workout_exercises`. |
| M3-10 | M3 | SQL scripts match actual Aiven database | PASS | Script columns, PKs, FKs, CHECKs and indexes match live metadata. | None. | Keep scripts authoritative. |
| M3-11 | M3 | Number of users determined | PASS | `SELECT COUNT(*) FROM users` = **1**. | None. | Keep. |
| M3-12 | M3 | Number of workouts determined | PASS | `SELECT COUNT(*) FROM workouts` = **0**. | Fitness data. | Generate test data (Appendix D). |
| M3-13 | M3 | Number of exercises determined | PARTIAL | No exercises table exists, so the count is structurally 0 and not queryable. | Exercises table. | Create it, then count. |
| M3-14 | M3 | Number of nutrition records determined | PASS | `SELECT COUNT(*) FROM nutrition_logs` = **0**. | Fitness data. | Generate test data. |
| M3-15 | M3 | Number of health metric records determined | PASS | `SELECT COUNT(*) FROM health_metrics` = **0**. | Fitness data. | Generate test data. |
| M3-16 | M3 | Dummy data exists | PARTIAL | `database/step3_sample_data.sql` can add 10 child rows, but the live DB has 0 fitness rows. Archived sample data targets a different schema. | Reproducible dataset. | Create and run a generator after approval. |
| M3-17 | M3 | Data is realistic and suitable for analytics | FAIL | No workouts, nutrition, or health rows exist; analytics cannot be demonstrated. | Realistic multi-user dataset. | Generate 1,000+ realistic rows across tables. |

### 2.3.2 SQL query engineering (M3-18 to M3-30)

| ID | Milestone | Mentor Requirement | Status | Evidence | Missing Work | Recommended Action |
|---|---|---|---|---|---|---|
| M3-18 | M3 | CREATE statements present | PASS | `CREATE TABLE IF NOT EXISTS` in `aiven_init.sql` and `step3_tables.sql`. | None. | Keep. |
| M3-19 | M3 | INSERT statements present | PASS | `step3_sample_data.sql`; parameterized app inserts in all CRUD routes. | More data. | Keep and generate data. |
| M3-20 | M3 | UPDATE statements present | PASS | Workout/nutrition edit routes; health upsert (`ON DUPLICATE KEY UPDATE`); profile update. | None. | Keep. |
| M3-21 | M3 | DELETE statements present | PASS | Workout/nutrition/health delete routes with ownership checks. | None. | Keep. |
| M3-22 | M3 | SELECT statements present | PASS | Used throughout routes and `step3_verify.sql`. | None. | Keep. |
| M3-23 | M3 | INNER JOIN query present | PASS | `database/step3_verify.sql` JOIN examples; a live `users JOIN workouts` query executed successfully. | None. | Add to an analytics query library. |
| M3-24 | M3 | LEFT JOIN query present | PASS | `step3_verify.sql`; live left-join summary returned 1 user row with zero counts. | None. | Add to the library. |
| M3-25 | M3 | Subqueries present | PASS | `step3_verify.sql` and a live correlated subquery comparing workout vs food calories executed. | None. | Add to the library. |
| M3-26 | M3 | Aggregate functions present | PASS | `COUNT`, `SUM`, `AVG`, `ROUND`, `COALESCE` in dashboard/reports; executed live. | MIN/MAX not required. | Keep. |
| M3-27 | M3 | GROUP BY used | PASS | Daily/weekly/monthly groupings in `reports.py`, executed live. | None. | Keep. |
| M3-28 | M3 | HAVING query present | FAIL | A full-project search found **no HAVING clause** anywhere. | HAVING-based filtering. | Add queries such as users averaging > 2500 kcal/day or weeks with > 3 workouts. |
| M3-29 | M3 | ORDER BY used | PASS | Lists and reports order by date/id; confirmed. | None. | Keep. |
| M3-30 | M3 | Indexing used | PASS | Composite indexes exist and `EXPLAIN` confirms use. | None. | Keep and document. |

### 2.3.3 Advanced analytics queries (M3-31 to M3-43)

| ID | Milestone | Mentor Requirement | Status | Evidence | Missing Work | Recommended Action |
|---|---|---|---|---|---|---|
| M3-31 | M3 | Weekly fitness progress report | PARTIAL | `reports.py` `weekly_workouts` groups by `DATE_SUB(workout_date, INTERVAL WEEKDAY(...) DAY)`; query executed, 0 rows. | Data plus a documented report definition. | Populate data, then validate week boundaries. |
| M3-32 | M3 | Workout performance analysis | PARTIAL | Daily/weekly/monthly duration and calorie aggregates exist, but there are no sets/reps/load/pace metrics to analyze performance. | Performance attributes. | Add `workout_exercises` metrics. |
| M3-33 | M3 | Nutrition intake analysis | PARTIAL | `nutrition_by_day` and `monthly_nutrition` sum calories and macros; query executed, 0 rows. | Data plus a dedicated report section. | Populate data and document output. |
| M3-34 | M3 | Protein intake analysis | PARTIAL | Protein is summed per day in `reports.py`; there is no dedicated protein report or ratio. | Dedicated protein analysis. | Add protein totals, averages, and macro-ratio query. |
| M3-35 | M3 | Strength gains versus protein intake | FAIL | No strength metric and no correlation query. | Strength metric + correlation SQL. | Add `workout_exercises.weight_used` and a correlation/aggregate query. |
| M3-36 | M3 | Caloric deficit summaries | FAIL | No deficit query; reports show calories in and out but never `in - out` as a deficit. | Deficit calculation. | Add daily/weekly deficit query with `SUM(intake) - SUM(expenditure)`. |
| M3-37 | M3 | Average workout duration | FAIL | No `AVG(duration_minutes)` query anywhere. | Average-duration query. | Add `AVG(duration_minutes)` by user/week/month. |
| M3-38 | M3 | Total workout calories | PASS | `SUM(calories_burned)` in dashboard totals and report aggregates; executed. | None. | Keep. |
| M3-39 | M3 | Weight changes | PARTIAL | `reports.py` computes `weight_change` when at least two health records exist; with 0 records it is `None`. | Data and a trend query. | Populate data; add first-vs-last and period-delta SQL. |
| M3-40 | M3 | BMI trends | PARTIAL | Monthly `AVG(weight / height^2)` exists; no trend chart or data. | Data + trend definition. | Populate data; add time-ordered BMI series. |
| M3-41 | M3 | Steps analysis | PARTIAL | Monthly `AVG(steps)` exists; no dedicated steps report or data. | Dedicated steps analysis. | Add weekly steps totals/averages and trend output. |
| M3-42 | M3 | Health metric trends | PARTIAL | Monthly weight/steps/BMI/activity calories are averaged; no trend visualization or data. | Data + trend output. | Populate data and add chronological series. |
| M3-43 | M3 | Workout performance correlated with nutrition intake | FAIL | No query joins or correlates workout performance with nutrition. The existing LEFT JOIN summary only counts rows per user. | A real correlation query. | Add a date-keyed aggregation of both domains, then correlate. |

### 2.3.4 Transactions and ACID (M3-44 to M3-53)

| ID | Milestone | Mentor Requirement | Status | Evidence | Missing Work | Recommended Action |
|---|---|---|---|---|---|---|
| M3-44 | M3 | Transactions implemented | PASS | `app/db.py` opens connections with `autocommit=False` and exposes `get_cursor(commit=True)` with `commit()`/`rollback()`. | None. | Keep. |
| M3-45 | M3 | Atomicity | PARTIAL | Single-statement writes are atomic through the helper. No multi-statement business transaction exists because there is no workout+exercises insert. | Multi-row atomic operation. | Implement workout+exercises in one transaction after schema fix. |
| M3-46 | M3 | Consistency | PASS | DB constraints (PK/FK/UNIQUE/CHECK/NOT NULL) enforce valid state. | None. | Keep. |
| M3-47 | M3 | Isolation | PARTIAL | InnoDB default isolation is used; no isolation level is configured or tested, and no concurrent-write test exists. | Isolation policy/test. | Document the default and add a concurrency test after approval. |
| M3-48 | M3 | Durability | PASS | InnoDB with committed transactions; Aiven manages persistence. Crash-recovery was not tested. | None (inspection). | State the evidence level in the ACID report. |
| M3-49 | M3 | Transaction boundaries, COMMIT, ROLLBACK, error handling | PASS | `get_cursor()` commits on success and rolls back on exception; routes surface safe DB errors. | None. | Keep. |
| M3-50 | M3 | Failed operations leave no partial records | PARTIAL | Rollback-on-exception logic exists; it was not exercised by a live failing write during this read-only audit. | A rollback test with a forced failure. | Add a live rollback test after approval. |
| M3-51 | M3 | Multi-related insert example (workout + exercises) | FAIL | No `workout_exercises` table or combined insert exists. | Junction table + combined insert. | Implement both transactionally. |
| M3-52 | M3 | Entire operation rolls back if one part fails | PARTIAL | The helper supports rollback, and the live test rolls everything back, but no application flow inserts two related records. | A real multi-insert flow. | Add one and test failure in the second insert. |
| M3-53 | M3 | Live transaction tests exist | PARTIAL | `tests/test_live_aiven.py` exists with rollback-only live tests, but it was **not executed** during this audit (it is skipped without `RUN_LIVE_DB_TESTS=1`). | A recorded execution result. | Run it after approval and capture output. |

### 2.3.5 Indexing (M3-54 to M3-63)

| ID | Milestone | Mentor Requirement | Status | Evidence | Missing Work | Recommended Action |
|---|---|---|---|---|---|---|
| M3-54 | M3 | Index on user_id | PASS | Leftmost column of all three composite child indexes. | None. | Keep. |
| M3-55 | M3 | Index on workout date | PASS | `idx_workouts_user_date (user_id, workout_date)`; `EXPLAIN` uses it. | None. | Keep. |
| M3-56 | M3 | Index on nutrition log date | PASS | `idx_nutrition_user_date (user_id, log_date)`; `EXPLAIN` uses it. | None. | Keep. |
| M3-57 | M3 | Index on health metric date | PASS | `uq_health_user_date (user_id, recorded_date)`; `EXPLAIN` uses it. | None. | Keep. |
| M3-58 | M3 | Indexes on foreign keys | PASS | Every FK column is the leftmost index column; MySQL also requires an FK index. | None. | Keep. |
| M3-59 | M3 | Indexes on frequently filtered columns | PARTIAL | User/date filters are covered. `meal_type`, `exercise_name`, and `gender` are not indexed, but current queries do not filter on them. | None unless new filters are added. | Revisit after new reports are added. |
| M3-60 | M3 | Indexes justified by actual query patterns | PASS | All application queries filter by `user_id` and often date ranges, matching the composite indexes. | None. | Keep. |
| M3-61 | M3 | Missing indexes identified | PASS | No critical missing index at current volume. A global (all-users) date report would scan, but no such production query exists. | Document the finding. | Add to the performance report. |
| M3-62 | M3 | Unnecessary indexes identified | PASS | No duplicate/redundant secondary indexes found; PK plus composite indexes are distinct. | None. | Keep. |
| M3-63 | M3 | EXPLAIN output inspected | PASS | Four `EXPLAIN` statements executed read-only: workouts range, nutrition range, health index scan, email const lookup. | A written record. | Add EXPLAIN output to the performance document. |

### 2.3.6 Milestone 3 deliverables (M3-64 to M3-74)

| ID | Milestone | Mentor Requirement | Status | Evidence | Missing Work | Recommended Action |
|---|---|---|---|---|---|---|
| M3-64 | M3 | Functional MySQL database | PASS | Live DB reachable, TLS verified, all representative queries executed. | None. | Keep. |
| M3-65 | M3 | Dummy fitness data | FAIL | 0 workouts, 0 nutrition rows, 0 health rows. | Populated dataset. | Generate data after approval. |
| M3-66 | M3 | SQL source files | PASS | `database/*.sql` plus inline queries in routes. | A consolidated query library. | Add an advanced query file. |
| M3-67 | M3 | DDL scripts | PASS | `aiven_init.sql`, `step3_tables.sql`. | None. | Keep one canonical DDL. |
| M3-68 | M3 | DML scripts | PASS | `step3_sample_data.sql`, parameterized app writes. | 1,000+ data script. | Add a generator/data file. |
| M3-69 | M3 | Advanced SQL query library | PARTIAL | `step3_verify.sql` has JOIN/subquery/aggregate examples; no library containing HAVING, window functions, deficit, or correlation queries. | A complete advanced query library. | Create `database/analytics_queries.sql`. |
| M3-70 | M3 | JOIN queries | PASS | INNER JOIN and LEFT JOIN examples exist and executed. | None. | Keep. |
| M3-71 | M3 | Subqueries | PASS | Correlated subquery example exists and executed. | None. | Keep. |
| M3-72 | M3 | Indexes deliverable | PASS | Indexes are defined in DDL and verified live. | Documentation. | Add to schema reference. |
| M3-73 | M3 | Transaction implementation deliverable | PASS | `app/db.py` transaction helper; live-test skeleton exists. | A demonstrated multi-row case. | Add after schema fix. |
| M3-74 | M3 | ACID validation deliverable | PARTIAL | Implementation exists; live tests exist but were not run in this audit; no written ACID validation report. | Validation evidence + report. | Run tests and document atomicity/consistency/isolation/durability. |

**Milestone 3 result:** 47 PASS, 19 PARTIAL, 8 FAIL, 0 NOT VERIFIED, 0 NOT APPLICABLE (74 total).

## 2.4 Milestone 4 — Analytics, Validation & Final Documentation (64 requirements)

### 2.4.1 Analytics and visualization (M4-01 to M4-24)

| ID | Milestone | Mentor Requirement | Status | Evidence | Missing Work | Recommended Action |
|---|---|---|---|---|---|---|
| M4-01 | M4 | Weekly progress reports | PARTIAL | `reports.py` `weekly_workouts` returns weekly count/minutes/calories; query executed, 0 rows. | Data and a richer weekly report. | Populate data; add week-over-week deltas. |
| M4-02 | M4 | Caloric deficit summaries | FAIL | No deficit computation (`intake - expenditure`). Reports total intake and output separately. | Deficit SQL and report section. | Add daily/weekly deficit query and template. |
| M4-03 | M4 | Health trend visualizations | FAIL | No chart/canvas/SVG data visualization exists; `main.js` only animates counters. | Chart library/integration. | Add Chart.js charts fed by real query results. |
| M4-04 | M4 | Workout summaries | PASS | Dashboard totals and daily/weekly/monthly workout tables exist and query live data. | None. | Keep. |
| M4-05 | M4 | Nutrition summaries | PASS | Daily/monthly nutrition aggregates for calories and macros exist. | None. | Keep. |
| M4-06 | M4 | Weight trends | PARTIAL | `weight_change` and monthly `AVG(weight)` exist; no trend chart and no data. | Visualization + data. | Add chronological weight series and chart. |
| M4-07 | M4 | BMI trends | PARTIAL | Monthly `AVG(BMI)` exists; no chart and no data. | Visualization + data. | Add chronological BMI series and chart. |
| M4-08 | M4 | Steps summaries | PARTIAL | Monthly `AVG(steps)` exists; no dedicated summary or data. | Dedicated steps report. | Add weekly totals/averages and chart. |
| M4-09 | M4 | SUM() used | PASS | `SUM(duration_minutes)`, `SUM(calories_burned)`, `SUM(calories)`, macro sums throughout. | None. | Keep. |
| M4-10 | M4 | AVG() used | PASS | `AVG(weight)`, `AVG(steps)`, `AVG(BMI)` in `reports.py`. | None. | Keep. |
| M4-11 | M4 | GROUP BY used | PASS | Daily/weekly/monthly grouping. | None. | Keep. |
| M4-12 | M4 | Other appropriate aggregates | PASS | `COUNT`, `ROUND`, `COALESCE` used; no MIN/MAX needed for current reports. | None. | Keep. |
| M4-13 | M4 | Report source tables documented | PARTIAL | `reports/index.html` says "SQL joins and aggregate functions"; README describes modules. No per-report source-table documentation. | Per-report documentation. | Add a report catalogue with tables/joins/aggregates. |
| M4-14 | M4 | Report SQL queries available | PASS | All queries are in `app/routes/reports.py`. | None. | Extract to a documented query library. |
| M4-15 | M4 | Report aggregation method documented | PARTIAL | Code shows GROUP BY and Python merging; not written up. | Aggregation documentation. | Document in the analytics report. |
| M4-16 | M4 | Report output available | PASS | `app/templates/reports/index.html` renders daily/weekly/monthly tables with empty states. | Authenticated render not tested. | Verify after data is loaded. |
| M4-17 | M4 | Reports work with actual database records | FAIL | Live fitness tables are empty, so no report can display meaningful data. The authenticated report page was not rendered in this audit. | Data + authenticated verification. | Populate data, log in, and capture outputs. |
| M4-18 | M4 | Distinguish implemented report vs template-only | NOT APPLICABLE | This is an audit-method instruction, not a project feature; this report makes the distinction (queries exist, data does not). | None. | None. |
| M4-19 | M4 | Visualizations retrieve data from MySQL | FAIL | No visualizations exist. | Chart implementation. | Add DB-fed charts. |
| M4-20 | M4 | Dates correctly represented in charts | PARTIAL | Dates are correct in tables (`DATE` columns, `ORDER BY`); no charts exist. | Chart date axis. | Add and verify ISO dates. |
| M4-21 | M4 | Trends calculated correctly | PARTIAL | Monthly averages are arithmetically correct; no trend series/chart exists to validate. | Trend series. | Add chronological trend queries. |
| M4-22 | M4 | Graphs use actual records | FAIL | No graphs. | Graphs fed by query results. | Implement with real data. |
| M4-23 | M4 | Empty datasets handled properly | PASS | Templates show explicit "No ... yet" / zero states; verified in template inspection. | None. | Keep. |
| M4-24 | M4 | No static chart passed off as DB-driven | PASS | No charts exist, so there are no static charts masquerading as live. | None. | Ensure future charts are data-driven. |

### 2.4.2 Dummy data and performance (M4-25 to M4-42)

| ID | Milestone | Mentor Requirement | Status | Evidence | Missing Work | Recommended Action |
|---|---|---|---|---|---|---|
| M4-25 | M4 | Dummy data generation scripts | FAIL | Only a manual 10-row sample SQL exists; no generator script. | A seeded generator. | Create `database/generate_dummy_data.py` (Appendix D). |
| M4-26 | M4 | Dataset of at least 1,000 entries | FAIL | Live total fitness rows = **0**; sample script = 10 rows max. | 1,000+ rows. | Generate and load after approval. |
| M4-27 | M4 | Reproducible method to populate test data | PARTIAL | Manual SQL can populate 10 rows but is not idempotent for workouts/nutrition and needs an existing user. | Deterministic generator. | Add a seeded, re-runnable generator with a cleanup option. |
| M4-28 | M4 | Data suitable for analytics | FAIL | No fitness data. | Realistic multi-month data. | Generate at least 90 days across multiple users. |
| M4-29 | M4 | Multiple users | FAIL | Only 1 user exists, and it is a real account. | Test users. | Add synthetic users with clearly marked emails. |
| M4-30 | M4 | Multiple workouts | FAIL | 0 workouts. | Many workouts. | Generate 300+ workouts. |
| M4-31 | M4 | Multiple nutrition records | FAIL | 0 nutrition rows. | Many nutrition rows. | Generate 500+ nutrition rows. |
| M4-32 | M4 | Multiple health metric records | FAIL | 0 health rows. | Many health rows. | Generate 300+ daily records. |
| M4-33 | M4 | 1,000+ satisfied by actual DB records | FAIL | Actual DB has 0 fitness rows. | Loaded dataset. | Load and verify `COUNT(*)`. |
| M4-34 | M4 | 1,000+ satisfied by documented test dataset | FAIL | No dataset sheet or documented dataset. | Dataset documentation. | Add `docs/SAMPLE_DATA.md`. |
| M4-35 | M4 | 1,000+ satisfied by tested generator | FAIL | No generator and no test. | Generator + test. | Build and test it. |
| M4-36 | M4 | Stress tests | FAIL | None found. | Stress test script. | Add after data load. |
| M4-37 | M4 | Performance tests | FAIL | None found. | Performance test script/report. | Add `tests/performance_test.py`. |
| M4-38 | M4 | Query timing measured | FAIL | No measured timings exist; none were invented in this audit. | Timing runs. | Measure with `time.perf_counter` or `EXPLAIN ANALYZE`. |
| M4-39 | M4 | Database load tests | FAIL | None found. | Load test. | Add a simple concurrent-read/write load test. |
| M4-40 | M4 | Large dataset tests | FAIL | No 1,000+ dataset. | Large dataset. | Load data then test. |
| M4-41 | M4 | Query optimization evidence | PARTIAL | `EXPLAIN` was run during this audit, but no written optimization record exists in the project. | Documented evidence. | Add EXPLAIN output and notes to the performance report. |
| M4-42 | M4 | Important queries tested with 1,000+ entries | FAIL | Dataset size is 0; no such test exists. | Data + tests. | Run after data generation. |

### 2.4.3 Data accuracy and documentation (M4-43 to M4-64)

| ID | Milestone | Mentor Requirement | Status | Evidence | Missing Work | Recommended Action |
|---|---|---|---|---|---|---|
| M4-43 | M4 | BMI calculations correct | PASS | Formula `weight / ((height/100)^2)` is correct in `health.py`, `reports.py`, and `utils.calculate_bmi`; `test_bmi_calculation_and_categories` passes. | None. | Keep; document rounding. |
| M4-44 | M4 | Calories handled consistently | PARTIAL | Food calories, workout calories, and health activity calories are separate columns. `reports.py` adds workout calories and activity calories into `total_calories_out`, which risks double counting if both represent the same activity. | A documented definition of each calorie field and a single expenditure total. | Define "calories out" once; avoid adding overlapping sources. |
| M4-45 | M4 | Weight values use consistent units | PASS | `health_metrics.weight DECIMAL(5,2)` and templates label values as `kg`; no lb/mixed units found. | None. | Keep; document kg. |
| M4-46 | M4 | Nutrition calculations correct | PASS | Macros are stored as grams and summed with `COALESCE(SUM(...),0)`; no invalid derived arithmetic found. | Macro-ratio calculation. | Add ratio and percentage queries. |
| M4-47 | M4 | Weekly summaries use correct date boundaries | PASS | `DATE_SUB(workout_date, INTERVAL WEEKDAY(workout_date) DAY)` yields Monday-based weeks; range filter uses start/end inclusive. | None. | Add a unit test for week boundaries. |
| M4-48 | M4 | Health trends use chronological records | PASS | Health lists and monthly reports `ORDER BY recorded_date DESC`; chronological ordering is correct. | None. | Keep. |
| M4-49 | M4 | Queries avoid duplicate counting | PARTIAL | Reports fetch each domain separately, so no join fan-out doubles counts; `COUNT(DISTINCT ...)` is used in the summary join. However, expenditure can double count if workout and health calories overlap. | A defined expenditure source. | Fix M4-44 and add duplicate-count tests. |
| M4-50 | M4 | User-specific reports filter the correct user | PASS | Every user-data query uses `WHERE user_id = %s` bound to `g.user["user_id"]`. | None. | Keep. |
| M4-51 | M4 | Database Design Document | PARTIAL | `README.md` has an architecture/schema section; `docs/archive/DATABASE_DESIGN_v1.md` is obsolete and contradicts the live schema. | Current design document. | Create `docs/DB_DESIGN.md`; mark archive as obsolete. |
| M4-52 | M4 | Data Dictionary document | FAIL | File absent. | Full data dictionary. | Create `docs/DATA_DICTIONARY.md`. |
| M4-53 | M4 | ER Diagram document | FAIL | File absent. | ER document plus image. | Create `docs/ER_DIAGRAM.md`. |
| M4-54 | M4 | Normalization Report document | FAIL | File absent. | 1NF/2NF/3NF report. | Create `docs/NORMALIZATION_REPORT.md`. |
| M4-55 | M4 | Physical Schema Blueprint document | FAIL | File absent. | Physical schema blueprint. | Create `docs/PHYSICAL_SCHEMA.md`. |
| M4-56 | M4 | SQL source files | PASS | `database/aiven_init.sql`, `step3_tables.sql`, `step3_sample_data.sql`, `step3_verify.sql`. | Consolidated analytics file. | Add `database/analytics_queries.sql`. |
| M4-57 | M4 | Sample Data Sheet | FAIL | No dataset sheet or documented record inventory. | Sample data sheet. | Create `docs/SAMPLE_DATA.md` with source, counts, seed, and ranges. |
| M4-58 | M4 | Sample Analytics Reports | FAIL | No document with sample outputs/results. | Sample report document. | Create `docs/ANALYTICS_REPORTS.md` after data load. |
| M4-59 | M4 | Database Schema Documentation | PARTIAL | `docs/STEP3_TABLES.md` describes the three child tables and mentions local MySQL Workbench; `README.md` summarizes schema. No complete current schema reference. | Complete schema reference. | Create `docs/SCHEMA_REFERENCE.md`. |
| M4-60 | M4 | Final Internship Project Report | FAIL | No final report file of any format. | Final project report. | Write and export it. |
| M4-61 | M4 | API Integration Guide | FAIL | There is no REST API and no API guide. The app is server-rendered. | API guide or explicit scope statement. | Add a guide or state that no external API is part of scope, with mentor approval. |
| M4-62 | M4 | Setup and Deployment Instructions | PASS | `README.md` covers install, env, TLS, run, and checks; `.env.example` and `certs/README.md` support setup. | None. | Keep. |
| M4-63 | M4 | Final report available as PDF or DOC/DOCX | FAIL | No `.pdf`, `.doc`, or `.docx` file exists in the project (verified by recursive search). | Portable final report. | Export the final report to PDF/DOCX. |
| M4-64 | M4 | Documentation matches actual implementation | PARTIAL | README and `.env.example` match the Aiven implementation. `docs/archive/*` describes a five-table local-MySQL design; `STEP3_TABLES.md` still references MySQL Workbench "Fitness Local". | Remove/obsolete outdated docs and correct local references. | Update or clearly archive stale documentation. |

**Milestone 4 result:** 18 PASS, 15 PARTIAL, 30 FAIL, 0 NOT VERIFIED, 1 NOT APPLICABLE (64 total).

## 2.5 Matrix totals

| Milestone | Total | PASS | PARTIAL | FAIL | NOT VERIFIED | NOT APPLICABLE |
|---|---:|---:|---:|---:|---:|---:|
| M1 — Entity Identification & Logic Mapping | 43 | 18 | 12 | 13 | 0 | 0 |
| M2 — ER Diagramming & Schema Normalization | 40 | 22 | 5 | 13 | 0 | 0 |
| M3 — Relational Implementation & Query Engineering | 74 | 47 | 19 | 8 | 0 | 0 |
| M4 — Analytics, Validation & Final Documentation | 64 | 18 | 15 | 30 | 0 | 1 |
| **TOTAL** | **221** | **105** | **51** | **64** | **0** | **1** |

**Applicable requirements:** 221 − 1 = **220**.  
**Completion:** 105 ÷ 220 × 100 = **47.73% ≈ 47.7%**.

> This is a requirement-checklist completion percentage only. It is not a quality score and not a guarantee that the application is production-ready.

---

# 3. Milestone-Wise Audit

## 3.1 Milestone 1 — Entity Identification & Logic Mapping

**Result:** 18 PASS / 12 PARTIAL / 13 FAIL / 0 NOT VERIFIED (41.9% of 43).

**What works**
- Users, workouts, nutrition logs, and health metrics exist as real tables with correct PKs/FKs.
- Profile data, workout activity, food intake, calories, protein, carbohydrates, fat, weight, derived BMI, and steps are represented.
- All four required 1:N relationships except workout→exercises are enforced by foreign keys.
- A user can have many workouts, many nutrition logs, and many health records over time.

**What is missing**
- No `exercises` entity. `workouts.exercise_name` is free text, so exercise details and performance are not modeled.
- No workout→exercises relationship, therefore no multiple exercises per workout.
- No heart rate, heart-rate zones, time-based/real-time metrics, or macronutrient ratios.
- No Data Dictionary, Logic Flow Diagram, or formal entity/attribute/PK/FK/cardinality deliverables.

**Next steps:** create the exercises/junction model (Appendix B), then write the Data Dictionary and Logic Flow documents (Appendix C).

## 3.2 Milestone 2 — ER Diagramming & Schema Normalization

**Result:** 22 PASS / 5 PARTIAL / 13 FAIL / 0 NOT VERIFIED (55.0% of 40).

**What works**
- The physical schema is clean and well-constrained: 4 PKs, 3 FKs with CASCADE, 2 UNIQUE constraints, 11 CHECK constraints, NOT NULL and DEFAULT rules.
- 1NF and 2NF are satisfied; formal 3NF holds within tables.
- Negative weight/calories/steps and invalid macro values are blocked at the database level.
- Duplicate emails and orphan users are blocked.

**What is missing**
- No ER diagram, no Crow's Foot notation, no cardinality, no normalization report, no physical blueprint, no consolidated PK/FK/constraint documentation.
- `height` is duplicated between `users` and `health_metrics`.
- Exercise/food names are free text rather than lookup entities.
- CHECK enforcement was inspected but not executed with a negative insert (read-only audit).

**Next steps:** draw the ER diagram from the live schema **after** adding `exercises` and `workout_exercises`; write the normalization report with concrete examples; resolve the height duplication policy.

## 3.3 Milestone 3 — Relational Implementation & Query Engineering

**Result:** 47 PASS / 19 PARTIAL / 8 FAIL / 0 NOT VERIFIED (63.5% of 74).

**What works**
- MySQL 8.4.11 is genuinely implemented on Aiven; scripts match the live schema.
- CRUD, JOINs, subqueries, aggregates, GROUP BY, ORDER BY, and indexing all exist.
- Transactions are implemented with `autocommit=False` and commit/rollback handling.
- Indexes are justified by query patterns and confirmed by `EXPLAIN`.
- Total workout calories and dashboard aggregates work.

**What is missing**
- No `HAVING` query.
- No strength-vs-protein correlation, no caloric-deficit query, no average-duration query.
- No normalised workout+exercises insert, so the key atomicity example cannot be demonstrated.
- No actual fitness data, so data-dependent queries return nothing.
- No 1,000+ dataset, no load/stress/performance tests, no measured timings.
- Live transaction tests exist but were not executed in this audit.

**Next steps:** fix the schema first, then add the missing analytics to `database/analytics_queries.sql`, generate data, and run transaction/performance tests.

## 3.4 Milestone 4 — Analytics, Validation & Final Documentation

**Result:** 18 PASS / 15 PARTIAL / 30 FAIL / 0 NOT VERIFIED / 1 N/A (28.6% of 63 applicable).

**What works**
- Workout and nutrition summaries use real SQL aggregates.
- BMI math is correct; weight units are consistent; user filtering is correct; weekly boundaries are Monday-based.
- Empty datasets are handled in templates.
- Setup/deployment documentation is strong.

**What is missing**
- No caloric-deficit summary, no charts, no real trend output, no data-driven visualizations.
- No 1,000+ dataset or generator, no performance/stress tests or timings.
- No Data Dictionary, ER diagram, normalization report, physical blueprint, sample data sheet, analytics report, final internship report, API guide, or PDF/DOCX deliverable.
- Archive documentation conflicts with the live schema.

**Next steps:** complete documentation and data/performance work **after** the schema and analytics are finished, so documents describe the final state.

---

# 4. Database Schema Audit

## 4.1 Actual live schema (verified)

### `users` (1 row)
| Column | Type | Null | Key / Rule |
|---|---|---|---|
| `user_id` | `INT UNSIGNED` | NO | PK, AUTO_INCREMENT |
| `full_name` | `VARCHAR(100)` | NO |  |
| `email` | `VARCHAR(150)` | NO | UNIQUE `uq_users_email` |
| `password_hash` | `VARCHAR(255)` | NO | hashed value only |
| `date_of_birth` | `DATE` | YES |  |
| `gender` | `ENUM(Male,Female,Other,Prefer not to say)` | YES |  |
| `height_cm` | `DECIMAL(5,2)` | YES | CHECK > 0 and < 300 |
| `created_at` | `TIMESTAMP` | NO | DEFAULT CURRENT_TIMESTAMP |
| `updated_at` | `TIMESTAMP` | NO | DEFAULT + ON UPDATE CURRENT_TIMESTAMP |

### `workouts` (0 rows)
| Column | Type | Null | Key / Rule |
|---|---|---|---|
| `workout_id` | `INT UNSIGNED` | NO | PK, AUTO_INCREMENT |
| `user_id` | `INT UNSIGNED` | NO | FK to `users.user_id`, CASCADE/CASCADE |
| `exercise_name` | `VARCHAR(100)` | NO | free text |
| `duration_minutes` | `INT UNSIGNED` | NO | CHECK 1–1440 |
| `calories_burned` | `INT UNSIGNED` | YES | CHECK <= 10000 |
| `workout_date` | `DATE` | NO | indexed with user_id |

### `nutrition_logs` (0 rows)
| Column | Type | Null | Key / Rule |
|---|---|---|---|
| `nutrition_id` | `INT UNSIGNED` | NO | PK, AUTO_INCREMENT |
| `user_id` | `INT UNSIGNED` | NO | FK to `users.user_id`, CASCADE/CASCADE |
| `food_name` | `VARCHAR(120)` | NO | free text |
| `meal_type` | `ENUM(Breakfast,Lunch,Dinner,Snack)` | NO |  |
| `calories` | `INT UNSIGNED` | NO | CHECK <= 10000 |
| `protein` | `DECIMAL(6,1)` | YES | CHECK 0–1000 |
| `carbohydrates` | `DECIMAL(6,1)` | YES | CHECK 0–1000 |
| `fat` | `DECIMAL(6,1)` | YES | CHECK 0–1000 |
| `log_date` | `DATE` | NO | indexed with user_id |

### `health_metrics` (0 rows)
| Column | Type | Null | Key / Rule |
|---|---|---|---|
| `metric_id` | `INT UNSIGNED` | NO | PK, AUTO_INCREMENT |
| `user_id` | `INT UNSIGNED` | NO | FK to `users.user_id`, CASCADE/CASCADE |
| `weight` | `DECIMAL(5,2)` | NO | CHECK > 0 and < 500 |
| `height` | `DECIMAL(5,2)` | NO | CHECK > 0 and < 300 |
| `steps` | `INT UNSIGNED` | NO | DEFAULT 0, CHECK <= 200000 |
| `calories_burned` | `INT UNSIGNED` | NO | DEFAULT 0, CHECK <= 10000 |
| `recorded_date` | `DATE` | NO | UNIQUE with user_id |

## 4.2 Constraints summary

| Type | Count | Names |
|---|---:|---|
| PRIMARY KEY | 4 | one per table |
| FOREIGN KEY | 3 | `fk_workouts_user`, `fk_nutrition_user`, `fk_health_user` |
| UNIQUE | 2 | `uq_users_email`, `uq_health_user_date` |
| CHECK | 11 | 4 health, 4 nutrition, 2 workouts, 1 users |
| DEFAULT | 4 | timestamps + steps + calories_burned |

**Referential integrity:** all FKs use `ON DELETE CASCADE ON UPDATE CASCADE`. Deleting a user removes their workouts, nutrition logs, and health records, preventing orphans. Updating a user id cascades. This policy was inspected in live metadata, not executed.

## 4.3 Schema mismatches and structural gaps

| Issue | Severity | Detail |
|---|---|---|
| No `exercises` table | P0 | Exercise is a free-text string, so exercise identity/attributes cannot be managed. |
| No `workout_exercises` table | P0 | One workout cannot contain many exercises; FK protection for exercise/workout children is impossible. |
| No heart-rate/time-based columns | P1 | No HR, zones, or DATETIME samples. |
| `height` duplicated | P2 | `users.height_cm` and `health_metrics.height` can diverge. |
| Free-text food names | P2 | No `foods` lookup; nutrition is usable but not normalized as a reference dataset. |
| Script duplication | P3 | `aiven_init.sql` and `step3_tables.sql` overlap; one should be canonical. |

---

# 5. ER Diagram Audit

## 5.1 Finding

**No ER diagram exists in any format.** A recursive search for `.drawio`, `.mmd`, `.png`, `.jpg`, `.jpeg`, `.pdf`, and `.docx` found no project diagram. The only diagram-like artifact is an ASCII sketch in `docs/archive/DATABASE_DESIGN_v1.md`, which is obsolete.

## 5.2 Comparison against the actual database

| ER requirement | Current state |
|---|---|
| All relevant entities represented | FAIL — no diagram. Required entities: users, workouts, exercises, workout_exercises, nutrition_logs, health_metrics. |
| Primary keys shown | FAIL |
| Foreign keys shown | FAIL |
| Relationships represented | FAIL |
| Cardinality indicated | FAIL |
| Crow's Foot notation | FAIL |
| Matches actual database | FAIL — archive sketch shows five tables (`users`, `workouts`, `daily_wellness`, `goals`, `progress`) that do not exist live. |

## 5.3 Mismatch detail (archive sketch vs live DB)

| Archive entity | Live status |
|---|---|
| `users` | Exists, similar purpose. |
| `workouts` | Exists, but archive columns differ from live. |
| `daily_wellness` | **Does not exist** live. |
| `goals` | **Does not exist** live. |
| `progress` | **Does not exist** live. |
| — | Live `nutrition_logs` and `health_metrics` are absent from the archive sketch. |

**Required action:** after adding `exercises` and `workout_exercises`, draw a single Crow's Foot ER diagram from the live schema and export it as `docs/ER_DIAGRAM.md` plus a PNG or drawio file.

---

# 6. Normalization Audit

## 6.1 First Normal Form (1NF)

**Result: PASS.**

- Every column holds one atomic value: `VARCHAR`, `INT`, `DECIMAL`, `DATE`, `TIMESTAMP`, `ENUM`.
- No arrays, JSON documents, or repeating groups.
- No comma-separated exercise lists: `workouts.exercise_name` is one value per row.
- No multiple foods in one field: `nutrition_logs.food_name` is one item per row; multiple foods are multiple rows.

**Caveat:** 1NF is met literally, but the single `exercise_name` column is the *reason* the many-exercises requirement fails. The correct fix is a junction table, not a delimited string.

## 6.2 Second Normal Form (2NF)

**Result: PASS.**

- Every table has a single-column surrogate primary key.
- There are no composite keys, so there can be no partial dependency.
- Example: in `nutrition_logs`, `protein` depends on the whole row identified by `nutrition_id`, not on part of a key.
- When `workout_exercises` is added with a composite key `(workout_id, exercise_id, set_number)`, attributes such as `reps` and `weight_used` must depend on the whole key. This must be checked at that time.

## 6.3 Third Normal Form (3NF)

**Result: PARTIAL.**

- Within each table, no non-key attribute determines another non-key attribute. For example, `users.email → user_id` is a candidate key direction, not a transitive dependency.
- Cross-table redundancy exists:
  - `users.height_cm` and `health_metrics.height` store the same real-world fact in two places.
  - `workouts.exercise_name` and `nutrition_logs.food_name` are repeated free-text values that a lookup table would normally own.
- `nutrition_logs` stores calories and three macros in one row. This is not a 3NF violation because they are independent measured values, but a derived macro-ratio should be computed, not stored, unless deliberately denormalized.

**Specific examples from the live schema**

| Table | Finding | Normal form impact |
|---|---|---|
| `users` | `height_cm` duplicates `health_metrics.height` | Cross-table redundancy; policy needed. |
| `health_metrics` | `height` repeats on every daily row | Historical snapshot is defensible, but must be documented. |
| `workouts` | `exercise_name` is free text | Lookup entity missing; not strictly a 3NF violation but weak modeling. |
| `nutrition_logs` | `food_name` is free text | Same as above. |
| `health_metrics` | `UNIQUE(user_id, recorded_date)` | Correctly enforces one row per user per day. |

## 6.4 Recommended normalization target

1. `exercises(exercise_id PK, exercise_name UNIQUE, muscle_group, equipment, met_value)`
2. `workout_exercises(workout_id FK, exercise_id FK, set_number, reps, weight_used, duration_seconds, distance_km, PRIMARY KEY(workout_id, exercise_id, set_number))`
3. Optional `foods(food_id PK, food_name UNIQUE, calories_per_100g, protein_per_100g, carbs_per_100g, fat_per_100g)` with `nutrition_logs.food_id` + `quantity_grams`.
4. Decide one source of height: keep `users.height_cm` as current profile and document `health_metrics.height` as a snapshot, or remove the duplicate.

---

# 7. SQL Query Audit

## 7.1 Query catalogue (existing)

| Query | Source | Purpose | Concepts | Executes? | Meaningful result? |
|---|---|---|---|---|---|
| List user workouts | `app/routes/workouts.py` | Show own workouts | SELECT, WHERE user_id, ORDER BY | Yes (inspected/parameterized) | No data (0 rows) |
| Workout totals | `app/routes/dashboard.py` | Count/minutes/calories | COUNT, SUM, COALESCE, WHERE | Yes | Returns zeros for user |
| List nutrition logs | `app/routes/nutrition.py` | Show food entries | SELECT, WHERE, ORDER BY | Yes | 0 rows |
| Nutrition macros | `app/routes/nutrition.py` | Sum calories/protein/carbs/fat | SUM, COALESCE | Yes | 0 rows |
| List health records | `app/routes/health.py` | Weight/steps/BMI | SELECT, calculated BMI, ORDER BY | Yes | 0 rows |
| Health upsert | `app/routes/health.py` | One record per day | INSERT ... ON DUPLICATE KEY UPDATE | Yes | 0 rows |
| Daily workout report | `app/routes/reports.py` | Per-day workout totals | GROUP BY, SUM, COUNT | Yes | 0 rows |
| Daily nutrition report | `app/routes/reports.py` | Per-day macro totals | GROUP BY, SUM | Yes | 0 rows |
| Daily health report | `app/routes/reports.py` | Weight/steps/BMI per day | Calculated column, ORDER BY | Yes | 0 rows |
| Weekly workouts | `app/routes/reports.py` | Monday-based weekly totals | DATE_SUB, WEEKDAY, GROUP BY | Yes | 0 rows |
| Monthly workouts/nutrition/health | `app/routes/reports.py` | Monthly aggregates | DATE_FORMAT, GROUP BY, AVG, SUM | Yes | 0 rows |
| INNER JOIN example | `database/step3_verify.sql` | Users with workouts | INNER JOIN | Yes | 0 rows |
| LEFT JOIN summary | `database/step3_verify.sql` | Per-user child counts | LEFT JOIN, COUNT(DISTINCT) | Yes | 1 row |
| Correlated subquery | `database/step3_verify.sql` | Compare daily calories | Correlated subquery | Yes | 0 rows |

## 7.2 SQL concept coverage

| Concept | Status | Evidence | Gap |
|---|---|---|---|
| CREATE | PASS | DDL scripts | None |
| INSERT | PASS | Sample + app | More data |
| UPDATE | PASS | Edit routes, upsert | None |
| DELETE | PASS | Delete routes | None |
| SELECT | PASS | Everywhere | None |
| INNER JOIN | PASS | `step3_verify.sql` | Not in a documented library |
| LEFT JOIN | PASS | `step3_verify.sql` | Not in a documented library |
| Subqueries | PASS | `step3_verify.sql`, live test | Not in a documented library |
| Aggregates | PASS | `SUM`, `COUNT`, `AVG`, `ROUND`, `COALESCE` | MIN/MAX not required |
| GROUP BY | PASS | Reports | None |
| **HAVING** | **FAIL** | No occurrence in the project | Must add |
| ORDER BY | PASS | Lists/reports | None |
| Indexing | PASS | Composite indexes + EXPLAIN | Document it |

## 7.3 Required SQL queries that are missing

These are not implemented yet. They are listed with purpose, tables, concepts and expected output; do not execute until the audit is approved.

| # | Missing query | Purpose | Tables | Concepts | Expected output |
|---|---|---|---|---|---|
| Q1 | Users averaging more than 2,500 kcal/day | Demonstrate HAVING | `nutrition_logs`, `users` | JOIN, GROUP BY, HAVING, AVG | One row per high-intake user |
| Q2 | Weeks with more than 3 workouts | Demonstrate HAVING on dates | `workouts` | WEEKDAY, GROUP BY, HAVING | Week start + workout count |
| Q3 | Daily/weekly caloric deficit | Deficit summary | `nutrition_logs`, `workouts`, `health_metrics` | JOIN by user/date, SUM, subtraction | Intake, expenditure, deficit per day |
| Q4 | Average workout duration per user/week | Duration analysis | `workouts` | AVG, GROUP BY | Average minutes |
| Q5 | Protein intake vs strength gain | Correlation | `nutrition_logs`, `workouts`, `workout_exercises` | JOIN, GROUP BY, correlation/ratio | Protein intake and load lifted per period |
| Q6 | Total workout calories by period | Confirm existing capability | `workouts` | SUM, GROUP BY | Calories per day/week |
| Q7 | Weight change per period | Weight trend | `health_metrics` | FIRST_VALUE/LAG or self-join | Start/end/delta weight |
| Q8 | BMI trend per period | BMI trend | `health_metrics` | Calculated BMI, ORDER BY date | Chronological BMI series |
| Q9 | Steps weekly totals and averages | Steps analysis | `health_metrics` | SUM, AVG, GROUP BY week | Steps per week |
| Q10 | Health metric trend series | Trend validation | `health_metrics` | ORDER BY, LAG/window | Chronological series |
| Q11 | Macro ratio percentages | Macronutrient ratio | `nutrition_logs` | SUM, ratio arithmetic | Protein/carb/fat % of calories |
| Q12 | Exercise frequency ranking | Exercise analysis | `workout_exercises`, `exercises` | JOIN, COUNT, GROUP BY, ORDER BY | Most frequent exercises |
| Q13 | User activity summary with HAVING | Combined analytics | `users`, `workouts`, `nutrition_logs`, `health_metrics` | Multiple LEFT JOINs, COUNT(DISTINCT), HAVING | Users meeting activity thresholds |

> Window functions (`LAG`, `FIRST_VALUE`) are supported by MySQL 8.4 and are a good fit for trend queries.

---

# 8. Transaction and ACID Audit

## 8.1 Implementation evidence

- `app/db.py` sets `autocommit=False`.
- `get_cursor(commit=True)` calls `db.commit()` on success and `db.rollback()` on exception.
- `execute()` wraps writes through that helper.
- `verify_connection()` and read paths use the same per-request connection.
- `tests/test_live_aiven.py` opens a live connection, starts transactions, and always rolls back in teardown.

## 8.2 ACID assessment

| Property | Status | Evidence | Limitation |
|---|---|---|---|
| Atomicity | PARTIAL | Commit/rollback helper; single-statement writes. | No multi-statement workout+exercises operation exists to prove all-or-nothing behavior. |
| Consistency | PASS | PK/FK/UNIQUE/CHECK/NOT NULL enforce valid state. | Constraint enforcement was inspected, not negatively tested. |
| Isolation | PARTIAL | InnoDB default isolation. | No isolation level configured or concurrency test run. |
| Durability | PASS | InnoDB + commit; Aiven managed persistence. | Crash recovery was not tested. |

## 8.3 What is missing

1. A real multi-row transaction: insert a workout and its exercises together, then commit or roll back as one unit.
2. A forced-failure test: make the second insert invalid and confirm the first insert is rolled back.
3. A recorded live-test run (currently skipped).
4. A short ACID validation document describing boundaries, isolation level, and evidence.

## 8.4 Safe test procedure (recommended later, not executed)

```text
BEGIN;
INSERT INTO workouts (...) VALUES (...);
INSERT INTO workout_exercises (...) VALUES (...);   -- force an invalid FK or CHECK
-- expect failure, then:
ROLLBACK;
SELECT COUNT(*) FROM workouts WHERE workout_id = <new id>;  -- expect 0
```

This must be run only after approval and only inside a transaction that is rolled back.

---

# 9. Analytics Audit

## 9.1 Report-by-report assessment

| Report | Source tables | SQL / aggregation | Output | Works with current records? |
|---|---|---|---|---|
| Dashboard workout totals | `workouts` | `COUNT`, `SUM`, `COALESCE` | Cards | Returns zeros; no data |
| Dashboard nutrition today | `nutrition_logs` | `SUM` by date | Cards | Returns zeros |
| Dashboard latest health | `health_metrics` | Latest row + BMI | Cards | No row |
| Daily workout report | `workouts` | `GROUP BY workout_date` | Table | 0 rows |
| Daily nutrition report | `nutrition_logs` | `GROUP BY log_date`, macro sums | Table | 0 rows |
| Daily health report | `health_metrics` | Per-day select + BMI | Table | 0 rows |
| Weekly workout report | `workouts` | Monday week grouping | Table | 0 rows |
| Monthly workout report | `workouts` | `DATE_FORMAT`, `GROUP BY` | Table | 0 rows |
| Monthly nutrition report | `nutrition_logs` | Monthly calorie sum | Table | 0 rows |
| Monthly health report | `health_metrics` | `AVG` weight/steps/BMI | Table | 0 rows |
| Weight change | `health_metrics` | First/last difference in Python | Value or blank | `None` (needs 2 rows) |
| Caloric deficit | — | **Not implemented** | — | No |
| Strength vs protein | — | **Not implemented** | — | No |
| Average duration | — | **Not implemented** | — | No |
| Charts/trends | — | **Not implemented** | — | No |

## 9.2 Implemented vs template-only

- **Implemented query + template:** daily/weekly/monthly workout, nutrition, health tables and dashboard cards. These are real SQL, not hardcoded.
- **Partial:** weight change, BMI trend, steps summary (SQL aggregates exist; no visualization or data).
- **Template-only or absent:** caloric deficit, strength-vs-protein, average duration, charts, health trend visualizations.
- **No fake data:** no hardcoded dashboard numbers were found.

## 9.3 Why data-dependent analytics cannot currently be demonstrated

The live DB has 1 real user and **0** workout, nutrition, and health rows. Every meaningful aggregate therefore returns 0 or no rows. The SQL is syntactically valid and executes, but the mentor cannot see trends, correlations, deficits, or charts until data is loaded.

## 9.4 Required analytics additions

1. Daily/weekly caloric deficit (`intake − expenditure`) with a clearly defined expenditure source.
2. Average workout duration by user/week/month.
3. Protein intake analysis, including macro-ratio percentages.
4. Strength-vs-protein correlation using `workout_exercises.weight_used`.
5. HAVING-based thresholds (high-intake users, high-frequency weeks).
6. Weight, BMI, steps, and health metric trend series ordered chronologically.
7. Chart.js (or equivalent) visualizations fed by those queries, with empty-state handling.

---

# 10. Dummy Data Audit

## 10.1 Current state

| Table | Live rows | Needed for analytics? |
|---|---:|---|
| `users` | 1 (real) | More synthetic users recommended |
| `workouts` | 0 | Yes |
| `workout_exercises` | table does not exist | Yes, after schema fix |
| `nutrition_logs` | 0 | Yes |
| `health_metrics` | 0 | Yes |
| **Fitness total** | **0** | — |

`database/step3_sample_data.sql` can insert only 3 workouts, 4 nutrition rows, and 3 health rows = **10 child rows**, and only for an existing user. It is not a generator and does not meet 1,000+.

## 10.2 Requirement interpretation

The 1,000+ requirement is **not** satisfied by:
- source-code lines,
- SQL statement counts,
- stale InnoDB `TABLE_ROWS` estimates,
- the 10-row sample script.

It requires either 1,000+ actual rows, a documented 1,000+ dataset, or a tested generator that produces 1,000+ rows.

## 10.3 Recommended dataset (post-approval)

| Table | Suggested rows | Notes |
|---|---:|---|
| `users` | 10 synthetic | Mark with a reserved domain such as `example.test`; keep the real user untouched. |
| `workouts` | 400 | 90–180 days, 2–5 per week per user, realistic durations. |
| `exercises` | 30 | Strength and cardio catalogue. |
| `workout_exercises` | 1,200 | 2–5 exercises per workout, sets/reps/load. |
| `nutrition_logs` | 1,200 | 3–4 meals/day across users. |
| `health_metrics` | 600 | One per user per day; weight, steps, calories. |
| **Total** | **~3,450** | Comfortably exceeds 1,000. |

## 10.4 Generator requirements

- Deterministic seed for reproducibility.
- Inserts inside transactions with rollback on failure.
- Clearly separated synthetic users (reserved email domain) to avoid mixing with the real account.
- Optional `--clean` mode that deletes only synthetic users (cascade removes children).
- Prints a row-count report at the end.
- Never runs automatically from the Flask app.

A suggested new file is `database/generate_dummy_data.py` with a companion `docs/SAMPLE_DATA.md`.

---

# 11. Performance Validation Audit

## 11.1 What exists

- No stress test, load test, benchmark, or timing script.
- No recorded execution times.
- No 1,000+ row dataset.
- `EXPLAIN` was executed during this audit, but the output is not stored in the project.
- `main.js` uses `performance.now()` only for a UI counter animation, not database timing.

## 11.2 EXPLAIN evidence gathered in this audit (read-only)

| Query pattern | Access path | Index used |
|---|---|---|
| Workouts by user + date range | `range` | `idx_workouts_user_date` |
| Nutrition by user + date range | `range` | `idx_nutrition_user_date` |
| Health by user + date range | `index` scan | `uq_health_user_date` |
| Login by email | `const`/unique lookup | `uq_users_email` |

No execution times are claimed here. The audit did not measure wall-clock query duration.

## 11.3 Required performance work

| Test | Dataset | Method | Expected | Actual |
|---|---|---|---|---|
| Daily report query | 1,000+ rows | `EXPLAIN ANALYZE` or Python timing | Under a defined threshold | Not measured |
| Weekly report query | 1,000+ rows | Same | Stable with data growth | Not measured |
| User dashboard totals | 1,000+ rows | Same | Index-assisted | Not measured |
| Nutrition macro aggregation | 1,000+ rows | Same | Index-assisted | Not measured |
| Health trend query | 1,000+ rows | Same | Index-assisted | Not measured |
| Concurrent reads | 10–20 clients | Simple load script | No errors, acceptable latency | Not measured |

**Report format to produce:** query, dataset size, execution time, method, expected result, actual result. Do not invent numbers.

---

# 12. Documentation Audit

## 12.1 Deliverable status

| # | Document | Status | Evidence / gap |
|---|---|---|---|
| 1 | Database Design Document | PARTIAL | `README.md` architecture; archive design is obsolete. Need `docs/DB_DESIGN.md`. |
| 2 | Data Dictionary | FAIL | Missing. Need `docs/DATA_DICTIONARY.md`. |
| 3 | ER Diagram | FAIL | Missing. Need `docs/ER_DIAGRAM.md` + image. |
| 4 | Normalization Report | FAIL | Missing. Need `docs/NORMALIZATION_REPORT.md`. |
| 5 | Physical Schema Blueprint | FAIL | Missing. Need `docs/PHYSICAL_SCHEMA.md`. |
| 6 | SQL source files | PASS | `database/*.sql`. |
| 7 | Sample Data Sheet | FAIL | Missing. Need `docs/SAMPLE_DATA.md`. |
| 8 | Sample Analytics Reports | FAIL | Missing. Need `docs/ANALYTICS_REPORTS.md`. |
| 9 | Database Schema Documentation | PARTIAL | `README.md`, `docs/STEP3_TABLES.md`; incomplete and partly local-MySQL oriented. Need `docs/SCHEMA_REFERENCE.md`. |
| 10 | Final Internship Project Report | FAIL | No file. Need a written report. |
| 11 | API Integration Guide | FAIL | No API and no guide. Add or document scope exclusion. |
| 12 | Setup and Deployment Instructions | PASS | `README.md`, `.env.example`, `certs/README.md`. |

## 12.2 Accuracy and consistency problems

- `docs/archive/DATABASE_DESIGN_v1.md` describes five tables that do not exist live (`daily_wellness`, `goals`, `progress`). It must not be presented as current.
- `docs/archive/PHASE1_SETUP_v1.md` and `docs/archive/STEP1_DATABASE_auto.md` describe a local MySQL install and a different schema.
- `docs/STEP3_TABLES.md` references MySQL Workbench "Fitness Local", which conflicts with the Aiven-only architecture.
- `README.md` matches the Aiven implementation better than the archive docs.
- No document currently contains a complete, accurate data dictionary or ER model.

## 12.3 Final report format

No `.pdf`, `.doc`, or `.docx` exists. The mentor-requested portable final report is **missing**. It must be produced after the implementation and documentation are finalized.

## 12.4 Recommended document outlines

| File | Suggested contents |
|---|---|
| `docs/DB_DESIGN.md` | Purpose, scope, architecture, entities, relationships, design decisions. |
| `docs/DATA_DICTIONARY.md` | Every table, column, type, nullability, default, key, constraint, description, units. |
| `docs/ER_DIAGRAM.md` | Crow's Foot diagram, entity list, PK/FK table, cardinality table. |
| `docs/NORMALIZATION_REPORT.md` | 1NF/2NF/3NF analysis with live examples and the planned junction table. |
| `docs/PHYSICAL_SCHEMA.md` | Logical→physical mapping, engines, charsets, indexes, storage, cascade policy. |
| `docs/SCHEMA_REFERENCE.md` | Live `SHOW CREATE TABLE` equivalents, constraints, indexes. |
| `docs/SAMPLE_DATA.md` | Generator command, seed, row counts, date ranges, synthetic-user policy. |
| `docs/ANALYTICS_REPORTS.md` | Each report: source tables, SQL, aggregation, sample output. |
| `docs/LOGIC_FLOW.md` | High-level logic/data-flow diagram and module interactions. |
| `docs/API_INTEGRATION_GUIDE.md` | Only if an API is added; otherwise a scope statement. |
| Final report `.pdf`/`.docx` | Compiled internship report referencing the above. |

---

# 13. Security Audit

## 13.1 Findings

| Check | Status | Evidence |
|---|---|---|
| Database connection configuration | PASS | `config.py` reads env vars; strict validation; no fallback. |
| Environment variables | PASS | `.env` gitignored; `.env.example` has placeholders only. |
| Database password handling | PASS | Never logged; sourced from env; not in source. |
| `SECRET_KEY` configuration | PASS | Required from env; validated; no hardcoded secret found. |
| SSL/TLS configuration | PASS | `app/db.py` requires TLS; `/db-check` shows TLS 1.3 cipher. |
| Certificate verification | PASS | `ssl_verify_cert=True`, `ssl_verify_identity=True`; `/db-check` shows `ssl_verified: true`. |
| SQL injection prevention | PASS | Parameterized queries with `%s` throughout; no string-built user SQL found. |
| Password hashing | PASS | Werkzeug hash/check; no plaintext storage. |
| User authorization | PASS | `login_required` on protected routes; `user_id` scoping and ownership checks. |
| Git ignore configuration | PASS | `.env`, `certs/*.pem`, venv and caches ignored. |
| Exposure of `.env` | PASS | Ignored; not committed. |
| Exposure of database certificates | PASS | `certs/*.pem` ignored. |
| Exposure of credentials in source | PASS | No hardcoded host/user/password/key found. |
| CSRF protection | PASS | Token on all POST forms; `validate_csrf()` enforced. |
| Security headers | PASS | `test_security_headers_are_present` passes. |
| Error handling | PASS | DB errors mapped to safe user-facing pages; no raw credentials shown. |
| Aiven-only connection | PASS | No SQLite/local MySQL/JSON/CSV storage code path. |

## 13.2 Notes and residual risks

- The audit did not attempt login or any authenticated write, so authorization was verified by code inspection, not by live session testing.
- No secrets are reproduced in this report.
- `.env` and `certs/ca.pem` must never be committed; the ignore rules are correct.
- No API keys or third-party tokens were found.
- The application does not expose a public API, which reduces attack surface but leaves the API guide deliverable missing.

**Security verdict:** no critical security defect was found in the inspected code. The security posture is a strength of the project.

---

# 14. Critical Missing Requirements

## P0 — Critical (blocking mentor evaluation)

| # | Missing requirement | Evidence | Why it blocks |
|---|---|---|---|
| P0-1 | No `exercises` entity | No table/route/template; `workouts.exercise_name` is free text (M1-04). | Exercise identification and details are a core Milestone 1 entity. |
| P0-2 | No `workout_exercises` relationship | No junction table; one workout cannot hold many exercises (M1-23, M1-26, M2-27). | Directly violates “One Workout → Many Exercises” and blocks the transaction example. |
| P0-3 | Live DB has 0 fitness records | `workouts=0`, `nutrition_logs=0`, `health_metrics=0`. | No report, trend, or correlation can be demonstrated. |
| P0-4 | No 1,000+ dataset or generator | Only a 10-row manual sample SQL (M4-25, M4-26). | Milestone 4 explicitly requires 1,000+ entries or a tested generator. |
| P0-5 | No ER diagram / Crow's Foot | No diagram file; archive sketch is obsolete (M2-01 to M2-08). | A named Milestone 2 deliverable is entirely absent. |
| P0-6 | No Data Dictionary or Normalization Report | Files absent (M1-30, M2-37). | Required Milestone 1/2 deliverables. |
| P0-7 | No heart rate, zones, or time-based metrics | No columns/table/docs (M1-18 to M1-20, M1-34, M1-35). | Core wellness data requested by the mentor is not modeled. |

## P1 — High

| # | Missing requirement | Evidence |
|---|---|---|
| P1-1 | No `HAVING` query | Full-project search found none (M3-28). |
| P1-2 | No strength-vs-protein correlation | No strength metric or correlation SQL (M3-35, M3-43). |
| P1-3 | No caloric deficit summary | Reports show intake/outtake separately only (M3-36, M4-02). |
| P1-4 | No average workout duration query | No `AVG(duration_minutes)` (M3-37). |
| P1-5 | No visualizations | No chart/canvas library or graph output (M4-03, M4-19, M4-22). |
| P1-6 | No performance/stress tests or timings | No test scripts, no measured times (M4-36 to M4-42). |
| P1-7 | No final internship report / PDF | No `.pdf`, `.doc`, `.docx` (M4-60, M4-63). |
| P1-8 | No multi-row transaction or ACID validation | No workout+exercises insert; live test skipped (M3-45, M3-51, M3-52, M3-74). |
| P1-9 | No Physical Schema Blueprint / PK-FK-constraint docs | Files absent (M2-38 to M2-40, M4-55). |

## P2 — Medium

| # | Missing requirement | Evidence |
|---|---|---|
| P2-1 | No sample data sheet or sample analytics report | Files absent (M4-57, M4-58). |
| P2-2 | No API integration guide | No API and no guide (M4-61). |
| P2-3 | Height duplicated across tables | `users.height_cm` vs `health_metrics.height` (M2-14, M2-34). |
| P2-4 | Food names not normalized | Free-text `food_name`; no `foods` table (M1-05, M2-14). |
| P2-5 | No macronutrient ratio | Macros stored as grams only; no ratio query/doc (M1-35, M3-34). |
| P2-6 | Stale archive documentation | Five-table design conflicts with live schema (M4-64). |

## P3 — Low

| # | Missing requirement | Evidence |
|---|---|---|
| P3-1 | Duplicate DDL scripts | `aiven_init.sql` and `step3_tables.sql` overlap. |
| P3-2 | README lacks links to design deliverables | No links to ER/data dictionary/etc. |
| P3-3 | Presentation polish | Report formatting, screenshots, and sample outputs need final assembly. |

---

# 15. Exact Files That Need Attention

## 15.1 Existing files to modify

| File | Current implementation | Problem | Required change |
|---|---|---|---|
| `database/aiven_init.sql` | Four tables with constraints | Missing `exercises`, `workout_exercises`, HR/time fields; height duplication | Add the new tables/columns after approval; keep idempotent `IF NOT EXISTS`. |
| `database/step3_tables.sql` | Duplicate child-table DDL | Overlaps `aiven_init.sql`; can drift | Retire or reduce to a pointer to the canonical script. |
| `database/step3_sample_data.sql` | 10 manual child rows | Far below 1,000; not idempotent for workouts/nutrition | Keep as a tiny demo or replace with generator output. |
| `database/step3_verify.sql` | Metadata + basic JOIN/subquery checks | No HAVING, deficit, duration, correlation | Extend with the missing queries or point to a new analytics library. |
| `app/routes/workouts.py` | Single `exercise_name` CRUD | Cannot insert multiple exercises transactionally | Add multi-exercise insert/update inside one transaction. |
| `app/templates/workouts/form.html` | Single exercise field | No repeated exercise rows | Add dynamic exercise rows/subform. |
| `app/routes/health.py` | Weight/height/steps/calories | No HR/time fields | Add HR/time inputs only if in scope. |
| `app/routes/nutrition.py` | Free-text food + macros | No food lookup or macro ratio | Optionally add `foods` reference and ratio calculation. |
| `app/routes/reports.py` | Daily/weekly/monthly tables | Missing deficit, avg duration, protein ratio, trends, correlation | Add queries and context values. |
| `app/templates/reports/index.html` | Table-only reports | No charts | Add Chart.js canvases and empty states. |
| `app/static/js/main.js` | UI animation only | No chart code | Add a chart module or separate `charts.js`. |
| `README.md` | Good setup docs | Does not link the missing deliverables; archive confusion | Update schema section and add documentation index. |
| `docs/STEP3_TABLES.md` | Partial table guide | References local MySQL Workbench "Fitness Local" | Correct to Aiven-only and mark as historical if superseded. |
| `docs/archive/*` | Old five-table/local designs | Conflicts with live schema | Move to an `archive/` note that explicitly says obsolete. |
| `tests/test_smoke.py` | 30 offline tests | Does not assert the new schema/relationships | Add tests for `exercises`, `workout_exercises`, new queries. |
| `tests/test_live_aiven.py` | Rollback-only live tests | Does not test workout+exercises transaction | Add multi-row rollback test. |

## 15.2 New files required

| New file | Why it is necessary |
|---|---|
| `database/analytics_queries.sql` | Central library for HAVING, deficit, duration, correlation, trends. |
| `database/generate_dummy_data.py` | Deterministic 1,000+ row generator. |
| `tests/performance_test.py` (or `database/performance_tests.sql`) | Query timing/load evidence. |
| `docs/DATA_DICTIONARY.md` | Milestone 1 deliverable. |
| `docs/LOGIC_FLOW.md` | Milestone 1 deliverable. |
| `docs/ER_DIAGRAM.md` + `.png`/`.drawio` | Milestone 2 deliverable. |
| `docs/NORMALIZATION_REPORT.md` | Milestone 2 deliverable. |
| `docs/PHYSICAL_SCHEMA.md` | Milestone 2 deliverable. |
| `docs/SCHEMA_REFERENCE.md` | Schema/PK/FK/constraint documentation. |
| `docs/DB_DESIGN.md` | Current design document. |
| `docs/SAMPLE_DATA.md` | Sample data sheet. |
| `docs/ANALYTICS_REPORTS.md` | Sample analytics outputs. |
| `docs/API_INTEGRATION_GUIDE.md` | Only if an API is added; otherwise a scope note. |
| Final internship report `.pdf`/`.docx` | Mentor-required portable report. |

> No required file should be created until the audit is approved.

---

# 16. Recommended Implementation Order

The order respects database dependencies: design → schema → application → data → analytics → validation → documentation.

## Milestone 1 & 2 — Design first

1. **Confirm scope** with the mentor: heart rate/zones, time-based metrics, food lookup, and whether an API is required.
2. **Finalize the logical model**: `users`, `exercises`, `workouts`, `workout_exercises`, `nutrition_logs`, `health_metrics`, optional `foods`, optional `heart_rate_samples`.
3. **Write the ER diagram** in Crow's Foot with PKs, FKs, and cardinalities.
4. **Write the Data Dictionary** for every table/column/type/constraint.
5. **Write the Normalization Report** (1NF/2NF/3NF with live examples and the new junction table).
6. **Write the Physical Schema Blueprint** (engines, charsets, indexes, cascade policy).
7. **Write the Logic Flow Diagram** showing Users → Activities/Workouts → Nutrition → BioMetrics → Reports.

## Milestone 3 — Schema and application

8. **Add schema changes**: `exercises`, `workout_exercises`, HR/time fields, and resolve the height duplication.
9. **Apply the schema to Aiven** only after approval and a backup/verification step.
10. **Update workout CRUD** to insert a workout plus multiple exercises inside one transaction.
11. **Add missing queries** to `database/analytics_queries.sql`: HAVING, deficit, average duration, protein ratio, correlation, trends.
12. **Update reports and dashboard** to call the new queries.
13. **Add live transaction tests**, including forced failure and rollback.

## Milestone 4 — Data, analytics, validation, documentation

14. **Build the dummy-data generator** and load 1,000+ realistic rows across multiple users.
15. **Validate data accuracy**: BMI, units, date boundaries, duplicate counting, user filtering.
16. **Add visualizations** (Chart.js or equivalent) fed only by real query results.
17. **Run performance tests** on 1,000+ rows and record query, dataset size, time, method, expected, actual.
18. **Run constraint tests** inside transactions (negative weight/calories/steps, duplicate email, invalid FK) and roll back.
19. **Write the remaining documents**: schema reference, sample data sheet, analytics reports, database design.
20. **Update `README.md`** and link every deliverable; mark `docs/archive/` as obsolete.
21. **Compile the final internship report** and export it to PDF/DOCX.
22. **Run the full readiness checklist** and fix only verified failures.

---

# 17. Final Mentor Readiness Checklist

| # | Requirement | Current status | What needs to be done | How to verify completion |
|---:|---|---|---|---|
| 1 | Users entity | PASS | None | `SHOW CREATE TABLE users;` |
| 2 | Exercises entity | FAIL | Create `exercises` table and CRUD or seed catalogue | `SHOW TABLES LIKE 'exercises';` |
| 3 | One Workout → Many Exercises | FAIL | Create `workout_exercises` with FKs | `SHOW CREATE TABLE workout_exercises;` |
| 4 | Workout performance details | PARTIAL | Add sets/reps/weight/duration/distance | Column check + sample row |
| 5 | Nutrition logs | PASS | None | `COUNT(*)` and table check |
| 6 | Health metrics | PASS | None | `COUNT(*)` and table check |
| 7 | Heart rate / zones / time-based metrics | FAIL | Add fields/table or get scope exclusion | Schema check + documentation |
| 8 | Data Dictionary | FAIL | Write `docs/DATA_DICTIONARY.md` | File review |
| 9 | Logic Flow Diagram | FAIL | Write `docs/LOGIC_FLOW.md` | File review |
| 10 | ER Diagram with Crow's Foot | FAIL | Draw and export from live schema | Diagram review against `SHOW CREATE TABLE` |
| 11 | Normalization Report | FAIL | Write 1NF/2NF/3NF analysis | File review |
| 12 | Physical Schema Blueprint | FAIL | Write `docs/PHYSICAL_SCHEMA.md` | File review |
| 13 | PK/FK/constraint documentation | PARTIAL | Add consolidated tables | File review |
| 14 | MySQL implementation | PASS | None | `/db-check` + live metadata |
| 15 | DDL/DML scripts | PASS | Keep one canonical DDL | Script review and execution |
| 16 | JOINs, subqueries, aggregates | PASS | None | Run examples |
| 17 | HAVING query | FAIL | Add to analytics library | Query executes and returns rows |
| 18 | Caloric deficit summary | FAIL | Add query + report section | Report shows deficit |
| 19 | Average workout duration | FAIL | Add `AVG(duration_minutes)` | Query output |
| 20 | Strength vs protein correlation | FAIL | Add strength metric + query | Query output with real data |
| 21 | Weight/BMI/steps/health trends | PARTIAL | Add chronological series + charts | Chart renders from DB |
| 22 | Visualizations | FAIL | Add Chart.js with real data | Screenshot + network/data check |
| 23 | Transactions / ACID | PARTIAL | Add multi-row transaction + tests | Rollback test output |
| 24 | Indexes + EXPLAIN | PASS | Document the evidence | Performance report |
| 25 | 1,000+ dataset | FAIL | Build generator and load data | `SELECT COUNT(*)` totals |
| 26 | Multiple users/workouts/nutrition/health | FAIL | Generate synthetic data | Counts per table |
| 27 | Performance tests | FAIL | Run and record timings | Performance report table |
| 28 | Sample Data Sheet | FAIL | Write `docs/SAMPLE_DATA.md` | File review |
| 29 | Sample Analytics Reports | FAIL | Write `docs/ANALYTICS_REPORTS.md` | File review |
| 30 | Database Design Document | PARTIAL | Write `docs/DB_DESIGN.md` | File review |
| 31 | Setup/Deployment Instructions | PASS | None | Follow README from scratch |
| 32 | API Integration Guide | FAIL | Write guide or scope exclusion | File review |
| 33 | Final report PDF/DOCX | FAIL | Compile and export | Open the file |
| 34 | Documentation matches implementation | PARTIAL | Fix archive/local references | Cross-check docs vs schema |
| 35 | Security (TLS, secrets, parameterization) | PASS | None | `/db-check`, code review |
| 36 | User ownership / authorization | PASS | Re-verify after changes | Route tests |

---

# 18. Overall Completion Percentage

## 18.1 Calculation

```text
Completion = PASS requirements / Total applicable requirements × 100
           = 105 / 220 × 100
           = 47.7272...%
           ≈ 47.7%
```

## 18.2 Breakdown

| Metric | Count |
|---|---:|
| Total requirements | 221 |
| PASS | **105** |
| PARTIAL | **51** |
| FAIL | **64** |
| NOT VERIFIED | **0** |
| NOT APPLICABLE | **1** |
| Applicable requirements | **220** |
| **Overall completion** | **47.7%** |

## 18.3 Milestone percentages

| Milestone | Applicable | PASS | Completion |
|---|---:|---:|---:|
| M1 — Entity Identification & Logic Mapping | 43 | 18 | **41.9%** |
| M2 — ER Diagramming & Schema Normalization | 40 | 22 | **55.0%** |
| M3 — Relational Implementation & Query Engineering | 74 | 47 | **63.5%** |
| M4 — Analytics, Validation & Final Documentation | 63 | 18 | **28.6%** |
| **Overall** | **220** | **105** | **47.7%** |

## 18.4 Interpretation

- The **implementation foundation is solid** (M3 63.5%): MySQL, schema, constraints, indexes, CRUD, JOINs, aggregates, transactions, and security are real and verified.
- The **documentation and analytics layers are the weakest** (M4 28.6%): no data, no charts, no performance evidence, and most named documents are absent.
- **Milestone 1/2 deliverables** (ER diagram, data dictionary, logic flow, normalization report) are largely missing even though the underlying schema is reasonable.
- The project is **not ready for mentor review** until at least the P0 items are resolved.

> This percentage measures requirement-checklist coverage only. It is not a quality score, and PARTIAL/FAIL items are not counted as complete.

---

# Appendix A — Required SQL Queries (summary)

The detailed list is in Section 7.3. In short, add these to `database/analytics_queries.sql`:

1. `HAVING` threshold query (users averaging > 2,500 kcal/day).
2. `HAVING` frequency query (weeks with > 3 workouts).
3. Caloric deficit (`SUM(intake) − SUM(expenditure)` per user/day).
4. Average workout duration (`AVG(duration_minutes)` by period).
5. Strength vs protein correlation (requires `workout_exercises.weight_used`).
6. Protein intake and macro-ratio percentages.
7. Weight change per period (first/last or `LAG`).
8. BMI trend series (chronological).
9. Steps weekly totals/averages.
10. Health metric trend series.
11. Exercise frequency ranking.
12. Combined user activity summary with `HAVING`.

Each query must be run against real data and its output captured in `docs/ANALYTICS_REPORTS.md`.

---

# Appendix B — Required Database Changes (summary)

Do **not** execute these until the audit is approved.

## B.1 New table: `exercises`

```text
exercise_id     INT UNSIGNED PK AUTO_INCREMENT
exercise_name   VARCHAR(100) NOT NULL UNIQUE
muscle_group    VARCHAR(50) NULL
equipment       VARCHAR(50) NULL
met_value       DECIMAL(4,2) NULL
created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

Purpose: make exercises first-class entities and remove free-text exercise identity.

## B.2 New table: `workout_exercises`

```text
workout_id       INT UNSIGNED NOT NULL  FK -> workouts.workout_id  ON DELETE CASCADE
exercise_id      INT UNSIGNED NOT NULL  FK -> exercises.exercise_id ON DELETE RESTRICT
set_number       INT UNSIGNED NOT NULL
reps             INT UNSIGNED NULL
weight_used      DECIMAL(6,2) NULL
duration_seconds INT UNSIGNED NULL
distance_km      DECIMAL(6,2) NULL
calories_burned  INT UNSIGNED NULL
PRIMARY KEY (workout_id, exercise_id, set_number)
```

Purpose: implement One Workout → Many Exercises and enable strength/performance analytics. The composite PK must be justified in the normalization report.

## B.3 Heart-rate / time-based support (if in scope)

Option A — extend `health_metrics`:

```text
resting_heart_rate  INT UNSIGNED NULL
avg_heart_rate      INT UNSIGNED NULL
max_heart_rate      INT UNSIGNED NULL
recorded_at         DATETIME NULL
```

Option B — dedicated samples table:

```text
heart_rate_id  INT UNSIGNED PK AUTO_INCREMENT
user_id        INT UNSIGNED FK -> users.user_id
recorded_at    DATETIME NOT NULL
bpm            INT UNSIGNED NOT NULL
zone_name      VARCHAR(20) NULL
```

Add CHECK constraints for plausible ranges (for example, bpm 20–250) and an index on `(user_id, recorded_at)`.

## B.4 Optional `foods` lookup

```text
food_id            INT UNSIGNED PK
food_name          VARCHAR(120) NOT NULL UNIQUE
calories_per_100g  INT UNSIGNED NOT NULL
protein_per_100g   DECIMAL(6,1) NULL
carbs_per_100g     DECIMAL(6,1) NULL
fat_per_100g       DECIMAL(6,1) NULL
```

Then add `nutrition_logs.food_id` and `quantity_grams`, or keep free text if the mentor accepts it.

## B.5 Height policy

Choose one:
- Keep `users.height_cm` as the current profile value and document `health_metrics.height` as a historical snapshot; or
- Remove `health_metrics.height` and join to `users.height_cm` in BMI queries.

Either choice must be documented and tested for consistency.

---

# Appendix C — Audit Evidence Commands (read-only)

These commands were used or are safe to repeat; they do not write data.

```text
-- Live metadata
SELECT table_name FROM information_schema.tables WHERE table_schema = DATABASE();
SELECT table_name, column_name, column_type, is_nullable, column_default
FROM information_schema.columns WHERE table_schema = DATABASE();
SELECT * FROM information_schema.table_constraints WHERE table_schema = DATABASE();
SELECT * FROM information_schema.check_constraints WHERE constraint_schema = DATABASE();
SELECT * FROM information_schema.statistics WHERE table_schema = DATABASE();

-- Counts
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM workouts;
SELECT COUNT(*) FROM nutrition_logs;
SELECT COUNT(*) FROM health_metrics;

-- Access paths
EXPLAIN SELECT workout_id FROM workouts
 WHERE user_id = ? AND workout_date BETWEEN ? AND ? ORDER BY workout_date DESC;
```

```text
-- Application verification
python -m unittest discover -s tests -v
python check_db.py
```

---

**End of audit report.** No project file, schema, or row was modified during this audit. Awaiting explicit approval before any implementation or data changes.
