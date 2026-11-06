-- ============================================================================
-- Fitness & Wellness Tracking Database System
-- File:    database/step3_sample_data.sql
-- Purpose: OPTIONAL sample workouts, nutrition entries, and health metrics
--          for the first user in your existing users table.
--
-- IMPORTANT:
--   This is a manual demo script only. The Flask application never loads this
--   file and never invents sample data. Dashboard and reports show only what
--   real users insert through the app.
--
-- AIVEN:
--   Run AFTER database/aiven_init.sql and after at least one real account has
--   been registered (or inserted) in the Aiven database.
--   Run it once; workouts and food entries have no daily unique rule, so a
--   second run creates duplicates. Health metrics update the same day instead.
-- ============================================================================

USE fitness_wellness_db;

-- Pick the first existing user. This avoids hard-coding a user_id.
-- If this returns NULL, register an account in FitTrack first.
SET @user_id = (SELECT user_id FROM users ORDER BY user_id LIMIT 1);

SELECT @user_id AS sample_user_id;


-- ----------------------------------------------------------------------------
-- Sample workouts
-- ----------------------------------------------------------------------------
INSERT INTO workouts
    (user_id, exercise_name, duration_minutes, calories_burned, workout_date)
VALUES
    (@user_id, 'Running',         30, 250, CURDATE()),
    (@user_id, 'Weight Training', 45, 300, DATE_SUB(CURDATE(), INTERVAL 1 DAY)),
    (@user_id, 'Cycling',         60, 400, DATE_SUB(CURDATE(), INTERVAL 2 DAY));


-- ----------------------------------------------------------------------------
-- Sample nutrition logs
-- protein, carbohydrates, and fat are measured in grams.
-- ----------------------------------------------------------------------------
INSERT INTO nutrition_logs
    (user_id, food_name, meal_type, calories, protein, carbohydrates, fat, log_date)
VALUES
    (@user_id, 'Oats with milk',       'Breakfast', 300, 12.0, 45.0, 6.0,  CURDATE()),
    (@user_id, 'Rice with chicken',    'Lunch',     550, 35.0, 60.0, 15.0, CURDATE()),
    (@user_id, 'Apple',                'Snack',      95, 0.5,  25.0, 0.3,  CURDATE()),
    (@user_id, 'Roti with vegetables', 'Dinner',    400, 12.0, 55.0, 10.0, DATE_SUB(CURDATE(), INTERVAL 1 DAY));


-- ----------------------------------------------------------------------------
-- Sample health metrics
-- One row per day. These three dates do not conflict with each other.
-- ----------------------------------------------------------------------------
INSERT INTO health_metrics
    (user_id, weight, height, steps, calories_burned, recorded_date)
VALUES
    (@user_id, 70.50, 175.00, 8000, 250, CURDATE()),
    (@user_id, 70.80, 175.00, 6500, 300, DATE_SUB(CURDATE(), INTERVAL 1 DAY)),
    (@user_id, 71.00, 175.00, 7200, 400, DATE_SUB(CURDATE(), INTERVAL 2 DAY))
AS new
ON DUPLICATE KEY UPDATE
    weight          = new.weight,
    height          = new.height,
    steps           = new.steps,
    calories_burned = new.calories_burned;


-- ----------------------------------------------------------------------------
-- Summary for the sample user
-- ----------------------------------------------------------------------------
SELECT
    u.user_id,
    u.full_name,
    COUNT(DISTINCT w.workout_id)   AS workouts,
    COUNT(DISTINCT n.nutrition_id) AS food_entries,
    COUNT(DISTINCT h.metric_id)    AS health_records
FROM users AS u
LEFT JOIN workouts AS w       ON w.user_id = u.user_id
LEFT JOIN nutrition_logs AS n ON n.user_id = u.user_id
LEFT JOIN health_metrics AS h ON h.user_id = u.user_id
WHERE u.user_id = @user_id
GROUP BY u.user_id, u.full_name;
