# Database Design — Fitness & Wellness Tracking

Database: **`fitness_wellness_db`**
Engine: **InnoDB**
Character set: **`utf8mb4`** / **`utf8mb4_unicode_ci`**

The design uses five normalized tables. Each table has one clear job, and every
row of user data is linked to exactly one user.

---

## 1. Relationship diagram

```text
┌──────────────────────────┐
│          users           │
│  user_id (PK)            │
│  email (UNIQUE)          │
│  password_hash           │
│  ...                     │
└────────────┬─────────────┘
             │ 1
             │
     ┌───────┼────────────┬────────────────┐
     │       │            │                │
     │ N     │ N          │ N              │ N
┌────▼────┐ ┌▼───────────┐ ┌▼────────────┐ ┌▼────────────┐
│ workouts│ │daily_      │ │   goals     │ │  progress   │
│         │ │wellness    │ │             │ │             │
└─────────┘ └────────────┘ └─────────────┘ └─────────────┘
```

- One **user** can have many **workouts**.
- One **user** can have many **daily wellness** rows — but only one per date.
- One **user** can have many **goals**.
- One **user** can have many **progress** entries — but only one per date.

All four child tables use:

```sql
FOREIGN KEY (user_id) REFERENCES users (user_id)
ON DELETE CASCADE ON UPDATE CASCADE
```

`ON DELETE CASCADE` means deleting a user automatically removes that user's
workouts, wellness logs, goals, and progress history. This prevents orphan rows.

---

## 2. Table-by-table explanation

### 2.1 `users`

Stores login credentials and basic profile information.

| Column          | Type           | Rules                          | Why |
| --------------- | -------------- | ------------------------------ | --- |
| `user_id`       | `INT UNSIGNED` | PK, auto-increment             | Stable numeric identifier |
| `full_name`     | `VARCHAR(100)` | NOT NULL                       | Display name |
| `email`         | `VARCHAR(150)` | NOT NULL, UNIQUE               | Login name; no duplicate accounts |
| `password_hash` | `VARCHAR(255)` | NOT NULL                       | Stores a hash, never the password |
| `date_of_birth` | `DATE`         | NULL allowed                   | Optional profile detail |
| `gender`        | `ENUM(...)`    | NULL allowed                   | Optional, limited to known values |
| `height_cm`     | `DECIMAL(5,2)` | NULL, CHECK 0 < height < 300   | Used for BMI/height display |
| `created_at`    | `TIMESTAMP`    | NOT NULL, default now          | Audit trail |
| `updated_at`    | `TIMESTAMP`    | Auto-updates on change         | Audit trail |

`email` uses the case-insensitive collation, so `User@Example.com` and
`user@example.com` are treated as the same address by the unique constraint.

`password_hash` is 255 characters because secure hashes (for example Werkzeug's
scrypt hash or bcrypt) can be long. **Never** change this column to store plain
text.

---

### 2.2 `workouts`

One row per workout session. A user can log several workouts on the same day,
so there is no unique constraint on `(user_id, workout_date)`.

| Column             | Type                | Rules                         | Why |
| ------------------ | ------------------- | ----------------------------- | --- |
| `workout_id`       | `INT UNSIGNED`      | PK, auto-increment            | Unique session ID |
| `user_id`          | `INT UNSIGNED`      | NOT NULL, FK → `users`        | Owner of the workout |
| `workout_type`     | `VARCHAR(80)`       | NOT NULL                      | Walking, running, gym, yoga, etc. |
| `duration_minutes` | `SMALLINT UNSIGNED` | NOT NULL, CHECK 1–1440        | Positive duration; max one day |
| `calories_burned`  | `SMALLINT UNSIGNED` | NULL, CHECK ≤ 10000           | Optional estimate |
| `workout_date`     | `DATE`              | NOT NULL                      | The day the workout happened |
| `notes`            | `VARCHAR(255)`      | NULL                          | Optional short note |
| `created_at`       | `TIMESTAMP`         | Default now                   | When the row was saved |
| `updated_at`       | `TIMESTAMP`         | Auto-updates                  | When it was last edited |

Index `idx_workouts_user_date (user_id, workout_date)` makes the common query
"show this user's workouts for a date range" fast.

---

### 2.3 `daily_wellness`

One row per user per day for water, sleep, and steps.

| Column             | Type                | Rules                          | Why |
| ------------------ | ------------------- | ------------------------------ | --- |
| `wellness_id`      | `INT UNSIGNED`      | PK, auto-increment             | Unique row ID |
| `user_id`          | `INT UNSIGNED`      | NOT NULL, FK → `users`         | Owner |
| `log_date`         | `DATE`              | NOT NULL                       | The day being tracked |
| `water_intake_ml`  | `SMALLINT UNSIGNED` | NOT NULL, default 0, CHECK ≤ 20000 | Millilitres are precise and easy to sum |
| `sleep_hours`      | `DECIMAL(3,1)`      | NOT NULL, default 0, CHECK 0–24 | Allows 7.5 hours without float errors |
| `steps`            | `INT UNSIGNED`      | NOT NULL, default 0, CHECK ≤ 200000 | Manual daily step count |
| `created_at`       | `TIMESTAMP`         | Default now                    | Audit trail |
| `updated_at`       | `TIMESTAMP`         | Auto-updates                   | Last edit time |

**`UNIQUE (user_id, log_date)`** is the most important rule here: a user has at
most one wellness record per day. In Phase 6 the app will use:

```sql
INSERT INTO daily_wellness (user_id, log_date, water_intake_ml, sleep_hours, steps)
VALUES (%s, %s, %s, %s, %s)
ON DUPLICATE KEY UPDATE
    water_intake_ml = VALUES(water_intake_ml),
    sleep_hours     = VALUES(sleep_hours),
    steps           = VALUES(steps);
```

This makes the daily form behave like "save today's numbers", whether it is the
first save or an update.

---

### 2.4 `goals`

Stores fitness targets. A user can have several goals, including several of the
same type (for example, a steps goal for this month and another for next month).

| Column         | Type            | Rules                              | Why |
| -------------- | --------------- | ---------------------------------- | --- |
| `goal_id`      | `INT UNSIGNED`  | PK, auto-increment                 | Unique goal ID |
| `user_id`      | `INT UNSIGNED`  | NOT NULL, FK → `users`             | Owner |
| `goal_title`   | `VARCHAR(100)`  | NOT NULL                           | Human-readable name |
| `goal_type`    | `ENUM(...)`     | NOT NULL                           | Weight loss, steps, sleep, etc. |
| `target_value` | `DECIMAL(8,2)`  | NOT NULL, CHECK > 0                | Numeric target |
| `unit`         | `ENUM(...)`     | NOT NULL                           | kg, steps, ml, hours, sessions/week |
| `start_date`   | `DATE`          | NOT NULL                           | When the goal begins |
| `target_date`  | `DATE`          | NOT NULL, CHECK ≥ `start_date`     | Deadline |
| `status`       | `ENUM(...)`     | NOT NULL, default `'Active'`       | Active / Completed / Cancelled |
| `created_at`   | `TIMESTAMP`     | Default now                        | Audit trail |
| `updated_at`   | `TIMESTAMP`     | Auto-updates                       | Last edit time |

The `unit` column is stored explicitly instead of being guessed from
`goal_type`. This keeps reports simple and lets the app display `10,000 steps`
or `2,000 ml` without a lookup table. The trade-off is that the app must
validate that the unit matches the goal type in Phase 7.

Index `idx_goals_user_status (user_id, status)` supports "show my active goals".

---

### 2.5 `progress`

Stores weight and body-fat history. This is separate from `users.height_cm`
because weight changes over time and needs a history, while height is a profile
attribute.

| Column                | Type           | Rules                              | Why |
| --------------------- | -------------- | ---------------------------------- | --- |
| `progress_id`         | `INT UNSIGNED` | PK, auto-increment                 | Unique row ID |
| `user_id`             | `INT UNSIGNED` | NOT NULL, FK → `users`             | Owner |
| `record_date`         | `DATE`         | NOT NULL                           | Measurement date |
| `weight_kg`           | `DECIMAL(5,2)` | NOT NULL, CHECK 0 < weight < 500   | Body weight |
| `body_fat_percentage` | `DECIMAL(4,1)` | NULL, CHECK 0–100                  | Optional body-fat estimate |
| `notes`               | `VARCHAR(255)` | NULL                               | Optional context |
| `created_at`          | `TIMESTAMP`    | Default now                        | Audit trail |
| `updated_at`          | `TIMESTAMP`    | Auto-updates                       | Last edit time |

**`UNIQUE (user_id, record_date)`** allows one measurement per day. If the user
weighs themselves twice, the app updates that day's value instead of creating
two conflicting rows.

---

## 3. Why this design is normalized

### First Normal Form (1NF)

Every column holds one atomic value. There are no comma-separated lists such as
`"water=2000,sleep=7.5"`. Each fact has its own column and row.

### Second Normal Form (2NF)

Every table has a single-column primary key (`user_id` is not part of a
composite key), so there can be no partial dependency on part of a key. All
non-key columns describe the whole row.

### Third Normal Form (3NF)

Non-key columns do not depend on other non-key columns. Examples:

- Water, sleep, and steps live in `daily_wellness`, not repeated in `users`.
- Weight history lives in `progress`, not as `current_weight` in `users`.
- Goal status belongs to the goal, not to the user.
- No calculated column such as `bmi` is stored, because it can be derived from
  height and weight.

### Why there is no `reports` table

Daily, weekly, and monthly reports are **derived data**. They are calculated
from `workouts`, `daily_wellness`, and `progress` with `WHERE`, `GROUP BY`, and
`SUM()` queries. Storing report totals would duplicate data and could become
out of date. Phase 8 will build report queries, not a report table.

---

## 4. Data type decisions

| Choice | Reason |
| ------ | ------ |
| `INT UNSIGNED` for IDs | IDs are positive; unsigned doubles the usable range and matches across parent/child tables. |
| `DECIMAL` for weight, height, sleep, body fat | Exact decimal arithmetic; `FLOAT` can produce values like `7.499999`. |
| `DATE` for calendar days | A workout date or log date has no time zone. |
| `TIMESTAMP` for created/updated | Records when the row was saved or changed. |
| `ENUM` for gender, goal type, unit, status | Restricts values to a known list at the database level. |
| `VARCHAR(n)` with sensible limits | Prevents oversized input and documents the expected length. |
| `utf8mb4` | Supports all Unicode characters, including emoji in notes/names. |
| `InnoDB` | Supports foreign keys and transactions. |

---

## 5. Integrity rules at a glance

| Rule | Where |
| ---- | ----- |
| Unique email | `users.email` |
| One wellness record per day | `daily_wellness(user_id, log_date)` |
| One weight record per day | `progress(user_id, record_date)` |
| Valid owner | `user_id` foreign keys |
| No orphan data | `ON DELETE CASCADE` |
| Positive workout duration | `chk_workouts_duration` |
| Valid water/sleep/steps | `chk_wellness_*` |
| Valid goal values/dates | `chk_goals_*` |
| Valid weight/body fat | `chk_progress_*` |

The Flask app will **also** validate input before sending it to MySQL. Database
constraints are the last line of defense, not the only one.

---

## 6. How reports will use the schema (Phase 8 preview)

These are examples only; they will be implemented in Phase 8.

**Daily summary**

```sql
SELECT
    COALESCE(SUM(w.duration_minutes), 0) AS total_minutes,
    COALESCE(SUM(w.calories_burned), 0)  AS total_calories,
    d.water_intake_ml,
    d.sleep_hours,
    d.steps
FROM workouts AS w
JOIN daily_wellness AS d
  ON d.user_id = w.user_id AND d.log_date = w.workout_date
WHERE w.user_id = %s AND w.workout_date = %s
GROUP BY d.water_intake_ml, d.sleep_hours, d.steps;
```

**Last 7 days**

```sql
SELECT log_date, water_intake_ml, sleep_hours, steps
FROM daily_wellness
WHERE user_id = %s
  AND log_date >= CURDATE() - INTERVAL 6 DAY
ORDER BY log_date;
```

**Current month**

```sql
SELECT *
FROM workouts
WHERE user_id = %s
  AND workout_date >= DATE_FORMAT(CURDATE(), '%Y-%m-01')
  AND workout_date <  DATE_FORMAT(CURDATE() + INTERVAL 1 MONTH, '%Y-%m-01')
ORDER BY workout_date DESC;
```

**Weight trend**

```sql
SELECT record_date, weight_kg, body_fat_percentage
FROM progress
WHERE user_id = %s
ORDER BY record_date;
```

All report queries use `%s` placeholders for user input. The `user_id` always
comes from the logged-in session, never from a hidden form field.

---

## 7. Security notes

- `password_hash` is never selected into a page template.
- Every query that includes user input uses parameterized `%s` placeholders.
- The Flask database account can only `SELECT`, `INSERT`, `UPDATE`, and
  `DELETE`; it cannot alter the schema.
- The app never trusts a `user_id` submitted by the browser. Phase 3 will store
  the logged-in user's ID in the Flask session.
- `.env` is ignored by Git, and `.env.example` contains placeholders only.
