-- ============================================================================
-- Fitness & Wellness Tracking Database System
-- File:    database/verify.sql
-- Purpose: Check that Step 1 created the database and four tables correctly.
--
-- Run after database/schema.sql in MySQL Workbench:
--   File > Open SQL Script > database/verify.sql
--   Click the lightning bolt (Execute).
--
-- The final section inserts temporary test rows inside a transaction and then
-- ROLLBACKs them. No test user or activity is left in the database.
-- ============================================================================

USE fitness_wellness_db;

-- ----------------------------------------------------------------------------
-- 1. Tables
-- Expected: health_metrics, nutrition_logs, users, workouts
-- ----------------------------------------------------------------------------
SELECT '1. TABLES' AS section;

SELECT table_name, engine, table_collation
FROM information_schema.tables
WHERE table_schema = DATABASE()
ORDER BY table_name;

-- ----------------------------------------------------------------------------
-- 2. Columns and data types
-- ----------------------------------------------------------------------------
SELECT '2. COLUMNS' AS section;

SELECT table_name, column_name, column_type,
       is_nullable, column_key, column_default, extra
FROM information_schema.columns
WHERE table_schema = DATABASE()
ORDER BY table_name, ordinal_position;

-- ----------------------------------------------------------------------------
-- 3. Foreign keys
-- Expected: workouts, nutrition_logs, and health_metrics point to users.
-- ----------------------------------------------------------------------------
SELECT '3. FOREIGN KEYS' AS section;

SELECT table_name, constraint_name, column_name,
       referenced_table_name, referenced_column_name
FROM information_schema.key_column_usage
WHERE table_schema = DATABASE()
  AND referenced_table_name IS NOT NULL
ORDER BY table_name, constraint_name;

-- ----------------------------------------------------------------------------
-- 4. Unique constraints
-- Expected: users.email and health_metrics(user_id, record_date).
-- ----------------------------------------------------------------------------
SELECT '4. UNIQUE CONSTRAINTS' AS section;

SELECT table_name, constraint_name
FROM information_schema.table_constraints
WHERE table_schema = DATABASE()
  AND constraint_type = 'UNIQUE'
ORDER BY table_name, constraint_name;

-- ----------------------------------------------------------------------------
-- 5. CHECK constraints
-- ----------------------------------------------------------------------------
SELECT '5. CHECK CONSTRAINTS' AS section;

SELECT tc.table_name, tc.constraint_name, cc.check_clause
FROM information_schema.table_constraints AS tc
JOIN information_schema.check_constraints AS cc
  ON cc.constraint_schema = tc.constraint_schema
 AND cc.constraint_name = tc.constraint_name
WHERE tc.table_schema = DATABASE()
  AND tc.constraint_type = 'CHECK'
ORDER BY tc.table_name, tc.constraint_name;

-- ----------------------------------------------------------------------------
-- 6. Relationship and BMI smoke test
-- Inserts one linked row into every table, reads it back, calculates BMI,
-- then rolls everything back.
-- ----------------------------------------------------------------------------
SELECT '6. RELATIONSHIP AND BMI TEST (temporary, rolled back)' AS section;

START TRANSACTION;

INSERT INTO users
    (full_name, email, password_hash, height_cm)
VALUES
    ('Step 1 Test', 'step1-test@example.invalid', 'temporary-test-hash', 170.00);

SET @test_user_id = LAST_INSERT_ID();

INSERT INTO workouts
    (user_id, workout_type, duration_minutes, calories_burned, workout_date)
VALUES
    (@test_user_id, 'Walking', 30, 120, CURDATE());

INSERT INTO nutrition_logs
    (user_id, log_date, meal_type, food_name, servings, calories, protein_g)
VALUES
    (@test_user_id, CURDATE(), 'Breakfast', 'Oats with milk', 1.00, 250, 9.0);

INSERT INTO health_metrics
    (user_id, record_date, weight_kg, steps, body_fat_percentage)
VALUES
    (@test_user_id, CURDATE(), 70.50, 8000, 18.0);

SELECT
    u.user_id,
    u.full_name,
    u.height_cm,
    w.workout_type,
    w.duration_minutes,
    n.meal_type,
    n.food_name,
    n.calories AS calories_consumed,
    h.weight_kg,
    h.steps,
    ROUND(h.weight_kg / ((u.height_cm / 100) * (u.height_cm / 100)), 2) AS bmi
FROM users AS u
JOIN workouts AS w       ON w.user_id = u.user_id
JOIN nutrition_logs AS n ON n.user_id = u.user_id
JOIN health_metrics AS h ON h.user_id = u.user_id
WHERE u.user_id = @test_user_id;

ROLLBACK;

SELECT 'Smoke test rolled back - no test data was saved.' AS result;

SELECT COUNT(*) AS test_user_rows_after_rollback
FROM users
WHERE email = 'step1-test@example.invalid';
