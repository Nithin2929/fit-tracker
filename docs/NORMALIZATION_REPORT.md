# FitTrack — Normalization Report (Milestone 2)

**Project:** FitTrack — Fitness & Wellness Tracking Database System  
**Database:** Aiven Cloud MySQL `fitness_wellness_db`  
**Scope:** the four live tables plus the four proposed tables and one proposed nullable column.  
**Method:** analysis of the actual `CREATE TABLE` definitions and live `information_schema` metadata. No table was modified to produce this report.

---

## 1. Executive summary

| Table | 1NF | 2NF | 3NF | Verdict |
|---|---|---|---|---|
| `users` | Yes | Yes | Yes | Normalized |
| `workouts` | Yes | Yes | **Partial** | `exercise_name` is a denormalized free-text label; normalized by `exercises` + `workout_exercises` |
| `nutrition_logs` | Yes | Yes | **Partial** | `food_name` is free text; macros are atomic and ratios are derivable, so no ratio column is needed |
| `health_metrics` | Yes | Yes | Yes (with documented snapshot semantics) | Height is a historical snapshot, not a copy of the current profile |
| `exercises` (proposed) | Yes | Yes | Yes | Catalogue with a natural unique key |
| `workout_exercises` (proposed) | Yes | Yes | Yes | Junction with surrogate PK and a unique ordering rule |
| `heart_rate_zones` (proposed) | Yes | Yes | Yes | Shared reference table |
| `heart_rate_samples` (proposed) | Yes | Yes | Yes | Time-series fact table; `zone_id` is a derived convenience reference |

**Conclusion:** the live schema is in 1NF and 2NF. It is *formally* in 3NF because no non-key column determines another non-key column inside a table; however, `workouts.exercise_name` and `nutrition_logs.food_name` are free-text reference values that should be normalized for the mentor's multi-exercise requirement. The proposed exercise migration fixes the only structural gap that blocks a required relationship.

---

## 2. Functional dependencies (actual schema)

Notation: `X → Y` means X determines Y.

### 2.1 `users`

```text
user_id      → full_name, email, password_hash, date_of_birth, gender,
               height_cm, created_at, updated_at
email        → user_id, full_name, password_hash, date_of_birth, gender,
               height_cm, created_at, updated_at   (candidate key)
```

- `user_id` is the chosen surrogate primary key.
- `email` is a natural candidate key enforced by `uq_users_email`.

### 2.2 `workouts`

```text
workout_id → user_id, exercise_name, duration_minutes, calories_burned, workout_date
```

No other non-key dependency is declared. `exercise_name` does **not** determine `duration_minutes` or `calories_burned`; the same exercise can be performed for different durations and burn different calories.

### 2.3 `nutrition_logs`

```text
nutrition_id → user_id, food_name, meal_type, calories, protein,
               carbohydrates, fat, log_date
```

`calories` is recorded energy intake; it is not functionally determined by the three macro grams because fibre, alcohol, rounding, and label data vary. Macro ratios are therefore **calculated**, not stored.

### 2.4 `health_metrics`

```text
metric_id → user_id, weight, height, steps, calories_burned, recorded_date
(user_id, recorded_date) → metric_id, weight, height, steps, calories_burned
```

`(user_id, recorded_date)` is a candidate key enforced by `uq_health_user_date`.

### 2.5 Proposed `workout_exercises`

```text
workout_exercise_id → workout_id, exercise_id, exercise_order, sets,
                      repetitions, weight_kg, duration_minutes, calories_burned
(workout_id, exercise_order) → workout_exercise_id, exercise_id, sets, ...
```

The unique pair is a candidate key, but the surrogate PK is retained for consistency with the rest of the schema and for simple foreign-key references from future features (for example, set-level logging).

### 2.6 Proposed heart-rate tables

```text
zone_id   → zone_name, minimum_percentage, maximum_percentage
sample_id → user_id, zone_id, heart_rate_bpm, recorded_at
```

`zone_id` is intentionally nullable. It is a resolved convenience value; the authoritative input is `heart_rate_bpm` plus the user's estimated maximum heart rate.

---

## 3. First Normal Form (1NF)

**Rule:** every column holds one atomic value; no repeating groups; no multi-valued columns; each row is unique.

| Table | Evidence | Result |
|---|---|---|
| `users` | Every column is scalar: `VARCHAR`, `DATE`, `ENUM`, `DECIMAL`, `TIMESTAMP`. One row per account, PK `user_id`. | Pass |
| `workouts` | One row per session. `exercise_name` holds one text label, not a comma-separated list. `duration_minutes`, `calories_burned`, and `workout_date` are scalar. | Pass |
| `nutrition_logs` | One row per food item. `food_name` is a single item. Calories and the three macro grams are separate numeric columns, not a repeat group. | Pass |
| `health_metrics` | One row per user per day. Weight, height, steps, and calories are separate scalar columns. | Pass |
| `exercises` (proposed) | One row per catalogue exercise; scalar attributes. | Pass |
| `workout_exercises` (proposed) | One row per exercise performed inside one workout; sets/reps/weight/duration are scalar. Repeating exercises become multiple rows, not `exercise1`, `exercise2` columns. | Pass |
| `heart_rate_zones` (proposed) | One row per zone; scalar bounds. | Pass |
| `heart_rate_samples` (proposed) | One row per reading; scalar BPM and timestamp. | Pass |

**Note on `workouts.exercise_name`:** storing one text value per row satisfies 1NF literally. The problem is not atomicity; it is that one session cannot represent multiple exercises. The correct 1NF-compliant fix is a child table, **not** a comma-separated string. This is exactly what `workout_exercises` provides.

**Note on `nutrition_logs`:** one row per food item is the correct granularity. Combining several foods into one row would make calories and macros ambiguous and would violate 1NF intent.

---

## 4. Second Normal Form (2NF)

**Rule:** the table is in 1NF and every non-key attribute depends on the **whole** primary key; no partial dependency on part of a composite key.

| Table | Key | Analysis | Result |
|---|---|---|---|
| `users` | `user_id` (single) | Every non-key column depends on the whole key. No composite key, so no partial dependency is possible. | Pass |
| `workouts` | `workout_id` (single) | All columns describe the session identified by `workout_id`. | Pass |
| `nutrition_logs` | `nutrition_id` (single) | All columns describe the food record identified by `nutrition_id`. | Pass |
| `health_metrics` | `metric_id` (single) | All columns describe the snapshot identified by `metric_id`. The unique `(user_id, recorded_date)` is a candidate key, not a composite PK. | Pass |
| `exercises` (proposed) | `exercise_id` (single) | Description fields depend on the exercise as a whole. | Pass |
| `workout_exercises` (proposed) | `workout_exercise_id` (single) | All performance values depend on the specific session line. If the composite `(workout_id, exercise_order)` were used as the PK instead, `exercise_id`, sets, reps, weight, duration, and calories would all depend on both columns, so 2NF would still hold. | Pass |
| `heart_rate_zones` (proposed) | `zone_id` (single) | Percentage bounds describe the zone. | Pass |
| `heart_rate_samples` (proposed) | `sample_id` (single) | BPM/timestamp describe the reading. | Pass |

**Key-design justification:** a surrogate key is used for `workout_exercises` because the current schema consistently uses surrogate PKs, and because a future set-level table can reference `workout_exercise_id` directly. The composite candidate key `(workout_id, exercise_order)` is still enforced by a UNIQUE constraint, so the business rule cannot be violated.

---

## 5. Third Normal Form (3NF)

**Rule:** the table is in 2NF and no non-key attribute transitively determines another non-key attribute.

### 5.1 `users` — pass

No non-key column determines another. `full_name`, `date_of_birth`, `gender`, and `height_cm` are independent profile facts. `created_at` and `updated_at` are audit timestamps.

### 5.2 `workouts` — formal pass, design partial

No non-key → non-key dependency is declared. The issue is **reference data**, not a transitive dependency:

- `exercise_name` is free text. Two rows saying `"Running"` and `"running "` are the same concept with no shared identity.
- The mentor requires one workout → many exercises, which a single column cannot express.

**Normalization improvement:** `exercises` (catalogue) + `workout_exercises` (session lines). The legacy column is a transitional label, not the final source of exercise identity.

### 5.3 `nutrition_logs` — formal pass, optional improvement

- `food_name` is free text, so spelling variants are not linked. A `foods` catalogue is a possible future normalization.
- **Macronutrient ratios must not be stored.** Protein/carbohydrate/fat ratios are derived from grams; storing them would create a transitive dependency (`protein, carbs, fat → ratio`) and would go stale if grams are edited.
- `calories` is recorded independently of the three macros, so it is not a derived duplicate.

The mentor's macro-ratio requirement is therefore satisfied by calculation, not by a new column.

### 5.4 `health_metrics` — pass, with snapshot policy

Potential concern: `users.height_cm` and `health_metrics.height` both store height.

Resolution:

- `users.height_cm` = current profile height, updated when the user's profile changes.
- `health_metrics.height` = height **at the time of that measurement**, used to compute the BMI for that date.
- Copying the current profile height into a historical record is not a transitive dependency; it is the documented snapshot design used by the application's BMI formula.

No schema change is required. If the mentor prefers a single source, the alternative is to remove `health_metrics.height` and join `users.height_cm`; that would make historical BMI change retroactively when the profile changes, which is worse for trend reporting.

### 5.5 Proposed tables — pass

- `exercises`: `exercise_name` is a candidate key. `muscle_group`, `exercise_type`, and `description` describe that exercise and nothing else.
- `workout_exercises`: no non-key determines another. `exercise_order` is a session-line attribute; it is not derived from `exercise_id` because the same exercise can appear at different orders.
- `heart_rate_zones`: bounds depend only on the zone.
- `heart_rate_samples`: `zone_id` is technically derivable from `heart_rate_bpm` and the zone thresholds. It is retained as a **denormalized convenience reference** for time-in-zone reporting, with two safeguards: it is nullable, and the application resolves it at write time. A strict 3NF alternative is to store only BPM and join to the zone table on percentage bounds; that join cannot use a simple foreign key and is slower for time-series reports. This trade-off is documented and tested for consistency.

---

## 6. Anomaly analysis

### 6.1 Insert anomalies

| Table | Anomaly | Example | Fix |
|---|---|---|---|
| `workouts` | Cannot insert a workout with several exercises. | A session with squat, bench, and row must be three unrelated workout rows or one free-text label. | `workout_exercises` junction. |
| `workouts` | Exercise identity is created implicitly. | Typo `"Runnin"` becomes a new pseudo-exercise; there is no catalogue row to reuse. | `exercises` catalogue with unique names. |
| `nutrition_logs` | Food identity is created implicitly. | `"Oats"`, `"oats"`, and `"Oatmeal"` are unrelated strings. | Optional `foods` lookup; not required by the mentor. |
| `health_metrics` | Cannot store several heart-rate readings in a day. | The unique daily rule blocks a second reading. | `heart_rate_samples` with DATETIME. |
| `heart_rate_samples` (proposed) | Cannot store a reading without a user. | FK rejects an unknown `user_id`. | Intended integrity rule. |

### 6.2 Update anomalies

| Table | Anomaly | Example | Fix |
|---|---|---|---|
| `workouts` | Renaming an exercise requires updating many free-text rows. | Changing `"Running"` to `"Outdoor Run"` across 40 sessions is error-prone. | Rename one `exercises` row. |
| `health_metrics` | A profile height update does not change history. | The user grows or corrects height; past BMI should remain based on the recorded height. | Documented snapshot policy. |
| `nutrition_logs` | Renaming a food requires many row updates. | `"Oats"` logged 100 times. | Optional `foods` lookup. |
| `heart_rate_samples` (proposed) | Editing BPM without editing `zone_id` would desynchronize the zone. | 120 BPM changed to 170 BPM but zone stays Zone 2. | Application recomputes the zone on every write; documented consistency rule. |

### 6.3 Delete anomalies

| Table | Anomaly | Example | Fix |
|---|---|---|---|
| `workouts` | Deleting one workout loses the only record of its exercise name. | A session label disappears with the row. | The catalogue persists independently in `exercises`. |
| `workouts` + `workout_exercises` | Deleting a workout must also remove its exercise lines. | Orphan junction rows would remain. | FK `ON DELETE CASCADE`. |
| `exercises` | Deleting a catalogue exercise that is used by history would destroy meaning. | `"Squat"` referenced by 50 sessions. | FK `ON DELETE RESTRICT`. |
| `heart_rate_zones` | Deleting a zone must not delete readings. | Zone 5 retired. | FK `ON DELETE SET NULL`; readings remain. |
| `users` | Deleting a user should remove personal data. | Account closure. | Existing `ON DELETE CASCADE` on all child tables. |

---

## 7. Recommended normalization target

```text
users
  └── workouts
        └── workout_exercises ── exercises
  └── nutrition_logs
  └── health_metrics
  └── heart_rate_samples ── heart_rate_zones
```

| Change | Reason | Status |
|---|---|---|
| Add `exercises` | Remove free-text exercise identity; enable categories. | Proposed migration |
| Add `workout_exercises` | Implement 1 workout → many exercises and performance detail. | Proposed migration |
| Add `heart_rate_zones` | Shared reference data for time-in-zone analysis. | Proposed migration |
| Add `heart_rate_samples` | Time-based biometric readings. | Proposed migration |
| Add `nutrition_logs.logged_at` | Optional meal timing; `log_date` remains authoritative. | Proposed migration |
| Keep BMI derived | Avoid a derived duplicate that can go stale. | Decision |
| Keep `users.height_cm` + `health_metrics.height` | Current profile vs historical snapshot. | Decision |
| Keep `food_name` free text | Not required for the mentor's normalization scope; optional `foods` future work. | Deferred |

---

## 8. What is **not** claimed

- The live database is **not** yet in the target normalized exercise model; `exercises` and `workout_exercises` do not exist in Aiven.
- No macro-ratio column exists, and none is needed.
- No BMI column exists, and none is needed.
- The `heart_rate_samples.zone_id` convenience reference is a documented, controlled denormalization, not a claim of perfect 3NF.
- The archive documents in `docs/archive/` describe an obsolete five-table design and are not evidence for this report.

---

**Related documents:** `docs/ER_DIAGRAM.md`, `docs/PHYSICAL_SCHEMA.md`, `docs/DATA_DICTIONARY.md`.
