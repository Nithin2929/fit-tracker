-- ============================================================================
-- Fitness & Wellness Tracking Database System
-- File:    database/verify.sql
-- Purpose: Check that the Phase 1 schema was created correctly.
--
-- Run after database/schema.sql:
--   Get-Content .\database\verify.sql -Raw | mysql -u root -p --default-character-set=utf8mb4
--
-- The last section inserts temporary rows inside a transaction and then
-- ROLLBACKs them. No test user or test activity is left in the database.
-- ============================================================================

USE fitness_wellness_db;

-- ----------------------------------------------------------------------------
-- 1. Tables and storage engine
-- ----------------------------------------------------------------------------
SELECT '1. TABLES' AS section;

SELECT table_name, engine, table_collation
FROM information_schema.tables
WHERE table_schema = DATABASE()
ORDER BY table_name;

-- ----------------------------------------------------------------------------
-- 2. Columns, data types, nullability, keys
-- ----------------------------------------------------------------------------
SELECT '2. COLUMNS' AS section;

SELECT table_name, column_name, column_type,
       is_nullable, column_key, column_default, extra
FROM information_schema.columns
WHERE table_schema = DATABASE()
ORDER BY table_name, ordinal_position;

-- ----------------------------------------------------------------------------
-- 3. Foreign keys (relationships)
-- Expected: workouts, daily_wellness, goals, progress each point to users.
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
-- Expected: users.email, daily_wellness(user_id, log_date),
--           progress(user_id, record_date).
-- ----------------------------------------------------------------------------
SELECT '4. UNIQUE CONSTRAINTS' AS section;

SELECT table_name, constraint_name
FROM information_schema.table_constraints
WHERE table_schema = DATABASE()
  AND constraint_type = 'UNIQUE'
ORDER BY table_name, constraint_name;

-- ----------------------------------------------------------------------------
-- 5. CHECK constraints
-- These protect the data even if a bug slips through the Python code.
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
-- 6. Relationship smoke test
-- Inserts one linked row into every table, reads it back with JOINs,
-- then rolls everything back. This proves the foreign keys work.
-- ----------------------------------------------------------------------------
SELECT '6. RELATIONSHIP SMOKE TEST (temporary, rolled back)' AS section;

START TRANSACTION;

INSERT INTO users (full_name, email, password_hash)
VALUES ('Phase 1 Schema Test', 'phase1-test@example.invalid', 'temporary-test-hash');

SET @test_user_id = LAST_INSERT_ID();

INSERT INTO workouts
    (user_id, workout_type, duration_minutes, calories_burned, workout_date)
VALUES
    (@test_user_id, 'Walking', 30, 120, CURDATE());

INSERT INTO daily_wellness
    (user_id, log_date, water_intake_ml, sleep_hours, steps)
VALUES
    (@test_user_id, CURDATE(), 2000, 7.5, 8000);

INSERT INTO goals
    (user_id, goal_title, goal_type, target_value, unit, start_date, target_date)
VALUES
    (@test_user_id, 'Walk 10,000 steps', 'Steps', 10000, 'steps',
     CURDATE(), DATE_ADD(CURDATE(), INTERVAL 30 DAY));

INSERT INTO progress
    (user_id, record_date, weight_kg, body_fat_percentage)
VALUES
    (@test_user_id, CURDATE(), 70.50, 18.0);

SELECT
    u.user_id,
    u.email,
    w.workout_type,
    d.water_intake_ml,
    d.sleep_hours,
    d.steps,
    g.goal_title,
    p.weight_kg
FROM users AS u
JOIN workouts AS w       ON w.user_id = u.user_id
JOIN daily_wellness AS d ON d.user_id = u.user_id
JOIN goals AS g          ON g.user_id = u.user_id
JOIN progress AS p       ON p.user_id = u.user_id
WHERE u.user_id = @test_user_id;

ROLLBACK;

SELECT 'Smoke test rolled back - no test data was saved.' AS result;

SELECT COUNT(*) AS test_user_rows_after_rollback
FROM users
WHERE email = 'phase1-test@example.invalid';
