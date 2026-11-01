-- ============================================================================
-- Fitness & Wellness Tracking Database System
-- File:    database/app_user.sql
-- Purpose: Create a dedicated MySQL account for the Flask application.
--
-- Run this AFTER database/schema.sql, as the MySQL root user:
--   Get-Content .\database\app_user.sql -Raw | mysql -u root -p
--
-- IMPORTANT:
--   1. Change the password below before running this file.
--   2. Use the SAME password in your .env file.
--   3. Never commit the real password to Git.
--
-- The app account only receives the four data permissions it needs.
-- It cannot create, drop, or alter tables.
-- ============================================================================

CREATE USER IF NOT EXISTS 'fitness_app'@'localhost'
    IDENTIFIED BY 'ChangeMe_StrongPassword_123!';

CREATE USER IF NOT EXISTS 'fitness_app'@'127.0.0.1'
    IDENTIFIED BY 'ChangeMe_StrongPassword_123!';

GRANT SELECT, INSERT, UPDATE, DELETE
    ON fitness_wellness_db.*
    TO 'fitness_app'@'localhost';

GRANT SELECT, INSERT, UPDATE, DELETE
    ON fitness_wellness_db.*
    TO 'fitness_app'@'127.0.0.1';

FLUSH PRIVILEGES;

SHOW GRANTS FOR 'fitness_app'@'localhost';
