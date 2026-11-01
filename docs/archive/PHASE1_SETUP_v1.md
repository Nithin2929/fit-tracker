# Phase 1 — Project Setup & MySQL Database Creation

This guide takes you from an empty folder to a working database with five
related tables. Follow the steps in order. Do not start Phase 2 until the
checklist at the end passes.

---

## 0. What Phase 1 builds

At the end of this phase you will have:

- the project folder structure for the Flask application;
- a Python virtual environment with the required packages;
- the MySQL database `fitness_wellness_db`;
- five tables: `users`, `workouts`, `daily_wellness`, `goals`, `progress`;
- primary keys, foreign keys, unique constraints, check constraints, and indexes;
- a dedicated MySQL account for the Flask app;
- a local `.env` file (not committed to Git);
- a verification script that proves the schema works.

**No user records are created.** The verification script inserts temporary
rows inside a transaction and rolls them back.

---

## 1. Check what is already installed

Open **PowerShell** and run:

```powershell
python --version
code --version
mysql --version
```

On this computer the first two work. `mysql` is not installed yet, so the last
command fails — that is expected. Install MySQL next.

---

## 2. Install MySQL Server 8.4

### Option A — MySQL Installer (recommended for beginners)

1. Open <https://dev.mysql.com/downloads/installer/>.
2. Download the **MySQL Installer for Windows** (the larger offline installer
   is fine).
3. Run the installer.
4. Choose **Custom** (or **Server only** if offered).
5. Select **MySQL Server 8.4.x** and move it to the products to install.
6. Click **Execute** and wait for the installation to finish.
7. The **Configuration** wizard opens. Use these values:

   | Setting               | Value                                              |
   | --------------------- | -------------------------------------------------- |
   | Config Type           | Development Computer                               |
   | Connectivity          | TCP/IP enabled, Port **3306**                      |
   | Authentication Method | Use Strong Password Encryption (**recommended**)   |
   | Root Password         | Choose a strong password and write it down         |
   | Windows Service Name  | `MySQL84`                                          |
   | Start at startup      | Enabled                                            |

8. Click **Execute**, then **Finish**.

> Keep the root password safe. You need it once to create the database and the
> application account. The Flask app will use its own account, not root.

### Option B — winget (faster, but you may still need configuration)

```powershell
winget install --id Oracle.MySQL -e --accept-source-agreements --accept-package-agreements
```

This installs the MySQL Server package. If the Windows service is not created
or the root password was not configured, run the MySQL Installer and use its
**Reconfigure** option. For a first project, Option A avoids this extra work.

### Add MySQL to PATH

The default installation folder is:

```text
C:\Program Files\MySQL\MySQL Server 8.4\bin
```

If `mysql --version` still says "not recognized":

1. Press **Windows + R**, type `sysdm.cpl`, press Enter.
2. Open **Advanced** → **Environment Variables**.
3. Under **User variables**, select **Path** → **Edit** → **New**.
4. Add `C:\Program Files\MySQL\MySQL Server 8.4\bin`.
5. Click OK on all windows.
6. **Close and reopen PowerShell**, then run `mysql --version` again.

### Start and check the MySQL service

```powershell
Get-Service -Name "MySQL*"
```

You should see a service such as `MySQL84` with status **Running**. If it is
stopped:

```powershell
Start-Service -Name "MySQL84"
```

Connect as root:

```powershell
mysql -u root -p -e "SELECT VERSION();"
```

Type the root password when prompted. You should see a version such as
`8.4.9`.

---

## 3. Create and activate the Python virtual environment

A virtual environment keeps this project's packages separate from the rest of
your computer.

```powershell
cd E:\ictproject

python -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -r requirements.txt
```

Your prompt should now start with `(.venv)`.

If PowerShell blocks the activation script, run this once **for your user
account**:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

Then activate again.

> If you prefer not to activate the environment, you can run
> `.\.venv\Scripts\python.exe -m pip install -r requirements.txt` instead.

Check that the packages import correctly:

```powershell
python -c "import flask, mysql.connector, dotenv; print('Dependencies OK')"
```

Expected output:

```text
Dependencies OK
```

---

## 4. Create the database and tables

Make sure you are in `E:\ictproject`, then run:

### PowerShell

```powershell
Get-Content .\database\schema.sql -Raw | mysql -u root -p --default-character-set=utf8mb4
```

### Command Prompt (cmd.exe)

```cmd
mysql -u root -p --default-character-set=utf8mb4 < database\schema.sql
```

> PowerShell does **not** support the `<` input-redirection operator, which is
> why the PowerShell command uses `Get-Content ... | mysql`.

Enter the root password. Expected output:

```text
message
Database and tables created successfully.
```

The script is safe to run again: it uses `CREATE DATABASE IF NOT EXISTS` and
`CREATE TABLE IF NOT EXISTS`, so it does not delete existing data.

---

## 5. Create the application database account (recommended)

Using `root` from a web application is a bad habit. The app only needs to read
and write rows, not create or drop tables.

1. Open `database/app_user.sql` in VS Code.
2. Replace `ChangeMe_StrongPassword_123!` with your own strong password.
3. Run the file:

```powershell
Get-Content .\database\app_user.sql -Raw | mysql -u root -p
```

Expected output: a `SHOW GRANTS` table containing:

```text
GRANT SELECT, INSERT, UPDATE, DELETE ON `fitness_wellness_db`.* TO `fitness_app`@`localhost`
```

> If the user already exists, `CREATE USER IF NOT EXISTS` will not change its
> password. Ask MySQL to change it explicitly:
>
> ```sql
> ALTER USER 'fitness_app'@'localhost' IDENTIFIED BY 'YourNewPassword';
> ALTER USER 'fitness_app'@'127.0.0.1' IDENTIFIED BY 'YourNewPassword';
> ```

---

## 6. Create your local `.env` file

```powershell
Copy-Item .env.example .env
```

Generate a secret key for Flask:

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

Open `.env` in VS Code and:

1. Paste the generated value after `SECRET_KEY=`.
2. Set `DB_PASSWORD` to the password you used in `database/app_user.sql`.
3. Leave `DB_HOST=127.0.0.1`, `DB_PORT=3306`, `DB_NAME=fitness_wellness_db`,
   and `DB_USER=fitness_app` as they are.

Example (with fake values):

```dotenv
SECRET_KEY=3f9c1a7e5b2d4c8f0a6e9d1b7c3f5a8e2d4b6c9f1a3e5d7b9c2f4a6e8d0b1c3f
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=fitness_wellness_db
DB_USER=fitness_app
DB_PASSWORD=MyLocalDevPassword!2026
```

`.env` is already listed in `.gitignore`, so it will not be committed.

---

## 7. Verify the database

Run the verification script:

```powershell
Get-Content .\database\verify.sql -Raw | mysql -u root -p --default-character-set=utf8mb4
```

You will see six sections.

### Section 1 — Tables

Expected table names (order may vary):

```text
daily_wellness
goals
progress
users
workouts
```

All should use the `InnoDB` engine and `utf8mb4_unicode_ci` collation.

### Section 2 — Columns

Check that each table has the expected columns and data types. For example,
`users.email` should be `varchar(150)` and `daily_wellness.sleep_hours`
should be `decimal(3,1)`.

### Section 3 — Foreign keys

Expected relationships:

| Child table      | Column    | Parent table | Parent column |
| ---------------- | --------- | ------------ | ------------- |
| `workouts`       | `user_id` | `users`      | `user_id`     |
| `daily_wellness` | `user_id` | `users`      | `user_id`     |
| `goals`          | `user_id` | `users`      | `user_id`     |
| `progress`       | `user_id` | `users`      | `user_id`     |

### Section 4 — Unique constraints

Expected:

- `uq_users_email` on `users(email)`;
- `uq_wellness_user_date` on `daily_wellness(user_id, log_date)`;
- `uq_progress_user_date` on `progress(user_id, record_date)`.

### Section 5 — CHECK constraints

You should see the constraints that protect height, duration, calories, water,
sleep, steps, goal dates, goal values, weight, and body-fat percentage.

### Section 6 — Relationship smoke test

The script inserts one linked row into every table, reads it back with JOINs,
then rolls back. Expected:

1. one row showing the test user's workout, wellness, goal, and weight;
2. `Smoke test rolled back - no test data was saved.`;
3. `test_user_rows_after_rollback` equal to **0**.

If the count is 0, no dummy user was left behind.

### Test the application account

```powershell
mysql -u fitness_app -p -e "USE fitness_wellness_db; SHOW TABLES;"
```

You should see the same five tables. This proves the app account can connect
and read the schema.

Optional: prove the app account cannot change the schema:

```powershell
mysql -u fitness_app -p -e "USE fitness_wellness_db; CREATE TABLE should_fail (id INT);"
```

This should fail with `Access denied`. That is the correct, safe result.

---

## 8. Optional: inspect the database visually

- **MySQL Workbench** (optional):
  <https://dev.mysql.com/downloads/workbench/>
  Create a connection with host `127.0.0.1`, port `3306`, user `fitness_app`
  (or `root` for administration).
- **VS Code extension**: search for "MySQL" by Weijan Chen, then add a
  connection using the same details.

You can also inspect one table in the terminal:

```powershell
mysql -u root -p -e "USE fitness_wellness_db; SHOW CREATE TABLE users\G"
```

---

## 9. Troubleshooting

| Problem | Cause and fix |
| ------- | ------------- |
| `mysql` is not recognized | MySQL `bin` folder is not on PATH. Follow the PATH steps in section 2 and reopen PowerShell. |
| `ERROR 2003 (HY000): Can't connect to MySQL server` | The service is stopped. Run `Get-Service -Name "MySQL*"`, then `Start-Service -Name "MySQL84"`. |
| `ERROR 1045 (28000): Access denied` | Wrong username/password. Use the root password chosen during installation. |
| `The '<' operator is reserved for future use` | You used cmd-style redirection in PowerShell. Use the `Get-Content ... | mysql` command. |
| `ERROR 1064 ... near 'CHECK'` | MySQL is older than 8.0.16, where CHECK constraints are not enforced. Install MySQL 8.4. |
| `Authentication plugin 'caching_sha2_password' cannot be loaded` | The MySQL driver is old. Run `pip install --upgrade mysql-connector-python`. |
| Port 3306 already in use | Run `Get-NetTCPConnection -LocalPort 3306` to see which process owns it. |
| `Unknown database 'fitness_wellness_db'` | Run `database/schema.sql` first. |
| `Table 'fitness_wellness_db.users' doesn't exist` | The schema script did not finish. Re-run it and read the first error. |

---

## 10. What each Phase 1 file is for

| File | Purpose |
| ---- | ------- |
| `database/schema.sql` | Creates the database and all five tables with keys and constraints. |
| `database/app_user.sql` | Creates the limited MySQL account the Flask app will use. |
| `database/verify.sql` | Prints schema details and runs a rolled-back relationship test. |
| `.env.example` | Documents the configuration values; copy it to `.env`. |
| `.gitignore` | Keeps `.env`, `.venv`, and generated files out of Git. |
| `requirements.txt` | Lists Flask, MySQL Connector, and python-dotenv. |
| `app/__init__.py` | Marks `app` as a Python package; the Flask factory comes in Phase 2. |
| `app/routes/__init__.py` | Placeholder for route Blueprints (auth, dashboard, etc.). |
| `app/templates/` | Will hold Jinja HTML templates. |
| `app/static/css/` | Will hold the green-and-white stylesheet. |
| `app/static/js/` | Will hold dashboard JavaScript. |
| `app/static/images/` | Will hold logos and icons. |
| `tests/` | Will hold automated tests in Phase 9. |
| `README.md` | Project overview, structure, and roadmap. |
| `docs/DATABASE_DESIGN.md` | Explains every table, relationship, and design decision. |

---

## 11. Phase 1 completion checklist

- [ ] MySQL Server 8.4 is installed and the service is running.
- [ ] `mysql --version` works in a new PowerShell window.
- [ ] `.venv` exists and `pip install -r requirements.txt` succeeded.
- [ ] `python -c "import flask, mysql.connector, dotenv"` prints no error.
- [ ] `schema.sql` ran successfully.
- [ ] `verify.sql` shows five tables and four foreign keys.
- [ ] The smoke test returned one row and `test_user_rows_after_rollback = 0`.
- [ ] `app_user.sql` created the `fitness_app` account.
- [ ] `.env` exists with a real `SECRET_KEY` and `DB_PASSWORD`.
- [ ] `mysql -u fitness_app -p` can see the five tables.

When every box is checked, Phase 1 is complete. Phase 2 will connect Flask to
this database and add a health-check page.
