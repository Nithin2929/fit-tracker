-- ============================================================================
-- Fitness & Wellness Tracking Database System
-- File:    database/schema.sql
-- Purpose: Create the database and the five Phase 1 tables.
-- Tested:  MySQL 8.4  (InnoDB, utf8mb4)
--
-- How to run (PowerShell):
--   Get-Content .\database\schema.sql -Raw | mysql -u root -p --default-character-set=utf8mb4
--
-- How to run (Command Prompt):
--   mysql -u root -p --default-character-set=utf8mb4 < database\schema.sql
--
-- This script is safe to re-run: it uses IF NOT EXISTS and never deletes data.
-- ============================================================================

CREATE DATABASE IF NOT EXISTS fitness_wellness_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE fitness_wellness_db;

-- ----------------------------------------------------------------------------
-- 1. users
-- One row per registered person.
-- email is UNIQUE so two accounts cannot use the same address.
-- password_hash stores a one-way hash (created in Phase 3), never the password.
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
-- A user can log many workouts. Each row is one workout session.
-- ON DELETE CASCADE: deleting a user removes that user's workouts.
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
-- 3. daily_wellness
-- One row per user per calendar day (UNIQUE user_id + log_date).
-- Water is stored in millilitres, sleep in hours, steps as a whole number.
-- Phase 6 will use INSERT ... ON DUPLICATE KEY UPDATE so a second save on the
-- same day updates the existing row instead of creating a duplicate.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS daily_wellness (
    wellness_id     INT UNSIGNED      NOT NULL AUTO_INCREMENT,
    user_id         INT UNSIGNED      NOT NULL,
    log_date        DATE              NOT NULL,
    water_intake_ml SMALLINT UNSIGNED NOT NULL DEFAULT 0,
    sleep_hours     DECIMAL(3,1)      NOT NULL DEFAULT 0.0,
    steps           INT UNSIGNED      NOT NULL DEFAULT 0,
    created_at      TIMESTAMP         NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP         NOT NULL DEFAULT CURRENT_TIMESTAMP
                                      ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (wellness_id),
    CONSTRAINT fk_wellness_user
        FOREIGN KEY (user_id) REFERENCES users (user_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT uq_wellness_user_date UNIQUE (user_id, log_date),
    CONSTRAINT chk_wellness_water
        CHECK (water_intake_ml <= 20000),
    CONSTRAINT chk_wellness_sleep
        CHECK (sleep_hours >= 0 AND sleep_hours <= 24),
    CONSTRAINT chk_wellness_steps
        CHECK (steps <= 200000)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- 4. goals
-- A user can create many fitness goals.
-- unit is stored explicitly so the dashboard can format the target correctly.
-- status lets the app show active, completed, and cancelled goals.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS goals (
    goal_id       INT UNSIGNED  NOT NULL AUTO_INCREMENT,
    user_id       INT UNSIGNED  NOT NULL,
    goal_title    VARCHAR(100)  NOT NULL,
    goal_type     ENUM(
                      'Weight Loss',
                      'Weight Gain',
                      'Muscle Gain',
                      'Steps',
                      'Water Intake',
                      'Sleep',
                      'Workout Frequency',
                      'Other'
                  ) NOT NULL,
    target_value  DECIMAL(8,2)  NOT NULL,
    unit          ENUM('kg', 'steps', 'ml', 'hours', 'sessions/week') NOT NULL,
    start_date    DATE          NOT NULL,
    target_date   DATE          NOT NULL,
    status        ENUM('Active', 'Completed', 'Cancelled')
                                NOT NULL DEFAULT 'Active',
    created_at    TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP
                                ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (goal_id),
    CONSTRAINT fk_goals_user
        FOREIGN KEY (user_id) REFERENCES users (user_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT chk_goals_target_value
        CHECK (target_value > 0),
    CONSTRAINT chk_goals_dates
        CHECK (target_date >= start_date),
    INDEX idx_goals_user_status (user_id, status)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- 5. progress
-- One weight/body-fat entry per user per day (UNIQUE user_id + record_date).
-- Keeping history lets Phase 8 draw weight trends and calculate change.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS progress (
    progress_id         INT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id             INT UNSIGNED NOT NULL,
    record_date         DATE         NOT NULL,
    weight_kg           DECIMAL(5,2) NOT NULL,
    body_fat_percentage DECIMAL(4,1) NULL,
    notes               VARCHAR(255) NULL,
    created_at          TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
                                     ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (progress_id),
    CONSTRAINT fk_progress_user
        FOREIGN KEY (user_id) REFERENCES users (user_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT uq_progress_user_date UNIQUE (user_id, record_date),
    CONSTRAINT chk_progress_weight
        CHECK (weight_kg > 0 AND weight_kg < 500),
    CONSTRAINT chk_progress_body_fat
        CHECK (body_fat_percentage IS NULL
               OR (body_fat_percentage >= 0 AND body_fat_percentage <= 100))
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;

SELECT 'Database and tables created successfully.' AS message;
