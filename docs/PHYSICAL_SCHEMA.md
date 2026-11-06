# FitTrack — Physical Schema Blueprint (Milestone 2)

**Project:** FitTrack — Fitness & Wellness Tracking Database System  
**DBMS:** Aiven Cloud MySQL `8.4.11`  
**Database:** `fitness_wellness_db`  
**Engine:** InnoDB, `utf8mb4`, `utf8mb4_unicode_ci` (all tables)  
**Evidence:** live `information_schema` metadata and `database/aiven_init.sql`.

> **Implementation status:** Sections 2–5 describe the four **live** tables and are verified. Sections 6–9 describe **proposed** tables/columns. They do **not** exist in Aiven until the draft migrations are approved and executed.

---

## 1. Physical design conventions

| Convention | Value |
|---|---|
| Storage engine | InnoDB (transactions, FKs, row-level locking) |
| Character set / collation | `utf8mb4` / `utf8mb4_unicode_ci` |
| Surrogate keys | `INT UNSIGNED AUTO_INCREMENT` |
| Timestamps | `TIMESTAMP` with `CURRENT_TIMESTAMP`; `DATETIME` for explicit readings |
| Money/measurements | `DECIMAL` (never `FLOAT`) for weight, height, macros, load |
| Boolean-like flags | none needed |
| FK delete policy | `CASCADE` for user-owned data; `RESTRICT` for reusable reference data; `SET NULL` for optional classification |
| FK update policy | `ON UPDATE CASCADE` throughout |

---

## 2. `users` (existing)

**Purpose:** account and profile identity.  
**Rows:** live user accounts only.  
**Primary key:** `user_id`.

| Column | Type | Null | Default | Key / constraint |
|---|---|---|---|---|
| `user_id` | `INT UNSIGNED` | No | `AUTO_INCREMENT` | PK |
| `full_name` | `VARCHAR(100)` | No | — | — |
| `email` | `VARCHAR(150)` | No | — | `uq_users_email` UNIQUE |
| `password_hash` | `VARCHAR(255)` | No | — | — |
| `date_of_birth` | `DATE` | Yes | `NULL` | — |
| `gender` | `ENUM('Male','Female','Other','Prefer not to say')` | Yes | `NULL` | — |
| `height_cm` | `DECIMAL(5,2)` | Yes | `NULL` | `chk_users_height_cm`: `NULL OR (height_cm > 0 AND height_cm < 300)` |
| `created_at` | `TIMESTAMP` | No | `CURRENT_TIMESTAMP` | — |
| `updated_at` | `TIMESTAMP` | No | `CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP` | — |

**Indexes:** `PRIMARY (user_id)`, `uq_users_email (email)`.

---

## 3. `workouts` (existing)

**Purpose:** one workout session per row. `exercise_name` is a legacy single-exercise label.

| Column | Type | Null | Default | Key / constraint |
|---|---|---|---|---|
| `workout_id` | `INT UNSIGNED` | No | `AUTO_INCREMENT` | PK |
| `user_id` | `INT UNSIGNED` | No | — | FK → `users.user_id` |
| `exercise_name` | `VARCHAR(100)` | No | — | Legacy free-text label |
| `duration_minutes` | `INT UNSIGNED` | No | — | `chk_workouts_duration`: `> 0 AND <= 1440` |
| `calories_burned` | `INT UNSIGNED` | Yes | `NULL` | `chk_workouts_calories`: `NULL OR <= 10000` |
| `workout_date` | `DATE` | No | — | — |

**FK:** `fk_workouts_user` → `users.user_id` `ON DELETE CASCADE ON UPDATE CASCADE`.  
**Indexes:** `PRIMARY (workout_id)`, `idx_workouts_user_date (user_id, workout_date)`.

---

## 4. `nutrition_logs` (existing)

**Purpose:** one food item per row, with energy and macronutrient grams.

| Column | Type | Null | Default | Key / constraint |
|---|---|---|---|---|
| `nutrition_id` | `INT UNSIGNED` | No | `AUTO_INCREMENT` | PK |
| `user_id` | `INT UNSIGNED` | No | — | FK → `users.user_id` |
| `food_name` | `VARCHAR(120)` | No | — | — |
| `meal_type` | `ENUM('Breakfast','Lunch','Dinner','Snack')` | No | — | — |
| `calories` | `INT UNSIGNED` | No | — | `chk_nutrition_calories`: `<= 10000` |
| `protein` | `DECIMAL(6,1)` | Yes | `NULL` | `chk_nutrition_protein`: `NULL OR 0..1000` |
| `carbohydrates` | `DECIMAL(6,1)` | Yes | `NULL` | `chk_nutrition_carbohydrates`: `NULL OR 0..1000` |
| `fat` | `DECIMAL(6,1)` | Yes | `NULL` | `chk_nutrition_fat`: `NULL OR 0..1000` |
| `log_date` | `DATE` | No | — | — |

**FK:** `fk_nutrition_user` → `users.user_id` `ON DELETE CASCADE ON UPDATE CASCADE`.  
**Indexes:** `PRIMARY (nutrition_id)`, `idx_nutrition_user_date (user_id, log_date)`.

**Proposed addition:** `logged_at DATETIME NULL` after `log_date` plus `idx_nutrition_user_time (user_id, logged_at)`. See `database/migration_nutrition_time.sql`. Existing rows keep `NULL`.

---

## 5. `health_metrics` (existing)

**Purpose:** one daily snapshot per user. BMI is derived, not stored.

| Column | Type | Null | Default | Key / constraint |
|---|---|---|---|---|
| `metric_id` | `INT UNSIGNED` | No | `AUTO_INCREMENT` | PK |
| `user_id` | `INT UNSIGNED` | No | — | FK → `users.user_id` |
| `weight` | `DECIMAL(5,2)` | No | — | `chk_health_weight`: `> 0 AND < 500` |
| `height` | `DECIMAL(5,2)` | No | — | `chk_health_height`: `> 0 AND < 300` |
| `steps` | `INT UNSIGNED` | No | `0` | `chk_health_steps`: `<= 200000` |
| `calories_burned` | `INT UNSIGNED` | No | `0` | `chk_health_calories_burned`: `<= 10000` |
| `recorded_date` | `DATE` | No | — | `uq_health_user_date (user_id, recorded_date)` |

**Unique rule:** `uq_health_user_date (user_id, recorded_date)` → at most one record per user per day.  
**FK:** `fk_health_user` → `users.user_id` `ON DELETE CASCADE ON UPDATE CASCADE`.  
**Indexes:** `PRIMARY (metric_id)`, `uq_health_user_date (user_id, recorded_date)`.

**BMI expression used by the application:**

```text
ROUND(weight / ((height / 100) * (height / 100)), 1)
```

---

## 6. `exercises` (proposed)

**Migration:** `database/migration_exercises.sql`  
**Status:** not applied.

| Column | Type | Null | Default | Key / constraint |
|---|---|---|---|---|
| `exercise_id` | `INT UNSIGNED` | No | `AUTO_INCREMENT` | PK |
| `exercise_name` | `VARCHAR(100)` | No | — | `uq_exercises_name` UNIQUE |
| `muscle_group` | `VARCHAR(50)` | Yes | `NULL` | — |
| `exercise_type` | `ENUM('Strength','Cardio','Flexibility','Balance','Other')` | No | `'Other'` | — |
| `description` | `VARCHAR(500)` | Yes | `NULL` | — |
| `created_at` | `TIMESTAMP` | No | `CURRENT_TIMESTAMP` | — |

**Indexes:** `PRIMARY (exercise_id)`, `uq_exercises_name (exercise_name)`.

---

## 7. `workout_exercises` (proposed)

**Migration:** `database/migration_exercises.sql`  
**Status:** not applied.

| Column | Type | Null | Default | Key / constraint |
|---|---|---|---|---|
| `workout_exercise_id` | `INT UNSIGNED` | No | `AUTO_INCREMENT` | PK |
| `workout_id` | `INT UNSIGNED` | No | — | FK → `workouts.workout_id` |
| `exercise_id` | `INT UNSIGNED` | No | — | FK → `exercises.exercise_id` |
| `exercise_order` | `INT UNSIGNED` | No | `1` | `uq_we_workout_order (workout_id, exercise_order)` |
| `sets` | `INT UNSIGNED` | Yes | `NULL` | `chk_we_sets`: `NULL OR 1..100` |
| `repetitions` | `INT UNSIGNED` | Yes | `NULL` | `chk_we_repetitions`: `NULL OR 1..1000` |
| `weight_kg` | `DECIMAL(6,2)` | Yes | `NULL` | `chk_we_weight`: `NULL OR 0..1000` |
| `duration_minutes` | `INT UNSIGNED` | Yes | `NULL` | `chk_we_duration`: `NULL OR 1..1440` |
| `calories_burned` | `INT UNSIGNED` | Yes | `NULL` | `chk_we_calories`: `NULL OR <= 10000` |

**FKs:**

- `fk_we_workout` → `workouts.workout_id` `ON DELETE CASCADE ON UPDATE CASCADE`.
- `fk_we_exercise` → `exercises.exercise_id` `ON DELETE RESTRICT ON UPDATE CASCADE`.

**Indexes:** `PRIMARY (workout_exercise_id)`, `uq_we_workout_order (workout_id, exercise_order)`, `idx_we_exercise (exercise_id)`.

**Why `ON DELETE RESTRICT` for exercises:** deleting a catalogue item that appears in history would make past sessions meaningless. The application refuses the delete and asks the user to keep the exercise.

---

## 8. `heart_rate_zones` (proposed)

**Migration:** `database/migration_heart_rate.sql`  
**Status:** not applied. Seeded with five shared zones.

| Column | Type | Null | Default | Key / constraint |
|---|---|---|---|---|
| `zone_id` | `INT UNSIGNED` | No | `AUTO_INCREMENT` | PK |
| `zone_name` | `VARCHAR(20)` | No | — | `uq_hr_zone_name` UNIQUE |
| `minimum_percentage` | `DECIMAL(5,2)` | No | — | `chk_hr_zone_order` |
| `maximum_percentage` | `DECIMAL(5,2)` | No | — | `chk_hr_zone_order` |

**Check:** `0 <= minimum_percentage < maximum_percentage <= 100`.

**Seed data:** Zone 1 `0–50`, Zone 2 `50–60`, Zone 3 `60–70`, Zone 4 `70–80`, Zone 5 `80–100`.

---

## 9. `heart_rate_samples` (proposed)

**Migration:** `database/migration_heart_rate.sql`  
**Status:** not applied. The table starts empty; no readings are invented.

| Column | Type | Null | Default | Key / constraint |
|---|---|---|---|---|
| `sample_id` | `INT UNSIGNED` | No | `AUTO_INCREMENT` | PK |
| `user_id` | `INT UNSIGNED` | No | — | FK → `users.user_id` |
| `zone_id` | `INT UNSIGNED` | Yes | `NULL` | FK → `heart_rate_zones.zone_id` |
| `heart_rate_bpm` | `SMALLINT UNSIGNED` | No | — | `chk_hr_bpm`: `20..250` |
| `recorded_at` | `DATETIME` | No | — | — |

**FKs:**

- `fk_hr_sample_user` → `users.user_id` `ON DELETE CASCADE ON UPDATE CASCADE`.
- `fk_hr_sample_zone` → `heart_rate_zones.zone_id` `ON DELETE SET NULL ON UPDATE CASCADE`.

**Indexes:** `PRIMARY (sample_id)`, `idx_hr_user_time (user_id, recorded_at)`, `idx_hr_zone (zone_id)`.

**Zone resolution:** `estimated_max_hr = 220 - age` (age from `date_of_birth`), else `190`. `percentage = bpm / estimated_max_hr * 100`. The zone whose `[minimum_percentage, maximum_percentage)` contains the percentage is stored. This is a convenience denormalization; the application recomputes it on every write.

---

## 10. Relationship summary

| Parent | Child | FK column | Delete rule | Status |
|---|---|---|---|---|
| `users` | `workouts` | `workouts.user_id` | CASCADE | Existing |
| `users` | `nutrition_logs` | `nutrition_logs.user_id` | CASCADE | Existing |
| `users` | `health_metrics` | `health_metrics.user_id` | CASCADE | Existing |
| `workouts` | `workout_exercises` | `workout_exercises.workout_id` | CASCADE | Proposed |
| `exercises` | `workout_exercises` | `workout_exercises.exercise_id` | RESTRICT | Proposed |
| `users` | `heart_rate_samples` | `heart_rate_samples.user_id` | CASCADE | Proposed |
| `heart_rate_zones` | `heart_rate_samples` | `heart_rate_samples.zone_id` | SET NULL | Proposed |

---

## 11. Required migrations

| Order | File | Creates / changes | Safe to re-run? | Executed? |
|---:|---|---|---|---|
| 1 | `database/migration_exercises.sql` | `exercises`, `workout_exercises`, catalogue seed, legacy backfill | Yes | **No** |
| 2 | `database/migration_heart_rate.sql` | `heart_rate_zones`, `heart_rate_samples`, zone seed | Yes | **No** |
| 3 | `database/migration_nutrition_time.sql` | nullable `nutrition_logs.logged_at` + index | Yes (information_schema guard) | **No** |

**Execution rule:** review each file, take a backup/snapshot, then run in order with the Aiven admin user. Do not run against production until the design is approved. The application detects missing tables/columns at runtime and shows a "migration required" notice instead of failing.

---

## 12. Verification queries (read-only)

```sql
-- Tables
SELECT table_name
FROM information_schema.tables
WHERE table_schema = DATABASE()
ORDER BY table_name;

-- Columns for one table
SELECT column_name, column_type, is_nullable, column_default, column_key, extra
FROM information_schema.columns
WHERE table_schema = DATABASE() AND table_name = 'workout_exercises'
ORDER BY ordinal_position;

-- FKs
SELECT constraint_name, table_name, column_name,
       referenced_table_name, referenced_column_name
FROM information_schema.key_column_usage
WHERE table_schema = DATABASE()
  AND referenced_table_name IS NOT NULL
ORDER BY table_name, constraint_name;

-- CHECK constraints
SELECT constraint_name, check_clause
FROM information_schema.check_constraints
WHERE constraint_schema = DATABASE()
ORDER BY constraint_name;

-- Indexes
SELECT table_name, index_name, column_name, non_unique
FROM information_schema.statistics
WHERE table_schema = DATABASE()
ORDER BY table_name, index_name, seq_in_index;
```

The full verification workbook is `database/verify_project_database.sql`.
