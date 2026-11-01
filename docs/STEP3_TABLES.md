# Step 3 — Create Workouts, Nutrition Logs, and Health Metrics Tables

**Goal:** add three child tables to your existing `fitness_wellness_db` database:

- `workouts`
- `nutrition_logs`
- `health_metrics`

Your existing `users` table is **not changed**. The new tables connect to it
with foreign keys.

---

## 1. Before you run the SQL

Open **MySQL Workbench**, connect to `Fitness Local`, and run:

```sql
USE fitness_wellness_db;
SHOW CREATE TABLE users;
```

Look at the `user_id` line. It will normally look like:

```text
`user_id` int NOT NULL AUTO_INCREMENT
```

The Step 3 script uses `INT` for `user_id`.

If your `users.user_id` is **`int unsigned`**, change these three lines in
`database/step3_tables.sql`:

```sql
user_id INT NOT NULL,
```

to:

```sql
user_id INT UNSIGNED NOT NULL,
```

There is one such line in each of the three table definitions. If you do not
match the types exactly, MySQL will reject the foreign key with error 3780.

---

## 2. Open the project in VS Code

```powershell
code E:\ictproject
```

Open this file:

```text
database\step3_tables.sql
```

The file contains all three `CREATE TABLE` statements.

---

## 3. Run the table-creation script

In MySQL Workbench:

1. Click **File → Open SQL Script**.
2. Select:

   ```text
   E:\ictproject\database\step3_tables.sql
   ```

3. Click the **lightning bolt** (Execute).
4. Expected output:

   ```text
   Step 3 tables created successfully.
   ```

If MySQL Workbench shows multiple result tabs, the final message is the
confirmation.

---

## 4. The three tables explained

### 4.1 `workouts`

```sql
CREATE TABLE IF NOT EXISTS workouts (
    workout_id       INT          NOT NULL AUTO_INCREMENT,
    user_id          INT          NOT NULL,
    exercise_name    VARCHAR(100) NOT NULL,
    duration_minutes INT UNSIGNED NOT NULL,
    calories_burned  INT UNSIGNED NULL,
    workout_date     DATE         NOT NULL,

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
```

Line-by-line:

- `workout_id INT NOT NULL AUTO_INCREMENT` creates a unique number for each
  workout. MySQL fills it automatically.
- `user_id INT NOT NULL` stores which user did the workout.
- `exercise_name VARCHAR(100) NOT NULL` stores text such as `Running` or `Yoga`.
- `duration_minutes INT UNSIGNED NOT NULL` stores a positive number of minutes.
- `calories_burned INT UNSIGNED NULL` is optional. `NULL` means “not entered.”
- `workout_date DATE NOT NULL` stores only the calendar date.
- `PRIMARY KEY (workout_id)` makes `workout_id` unique.
- `FOREIGN KEY ... REFERENCES users(user_id)` says the user must exist.
- `ON DELETE CASCADE` deletes this user's workouts if the user is deleted.
- `ON UPDATE CASCADE` updates the link if the user ID changes.
- `CHECK` rules reject zero-minute workouts, workouts longer than 24 hours, and
  unrealistic calorie values.
- `INDEX` speeds up date-range queries.
- `InnoDB` is required for foreign keys.
- `utf8mb4` supports all normal text.

---

### 4.2 `nutrition_logs`

```sql
CREATE TABLE IF NOT EXISTS nutrition_logs (
    nutrition_id  INT          NOT NULL AUTO_INCREMENT,
    user_id       INT          NOT NULL,
    food_name     VARCHAR(120) NOT NULL,
    meal_type     ENUM('Breakfast', 'Lunch', 'Dinner', 'Snack') NOT NULL,
    calories      INT UNSIGNED NOT NULL,
    protein       DECIMAL(6,1) NULL,
    carbohydrates DECIMAL(6,1) NULL,
    fat           DECIMAL(6,1) NULL,
    log_date      DATE         NOT NULL,

    PRIMARY KEY (nutrition_id),

    CONSTRAINT fk_nutrition_user
        FOREIGN KEY (user_id) REFERENCES users (user_id)
        ON DELETE CASCADE ON UPDATE CASCADE,

    CONSTRAINT chk_nutrition_calories
        CHECK (calories <= 10000),

    CONSTRAINT chk_nutrition_protein
        CHECK (protein IS NULL OR (protein >= 0 AND protein <= 1000)),

    CONSTRAINT chk_nutrition_carbohydrates
        CHECK (carbohydrates IS NULL OR (carbohydrates >= 0 AND carbohydrates <= 1000)),

    CONSTRAINT chk_nutrition_fat
        CHECK (fat IS NULL OR (fat >= 0 AND fat <= 1000)),

    INDEX idx_nutrition_user_date (user_id, log_date)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;
```

Important points:

- `meal_type ENUM(...)` accepts only Breakfast, Lunch, Dinner, or Snack.
- `calories`, `protein`, `carbohydrates`, and `fat` describe the food entry.
- `protein`, `carbohydrates`, and `fat` use `DECIMAL(6,1)` because values such
  as `12.5` grams should be stored exactly.
- A user can log many foods on the same day, so there is **no daily unique
  constraint** here.
- The foreign key prevents a food log from belonging to a non-existent user.

---

### 4.3 `health_metrics`

```sql
CREATE TABLE IF NOT EXISTS health_metrics (
    metric_id       INT          NOT NULL AUTO_INCREMENT,
    user_id         INT          NOT NULL,
    weight          DECIMAL(5,2) NOT NULL,
    height          DECIMAL(5,2) NOT NULL,
    steps           INT UNSIGNED NOT NULL DEFAULT 0,
    calories_burned INT UNSIGNED NOT NULL DEFAULT 0,
    recorded_date   DATE         NOT NULL,

    PRIMARY KEY (metric_id),

    CONSTRAINT fk_health_user
        FOREIGN KEY (user_id) REFERENCES users (user_id)
        ON DELETE CASCADE ON UPDATE CASCADE,

    CONSTRAINT uq_health_user_date UNIQUE (user_id, recorded_date),

    CONSTRAINT chk_health_weight
        CHECK (weight > 0 AND weight < 500),

    CONSTRAINT chk_health_height
        CHECK (height > 0 AND height < 300),

    CONSTRAINT chk_health_steps
        CHECK (steps <= 200000),

    CONSTRAINT chk_health_calories_burned
        CHECK (calories_burned <= 10000)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;
```

Important points:

- `weight` is in kilograms.
- `height` is in centimetres.
- `steps` defaults to 0.
- `calories_burned` is the daily total recorded by the user or a tracker.
- `UNIQUE (user_id, recorded_date)` allows only one health record per user per
  day.
- BMI is **calculated**, not stored:

  ```text
  BMI = weight / ((height / 100) * (height / 100))
  ```

  Example: weight = 70.5 kg, height = 175 cm.

  ```text
  height in metres = 1.75
  BMI = 70.5 / (1.75 × 1.75)
  BMI ≈ 23.02
  ```

---

## 5. Primary keys and foreign keys

### Primary key (PK)

A primary key uniquely identifies one row in its own table.

```text
users.user_id
workouts.workout_id
nutrition_logs.nutrition_id
health_metrics.metric_id
```

Two rows cannot have the same primary key value, and a primary key cannot be
`NULL`.

### Foreign key (FK)

A foreign key is a column that points to a primary key in another table.

```text
workouts.user_id       → users.user_id
nutrition_logs.user_id → users.user_id
health_metrics.user_id → users.user_id
```

The foreign key guarantees that you cannot add a workout for user `99` if user
`99` does not exist. This protects the database from orphan rows.

### Relationship type

```text
users 1 ───< workouts
users 1 ───< nutrition_logs
users 1 ───< health_metrics
```

One user can have many workouts, many food logs, and many health records. This
is called a **one-to-many** relationship.

---

## 6. Add sample data

Open and run:

```text
E:\ictproject\database\step3_sample_data.sql
```

The script picks the first user in your `users` table:

```sql
SET @user_id = (SELECT user_id FROM users ORDER BY user_id LIMIT 1);
```

It then inserts:

- 3 workouts (Running, Weight Training, Cycling)
- 4 nutrition entries (Breakfast, Lunch, Snack, Dinner)
- 3 daily health records

> The sample script uses `ON DUPLICATE KEY UPDATE` for health metrics, so the
> three daily rows are updated if you run it again. Workouts and food entries
> do not have a unique daily rule, so running the whole script repeatedly will
> add duplicate workout/food rows. Run it once for testing.

---

## 7. Check the tables with SELECT

Open a new query tab in MySQL Workbench and run:

```sql
USE fitness_wellness_db;

SELECT * FROM workouts;
SELECT * FROM nutrition_logs;
SELECT * FROM health_metrics;
```

### Workouts with user names

```sql
SELECT
    u.full_name,
    w.exercise_name,
    w.duration_minutes,
    w.calories_burned,
    w.workout_date
FROM users AS u
JOIN workouts AS w ON w.user_id = u.user_id
ORDER BY w.workout_date DESC;
```

### Nutrition with user names

```sql
SELECT
    u.full_name,
    n.food_name,
    n.meal_type,
    n.calories,
    n.protein,
    n.carbohydrates,
    n.fat,
    n.log_date
FROM users AS u
JOIN nutrition_logs AS n ON n.user_id = u.user_id
ORDER BY n.log_date DESC;
```

### BMI calculation

```sql
SELECT
    u.full_name,
    h.recorded_date,
    h.weight,
    h.height,
    ROUND(h.weight / ((h.height / 100) * (h.height / 100)), 2) AS bmi
FROM users AS u
JOIN health_metrics AS h ON h.user_id = u.user_id
ORDER BY h.recorded_date DESC;
```

Expected BMI for the sample user:

```text
70.50 kg, 175 cm → 23.02
70.80 kg, 175 cm → 23.12
71.00 kg, 175 cm → 23.18
```

### Count records

```sql
SELECT 'users' AS table_name, COUNT(*) AS total FROM users
UNION ALL
SELECT 'workouts', COUNT(*) FROM workouts
UNION ALL
SELECT 'nutrition_logs', COUNT(*) FROM nutrition_logs
UNION ALL
SELECT 'health_metrics', COUNT(*) FROM health_metrics;
```

---

## 8. Full verification script

For a complete check, open and run:

```text
E:\ictproject\database\step3_verify.sql
```

It displays:

1. all tables;
2. columns and types;
3. foreign keys;
4. unique constraints;
5. CHECK constraints;
6. sample records;
7. user/workout JOIN;
8. user/nutrition JOIN;
9. BMI values;
10. daily summary using aggregate functions;
11. row counts.

---

## 9. Common SQL errors and fixes

| Error | Meaning | Fix |
|---|---|---|
| `ERROR 1049: Unknown database` | Database name is wrong or not created | Run `USE fitness_wellness_db;` and check the name |
| `ERROR 1050: Table already exists` | Table was created earlier | Safe; the script uses `IF NOT EXISTS` |
| `ERROR 1064: You have an error in your SQL syntax` | Typo or missing comma/parenthesis | Compare your code with the file; run the whole script |
| `ERROR 1146: Table doesn't exist` | `users` table is missing or wrong database selected | Run `USE fitness_wellness_db; SHOW TABLES;` |
| `ERROR 1452: Cannot add or update a child row` | The `user_id` does not exist in `users` | Insert the user first or use an existing `user_id` |
| `ERROR 3780: Referencing column and referenced column are incompatible` | Signed/unsigned type mismatch | Match `INT` or `INT UNSIGNED` exactly |
| `ERROR 1215: Cannot add foreign key constraint` | Type, engine, or index problem | Use `InnoDB`; match types; keep the provided indexes |
| `ERROR 1364: Field doesn't have a default value` | A required column was left out | Provide every `NOT NULL` value |
| `ERROR 1264: Out of range value` | Number is too large or negative for the column | Use a realistic positive value |
| `ERROR 3819: Check constraint is violated` | A CHECK rule failed | Check duration, calories, weight, height, steps |
| `ERROR 1062: Duplicate entry` | A unique value already exists | Use a different email/date or update the existing row |
| `ERROR 1292: Incorrect date value` | Date is not in `YYYY-MM-DD` format | Use `2026-10-31`, not `31/10/2026` |

### If `SHOW CREATE TABLE users` shows `int unsigned`

Change the three `user_id` lines in `step3_tables.sql` to:

```sql
user_id INT UNSIGNED NOT NULL,
```

Then run the script again.

### If the foreign key error continues

Run this to inspect both columns:

```sql
SELECT table_name, column_name, column_type
FROM information_schema.columns
WHERE table_schema = 'fitness_wellness_db'
  AND column_name = 'user_id'
ORDER BY table_name;
```

Both `users.user_id` and the child `user_id` must show the same `column_type`.

---

## 10. Step 3 checklist

- [ ] `SHOW CREATE TABLE users;` shows the `user_id` type.
- [ ] `database/step3_tables.sql` ran successfully.
- [ ] `SHOW TABLES;` lists `users`, `workouts`, `nutrition_logs`,
      `health_metrics`.
- [ ] `database/step3_sample_data.sql` inserted sample records.
- [ ] `SELECT * FROM workouts;` shows rows.
- [ ] `SELECT * FROM nutrition_logs;` shows rows.
- [ ] `SELECT * FROM health_metrics;` shows rows.
- [ ] The JOIN queries show the user's name with each record.
- [ ] The BMI query returns about `23.02`, `23.12`, and `23.18`.
- [ ] `database/step3_verify.sql` shows 3 foreign keys.

When all boxes are checked, reply **“Step 3 verified”** and include any error
message you saw. Then we will start **Step 4: connecting Python Flask to MySQL**.
