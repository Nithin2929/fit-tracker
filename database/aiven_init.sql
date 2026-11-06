-- ============================================================================
-- FitTrack - Aiven Cloud MySQL initialization
-- File: database/aiven_init.sql
--
-- WHAT THIS DOES
--   Creates the four FitTrack tables in the CURRENT Aiven database:
--     users, workouts, nutrition_logs, health_metrics
--
-- SAFETY
--   - Safe to run more than once: every statement uses IF NOT EXISTS.
--   - Never drops, truncates, or deletes existing tables or rows.
--   - Does not create a local database and does not use CREATE DATABASE.
--
-- BEFORE RUNNING
--   1. In the Aiven console, make sure your MySQL service is running and the
--      database named fitness_wellness_db exists (or create it with your Aiven
--      admin user). Aiven sometimes names the first database "defaultdb".
--   2. Connect with your Aiven credentials, for example:
--        mysql --host YOUR_HOST --port YOUR_PORT --user YOUR_USER \
--              --password --ssl-ca certs/ca.pem fitness_wellness_db
--   3. Run this file:
--        mysql ... fitness_wellness_db < database/aiven_init.sql
--
-- USER ID TYPE
--   This script matches the original FitTrack schema where users.user_id is
--   INT UNSIGNED. If your existing users table uses a different type, check:
--
--     SELECT column_type
--     FROM information_schema.columns
--     WHERE table_schema = DATABASE()
--       AND table_name = 'users'
--       AND column_name = 'user_id';
--
--   If it returns "int", change all four "INT UNSIGNED" occurrences below to
--   "INT" before running the script on that existing database.
-- ============================================================================

USE fitness_wellness_db;

SELECT DATABASE() AS active_database;


-- ----------------------------------------------------------------------------
-- 1. users
--    Existing FitTrack accounts. A fresh Aiven database gets the same shape as
--    the original users table.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    user_id        INT UNSIGNED  NOT NULL AUTO_INCREMENT,
    full_name      VARCHAR(100)  NOT NULL,
    email          VARCHAR(150)  NOT NULL,
    password_hash  VARCHAR(255)  NOT NULL,
    date_of_birth  DATE          NULL,
    gender         ENUM('Male', 'Female', 'Other', 'Prefer not to say') NULL,
    height_cm      DECIMAL(5,2)  NULL,
    created_at     TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at     TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP
                                 ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (user_id),

    CONSTRAINT uq_users_email UNIQUE (email),

    CONSTRAINT chk_users_height_cm
        CHECK (height_cm IS NULL OR (height_cm > 0 AND height_cm < 300))
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;


-- ----------------------------------------------------------------------------
-- 2. workouts
--    One row per workout session. user_id points to users.user_id.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS workouts (
    workout_id       INT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id          INT UNSIGNED NOT NULL,
    exercise_name    VARCHAR(100) NOT NULL,
    duration_minutes INT UNSIGNED NOT NULL,
    calories_burned  INT UNSIGNED NULL,
    workout_date     DATE         NOT NULL,

    PRIMARY KEY (workout_id),

    CONSTRAINT fk_workouts_user
        FOREIGN KEY (user_id) REFERENCES users (user_id)
        ON DELETE CASCADE ON UPDATE CASCADE,

    CONSTRAINT chk_workouts_duration
        CHECK (duration_minutes > 0 AND duration_minutes <= 1440),

    CONSTRAINT chk_workouts_calories
        CHECK (calories_burned IS NULL OR calories_burned <= 10000),

    INDEX idx_workouts_user_date (user_id, workout_date)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;


-- ----------------------------------------------------------------------------
-- 3. nutrition_logs
--    One row per food item. Several items may be logged on the same day.
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
-- 4. health_metrics
--    One record per user per day. BMI is calculated by the app, not stored.
--    The unique constraint is preserved from the original schema.
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


SELECT 'FitTrack Aiven tables created or already present.' AS message;
