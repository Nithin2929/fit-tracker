-- ============================================================================
-- Fitness & Wellness Tracking Database System
-- File:    database/step3_tables.sql
-- Step 3: Create the workouts, nutrition_logs, and health_metrics tables.
--
-- AIVEN CLOUD MYSQL:
--   Run this against your online Aiven database, not a local MySQL server.
--   For a fresh Aiven database, database/aiven_init.sql creates all four
--   tables (including users). This file is for an Aiven database where the
--   users table already exists.
--
-- IMPORTANT:
--   Your existing users table was created earlier. This script does NOT create
--   or change the users table. It only adds three child tables that point to it.
--
--   Run this check first:
--
--   SHOW CREATE TABLE users;
--
--   The three tables below use INT UNSIGNED for user_id, matching the original
--   FitTrack schema. If your users.user_id is signed `int`, change every
--   `user_id ... INT UNSIGNED NOT NULL` below to `INT NOT NULL`.
--
-- HOW TO RUN:
--   Connect to Aiven with the mysql client and select fitness_wellness_db, then
--   run this file. Example:
--     mysql --host YOUR_HOST --port YOUR_PORT --user YOUR_USER --password \
--           --ssl-ca certs/ca.pem fitness_wellness_db < database/step3_tables.sql
-- ============================================================================

USE fitness_wellness_db;

-- ----------------------------------------------------------------------------
-- Check the exact type of users.user_id before creating the foreign keys.
-- ----------------------------------------------------------------------------
SELECT column_name, column_type
FROM information_schema.columns
WHERE table_schema = DATABASE()
  AND table_name = 'users'
  AND column_name = 'user_id';


-- ----------------------------------------------------------------------------
-- 1. workouts
-- One row for each workout session.
-- A user can have many workouts, so this is a one-to-many relationship.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS workouts (
    workout_id       INT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id          INT UNSIGNED NOT NULL,
    exercise_name    VARCHAR(100) NOT NULL,
    duration_minutes INT UNSIGNED NOT NULL,
    calories_burned  INT UNSIGNED NULL,
    workout_date     DATE         NOT NULL,

    PRIMARY KEY (workout_id),

    -- Link each workout to an existing user.
    -- If the user is deleted, that user's workouts are deleted too.
    CONSTRAINT fk_workouts_user
        FOREIGN KEY (user_id) REFERENCES users (user_id)
        ON DELETE CASCADE ON UPDATE CASCADE,

    -- A workout must last between 1 minute and 24 hours.
    CONSTRAINT chk_workouts_duration
        CHECK (duration_minutes > 0 AND duration_minutes <= 1440),

    -- Calories are optional, but must be realistic if entered.
    CONSTRAINT chk_workouts_calories
        CHECK (calories_burned IS NULL OR calories_burned <= 10000),

    -- Speeds up "show this user's workouts for a date range" queries.
    INDEX idx_workouts_user_date (user_id, workout_date)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;


-- ----------------------------------------------------------------------------
-- 2. nutrition_logs
-- One row for each food item eaten.
-- A user can log many foods on the same day, so there is no daily unique key.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS nutrition_logs (
    nutrition_id  INT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id       INT UNSIGNED NOT NULL,
    food_name     VARCHAR(120) NOT NULL,
    meal_type     ENUM('Breakfast', 'Lunch', 'Dinner', 'Snack') NOT NULL,
    calories      INT UNSIGNED NOT NULL,
    protein       DECIMAL(6,1) NULL,
    carbohydrates DECIMAL(6,1) NULL,
    fat           DECIMAL(6,1) NULL,
    log_date      DATE         NOT NULL,

    PRIMARY KEY (nutrition_id),

    CONSTRAINT fk_nutrition_user
        FOREIGN KEY (user_id) REFERENCES users (user_id)
        ON DELETE CASCADE ON UPDATE CASCADE,

    CONSTRAINT chk_nutrition_calories
        CHECK (calories <= 10000),

    CONSTRAINT chk_nutrition_protein
        CHECK (protein IS NULL OR (protein >= 0 AND protein <= 1000)),

    CONSTRAINT chk_nutrition_carbohydrates
        CHECK (carbohydrates IS NULL OR (carbohydrates >= 0 AND carbohydrates <= 1000)),

    CONSTRAINT chk_nutrition_fat
        CHECK (fat IS NULL OR (fat >= 0 AND fat <= 1000)),

    INDEX idx_nutrition_user_date (user_id, log_date)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;


-- ----------------------------------------------------------------------------
-- 3. health_metrics
-- One row per user per day for weight, height, steps, and daily calories burned.
--
-- UNIQUE (user_id, recorded_date) means a user can have only one health record
-- for a given date. If they update today's weight, the app should UPDATE the
-- existing row instead of inserting a duplicate.
--
-- BMI is calculated, not stored:
--   BMI = weight / ((height / 100) * (height / 100))
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS health_metrics (
    metric_id       INT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id         INT UNSIGNED NOT NULL,
    weight          DECIMAL(5,2) NOT NULL,
    height          DECIMAL(5,2) NOT NULL,
    steps           INT UNSIGNED NOT NULL DEFAULT 0,
    calories_burned INT UNSIGNED NOT NULL DEFAULT 0,
    recorded_date   DATE         NOT NULL,

    PRIMARY KEY (metric_id),

    CONSTRAINT fk_health_user
        FOREIGN KEY (user_id) REFERENCES users (user_id)
        ON DELETE CASCADE ON UPDATE CASCADE,

    -- One health record per user per day.
    CONSTRAINT uq_health_user_date UNIQUE (user_id, recorded_date),

    CONSTRAINT chk_health_weight
        CHECK (weight > 0 AND weight < 500),

    CONSTRAINT chk_health_height
        CHECK (height > 0 AND height < 300),

    CONSTRAINT chk_health_steps
        CHECK (steps <= 200000),

    CONSTRAINT chk_health_calories_burned
        CHECK (calories_burned <= 10000)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;


SELECT 'Step 3 tables created successfully.' AS message;
