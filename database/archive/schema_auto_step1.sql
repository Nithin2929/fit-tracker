-- ============================================================================
-- Fitness & Wellness Tracking Database System
-- File:    database/schema.sql
-- Step:    1 - Create the database and the four main tables
-- Tested:  MySQL 8.4 (InnoDB, utf8mb4)
--
-- RUN THIS FILE IN MYSQL WORKBENCH:
--   File > Open SQL Script > database/schema.sql
--   Click the lightning bolt (Execute) button.
--
-- OR FROM POWERSHELL:
--   Get-Content .\database\schema.sql -Raw | mysql -u root -p --default-character-set=utf8mb4
--
-- This script is safe to run again: it uses IF NOT EXISTS and never deletes data.
-- ============================================================================


-- ----------------------------------------------------------------------------
-- 1. Create the database
-- ----------------------------------------------------------------------------
-- utf8mb4 stores all normal text, including Indian-language characters and emoji.
-- utf8mb4_unicode_ci makes text comparisons case-insensitive.
CREATE DATABASE IF NOT EXISTS fitness_wellness_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

-- Tell MySQL which database the following commands belong to.
USE fitness_wellness_db;


-- ----------------------------------------------------------------------------
-- 2. users
-- One row for each registered person.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    -- A number that MySQL creates automatically for every new user.
    user_id        INT UNSIGNED  NOT NULL AUTO_INCREMENT,

    -- The user's display name. Empty values are not allowed.
    full_name      VARCHAR(100)  NOT NULL,

    -- Login email. It must be unique across all users.
    email          VARCHAR(150)  NOT NULL,

    -- A one-way password hash, never the real password.
    password_hash  VARCHAR(255)  NOT NULL,

    -- Optional profile details.
    date_of_birth  DATE          NULL,
    gender         ENUM('Male', 'Female', 'Other', 'Prefer not to say') NULL,
    height_cm      DECIMAL(5,2)  NULL,

    -- Automatically record when the account was created and last changed.
    created_at     TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at     TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP
                                 ON UPDATE CURRENT_TIMESTAMP,

    -- user_id uniquely identifies each row.
    PRIMARY KEY (user_id),

    -- No two accounts may use the same email address.
    CONSTRAINT uq_users_email UNIQUE (email),

    -- Height must be a realistic positive value or left empty.
    CONSTRAINT chk_users_height_cm
        CHECK (height_cm IS NULL OR (height_cm > 0 AND height_cm < 300))
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;


-- ----------------------------------------------------------------------------
-- 3. workouts
-- One row for each workout session. A user can have many workouts.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS workouts (
    workout_id       INT UNSIGNED      NOT NULL AUTO_INCREMENT,
    user_id          INT UNSIGNED      NOT NULL,
    workout_type     VARCHAR(80)       NOT NULL,
    duration_minutes SMALLINT UNSIGNED NOT NULL,
    calories_burned  SMALLINT UNSIGNED NULL,
    workout_date     DATE              NOT NULL,
    notes            VARCHAR(255)      NULL,
    created_at       TIMESTAMP         NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at       TIMESTAMP         NOT NULL DEFAULT CURRENT_TIMESTAMP
                                       ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (workout_id),

    -- Link this workout to an existing user.
    -- If that user is deleted, this user's workouts are deleted too.
    CONSTRAINT fk_workouts_user
        FOREIGN KEY (user_id) REFERENCES users (user_id)
        ON DELETE CASCADE ON UPDATE CASCADE,

    -- A workout must last between 1 minute and 24 hours.
    CONSTRAINT chk_workouts_duration
        CHECK (duration_minutes > 0 AND duration_minutes <= 1440),

    -- Calories are optional, but cannot be an unrealistic number.
    CONSTRAINT chk_workouts_calories
        CHECK (calories_burned IS NULL OR calories_burned <= 10000),

    -- This index speeds up reports that filter by user and date.
    INDEX idx_workouts_user_date (user_id, workout_date)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;


-- ----------------------------------------------------------------------------
-- 4. nutrition_logs
-- One row for each food item a user logs.
-- Several rows can exist for the same meal, so there is no daily unique key.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS nutrition_logs (
    nutrition_id  INT UNSIGNED  NOT NULL AUTO_INCREMENT,
    user_id       INT UNSIGNED  NOT NULL,
    log_date      DATE          NOT NULL,
    meal_type     ENUM('Breakfast', 'Lunch', 'Dinner', 'Snack') NOT NULL,
    food_name     VARCHAR(120)  NOT NULL,

    -- How many servings were eaten. 1.50 means one and a half servings.
    servings      DECIMAL(5,2)  NOT NULL DEFAULT 1.00,

    -- Total calories for this log entry (already multiplied by servings).
    calories      INT UNSIGNED  NOT NULL,

    -- Optional macronutrients, measured in grams.
    protein_g     DECIMAL(6,1)  NULL,
    carbs_g       DECIMAL(6,1)  NULL,
    fat_g         DECIMAL(6,1)  NULL,

    notes         VARCHAR(255)  NULL,
    created_at    TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP
                                ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (nutrition_id),

    CONSTRAINT fk_nutrition_user
        FOREIGN KEY (user_id) REFERENCES users (user_id)
        ON DELETE CASCADE ON UPDATE CASCADE,

    CONSTRAINT chk_nutrition_servings
        CHECK (servings > 0 AND servings <= 100),

    CONSTRAINT chk_nutrition_calories
        CHECK (calories <= 10000),

    CONSTRAINT chk_nutrition_protein
        CHECK (protein_g IS NULL OR (protein_g >= 0 AND protein_g <= 1000)),

    CONSTRAINT chk_nutrition_carbs
        CHECK (carbs_g IS NULL OR (carbs_g >= 0 AND carbs_g <= 1000)),

    CONSTRAINT chk_nutrition_fat
        CHECK (fat_g IS NULL OR (fat_g >= 0 AND fat_g <= 1000)),

    INDEX idx_nutrition_user_date (user_id, log_date)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;


-- ----------------------------------------------------------------------------
-- 5. health_metrics
-- One row per user per day for weight, steps, and optional body fat.
-- BMI is NOT stored here: it is calculated from users.height_cm and
-- health_metrics.weight_kg when a report is generated.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS health_metrics (
    metric_id           INT UNSIGNED  NOT NULL AUTO_INCREMENT,
    user_id             INT UNSIGNED  NOT NULL,
    record_date         DATE          NOT NULL,
    weight_kg           DECIMAL(5,2)  NOT NULL,
    steps               INT UNSIGNED  NOT NULL DEFAULT 0,
    body_fat_percentage DECIMAL(4,1)  NULL,
    notes               VARCHAR(255)  NULL,
    created_at          TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP
                                      ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (metric_id),

    CONSTRAINT fk_health_user
        FOREIGN KEY (user_id) REFERENCES users (user_id)
        ON DELETE CASCADE ON UPDATE CASCADE,

    -- One health record per user per day.
    CONSTRAINT uq_health_user_date UNIQUE (user_id, record_date),

    CONSTRAINT chk_health_weight
        CHECK (weight_kg > 0 AND weight_kg < 500),

    CONSTRAINT chk_health_steps
        CHECK (steps <= 200000),

    CONSTRAINT chk_health_body_fat
        CHECK (body_fat_percentage IS NULL
               OR (body_fat_percentage >= 0 AND body_fat_percentage <= 100))
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;


-- A friendly confirmation message after the script finishes.
SELECT 'Database and four tables created successfully.' AS message;
