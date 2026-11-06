-- ============================================================================
-- FitTrack - DRAFT migration: heart-rate zones + time-based samples
-- File: database/migration_heart_rate.sql
--
-- STATUS: DRAFT. NOT EXECUTED AGAINST AIVEN.
-- Apply only after the Milestone 2 design is approved.
--
-- DESIGN DECISION
--   Zones are SHARED reference data expressed as a percentage of an estimated
--   maximum heart rate. They are not personalised rows in this milestone.
--   A sample stores the resolved zone_id as a convenience; the application
--   resolves the zone from heart_rate_bpm and the user's estimated maximum.
--
-- SAFETY
--   - No DROP, TRUNCATE, or DELETE.
--   - No heart-rate values are invented: the samples table starts empty.
--   - Re-runnable: IF NOT EXISTS plus ON DUPLICATE KEY UPDATE for zone seeds.
-- ============================================================================

USE fitness_wellness_db;

-- ----------------------------------------------------------------------------
-- 1. Shared heart-rate zone reference data
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS heart_rate_zones (
    zone_id             INT UNSIGNED NOT NULL AUTO_INCREMENT,
    zone_name           VARCHAR(20)  NOT NULL,
    minimum_percentage  DECIMAL(5,2) NOT NULL,
    maximum_percentage  DECIMAL(5,2) NOT NULL,

    PRIMARY KEY (zone_id),
    CONSTRAINT uq_hr_zone_name UNIQUE (zone_name),
    CONSTRAINT chk_hr_zone_order
        CHECK (minimum_percentage >= 0
           AND maximum_percentage <= 100
           AND minimum_percentage < maximum_percentage)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;

INSERT INTO heart_rate_zones
    (zone_name, minimum_percentage, maximum_percentage)
VALUES
    ('Zone 1',  0.00,  50.00),
    ('Zone 2', 50.00,  60.00),
    ('Zone 3', 60.00,  70.00),
    ('Zone 4', 70.00,  80.00),
    ('Zone 5', 80.00, 100.00)
ON DUPLICATE KEY UPDATE
    minimum_percentage = VALUES(minimum_percentage),
    maximum_percentage = VALUES(maximum_percentage);

-- ----------------------------------------------------------------------------
-- 2. Time-stamped heart-rate samples
--    One row per reading, many readings per user per day. This is deliberately
--    separate from health_metrics, which keeps its one-record-per-day rule.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS heart_rate_samples (
    sample_id       INT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id         INT UNSIGNED NOT NULL,
    zone_id         INT UNSIGNED NULL,
    heart_rate_bpm  SMALLINT UNSIGNED NOT NULL,
    recorded_at     DATETIME     NOT NULL,

    PRIMARY KEY (sample_id),

    CONSTRAINT fk_hr_sample_user
        FOREIGN KEY (user_id) REFERENCES users (user_id)
        ON DELETE CASCADE ON UPDATE CASCADE,

    CONSTRAINT fk_hr_sample_zone
        FOREIGN KEY (zone_id) REFERENCES heart_rate_zones (zone_id)
        ON DELETE SET NULL ON UPDATE CASCADE,

    CONSTRAINT chk_hr_bpm
        CHECK (heart_rate_bpm >= 20 AND heart_rate_bpm <= 250),

    INDEX idx_hr_user_time (user_id, recorded_at),
    INDEX idx_hr_zone (zone_id)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- 3. Verification (read-only)
-- ----------------------------------------------------------------------------
SELECT 'heart_rate_zones' AS table_name, COUNT(*) AS rows_after_migration
FROM heart_rate_zones
UNION ALL
SELECT 'heart_rate_samples', COUNT(*) FROM heart_rate_samples;

SELECT 'Migration heart_rate: samples start empty by design.' AS message;
