-- ============================================================================
-- Fitness & Wellness Tracking Database System
-- File:    database/step3_verify.sql
-- Purpose: Check the three Step 3 tables and display sample results.
--
-- AIVEN:
--   Run this against the online Aiven database after database/aiven_init.sql.
--   It only reads metadata and rows; it never changes data.
-- ============================================================================

USE fitness_wellness_db;

-- ----------------------------------------------------------------------------
-- 1. Tables in the database
-- Expected: health_metrics, nutrition_logs, users, workouts
-- ----------------------------------------------------------------------------
SELECT '1. TABLES' AS section;

SHOW TABLES;

-- ----------------------------------------------------------------------------
-- 2. Columns in each Step 3 table
-- ----------------------------------------------------------------------------
SELECT '2. COLUMNS' AS section;

SELECT table_name, column_name, column_type, is_nullable, column_key
FROM information_schema.columns
WHERE table_schema = DATABASE()
  AND table_name IN ('workouts', 'nutrition_logs', 'health_metrics')
ORDER BY table_name, ordinal_position;

-- ----------------------------------------------------------------------------
-- 3. Foreign keys
-- Expected: three relationships, all pointing to users.user_id
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
-- Expected: health_metrics uq_health_user_date
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
-- 6. View the sample records
-- ----------------------------------------------------------------------------
SELECT '6. WORKOUTS' AS section;
SELECT * FROM workouts ORDER BY workout_date DESC, workout_id DESC;

SELECT '7. NUTRITION LOGS' AS section;
SELECT * FROM nutrition_logs ORDER BY log_date DESC, nutrition_id DESC;

SELECT '8. HEALTH METRICS' AS section;
SELECT * FROM health_metrics ORDER BY recorded_date DESC, metric_id DESC;

-- ----------------------------------------------------------------------------
-- 7. JOIN query: user + workouts
-- ----------------------------------------------------------------------------
SELECT '9. USER AND WORKOUT JOIN' AS section;

SELECT
    u.user_id,
    u.full_name,
    w.exercise_name,
    w.duration_minutes,
    w.calories_burned,
    w.workout_date
FROM users AS u
JOIN workouts AS w ON w.user_id = u.user_id
ORDER BY w.workout_date DESC, w.workout_id DESC;

-- ----------------------------------------------------------------------------
-- 8. JOIN query: user + nutrition
-- ----------------------------------------------------------------------------
SELECT '10. USER AND NUTRITION JOIN' AS section;

SELECT
    u.user_id,
    u.full_name,
    n.food_name,
    n.meal_type,
    n.calories,
    n.protein,
    n.carbohydrates,
    n.fat,
    n.log_date
FROM users AS u
JOIN nutrition_logs AS n ON n.user_id = u.user_id
ORDER BY n.log_date DESC, n.nutrition_id DESC;

-- ----------------------------------------------------------------------------
-- 9. BMI calculation
-- BMI = weight / ((height / 100) * (height / 100))
-- ----------------------------------------------------------------------------
SELECT '11. BMI CALCULATION' AS section;

SELECT
    u.full_name,
    h.recorded_date,
    h.weight,
    h.height,
    ROUND(h.weight / ((h.height / 100) * (h.height / 100)), 2) AS bmi
FROM users AS u
JOIN health_metrics AS h ON h.user_id = u.user_id
ORDER BY h.recorded_date DESC;

-- ----------------------------------------------------------------------------
-- 10. Daily summary with aggregate functions
-- Subqueries prevent workout and food rows from multiplying each other.
-- ----------------------------------------------------------------------------
SELECT '12. DAILY SUMMARY' AS section;

SELECT
    h.recorded_date,
    h.weight,
    h.height,
    ROUND(h.weight / ((h.height / 100) * (h.height / 100)), 2) AS bmi,
    h.steps,
    h.calories_burned,
    (
        SELECT COALESCE(SUM(w.calories_burned), 0)
        FROM workouts AS w
        WHERE w.user_id = h.user_id
          AND w.workout_date = h.recorded_date
    ) AS workout_calories,
    (
        SELECT COALESCE(SUM(n.calories), 0)
        FROM nutrition_logs AS n
        WHERE n.user_id = h.user_id
          AND n.log_date = h.recorded_date
    ) AS food_calories
FROM health_metrics AS h
WHERE h.user_id = (SELECT user_id FROM users ORDER BY user_id LIMIT 1)
ORDER BY h.recorded_date DESC;

-- ----------------------------------------------------------------------------
-- 11. Row counts
-- ----------------------------------------------------------------------------
SELECT '13. ROW COUNTS' AS section;

SELECT 'users' AS table_name, COUNT(*) AS row_count FROM users
UNION ALL
SELECT 'workouts', COUNT(*) FROM workouts
UNION ALL
SELECT 'nutrition_logs', COUNT(*) FROM nutrition_logs
UNION ALL
SELECT 'health_metrics', COUNT(*) FROM health_metrics;
