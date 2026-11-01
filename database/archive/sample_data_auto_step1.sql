-- ============================================================================
-- Fitness & Wellness Tracking Database System
-- File:    database/sample_data.sql
-- Purpose: Insert dummy records for testing the dashboard and reports.
--
-- Run AFTER database/schema.sql:
--   File > Open SQL Script > database/sample_data.sql
--   Click the lightning bolt (Execute).
--
-- Login password for every sample user is:  Password123!
-- The password is stored as a hash, not as plain text.
--
-- This script is safe to re-run. It first deletes only the three sample
-- accounts below; ON DELETE CASCADE removes their old workouts, food logs,
-- and health records. Real users are not touched.
-- ============================================================================

USE fitness_wellness_db;

-- Remove only the sample accounts from a previous run.
DELETE FROM users
WHERE email IN (
    'aarav@example.com',
    'priya@example.com',
    'rahul@example.com'
);

-- ----------------------------------------------------------------------------
-- Sample users
-- All three use the password: Password123!
-- ----------------------------------------------------------------------------
INSERT INTO users
    (full_name, email, password_hash, date_of_birth, gender, height_cm)
VALUES
    (
        'Aarav Kumar',
        'aarav@example.com',
        'scrypt:32768:8:1$Wf91q1mTB9c00I6B$e30f861a3aaeff05e5800c41664df84545173b62c0681a67e388ac460519f2e0d789ee4c98e3dfcf3322c4855071bdaee76756c8f8c138254ddcaf22b909e3d2',
        '1998-05-14', 'Male', 175.00
    ),
    (
        'Priya Sharma',
        'priya@example.com',
        'scrypt:32768:8:1$Wf91q1mTB9c00I6B$e30f861a3aaeff05e5800c41664df84545173b62c0681a67e388ac460519f2e0d789ee4c98e3dfcf3322c4855071bdaee76756c8f8c138254ddcaf22b909e3d2',
        '2000-11-02', 'Female', 162.00
    ),
    (
        'Rahul Verma',
        'rahul@example.com',
        'scrypt:32768:8:1$Wf91q1mTB9c00I6B$e30f861a3aaeff05e5800c41664df84545173b62c0681a67e388ac460519f2e0d789ee4c98e3dfcf3322c4855071bdaee76756c8f8c138254ddcaf22b909e3d2',
        '1995-02-20', 'Male', 180.00
    );

SET @aarav = (SELECT user_id FROM users WHERE email = 'aarav@example.com');
SET @priya = (SELECT user_id FROM users WHERE email = 'priya@example.com');
SET @rahul = (SELECT user_id FROM users WHERE email = 'rahul@example.com');


-- ----------------------------------------------------------------------------
-- Workouts
-- ----------------------------------------------------------------------------
INSERT INTO workouts
    (user_id, workout_type, duration_minutes, calories_burned, workout_date, notes)
VALUES
    (@aarav, 'Running',           35, 320, CURDATE(),                         'Morning run in the park'),
    (@aarav, 'Strength Training', 45, 280, DATE_SUB(CURDATE(), INTERVAL 1 DAY), 'Upper body'),
    (@aarav, 'Cycling',           60, 450, DATE_SUB(CURDATE(), INTERVAL 2 DAY), 'Weekend ride'),

    (@priya, 'Yoga',              40, 150, CURDATE(),                         'Flexibility session'),
    (@priya, 'Walking',           50, 200, DATE_SUB(CURDATE(), INTERVAL 1 DAY), 'Evening walk'),

    (@rahul, 'Gym',               60, 400, CURDATE(),                         'Chest and back'),
    (@rahul, 'Football',          90, 600, DATE_SUB(CURDATE(), INTERVAL 3 DAY), 'College match');


-- ----------------------------------------------------------------------------
-- Nutrition logs
-- Calories are the total for the entry.
-- ----------------------------------------------------------------------------
INSERT INTO nutrition_logs
    (user_id, log_date, meal_type, food_name, servings, calories, protein_g, carbs_g, fat_g, notes)
VALUES
    (@aarav, CURDATE(), 'Breakfast', 'Oats with milk',              1.00, 250, 9.0,  40.0, 6.0,  ''),
    (@aarav, CURDATE(), 'Lunch',     'Grilled chicken with rice',   1.00, 550, 40.0, 60.0, 12.0, ''),
    (@aarav, CURDATE(), 'Snack',     'Apple',                       1.00, 95,  0.5,  25.0, 0.3,  ''),

    (@priya, CURDATE(), 'Breakfast', 'Idli with sambar',            3.00, 300, 8.0,  55.0, 4.0,  ''),
    (@priya, CURDATE(), 'Lunch',     'Paneer curry with roti',      1.00, 420, 20.0, 45.0, 16.0, ''),
    (@priya, CURDATE(), 'Snack',     'Mixed fruit salad',           1.00, 180, 2.0,  40.0, 1.0,  ''),

    (@rahul, CURDATE(), 'Breakfast', 'Boiled eggs',                 2.00, 140, 12.0, 1.0,  10.0, ''),
    (@rahul, CURDATE(), 'Lunch',     'Chicken biryani',             1.00, 650, 30.0, 80.0, 20.0, ''),
    (@rahul, CURDATE(), 'Snack',     'Banana',                      1.00, 105, 1.3,  27.0, 0.4,  '');


-- ----------------------------------------------------------------------------
-- Health metrics
-- One row per user per day. BMI is calculated later from height and weight.
-- ----------------------------------------------------------------------------
INSERT INTO health_metrics
    (user_id, record_date, weight_kg, steps, body_fat_percentage, notes)
VALUES
    (@aarav, CURDATE(),                         71.20, 9200, 17.8, 'Morning measurement'),
    (@aarav, DATE_SUB(CURDATE(), INTERVAL 1 DAY), 71.40, 10400, 18.0, ''),
    (@aarav, DATE_SUB(CURDATE(), INTERVAL 2 DAY), 71.60, 8600, 18.1, ''),
    (@aarav, DATE_SUB(CURDATE(), INTERVAL 3 DAY), 71.80, 12100, 18.2, ''),
    (@aarav, DATE_SUB(CURDATE(), INTERVAL 4 DAY), 72.00, 7400, 18.4, ''),
    (@aarav, DATE_SUB(CURDATE(), INTERVAL 5 DAY), 72.30, 9800, 18.5, ''),
    (@aarav, DATE_SUB(CURDATE(), INTERVAL 6 DAY), 72.50, 11200, 18.6, ''),

    (@priya, CURDATE(),                         60.20, 7800, 24.0, ''),
    (@priya, DATE_SUB(CURDATE(), INTERVAL 1 DAY), 60.30, 9100, 24.1, ''),
    (@priya, DATE_SUB(CURDATE(), INTERVAL 2 DAY), 60.50, 6500, 24.2, ''),

    (@rahul, CURDATE(),                         81.80, 8800, 20.5, ''),
    (@rahul, DATE_SUB(CURDATE(), INTERVAL 1 DAY), 82.00, 7600, 20.7, '');


-- ----------------------------------------------------------------------------
-- Summary of the dummy data
-- ----------------------------------------------------------------------------
SELECT 'Sample data inserted. Login password for all sample users: Password123!' AS message;

SELECT
    u.user_id,
    u.full_name,
    u.email,
    COUNT(DISTINCT w.workout_id)   AS workouts,
    COUNT(DISTINCT n.nutrition_id) AS food_entries,
    COUNT(DISTINCT h.metric_id)    AS health_records
FROM users AS u
LEFT JOIN workouts AS w       ON w.user_id = u.user_id
LEFT JOIN nutrition_logs AS n ON n.user_id = u.user_id
LEFT JOIN health_metrics AS h ON h.user_id = u.user_id
WHERE u.email IN ('aarav@example.com', 'priya@example.com', 'rahul@example.com')
GROUP BY u.user_id, u.full_name, u.email
ORDER BY u.user_id;
