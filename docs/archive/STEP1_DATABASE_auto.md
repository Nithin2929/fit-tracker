# Step 1 — Create and Verify the MySQL Database

**Goal:** create the database `fitness_wellness_db` with four tables:

- `users`
- `workouts`
- `nutrition_logs`
- `health_metrics`

Do not build the Flask pages yet. Finish and verify this step first.

---

## 1. Software to install and open

You need:

1. **MySQL Server 8.4** — stores the database.
2. **MySQL Workbench** — the visual tool for running SQL.
3. **Visual Studio Code** — already installed; used to view and edit files.

### Recommended: MySQL Installer

1. Open <https://dev.mysql.com/downloads/installer/>.
2. Download the **MySQL Installer for Windows**.
3. Run the installer and choose **Custom**.
4. Select:
   - **MySQL Server 8.4.x**
   - **MySQL Workbench 8.0 CE** (or the current version)
5. Click **Next → Execute** and wait.
6. In the configuration wizard, use:

| Setting | Value |
|---|---|
| Config Type | Development Computer |
| Connectivity | TCP/IP enabled |
| Port | `3306` |
| Authentication | Use Strong Password Encryption |
| Root Password | Choose a strong password and write it down |
| Windows Service Name | `MySQL84` |
| Start at startup | Enabled |

7. Click **Execute → Finish**.

### Alternative: winget

```powershell
winget install --id Oracle.MySQL -e --accept-source-agreements --accept-package-agreements
winget install --id Oracle.MySQLWorkbench -e --accept-source-agreements --accept-package-agreements
```

If the MySQL service or root password is not configured automatically, open the
MySQL Installer and choose **Reconfigure**.

### Check the service

Open PowerShell:

```powershell
Get-Service -Name "MySQL*"
```

You should see `MySQL84` with status **Running**. If it is stopped:

```powershell
Start-Service -Name "MySQL84"
```

---

## 2. Open MySQL Workbench and create a connection

1. Open **MySQL Workbench**.
2. Click the **+** button beside **MySQL Connections**.
3. Enter:

| Field | Value |
|---|---|
| Connection Name | `Fitness Local` |
| Hostname | `127.0.0.1` |
| Port | `3306` |
| Username | `root` |
| Password | Click **Store in Vault**, enter your root password |

4. Click **Test Connection**.
5. Expected message: “Successfully made the MySQL connection.”
6. Click **OK**, then open the **Fitness Local** connection.

The Workbench window has:

- a **query editor** in the middle;
- a **Navigator** panel on the left with **SCHEMAS**;
- an **Output** panel at the bottom.

---

## 3. Where the files are

Open VS Code:

```powershell
code E:\ictproject
```

The Step 1 files are:

```text
E:\ictproject\
└── database\
    ├── schema.sql          # creates database + four tables
    ├── verify.sql          # checks the structure and rolls back test data
    ├── sample_data.sql     # optional dummy records for testing
    └── app_user.sql        # optional Flask database account
```

> `database\archive\` contains the earlier five-table design. You do not need to
> run anything from that folder.

---

## 4. Run `schema.sql`

1. In MySQL Workbench, click **File → Open SQL Script**.
2. Select:

   ```text
   E:\ictproject\database\schema.sql
   ```

3. Click the **lightning bolt** (Execute) or press **Ctrl + Shift + Enter**.
4. Look at the **Output** panel.

Expected output:

```text
Database and four tables created successfully.
```

### Check the tables visually

1. In **SCHEMAS**, refresh if needed.
2. Expand `fitness_wellness_db` → **Tables**.

Expected:

```text
health_metrics
nutrition_logs
users
workouts
```

### Check with SQL

Open a new query tab and run:

```sql
USE fitness_wellness_db;
SHOW TABLES;
```

Expected: the same four table names.

---

## 5. Run `verify.sql`

1. Click **File → Open SQL Script**.
2. Select:

   ```text
   E:\ictproject\database\verify.sql
   ```

3. Click the lightning bolt.
4. Read each result grid.

Expected results:

| Check | Expected |
|---|---|
| Tables | 4: `health_metrics`, `nutrition_logs`, `users`, `workouts` |
| Foreign keys | 3, all pointing to `users.user_id` |
| Unique constraints | `users.email` and `health_metrics(user_id, record_date)` |
| CHECK constraints | 11 rules |
| BMI test | 1 temporary row, `bmi ≈ 24.39` |
| Rollback | `test_user_rows_after_rollback = 0` |

The BMI test inserts one temporary user, workout, food entry, and health record,
joins the tables, calculates BMI, then runs `ROLLBACK`. No test user remains.

---

## 6. Optional: insert dummy data

This step is optional, but it gives the future dashboard something to display.

1. Click **File → Open SQL Script**.
2. Select:

   ```text
   E:\ictproject\database\sample_data.sql
   ```

3. Click the lightning bolt.

Expected final result:

| user_id | full_name | email | workouts | food_entries | health_records |
|---|---|---|---|---|---|
| 1 | Aarav Kumar | aarav@example.com | 3 | 3 | 7 |
| 2 | Priya Sharma | priya@example.com | 2 | 3 | 3 |
| 3 | Rahul Verma | rahul@example.com | 2 | 3 | 2 |

> The IDs may differ if you have run the script before. The counts are the
> important part.

All dummy users have the password:

```text
Password123!
```

The password is stored as a hash, not as plain text.

The script starts by deleting only these three sample accounts:

```sql
DELETE FROM users
WHERE email IN ('aarav@example.com', 'priya@example.com', 'rahul@example.com');
```

Because of `ON DELETE CASCADE`, their old workouts, nutrition logs, and health
records are removed too. Real users are not touched.

---

## 7. Explain the SQL line by line

### Create the database

```sql
CREATE DATABASE IF NOT EXISTS fitness_wellness_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;
```

- `CREATE DATABASE` makes a container for tables.
- `IF NOT EXISTS` avoids an error if it already exists.
- `utf8mb4` supports all normal text, including Tamil/Hindi and emoji.
- `utf8mb4_unicode_ci` makes text comparison case-insensitive.
- `USE fitness_wellness_db;` selects the database for the next commands.

### `users`

```sql
user_id INT UNSIGNED NOT NULL AUTO_INCREMENT
```

- `INT UNSIGNED`: a positive whole number.
- `NOT NULL`: a value is required.
- `AUTO_INCREMENT`: MySQL generates 1, 2, 3... automatically.

```sql
PRIMARY KEY (user_id)
```

The primary key uniquely identifies each row.

```sql
CONSTRAINT uq_users_email UNIQUE (email)
```

No two accounts can use the same email.

```sql
password_hash VARCHAR(255) NOT NULL
```

Stores a one-way hash, never the real password.

```sql
height_cm DECIMAL(5,2)
```

Stores values such as `175.50` exactly. `DECIMAL` avoids floating-point rounding
problems.

```sql
CHECK (height_cm IS NULL OR (height_cm > 0 AND height_cm < 300))
```

Height may be empty, but if entered it must be between 0 and 300 cm.

### `workouts`

```sql
FOREIGN KEY (user_id) REFERENCES users (user_id)
ON DELETE CASCADE ON UPDATE CASCADE
```

- The foreign key guarantees the user exists.
- `ON DELETE CASCADE` removes that user's workouts if the user is deleted.
- `ON UPDATE CASCADE` keeps the link correct if the user ID changes.

```sql
CHECK (duration_minutes > 0 AND duration_minutes <= 1440)
```

A workout lasts at least 1 minute and at most 24 hours (1440 minutes).

```sql
INDEX idx_workouts_user_date (user_id, workout_date)
```

An index speeds up queries such as “show this user's workouts for this week.”

### `nutrition_logs`

```sql
meal_type ENUM('Breakfast', 'Lunch', 'Dinner', 'Snack') NOT NULL
```

`ENUM` accepts only the listed values.

```sql
servings DECIMAL(5,2) NOT NULL DEFAULT 1.00
```

Stores how many servings were eaten. `1.50` means one and a half servings.

```sql
calories INT UNSIGNED NOT NULL
```

Stores total calories for that entry. The Flask form will calculate or accept the
total for the amount eaten.

```sql
protein_g DECIMAL(6,1) NULL
```

Optional protein value. `NULL` means “not provided,” which is different from 0.

There is no daily unique key because a person can log many foods in one day.

### `health_metrics`

```sql
record_date DATE NOT NULL
```

The day of the measurement.

```sql
UNIQUE (user_id, record_date)
```

One health record per user per day. If the user updates today's weight, the app
will update the existing row instead of adding a duplicate.

```sql
weight_kg DECIMAL(5,2) NOT NULL
```

Stores weight exactly, for example `71.20`.

```sql
steps INT UNSIGNED NOT NULL DEFAULT 0
```

Stores daily steps. Zero is allowed.

```sql
body_fat_percentage DECIMAL(4,1) NULL
```

Optional body-fat percentage, checked between 0 and 100.

### BMI calculation

BMI is **not stored**. It is calculated in a query:

```sql
ROUND(weight_kg / ((height_cm / 100) * (height_cm / 100)), 2) AS bmi
```

For weight `70.5` kg and height `170` cm:

```text
height in metres = 170 / 100 = 1.70
BMI = 70.5 / (1.70 × 1.70)
BMI = 70.5 / 2.89
BMI ≈ 24.39
```

Keeping BMI calculated avoids storing the same fact twice, which supports 3NF.

---

## 8. Why the design is normalized

- **1NF:** each column holds one value; no comma-separated lists.
- **2NF:** each table has a single-column primary key, so no column depends on
  only part of a key.
- **3NF:** derived values such as BMI are calculated, not stored. Workouts,
  nutrition, and health measurements each have their own table.

Reports will use `JOIN`, `SUM`, `AVG`, `COUNT`, and `GROUP BY` across these tables.
No separate report table is required.

---

## 9. Common errors and fixes

| Error | Meaning | Fix |
|---|---|---|
| `Can't connect to MySQL server` | MySQL is not running | Start the `MySQL84` service |
| `Access denied for user 'root'@'localhost'` | Wrong root password | Re-enter the password or reconfigure MySQL |
| `Unknown database 'fitness_wellness_db'` | Schema was not run | Run `database/schema.sql` first |
| `Table already exists` | Script was run before | Safe; the script uses `IF NOT EXISTS` |
| `ERROR 1064 ... near 'CHECK'` | MySQL older than 8.0.16 | Install MySQL 8.4 |
| `ERROR 1215` / `errno 150` | Foreign key type mismatch | Use the provided script exactly |
| `ERROR 1822` | Missing foreign-key index | Use the provided script; indexes are included |
| `Data too long for column` | Input is too long | Shorten it or increase the column size carefully |
| No tables visible in Workbench | Navigator not refreshed | Refresh **SCHEMAS** |
| `CREATE USER` password rejected | Password policy is strict | Use upper case, lower case, a number, and a symbol |

Useful checks:

```sql
USE fitness_wellness_db;
SHOW TABLES;
SHOW CREATE TABLE users;
DESCRIBE health_metrics;
```

Foreign-key check:

```sql
SELECT table_name, constraint_name, column_name,
       referenced_table_name, referenced_column_name
FROM information_schema.key_column_usage
WHERE table_schema = 'fitness_wellness_db'
  AND referenced_table_name IS NOT NULL;
```

---

## 10. Optional: create the Flask database account

The Flask app should not log in as `root`.

1. Open `database/app_user.sql`.
2. Replace `ChangeMe_StrongPassword_123!` with a strong password.
3. Run the file in Workbench as root.
4. Use the same password later in the Flask `.env` file.

Expected output:

```text
GRANT SELECT, INSERT, UPDATE, DELETE ON `fitness_wellness_db`.* TO `fitness_app`@`localhost`
```

---

## 11. Step 1 checklist

- [ ] MySQL Server 8.4 is installed and running.
- [ ] MySQL Workbench is installed.
- [ ] The `Fitness Local` connection works.
- [ ] `database/schema.sql` ran successfully.
- [ ] `fitness_wellness_db` contains four tables.
- [ ] `database/verify.sql` shows 3 foreign keys and 2 unique constraints.
- [ ] The BMI test returns approximately `24.39`.
- [ ] `test_user_rows_after_rollback` is `0`.
- [ ] Optional: dummy data inserted and summary counts match.
- [ ] Optional: `fitness_app` account created.

When every item is complete, reply **“Step 1 verified”** and include any error
message or screenshot description. Then we will move to **Step 2: connecting
Flask to MySQL**.
