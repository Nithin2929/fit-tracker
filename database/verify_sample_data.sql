-- ============================================================================
-- FitTrack - verify the generated sample dataset
-- File: database/verify_sample_data.sql
--
-- PURPOSE
--   Read-only validation of database/sample_data.sql after it has been loaded
--   into a SEPARATE test/sample/dev database.
--
-- PREREQUISITES
--   - The test database has aiven_init.sql applied.
--   - migration_exercises.sql, migration_heart_rate.sql, and
--     migration_nutrition_time.sql have been applied there.
--   - sample_data.sql has been loaded there.
--
-- SAFETY
--   Every statement is a SELECT. Nothing is inserted, updated, deleted, or
--   dropped. Do not run this against production expecting sample rows; the
--   counts will simply be lower and the PASS/FAIL checks still work.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. Row counts
-- ----------------------------------------------------------------------------
SELECT 'users' AS table_name, COUNT(*) AS rows_loaded,
       CASE WHEN COUNT(*) >= 30 THEN 'PASS' ELSE 'FAIL' END AS expected
FROM users
UNION ALL
SELECT 'exercises', COUNT(*),
       CASE WHEN COUNT(*) >= 24 THEN 'PASS' ELSE 'FAIL' END
FROM exercises
UNION ALL
SELECT 'workouts', COUNT(*),
       CASE WHEN COUNT(*) >= 720 THEN 'PASS' ELSE 'FAIL' END
FROM workouts
UNION ALL
SELECT 'workout_exercises', COUNT(*),
       CASE WHEN COUNT(*) >= 1300 THEN 'PASS' ELSE 'FAIL' END
FROM workout_exercises
UNION ALL
SELECT 'nutrition_logs', COUNT(*),
       CASE WHEN COUNT(*) >= 1200 THEN 'PASS' ELSE 'FAIL' END
FROM nutrition_logs
UNION ALL
SELECT 'health_metrics', COUNT(*),
       CASE WHEN COUNT(*) >= 900 THEN 'PASS' ELSE 'FAIL' END
FROM health_metrics
UNION ALL
SELECT 'heart_rate_samples', COUNT(*),
       CASE WHEN COUNT(*) >= 360 THEN 'PASS' ELSE 'FAIL' END
FROM heart_rate_samples;

-- Total must exceed the mentor's 1,000-record requirement.
SELECT COUNT(*) AS total_sample_records,
       CASE WHEN COUNT(*) >= 1000 THEN 'PASS' ELSE 'FAIL' END AS requirement_1000
FROM (
    SELECT user_id AS id FROM users
    UNION ALL SELECT exercise_id FROM exercises
    UNION ALL SELECT workout_id FROM workouts
    UNION ALL SELECT workout_exercise_id FROM workout_exercises
    UNION ALL SELECT nutrition_id FROM nutrition_logs
    UNION ALL SELECT metric_id FROM health_metrics
    UNION ALL SELECT sample_id FROM heart_rate_samples
) AS all_sample_rows;

-- ----------------------------------------------------------------------------
-- 2. Foreign-key integrity: every orphan count must be 0
-- ----------------------------------------------------------------------------
SELECT 'workouts_with_unknown_user' AS check_name, COUNT(*) AS violations,
       CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END AS result
FROM workouts AS w
LEFT JOIN users AS u ON u.user_id = w.user_id
WHERE u.user_id IS NULL
UNION ALL
SELECT 'nutrition_with_unknown_user', COUNT(*),
       CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END
FROM nutrition_logs AS n
LEFT JOIN users AS u ON u.user_id = n.user_id
WHERE u.user_id IS NULL
UNION ALL
SELECT 'health_with_unknown_user', COUNT(*),
       CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END
FROM health_metrics AS h
LEFT JOIN users AS u ON u.user_id = h.user_id
WHERE u.user_id IS NULL
UNION ALL
SELECT 'junction_with_unknown_workout', COUNT(*),
       CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END
FROM workout_exercises AS we
LEFT JOIN workouts AS w ON w.workout_id = we.workout_id
WHERE w.workout_id IS NULL
UNION ALL
SELECT 'junction_with_unknown_exercise', COUNT(*),
       CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END
FROM workout_exercises AS we
LEFT JOIN exercises AS e ON e.exercise_id = we.exercise_id
WHERE e.exercise_id IS NULL
UNION ALL
SELECT 'samples_with_unknown_user', COUNT(*),
       CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END
FROM heart_rate_samples AS s
LEFT JOIN users AS u ON u.user_id = s.user_id
WHERE u.user_id IS NULL
UNION ALL
SELECT 'samples_with_unknown_zone', COUNT(*),
       CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END
FROM heart_rate_samples AS s
LEFT JOIN heart_rate_zones AS z ON z.zone_id = s.zone_id
WHERE s.zone_id IS NOT NULL AND z.zone_id IS NULL;

-- ----------------------------------------------------------------------------
-- 3. Duplicate checks
-- ----------------------------------------------------------------------------
SELECT 'duplicate_user_emails' AS check_name, COUNT(*) AS violations,
       CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END AS result
FROM (
    SELECT email FROM users GROUP BY email HAVING COUNT(*) > 1
) AS duplicates
UNION ALL
SELECT 'duplicate_exercise_names', COUNT(*),
       CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END
FROM (
    SELECT exercise_name FROM exercises GROUP BY exercise_name HAVING COUNT(*) > 1
) AS duplicates
UNION ALL
SELECT 'duplicate_health_user_date', COUNT(*),
       CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END
FROM (
    SELECT user_id, recorded_date FROM health_metrics
    GROUP BY user_id, recorded_date HAVING COUNT(*) > 1
) AS duplicates
UNION ALL
SELECT 'duplicate_workout_exercise_order', COUNT(*),
       CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END
FROM (
    SELECT workout_id, exercise_order FROM workout_exercises
    GROUP BY workout_id, exercise_order HAVING COUNT(*) > 1
) AS duplicates;

-- No workout should be without at least one exercise line in this dataset.
SELECT 'workouts_without_exercise_lines' AS check_name, COUNT(*) AS violations,
       CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END AS result
FROM workouts AS w
LEFT JOIN workout_exercises AS we ON we.workout_id = w.workout_id
WHERE we.workout_exercise_id IS NULL;

-- ----------------------------------------------------------------------------
-- 4. Invalid-value checks: every violation count must be 0
-- ----------------------------------------------------------------------------
SELECT 'invalid_workout_duration' AS check_name, COUNT(*) AS violations,
       CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END AS result
FROM workouts
WHERE duration_minutes <= 0 OR duration_minutes > 1440
UNION ALL
SELECT 'invalid_workout_calories', COUNT(*),
       CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END
FROM workouts
WHERE calories_burned IS NOT NULL
  AND (calories_burned < 0 OR calories_burned > 10000)
UNION ALL
SELECT 'invalid_nutrition_calories', COUNT(*),
       CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END
FROM nutrition_logs
WHERE calories > 10000
UNION ALL
SELECT 'invalid_macros', COUNT(*),
       CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END
FROM nutrition_logs
WHERE (protein IS NOT NULL AND (protein < 0 OR protein > 1000))
   OR (carbohydrates IS NOT NULL AND (carbohydrates < 0 OR carbohydrates > 1000))
   OR (fat IS NOT NULL AND (fat < 0 OR fat > 1000))
UNION ALL
SELECT 'invalid_health_weight_or_height', COUNT(*),
       CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END
FROM health_metrics
WHERE weight <= 0 OR weight >= 500 OR height <= 0 OR height >= 300
UNION ALL
SELECT 'invalid_health_steps', COUNT(*),
       CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END
FROM health_metrics
WHERE steps > 200000
UNION ALL
SELECT 'invalid_health_calories', COUNT(*),
       CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END
FROM health_metrics
WHERE calories_burned > 10000
UNION ALL
SELECT 'invalid_exercise_sets_reps', COUNT(*),
       CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END
FROM workout_exercises
WHERE (sets IS NOT NULL AND (sets < 1 OR sets > 100))
   OR (repetitions IS NOT NULL AND (repetitions < 1 OR repetitions > 1000))
UNION ALL
SELECT 'invalid_exercise_weight', COUNT(*),
       CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END
FROM workout_exercises
WHERE weight_kg IS NOT NULL AND (weight_kg < 0 OR weight_kg > 1000)
UNION ALL
SELECT 'invalid_heart_rate_bpm', COUNT(*),
       CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END
FROM heart_rate_samples
WHERE heart_rate_bpm < 20 OR heart_rate_bpm > 250;

-- ----------------------------------------------------------------------------
-- 5. Realistic date ranges
-- ----------------------------------------------------------------------------
SELECT 'future_workout_dates' AS check_name, COUNT(*) AS violations,
       CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END AS result
FROM workouts WHERE workout_date > CURDATE()
UNION ALL
SELECT 'future_nutrition_dates', COUNT(*),
       CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END
FROM nutrition_logs WHERE log_date > CURDATE()
UNION ALL
SELECT 'future_health_dates', COUNT(*),
       CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END
FROM health_metrics WHERE recorded_date > CURDATE()
UNION ALL
SELECT 'future_heart_rate_samples', COUNT(*),
       CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END
FROM heart_rate_samples WHERE recorded_at > NOW();

SELECT MIN(workout_date) AS first_workout,
       MAX(workout_date) AS last_workout,
       MIN(log_date) AS first_nutrition,
       MAX(log_date) AS last_nutrition,
       MIN(recorded_date) AS first_health,
       MAX(recorded_date) AS last_health
FROM workouts, nutrition_logs, health_metrics;

-- ----------------------------------------------------------------------------
-- 6. Analytics suitability
-- ----------------------------------------------------------------------------
SELECT COUNT(DISTINCT user_id) AS users_with_workouts,
       COUNT(DISTINCT workout_date) AS distinct_workout_days,
       ROUND(AVG(duration_minutes), 1) AS average_duration,
       SUM(calories_burned) AS total_calories
FROM workouts;

SELECT COUNT(DISTINCT user_id) AS users_with_nutrition,
       COUNT(DISTINCT log_date) AS distinct_nutrition_days,
       SUM(calories) AS total_calories,
       ROUND(SUM(protein), 1) AS total_protein
FROM nutrition_logs;

SELECT COUNT(DISTINCT user_id) AS users_with_health,
       COUNT(DISTINCT recorded_date) AS distinct_health_days,
       ROUND(AVG(weight), 1) AS average_weight,
       ROUND(AVG(steps), 0) AS average_steps
FROM health_metrics;

-- ----------------------------------------------------------------------------
-- 7. Compact PASS/FAIL summary
-- ----------------------------------------------------------------------------
SELECT 'FK integrity' AS area,
       CASE WHEN (
           SELECT COUNT(*) FROM workouts w
           LEFT JOIN users u ON u.user_id = w.user_id
           WHERE u.user_id IS NULL
       ) = 0 THEN 'PASS' ELSE 'FAIL' END AS result
UNION ALL
SELECT 'Duplicate emails',
       CASE WHEN (SELECT COUNT(*) FROM (
           SELECT email FROM users GROUP BY email HAVING COUNT(*) > 1
       ) d) = 0 THEN 'PASS' ELSE 'FAIL' END
UNION ALL
SELECT 'Health daily uniqueness',
       CASE WHEN (SELECT COUNT(*) FROM (
           SELECT user_id, recorded_date FROM health_metrics
           GROUP BY user_id, recorded_date HAVING COUNT(*) > 1
       ) d) = 0 THEN 'PASS' ELSE 'FAIL' END
UNION ALL
SELECT 'Non-negative / bounded values',
       CASE WHEN (
           SELECT COUNT(*) FROM workouts
           WHERE duration_minutes <= 0 OR duration_minutes > 1440
       ) = 0 THEN 'PASS' ELSE 'FAIL' END
UNION ALL
SELECT 'Heart-rate bounds',
       CASE WHEN (
           SELECT COUNT(*) FROM heart_rate_samples
           WHERE heart_rate_bpm < 20 OR heart_rate_bpm > 250
       ) = 0 THEN 'PASS' ELSE 'FAIL' END
UNION ALL
SELECT '1,000+ records',
       CASE WHEN (
           (SELECT COUNT(*) FROM users)
         + (SELECT COUNT(*) FROM exercises)
         + (SELECT COUNT(*) FROM workouts)
         + (SELECT COUNT(*) FROM workout_exercises)
         + (SELECT COUNT(*) FROM nutrition_logs)
         + (SELECT COUNT(*) FROM health_metrics)
         + (SELECT COUNT(*) FROM heart_rate_samples)
       ) >= 1000 THEN 'PASS' ELSE 'FAIL' END;
