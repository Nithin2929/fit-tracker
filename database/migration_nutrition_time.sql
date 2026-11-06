-- ============================================================================
-- FitTrack - DRAFT migration: optional nutrition time-of-day
-- File: database/migration_nutrition_time.sql
--
-- STATUS: DRAFT. NOT EXECUTED AGAINST AIVEN.
--
-- DESIGN DECISION
--   Time of day is OPTIONAL. The mentor requires date-based daily calorie and
--   macronutrient reporting, which already works with `log_date`. A nullable
--   `logged_at` column is added so a future UI can capture meal timing without
--   breaking the existing daily aggregation. `log_date` remains authoritative.
--
-- SAFETY
--   - Additive nullable column only.
--   - No existing value is changed or deleted.
--   - Idempotent in MySQL 8 using information_schema checks (MySQL does not
--     support ADD COLUMN IF NOT EXISTS).
-- ============================================================================

USE fitness_wellness_db;

SET @column_exists := (
    SELECT COUNT(*)
    FROM information_schema.columns
    WHERE table_schema = DATABASE()
      AND table_name = 'nutrition_logs'
      AND column_name = 'logged_at'
);

SET @ddl := IF(
    @column_exists = 0,
    'ALTER TABLE nutrition_logs ADD COLUMN logged_at DATETIME NULL AFTER log_date',
    'SELECT ''nutrition_logs.logged_at already exists'' AS message'
);

PREPARE migration_statement FROM @ddl;
EXECUTE migration_statement;
DEALLOCATE PREPARE migration_statement;

SET @index_exists := (
    SELECT COUNT(*)
    FROM information_schema.statistics
    WHERE table_schema = DATABASE()
      AND table_name = 'nutrition_logs'
      AND index_name = 'idx_nutrition_user_time'
);

SET @index_ddl := IF(
    @index_exists = 0,
    'CREATE INDEX idx_nutrition_user_time ON nutrition_logs (user_id, logged_at)',
    'SELECT ''idx_nutrition_user_time already exists'' AS message'
);

PREPARE index_statement FROM @index_ddl;
EXECUTE index_statement;
DEALLOCATE PREPARE index_statement;

SELECT 'Migration nutrition_time: logged_at is nullable; existing rows keep NULL.' AS message;
