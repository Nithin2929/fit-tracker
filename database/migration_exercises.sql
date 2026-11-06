-- ============================================================================
-- FitTrack - DRAFT migration: exercises + workout_exercises
-- File: database/migration_exercises.sql
--
-- STATUS: DRAFT. NOT EXECUTED AGAINST AIVEN.
-- Apply only after the Milestone 2 design is approved.
--
-- WHAT THIS DOES
--   1. Creates the `exercises` catalogue.
--   2. Creates the `workout_exercises` junction (one workout -> many exercises).
--   3. Seeds a small, reusable exercise catalogue.
--   4. Backfills the catalogue from existing distinct workouts.exercise_name.
--   5. Backfills one workout_exercises row for every existing workout.
--
-- SAFETY
--   - No DROP, TRUNCATE, or DELETE.
--   - `workouts.exercise_name` is preserved as a legacy label.
--   - Re-runnable: IF NOT EXISTS plus NOT EXISTS guards.
--
-- ROLLBACK (only if the migration is rejected immediately after applying)
--   DROP TABLE IF EXISTS workout_exercises;
--   DROP TABLE IF EXISTS exercises;
--   The four original tables and their data are untouched.
-- ============================================================================

USE fitness_wellness_db;

-- ----------------------------------------------------------------------------
-- 1. Exercise catalogue
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS exercises (
    exercise_id    INT UNSIGNED NOT NULL AUTO_INCREMENT,
    exercise_name  VARCHAR(100) NOT NULL,
    muscle_group   VARCHAR(50)  NULL,
    exercise_type  ENUM('Strength', 'Cardio', 'Flexibility', 'Balance', 'Other')
                   NOT NULL DEFAULT 'Other',
    description    VARCHAR(500) NULL,
    created_at     TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (exercise_id),
    CONSTRAINT uq_exercises_name UNIQUE (exercise_name)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- 2. Workout -> exercise junction
--    Surrogate PK follows the existing FitTrack key style. The UNIQUE
--    (workout_id, exercise_order) rule preserves session order and prevents
--    two exercises from occupying the same position in one workout.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS workout_exercises (
    workout_exercise_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    workout_id          INT UNSIGNED NOT NULL,
    exercise_id         INT UNSIGNED NOT NULL,
    exercise_order      INT UNSIGNED NOT NULL DEFAULT 1,
    sets                INT UNSIGNED NULL,
    repetitions         INT UNSIGNED NULL,
    weight_kg           DECIMAL(6,2) NULL,
    duration_minutes    INT UNSIGNED NULL,
    calories_burned     INT UNSIGNED NULL,

    PRIMARY KEY (workout_exercise_id),

    CONSTRAINT fk_we_workout
        FOREIGN KEY (workout_id) REFERENCES workouts (workout_id)
        ON DELETE CASCADE ON UPDATE CASCADE,

    CONSTRAINT fk_we_exercise
        FOREIGN KEY (exercise_id) REFERENCES exercises (exercise_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,

    CONSTRAINT uq_we_workout_order UNIQUE (workout_id, exercise_order),

    CONSTRAINT chk_we_sets
        CHECK (sets IS NULL OR (sets > 0 AND sets <= 100)),
    CONSTRAINT chk_we_repetitions
        CHECK (repetitions IS NULL OR (repetitions > 0 AND repetitions <= 1000)),
    CONSTRAINT chk_we_weight
        CHECK (weight_kg IS NULL OR (weight_kg >= 0 AND weight_kg <= 1000)),
    CONSTRAINT chk_we_duration
        CHECK (duration_minutes IS NULL OR
               (duration_minutes > 0 AND duration_minutes <= 1440)),
    CONSTRAINT chk_we_calories
        CHECK (calories_burned IS NULL OR calories_burned <= 10000),

    INDEX idx_we_exercise (exercise_id)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- 3. Seed a small reusable catalogue.
--    ON DUPLICATE KEY UPDATE keeps the script re-runnable without touching
--    exercise_id values that workouts may already reference.
-- ----------------------------------------------------------------------------
INSERT INTO exercises (exercise_name, muscle_group, exercise_type, description)
VALUES
    ('Running',            'Full body',    'Cardio',      'Steady or interval running outdoors or on a treadmill.'),
    ('Walking',            'Full body',    'Cardio',      'Low-impact walking session.'),
    ('Cycling',            'Legs',         'Cardio',      'Indoor or outdoor cycling session.'),
    ('Swimming',           'Full body',    'Cardio',      'Pool or open-water swimming.'),
    ('Rowing',             'Full body',    'Cardio',      'Rowing machine or on-water rowing.'),
    ('Jump Rope',          'Full body',    'Cardio',      'Skipping rope for conditioning.'),
    ('Squat',              'Legs',         'Strength',    'Bodyweight or loaded squat.'),
    ('Deadlift',           'Posterior chain', 'Strength', 'Hip-hinge barbell or dumbbell lift.'),
    ('Bench Press',        'Chest',        'Strength',    'Flat, incline, or dumbbell press.'),
    ('Overhead Press',     'Shoulders',    'Strength',    'Standing or seated vertical press.'),
    ('Barbell Row',        'Back',         'Strength',    'Bent-over row for upper-body pulling.'),
    ('Pull-up',            'Back',         'Strength',    'Bodyweight vertical pull.'),
    ('Push-up',            'Chest',        'Strength',    'Bodyweight horizontal push.'),
    ('Lunge',              'Legs',         'Strength',    'Forward, reverse, or walking lunge.'),
    ('Plank',              'Core',         'Strength',    'Isometric core hold.'),
    ('Yoga',               'Full body',    'Flexibility','Mobility and flexibility practice.'),
    ('Stretching',         'Full body',    'Flexibility','Guided static or dynamic stretching.'),
    ('Balance Drill',      'Full body',    'Balance',    'Single-leg or stability exercises.')
ON DUPLICATE KEY UPDATE
    muscle_group  = VALUES(muscle_group),
    exercise_type = VALUES(exercise_type),
    description   = VALUES(description);

-- ----------------------------------------------------------------------------
-- 4. Backfill the catalogue from existing free-text exercise names.
--    Long names are trimmed to the VARCHAR(100) limit. Duplicate names are
--    ignored by the UNIQUE constraint.
-- ----------------------------------------------------------------------------
INSERT INTO exercises (exercise_name, muscle_group, exercise_type, description)
SELECT DISTINCT
       LEFT(TRIM(workouts.exercise_name), 100),
       NULL,
       'Other',
       'Imported from the legacy workouts.exercise_name field.'
FROM workouts
WHERE TRIM(workouts.exercise_name) <> ''
  AND NOT EXISTS (
      SELECT 1 FROM exercises
      WHERE exercises.exercise_name = LEFT(TRIM(workouts.exercise_name), 100)
  );

-- ----------------------------------------------------------------------------
-- 5. Backfill one junction row per existing workout.
--    Existing workouts carry no sets/reps/weight, so those stay NULL.
--    The session duration and calories are copied into the single exercise row
--    only when the workout has exactly one legacy exercise (which is always
--    true for the current schema).
-- ----------------------------------------------------------------------------
INSERT INTO workout_exercises
    (workout_id, exercise_id, exercise_order, sets, repetitions,
     weight_kg, duration_minutes, calories_burned)
SELECT
    workouts.workout_id,
    exercises.exercise_id,
    1,
    NULL,
    NULL,
    NULL,
    workouts.duration_minutes,
    workouts.calories_burned
FROM workouts
JOIN exercises
  ON exercises.exercise_name = LEFT(TRIM(workouts.exercise_name), 100)
WHERE NOT EXISTS (
    SELECT 1 FROM workout_exercises
    WHERE workout_exercises.workout_id = workouts.workout_id
);

-- ----------------------------------------------------------------------------
-- 6. Verification (read-only)
-- ----------------------------------------------------------------------------
SELECT 'exercises' AS table_name, COUNT(*) AS rows_after_migration FROM exercises
UNION ALL
SELECT 'workout_exercises', COUNT(*) FROM workout_exercises
UNION ALL
SELECT 'workouts_without_exercises', COUNT(*)
FROM workouts
WHERE NOT EXISTS (
    SELECT 1 FROM workout_exercises
    WHERE workout_exercises.workout_id = workouts.workout_id
);

SELECT 'Migration exercises: review the counts, then COMMIT.' AS message;
