# FitTrack — Data Dictionary

**Project:** FitTrack — Fitness & Wellness Tracking Database System  
**Milestone:** 1 — Entity Identification & Logic Mapping  
**Database:** Aiven Cloud MySQL `fitness_wellness_db` (MySQL `8.4.11`)  
**Evidence:** Live `information_schema` metadata (read-only), `database/aiven_init.sql`, and the existing Flask routes.  
**Status:** Existing entities are verified against the live database. Proposed entities are **design only** and are **not implemented** in the database or application.

> **Important:** No table was created or altered while producing this document. No row was inserted, updated, or deleted. Proposed fields and tables must not be treated as existing until they are approved and implemented in a later milestone.

---

## 1. Entity summary

| Entity | Type | Live table | Rows in live DB | Purpose |
|---|---|---|---:|---|
| `users` | Existing | `users` | 1 | Registered user profile and authentication identity. |
| `workouts` | Existing | `workouts` | 0 | One workout session per row, including a legacy free-text exercise label. |
| `nutrition_logs` | Existing | `nutrition_logs` | 0 | One food item per row with calories and macronutrients. |
| `health_metrics` | Existing | `health_metrics` | 0 | One daily health snapshot per user: weight, height, steps, calories. |
| `exercises` | Proposed | — | — | Exercise catalogue with a name and category. |
| `workout_exercises` | Proposed | — | — | Junction table linking one workout to many exercises, with sets, reps, weight, duration, and order. |
| `heart_rate_zones` | Proposed | — | — | Reference table defining heart-rate zone boundaries. |
| `heart_rate_samples` | Proposed | — | — | Time-based heart-rate readings linked to a user and, optionally, a zone. |

**Data categories**

| Mentor category | Existing entity | Proposed entity |
|---|---|---|
| Users | `users` | — |
| Activities / Workouts | `workouts` | `exercises`, `workout_exercises` |
| Nutrition | `nutrition_logs` | — (a `foods` lookup is an optional Milestone 2 normalization improvement) |
| BioMetrics / Health | `health_metrics` | `heart_rate_samples`, `heart_rate_zones` |

---

## 2. Notation

| Column | Meaning |
|---|---|
| **PK** | Primary key. `Yes (PK)` means the column is the primary key. |
| **FK** | Foreign key target. `—` means no foreign key. |
| **Nullable** | `No` means `NOT NULL`; `Yes` means `NULL` is allowed. |
| **Default** | Database default, `—` when there is none. |
| **Existing or proposed** | `Existing` = verified in the live database; `Proposed` = design only, not implemented. |

---

## 3. Existing entity — `users`

**Purpose:** stores registered users and authentication identity.  
**Primary key:** `user_id`.  
**Foreign keys:** none.  
**Relationships:** one user to many workouts, nutrition logs, health metric records, and (proposed) heart-rate samples.

| Entity | Attribute | Data type | PK | FK | Nullable | Default | Description | Existing or proposed |
|---|---|---|---|---|---|---|---|---|
| users | `user_id` | `INT UNSIGNED` | Yes (PK) | — | No | `AUTO_INCREMENT` | Surrogate identifier for the user. | Existing |
| users | `full_name` | `VARCHAR(100)` | No | — | No | — | Display name. | Existing |
| users | `email` | `VARCHAR(150)` | No | — | No | — | Login email; protected by `uq_users_email` UNIQUE constraint. | Existing |
| users | `password_hash` | `VARCHAR(255)` | No | — | No | — | Werkzeug password hash; plaintext passwords are never stored. | Existing |
| users | `date_of_birth` | `DATE` | No | — | Yes | `NULL` | Date of birth; can support age-based maximum heart-rate estimates. | Existing |
| users | `gender` | `ENUM('Male','Female','Other','Prefer not to say')` | No | — | Yes | `NULL` | Profile gender. | Existing |
| users | `height_cm` | `DECIMAL(5,2)` | No | — | Yes | `NULL` | Profile height in centimetres; CHECK requires greater than 0 and less than 300. | Existing |
| users | `created_at` | `TIMESTAMP` | No | — | No | `CURRENT_TIMESTAMP` | Account creation timestamp. | Existing |
| users | `updated_at` | `TIMESTAMP` | No | — | No | `CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP` | Last profile update timestamp. | Existing |

---

## 4. Existing entity — `workouts`

**Purpose:** stores one workout session per row.  
**Primary key:** `workout_id`.  
**Foreign key:** `user_id` → `users.user_id` on `ON DELETE CASCADE ON UPDATE CASCADE`.  
**Relationships:** many workouts belong to one user; one workout to many (proposed) `workout_exercises` rows.

| Entity | Attribute | Data type | PK | FK | Nullable | Default | Description | Existing or proposed |
|---|---|---|---|---|---|---|---|---|
| workouts | `workout_id` | `INT UNSIGNED` | Yes (PK) | — | No | `AUTO_INCREMENT` | Surrogate identifier for the workout session. | Existing |
| workouts | `user_id` | `INT UNSIGNED` | No | `users.user_id` | No | — | Owner of the workout. | Existing |
| workouts | `exercise_name` | `VARCHAR(100)` | No | — | No | — | **Legacy free-text exercise label.** One value per workout row; this is why one workout cannot currently contain many exercises. | Existing |
| workouts | `duration_minutes` | `INT UNSIGNED` | No | — | No | — | Total session duration in minutes; CHECK requires 1–1440. | Existing |
| workouts | `calories_burned` | `INT UNSIGNED` | No | — | Yes | `NULL` | Estimated session calories; CHECK requires 10,000 or fewer when present. | Existing |
| workouts | `workout_date` | `DATE` | No | — | No | — | Date of the workout. Time of day is not stored. | Existing |

**Indexes:** `PRIMARY (workout_id)`, `idx_workouts_user_date (user_id, workout_date)`.

---

## 5. Existing entity — `nutrition_logs`

**Purpose:** stores one food item per row with calories and macronutrients.  
**Primary key:** `nutrition_id`.  
**Foreign key:** `user_id` → `users.user_id` on `ON DELETE CASCADE ON UPDATE CASCADE`.  
**Relationships:** many nutrition logs belong to one user.

| Entity | Attribute | Data type | PK | FK | Nullable | Default | Description | Existing or proposed |
|---|---|---|---|---|---|---|---|---|
| nutrition_logs | `nutrition_id` | `INT UNSIGNED` | Yes (PK) | — | No | `AUTO_INCREMENT` | Surrogate identifier for the food record. | Existing |
| nutrition_logs | `user_id` | `INT UNSIGNED` | No | `users.user_id` | No | — | Owner of the nutrition record. | Existing |
| nutrition_logs | `food_name` | `VARCHAR(120)` | No | — | No | — | Free-text name of one food item. | Existing |
| nutrition_logs | `meal_type` | `ENUM('Breakfast','Lunch','Dinner','Snack')` | No | — | No | — | Meal category. | Existing |
| nutrition_logs | `calories` | `INT UNSIGNED` | No | — | No | — | Energy intake for this food item, in kilocalories; CHECK requires 10,000 or fewer. | Existing |
| nutrition_logs | `protein` | `DECIMAL(6,1)` | No | — | Yes | `NULL` | Protein in grams; CHECK requires 0–1000 when present. | Existing |
| nutrition_logs | `carbohydrates` | `DECIMAL(6,1)` | No | — | Yes | `NULL` | Carbohydrates in grams; CHECK requires 0–1000 when present. | Existing |
| nutrition_logs | `fat` | `DECIMAL(6,1)` | No | — | Yes | `NULL` | Fat in grams; CHECK requires 0–1000 when present. | Existing |
| nutrition_logs | `log_date` | `DATE` | No | — | No | — | Date of intake. **Time of day is not stored in the live table.** | Existing |
| nutrition_logs | `logged_at` | `DATETIME` | No | — | Yes | `NULL` | Optional meal timestamp proposed by `database/migration_nutrition_time.sql`. `log_date` remains authoritative for daily totals. | Proposed |

**Indexes:** `PRIMARY (nutrition_id)`, `idx_nutrition_user_date (user_id, log_date)`.

---

## 6. Existing entity — `health_metrics`

**Purpose:** stores one daily health snapshot per user.  
**Primary key:** `metric_id`.  
**Foreign key:** `user_id` → `users.user_id` on `ON DELETE CASCADE ON UPDATE CASCADE`.  
**Relationships:** many daily health records belong to one user; one record per user per day via `uq_health_user_date`.

| Entity | Attribute | Data type | PK | FK | Nullable | Default | Description | Existing or proposed |
|---|---|---|---|---|---|---|---|---|
| health_metrics | `metric_id` | `INT UNSIGNED` | Yes (PK) | — | No | `AUTO_INCREMENT` | Surrogate identifier for the daily health record. | Existing |
| health_metrics | `user_id` | `INT UNSIGNED` | No | `users.user_id` | No | — | Owner of the health record. | Existing |
| health_metrics | `weight` | `DECIMAL(5,2)` | No | — | No | — | Body weight in kilograms; CHECK requires greater than 0 and less than 500. | Existing |
| health_metrics | `height` | `DECIMAL(5,2)` | No | — | No | — | Height in centimetres at the time of the record; CHECK requires greater than 0 and less than 300. | Existing |
| health_metrics | `steps` | `INT UNSIGNED` | No | — | No | `0` | Daily step count; CHECK requires 200,000 or fewer. | Existing |
| health_metrics | `calories_burned` | `INT UNSIGNED` | No | — | No | `0` | Daily activity calories; CHECK requires 10,000 or fewer. | Existing |
| health_metrics | `recorded_date` | `DATE` | No | — | No | — | Date of the health snapshot. Time of day is not stored. | Existing |

**Indexes and constraints:** `PRIMARY (metric_id)`, `uq_health_user_date (user_id, recorded_date)` UNIQUE, plus CHECK constraints on weight, height, steps and calories.

**BMI note:** BMI is **not stored**. It is derived from `weight` and `height` with:

```text
BMI = weight_kg / ((height_cm / 100) * (height_cm / 100))
```

The application rounds BMI to one decimal place. No BMI column is required for Milestone 1; a stored/generated BMI column is an optional Milestone 2 decision.

---

## 7. Proposed entity — `exercises`

**Status:** Proposed, not implemented.  
**Purpose:** a reusable exercise catalogue so an exercise has a stable identity and category.  
**Primary key:** `exercise_id`.  
**Foreign keys:** none.  
**Relationships:** one exercise to many `workout_exercises` rows.

| Entity | Attribute | Data type | PK | FK | Nullable | Default | Description | Existing or proposed |
|---|---|---|---|---|---|---|---|---|
| exercises | `exercise_id` | `INT UNSIGNED` | Yes (PK) | — | No | `AUTO_INCREMENT` | Surrogate identifier for the exercise. | Proposed |
| exercises | `exercise_name` | `VARCHAR(100)` | No | — | No | — | Canonical exercise name; UNIQUE (`uq_exercises_name`). | Proposed |
| exercises | `muscle_group` | `VARCHAR(50)` | No | — | Yes | `NULL` | Primary muscle group, such as Legs, Chest, Back, Shoulders, Core, or Full body. | Proposed |
| exercises | `exercise_type` | `ENUM('Strength','Cardio','Flexibility','Balance','Other')` | No | — | No | `'Other'` | Exercise classification used for workout-category summaries. | Proposed |
| exercises | `description` | `VARCHAR(500)` | No | — | Yes | `NULL` | Optional coaching or technique notes. | Proposed |
| exercises | `created_at` | `TIMESTAMP` | No | — | No | `CURRENT_TIMESTAMP` | Catalogue creation timestamp. | Proposed |

**Why these attributes:** they identify and classify an exercise. Sets, repetitions, weight, and duration describe a specific performance, so they belong in `workout_exercises`, not in the catalogue. Migration: `database/migration_exercises.sql`.

---

## 8. Proposed entity — `workout_exercises`

**Status:** Proposed, not implemented.  
**Purpose:** junction table that implements **one workout → many exercises** and stores per-exercise performance.  
**Primary key:** `workout_exercise_id`.  
**Foreign keys:** `workout_id` → `workouts.workout_id`; `exercise_id` → `exercises.exercise_id`.  
**Relationships:** many rows belong to one workout; many rows reference one exercise; resolves the many-to-many relationship between workouts and exercises.

| Entity | Attribute | Data type | PK | FK | Nullable | Default | Description | Existing or proposed |
|---|---|---|---|---|---|---|---|---|
| workout_exercises | `workout_exercise_id` | `INT UNSIGNED` | Yes (PK) | — | No | `AUTO_INCREMENT` | Surrogate identifier for one exercise entry within a workout. | Proposed |
| workout_exercises | `workout_id` | `INT UNSIGNED` | No | `workouts.workout_id` | No | — | Parent workout; proposed `ON DELETE CASCADE`. | Proposed |
| workout_exercises | `exercise_id` | `INT UNSIGNED` | No | `exercises.exercise_id` | No | — | Exercise performed; proposed `ON DELETE RESTRICT`. | Proposed |
| workout_exercises | `exercise_order` | `INT UNSIGNED` | No | — | No | — | Position of the exercise inside the workout (1, 2, 3, …); proposed `UNIQUE (workout_id, exercise_order)`. | Proposed |
| workout_exercises | `sets` | `INT UNSIGNED` | No | — | Yes | `NULL` | Number of sets performed; CHECK 1–100 when present. | Proposed |
| workout_exercises | `repetitions` | `INT UNSIGNED` | No | — | Yes | `NULL` | Repetitions per set; CHECK 1–1000 when present. | Proposed |
| workout_exercises | `weight_kg` | `DECIMAL(6,2)` | No | — | Yes | `NULL` | Weight used, in kilograms; CHECK 0–1000 when present. | Proposed |
| workout_exercises | `duration_minutes` | `INT UNSIGNED` | No | — | Yes | `NULL` | Exercise duration in minutes; CHECK 1–1440 when present. | Proposed |
| workout_exercises | `calories_burned` | `INT UNSIGNED` | No | — | Yes | `NULL` | Calories attributed to this exercise; CHECK 10,000 or fewer. | Proposed |

**Relationship to the current `workouts.exercise_name` field**

- `workouts.exercise_name` is the current, denormalized free-text label. It allows exactly one exercise label per workout row.
- The proposed design keeps `workouts` as the session header and moves exercise detail into `workout_exercises`.
- Migration path for a later milestone: keep `exercise_name` during the transition, create one `exercises` row per distinct name, create `workout_exercises` rows linked to each workout, then deprecate `exercise_name` after the application is updated and verified.
- **Do not drop `exercise_name` now.** No schema change is part of Milestone 1.

---

## 9. Proposed entity — `heart_rate_zones`

**Status:** Proposed, not implemented.  
**Purpose:** reference table defining heart-rate zones so time-in-zone can be classified consistently.  
**Primary key:** `zone_id`.  
**Foreign keys:** none.  
**Relationships:** one zone to many `heart_rate_samples` rows (proposed).

| Entity | Attribute | Data type | PK | FK | Nullable | Default | Description | Existing or proposed |
|---|---|---|---|---|---|---|---|---|
| heart_rate_zones | `zone_id` | `INT UNSIGNED` | Yes (PK) | — | No | `AUTO_INCREMENT` | Surrogate identifier for the zone. | Proposed |
| heart_rate_zones | `zone_name` | `VARCHAR(20)` | No | — | No | — | Zone label (`Zone 1` … `Zone 5`); UNIQUE (`uq_hr_zone_name`). | Proposed |
| heart_rate_zones | `minimum_percentage` | `DECIMAL(5,2)` | No | — | No | — | Inclusive lower bound as a percentage of estimated maximum heart rate. | Proposed |
| heart_rate_zones | `maximum_percentage` | `DECIMAL(5,2)` | No | — | No | — | Exclusive upper bound as a percentage; CHECK `0 <= min < max <= 100`. | Proposed |

**Scope note:** these are **shared reference** thresholds. The application applies them to `estimated_max_hr = 220 − age` (fallback `190`) and resolves a sample's zone. Per-user thresholds are a documented future enhancement, not part of the current migration. Migration: `database/migration_heart_rate.sql`.

---

## 10. Proposed entity — `heart_rate_samples`

**Status:** Proposed, not implemented.  
**Purpose:** stores time-based heart-rate readings so the system can support real-time or time-based health metrics and zone analysis.  
**Primary key:** `sample_id`.  
**Foreign keys:** `user_id` → `users.user_id`; `zone_id` → `heart_rate_zones.zone_id`.  
**Relationships:** many samples belong to one user; many samples can be classified into one zone.

| Entity | Attribute | Data type | PK | FK | Nullable | Default | Description | Existing or proposed |
|---|---|---|---|---|---|---|---|---|
| heart_rate_samples | `sample_id` | `INT UNSIGNED` | Yes (PK) | — | No | `AUTO_INCREMENT` | Surrogate identifier for the reading. | Proposed |
| heart_rate_samples | `user_id` | `INT UNSIGNED` | No | `users.user_id` | No | — | Owner of the reading. | Proposed |
| heart_rate_samples | `zone_id` | `INT UNSIGNED` | No | `heart_rate_zones.zone_id` | Yes | `NULL` | Zone assigned from the BPM value; nullable when a reading cannot be classified. | Proposed |
| heart_rate_samples | `heart_rate_bpm` | `SMALLINT UNSIGNED` | No | — | No | — | Heart rate in beats per minute; CHECK 20–250. | Proposed |
| heart_rate_samples | `recorded_at` | `DATETIME` | No | — | No | — | Exact timestamp of the reading; this is what makes the record time-based. | Proposed |

**Proposed indexes:** `(user_id, recorded_at)` for time-series queries and `(zone_id)` for the FK.  
**Data-integrity note:** `zone_id` is recalculated by the application from `heart_rate_bpm` and the zone bounds on every write. MySQL CHECK constraints cannot reference another table, so the database cannot enforce cross-table agreement by itself; the application rule is tested. Migration: `database/migration_heart_rate.sql`.

---

## 11. Existing constraints and relationships (summary)

| Table | Primary key | Foreign keys | Unique constraints | CHECK constraints |
|---|---|---|---|---|
| `users` | `user_id` | — | `uq_users_email (email)` | `chk_users_height_cm` |
| `workouts` | `workout_id` | `user_id` → `users.user_id` | — | `chk_workouts_duration`, `chk_workouts_calories` |
| `nutrition_logs` | `nutrition_id` | `user_id` → `users.user_id` | — | `chk_nutrition_calories`, `chk_nutrition_protein`, `chk_nutrition_carbohydrates`, `chk_nutrition_fat` |
| `health_metrics` | `metric_id` | `user_id` → `users.user_id` | `uq_health_user_date (user_id, recorded_date)` | `chk_health_weight`, `chk_health_height`, `chk_health_steps`, `chk_health_calories_burned` |
| `exercises` (proposed) | `exercise_id` | — | `exercise_name` | ENUM domain only |
| `workout_exercises` (proposed) | `workout_exercise_id` | `workout_id` → `workouts`; `exercise_id` → `exercises` | `(workout_id, exercise_order)` | sets, repetitions, weight, duration, calories |
| `heart_rate_zones` (proposed) | `zone_id` | — | `zone_name` | `chk_hr_zone_order` |
| `heart_rate_samples` (proposed) | `sample_id` | `user_id` → `users`; `zone_id` → `heart_rate_zones` | — | `chk_hr_bpm` |

All three existing foreign keys use `ON DELETE CASCADE ON UPDATE CASCADE`. Proposed delete rules: workout → workout_exercises CASCADE; exercise → workout_exercises RESTRICT; user → heart_rate_samples CASCADE; zone → heart_rate_samples SET NULL.

---

## 12. Macronutrient ratio definitions (existing fields only)

Macronutrient ratios are **calculable** from the existing `nutrition_logs.protein`, `carbohydrates`, and `fat` columns. No new column is required for Milestone 1.

Use the Atwater energy factors:

```text
protein_kcal      = protein_g * 4
carbohydrate_kcal = carbohydrates_g * 4
fat_kcal          = fat_g * 9
total_macro_kcal  = protein_kcal + carbohydrate_kcal + fat_kcal

protein_ratio_pct      = protein_kcal      / NULLIF(total_macro_kcal, 0) * 100
carbohydrate_ratio_pct = carbohydrate_kcal / NULLIF(total_macro_kcal, 0) * 100
fat_ratio_pct          = fat_kcal          / NULLIF(total_macro_kcal, 0) * 100
```

**Accuracy note:** the stored `calories` value may not equal `total_macro_kcal` because of fibre, alcohol, label rounding, or manufacturer data. Any macronutrient-ratio report should state which denominator it uses (macro-derived energy or the stored calorie value).

---

## 13. Time-based and calorie definitions

| Concept | Existing field | Proposed field | Notes |
|---|---|---|---|
| Body weight | `health_metrics.weight` | — | Kilograms, daily snapshot. |
| BMI | Derived from `weight` and `height` | Optional stored/generated column in Milestone 2 | Not currently stored. |
| Intake calories | `nutrition_logs.calories` | — | Per food item. |
| Session activity calories | `workouts.calories_burned` | — | Per workout session. |
| Daily activity calories | `health_metrics.calories_burned` | — | Daily aggregate. Must be defined carefully to avoid double counting with `workouts.calories_burned`. |
| Steps | `health_metrics.steps` | — | Daily. |
| Heart rate | — | `heart_rate_samples.heart_rate_bpm`, `heart_rate_samples.recorded_at` | Time-based. |
| Heart-rate zones | — | `heart_rate_zones` + `heart_rate_samples.zone_id` | Global default thresholds in this draft. |
| Time-based health records | `health_metrics.recorded_date` is date-only | `heart_rate_samples.recorded_at` | Other health metrics remain daily in this draft. |
| Nutrition time of day | `nutrition_logs.log_date` is date-only | Optional `logged_at DATETIME` | Not required for Milestone 1; recommended if the mentor wants meal timing. |

---

## 14. Status and limitations

- The four existing entities and all their columns, types, nullability, defaults, keys, and constraints were verified read-only against the live Aiven database.
- The four proposed entities are a design proposal. They are **not** present in the database, and no application route uses them.
- `workouts.exercise_name` remains the only exercise representation in the current implementation.
- Heart rate and heart-rate zones are not implemented.
- No data was inserted or modified while preparing this dictionary.
- The `docs/archive/` documents describe an older five-table design and must not be used as the current data dictionary.

---

**Document status:** Created for Milestone 1; proposed entity design updated for the finalized Milestone 2 model.  
**Next document:** `docs/LOGIC_FLOW.md`.  
**Final Milestone 1 summary:** `docs/MILESTONE_1_REPORT.md`.
