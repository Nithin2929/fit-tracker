# FitTrack — Entity Relationship Diagram (Milestone 2)

**Project:** FitTrack — Fitness & Wellness Tracking Database System  
**Database:** Aiven Cloud MySQL `fitness_wellness_db` (MySQL `8.4.11`)  
**Milestone:** 2 — ER Diagramming & Schema Normalization  
**Status:** Final logical design for review. The four **existing** tables are live. The four **proposed** tables and three proposed columns are draft migrations only and are **not applied**.

> `workouts.exercise_name` is retained as a legacy label during the transition. The normalized exercise model adds `exercises` and `workout_exercises`; it does not delete the legacy column.

---

## 1. Notation

Crow's Foot symbols used by Mermaid `erDiagram`:

| Symbol | Meaning |
|---|---|
| `||` | Exactly one (mandatory one) |
| `o|` | Zero or one (optional one) |
| `}o` | Zero or many |
| `}|` | One or many |

- `PK` = primary key, `FK` = foreign key, `UK` = unique key.
- **Existing** entities are live in Aiven today.
- **Proposed** entities are designed and scripted but not present in the live database.

---

## 2. Entity status

| Entity | Status | Live in Aiven? | Migration file |
|---|---|---|---|
| `users` | Existing | Yes | — |
| `workouts` | Existing | Yes | — |
| `nutrition_logs` | Existing | Yes | — (optional `logged_at` in `migration_nutrition_time.sql`) |
| `health_metrics` | Existing | Yes | — |
| `exercises` | Proposed | **No** | `database/migration_exercises.sql` |
| `workout_exercises` | Proposed | **No** | `database/migration_exercises.sql` |
| `heart_rate_zones` | Proposed | **No** | `database/migration_heart_rate.sql` |
| `heart_rate_samples` | Proposed | **No** | `database/migration_heart_rate.sql` |

---

## 3. Crow's Foot ER diagram — full target model

The diagram shows the target model after all three draft migrations are approved. All relationship lines below are mandatory on the child side unless marked optional.

```mermaid
erDiagram
    users ||--o{ workouts : "owns"
    users ||--o{ nutrition_logs : "logs"
    users ||--o{ health_metrics : "records"
    users ||--o{ heart_rate_samples : "has (proposed)"

    workouts ||--o{ workout_exercises : "contains (proposed)"
    exercises ||--o{ workout_exercises : "is used in (proposed)"

    heart_rate_zones o|--o{ heart_rate_samples : "classifies (proposed, optional)"

    users {
        int unsigned user_id PK
        varchar full_name
        varchar email UK
        varchar password_hash
        date date_of_birth
        enum gender
        decimal height_cm
        timestamp created_at
        timestamp updated_at
    }

    workouts {
        int unsigned workout_id PK
        int unsigned user_id FK
        varchar exercise_name "legacy label"
        int unsigned duration_minutes
        int unsigned calories_burned
        date workout_date
    }

    nutrition_logs {
        int unsigned nutrition_id PK
        int unsigned user_id FK
        varchar food_name
        enum meal_type
        int unsigned calories
        decimal protein
        decimal carbohydrates
        decimal fat
        date log_date
        datetime logged_at "proposed, nullable"
    }

    health_metrics {
        int unsigned metric_id PK
        int unsigned user_id FK
        decimal weight
        decimal height
        int unsigned steps
        int unsigned calories_burned
        date recorded_date
    }

    exercises {
        int unsigned exercise_id PK
        varchar exercise_name UK
        varchar muscle_group
        enum exercise_type
        varchar description
        timestamp created_at
    }

    workout_exercises {
        int unsigned workout_exercise_id PK
        int unsigned workout_id FK
        int unsigned exercise_id FK
        int unsigned exercise_order
        int unsigned sets
        int unsigned repetitions
        decimal weight_kg
        int unsigned duration_minutes
        int unsigned calories_burned
    }

    heart_rate_zones {
        int unsigned zone_id PK
        varchar zone_name UK
        decimal minimum_percentage
        decimal maximum_percentage
    }

    heart_rate_samples {
        int unsigned sample_id PK
        int unsigned user_id FK
        int unsigned zone_id FK "nullable"
        smallint unsigned heart_rate_bpm
        datetime recorded_at
    }
```

---

## 4. Crow's Foot ER diagram — currently implemented only

This is the exact live model and can be verified with `SHOW CREATE TABLE` today.

```mermaid
erDiagram
    users ||--o{ workouts : "owns"
    users ||--o{ nutrition_logs : "logs"
    users ||--o{ health_metrics : "records"

    users {
        int unsigned user_id PK
        varchar full_name
        varchar email UK
        varchar password_hash
        date date_of_birth
        enum gender
        decimal height_cm
        timestamp created_at
        timestamp updated_at
    }

    workouts {
        int unsigned workout_id PK
        int unsigned user_id FK
        varchar exercise_name
        int unsigned duration_minutes
        int unsigned calories_burned
        date workout_date
    }

    nutrition_logs {
        int unsigned nutrition_id PK
        int unsigned user_id FK
        varchar food_name
        enum meal_type
        int unsigned calories
        decimal protein
        decimal carbohydrates
        decimal fat
        date log_date
    }

    health_metrics {
        int unsigned metric_id PK
        int unsigned user_id FK
        decimal weight
        decimal height
        int unsigned steps
        int unsigned calories_burned
        date recorded_date
    }
```

---

## 5. Relationship catalogue

| # | Entity A | Cardinality | Entity B | Optionality | Foreign key | Meaning | Status |
|---:|---|---|---|---|---|---|---|
| R1 | `users` | 1 → 0..N | `workouts` | Workout must have one user; a user may have zero workouts | `workouts.user_id` → `users.user_id` | A user owns many workout sessions. | Existing |
| R2 | `users` | 1 → 0..N | `nutrition_logs` | Log must have one user; a user may have zero logs | `nutrition_logs.user_id` → `users.user_id` | A user logs many food items. | Existing |
| R3 | `users` | 1 → 0..N | `health_metrics` | Record must have one user; a user may have zero records | `health_metrics.user_id` → `users.user_id` | A user records many daily health snapshots. | Existing |
| R4 | `workouts` | 1 → 0..N | `workout_exercises` | Exercise entry must have one workout; a workout may initially have zero entries | `workout_exercises.workout_id` → `workouts.workout_id` | One workout contains many exercises. | Proposed |
| R5 | `exercises` | 1 → 0..N | `workout_exercises` | Entry must reference one exercise; an exercise may be unused | `workout_exercises.exercise_id` → `exercises.exercise_id` | One exercise can appear in many workouts. | Proposed |
| R6 | `workouts` | M ↔ N | `exercises` | Resolved by R4 + R5 | Junction `workout_exercises` | The same exercise can appear in different workouts. | Proposed |
| R7 | `users` | 1 → 0..N | `heart_rate_samples` | Sample must have one user; a user may have zero samples | `heart_rate_samples.user_id` → `users.user_id` | A user has many time-stamped heart-rate readings. | Proposed |
| R8 | `heart_rate_zones` | 1 → 0..N | `heart_rate_samples` | Sample may have zero or one zone | `heart_rate_samples.zone_id` → `heart_rate_zones.zone_id` (nullable) | A shared zone classifies many readings; a reading is in at most one zone. | Proposed |

### Cardinality summary required by the mentor

| Requirement | Model | Status |
|---|---|---|
| One user → many workouts | `users ||--o{ workouts` | Implemented |
| One workout → many exercises | `workouts ||--o{ workout_exercises }o--|| exercises` | Designed, migration pending |
| One user → many nutrition logs | `users ||--o{ nutrition_logs` | Implemented |
| One user → many health records | `users ||--o{ health_metrics` | Implemented |
| One user → many heart-rate samples | `users ||--o{ heart_rate_samples` | Designed, migration pending |
| One zone → many samples | `heart_rate_zones o|--o{ heart_rate_samples` | Designed, migration pending |

---

## 6. Resolved Milestone 2 design decisions

### 6.1 Exercise relationship

A workout is a **session header**; an exercise is a **catalogue item**; `workout_exercises` is the **session line** that records what was actually performed.

- `exercises` stores identity and classification only (`exercise_name`, `muscle_group`, `exercise_type`, `description`).
- `workout_exercises` stores the performance values that belong to one session (`sets`, `repetitions`, `weight_kg`, `duration_minutes`, `calories_burned`) plus `exercise_order`.
- A surrogate `workout_exercise_id` PK matches the existing FitTrack key style. `UNIQUE (workout_id, exercise_order)` guarantees deterministic ordering and prevents duplicate positions.
- The same `exercise_id` may appear in many workouts and more than once in one workout at different orders (for supersets or repeated blocks).

### 6.2 Exercise migration

`workouts.exercise_name` is preserved as a legacy label:

1. Create `exercises`; seed a reusable catalogue.
2. Copy every distinct non-empty legacy name into `exercises` if it is not already present.
3. Create one `workout_exercises` row per existing workout, linking its legacy name to the catalogue and copying the session duration/calories.
4. Update the application to write the junction. The legacy label is still written so old exports/queries keep working.
5. Remove or deprecate `exercise_name` only in a later, separately approved migration after every route and report reads the junction.

### 6.3 Heart-rate zones: shared reference data

- Zones are **shared reference rows**, not per-user rows, in Milestone 2.
- Percentages are applied to an estimated maximum heart rate: `220 − age` when the user's date of birth is known, otherwise `190`.
- The zone is resolved by the application and stored in `heart_rate_samples.zone_id`, which is nullable because a reading below Zone 1 or without a profile age cannot be classified.
- Per-user zone thresholds are a documented future enhancement; they would add a `user_id` to the zone table or a separate override table.

### 6.4 Health metric dates

- `health_metrics` keeps `UNIQUE (user_id, recorded_date)`: at most one daily snapshot per user.
- `heart_rate_samples.recorded_at` is `DATETIME`: many samples per user per day.
- This deliberately separates daily biometrics from time-series readings.

### 6.5 Nutrition timestamps

- Daily reporting only needs `log_date`, which already exists.
- A nullable `nutrition_logs.logged_at DATETIME` is proposed for optional meal timing.
- `log_date` remains authoritative for daily totals; `logged_at` never replaces it, so existing reports and constraints are unaffected.

### 6.6 BMI: derived, not stored

BMI remains a calculated value:

```text
BMI = weight_kg / ((height_cm / 100) ^ 2)
```

- No BMI column is added.
- Storing BMI would duplicate data derivable from `weight` and `height`, creating an update anomaly if one changes without the other.
- The application rounds to one decimal place consistently.
- If a future requirement needs indexing by BMI, a generated column can be added without changing this logical model.

### 6.7 Height duplication

`users.height_cm` is the **current profile height**. `health_metrics.height` is the **height recorded with that historical measurement**. They are not redundant copies of the same fact: one changes over time, the other is a snapshot used for the BMI at that date. This distinction is documented and will be stated in the normalization report.

---

## 7. Proposed physical details

| Table | PK | FKs | Unique | Checks | Indexes |
|---|---|---|---|---|---|
| `exercises` | `exercise_id` | — | `exercise_name` | `exercise_type` ENUM domain | PK, unique name |
| `workout_exercises` | `workout_exercise_id` | `workout_id`, `exercise_id` | `(workout_id, exercise_order)` | sets, repetitions, weight, duration, calories | PK, unique order, `idx_we_exercise` |
| `heart_rate_zones` | `zone_id` | — | `zone_name` | `0 <= min < max <= 100` | PK, unique name |
| `heart_rate_samples` | `sample_id` | `user_id`, `zone_id` | — | `bpm BETWEEN 20 AND 250` | PK, `(user_id, recorded_at)`, `zone_id` |

Full column types and constraints are in `docs/PHYSICAL_SCHEMA.md`; data types and descriptions are in `docs/DATA_DICTIONARY.md`.

---

## 8. What this diagram does not claim

- It does **not** claim that `exercises`, `workout_exercises`, `heart_rate_zones`, or `heart_rate_samples` exist in Aiven today.
- It does **not** claim that `nutrition_logs.logged_at` exists.
- It does **not** model authentication tables, an external API, a device integration, or a food catalogue, because none of these are required by the mentor's four milestones.
- It does **not** show the application-layer ownership filter (`WHERE user_id = %s`); that is security logic, not a database relationship.

---

**Next documents:** `docs/NORMALIZATION_REPORT.md`, `docs/PHYSICAL_SCHEMA.md`.  
**Draft migrations:** `database/migration_exercises.sql`, `database/migration_heart_rate.sql`, `database/migration_nutrition_time.sql`.
