# Fitness & Wellness Tracking Database System

A Flask + MySQL web application for tracking user profiles, workouts, nutrition,
weight, BMI, calories, steps, and fitness reports.

> **Current status: Step 3 — creating the workout, nutrition, and health tables.**
> Your `users` table and the `fitness_wellness_db` database already exist.

---

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | HTML5, CSS3, vanilla JavaScript |
| Backend | Python 3.12, Flask |
| Database | MySQL 8.4, InnoDB, `utf8mb4` |
| DB driver | `mysql-connector-python` |
| DB tool | MySQL Workbench |
| Editor | Visual Studio Code |

---

## Current database

Database: **`fitness_wellness_db`**

| Table | Status | Purpose |
|---|---|---|
| `users` | Already created by you | User profile and login details |
| `workouts` | Step 3 | Workout sessions and calories burned |
| `nutrition_logs` | Step 3 | Food entries and macronutrients |
| `health_metrics` | Step 3 | Daily weight, height, steps, calories burned |

Relationships:

```text
users 1 ───< workouts
users 1 ───< nutrition_logs
users 1 ───< health_metrics
```

Each child table uses `user_id` as a foreign key to `users.user_id`.

---

## Step 3 files

```text
E:\ictproject\
└── database\
    ├── step3_tables.sql       # creates the three new tables
    ├── step3_sample_data.sql  # inserts sample workouts/food/health records
    ├── step3_verify.sql       # checks keys, constraints, joins, BMI
    └── app_user.sql           # optional limited MySQL account for Flask
```

The earlier auto-generated schema files are in `database\archive\` for
reference. Do not run them for this step.

Full instructions:

```text
E:\ictproject\docs\STEP3_TABLES.md
```

---

## How to run Step 3

### 1. Check the `user_id` type

In MySQL Workbench:

```sql
USE fitness_wellness_db;
SHOW CREATE TABLE users;
```

If `user_id` is `int unsigned`, change the three `user_id` lines in
`database\step3_tables.sql` to `INT UNSIGNED`.

### 2. Create the tables

Open and run:

```text
E:\ictproject\database\step3_tables.sql
```

Expected message:

```text
Step 3 tables created successfully.
```

### 3. Add sample data

Open and run:

```text
E:\ictproject\database\step3_sample_data.sql
```

### 4. Verify

Open and run:

```text
E:\ictproject\database\step3_verify.sql
```

Expected:

- four tables: `users`, `workouts`, `nutrition_logs`, `health_metrics`
- three foreign keys
- sample workouts, nutrition logs, and health records
- BMI values around `23.02`, `23.12`, and `23.18`

---

## Useful queries

```sql
USE fitness_wellness_db;

SELECT * FROM users;
SELECT * FROM workouts;
SELECT * FROM nutrition_logs;
SELECT * FROM health_metrics;
```

Workout JOIN:

```sql
SELECT u.full_name, w.exercise_name, w.duration_minutes,
       w.calories_burned, w.workout_date
FROM users AS u
JOIN workouts AS w ON w.user_id = u.user_id
ORDER BY w.workout_date DESC;
```

BMI:

```sql
SELECT u.full_name, h.recorded_date, h.weight, h.height,
       ROUND(h.weight / ((h.height / 100) * (h.height / 100)), 2) AS bmi
FROM users AS u
JOIN health_metrics AS h ON h.user_id = u.user_id
ORDER BY h.recorded_date DESC;
```

---

## Development roadmap

- [x] **Step 1** — Project folder and MySQL database
- [x] **Step 2** — `users` table and first sample user
- [x] **Step 3** — Workouts, nutrition logs, health metrics
- [ ] **Step 4** — Connect Flask to MySQL
- [ ] **Step 5** — Registration and login
- [ ] **Step 6** — Dashboard
- [ ] **Step 7** — Workout tracking module
- [ ] **Step 8** — Nutrition tracking module
- [ ] **Step 9** — Health metrics and BMI module
- [ ] **Step 10** — Daily, weekly, monthly reports
- [ ] **Step 11** — Testing and final improvements

---

## Important notes

- Do not create another database or project folder.
- Use only `E:\ictproject` and `fitness_wellness_db`.
- Passwords must be hashed before real registration is implemented.
- Every Flask query will use `%s` placeholders, not string concatenation.
- Keep `.env` out of Git; use `.env.example` as the template.

---

## Author

College industry project — Fitness & Wellness Tracking Database System.
"# fitnesstrack" 
