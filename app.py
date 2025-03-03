from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
import datetime

app = Flask(__name__)
app.secret_key = "securekey2025"  # Secret key for sessions

# Predefined admin credentials
ADMIN_PASSWORD = "244466666"  # Password for administrators (AGNES and STANLY)

# Database connection
def get_db_connection():
    conn = sqlite3.connect('license_database.db', timeout=10)  # 10-second timeout
    conn.row_factory = sqlite3.Row
    return conn

# Initialize database
def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS licenses (
            entry_number INTEGER NOT NULL,
            Business_name TEXT NOT NULL CHECK(Business_name = UPPER(Business_name)),
            Business_ID TEXT NOT NULL,
            owner_phone TEXT NOT NULL CHECK(length(owner_phone) = 10 AND owner_phone LIKE '07%'),
            Activity TEXT NOT NULL CHECK(Activity = UPPER(Activity)),
            business_location TEXT,
            date_registered TEXT NOT NULL,
            date_renewed TEXT,
            status TEXT,
            year INTEGER NOT NULL,
            PRIMARY KEY(entry_number, year),
            UNIQUE(Business_name)
        )
    ''')

    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            password TEXT
        )
    ''')

    conn.commit()
    conn.close()

# Generate next entry number
def get_next_entry_number():
    current_year = datetime.datetime.now().year
    conn = get_db_connection()
    cursor = conn.execute("SELECT MAX(entry_number) FROM licenses WHERE year = ?", (current_year,))
    last_entry = cursor.fetchone()[0]
    conn.close()
    return 1 if last_entry is None else last_entry + 1

# Check for missing entry numbers
def has_missing_entry_numbers():
    current_year = datetime.datetime.now().year
    conn = get_db_connection()
    cursor = conn.execute("SELECT entry_number FROM licenses WHERE year = ? ORDER BY entry_number", (current_year,))
    entry_numbers = [row["entry_number"] for row in cursor.fetchall()]
    conn.close()

    if not entry_numbers:
        return False  # No entries yet, so no gaps

    # Check for gaps in the sequence
    for i in range(1, entry_numbers[-1] + 1):
        if i not in entry_numbers:
            return True  # Gap found

    return False  # No gaps

# Login Page
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].upper()
        password = request.form["password"]

        # Check if the user is an admin
        if username in {"AGNES", "STANLY"} and password == ADMIN_PASSWORD:
            session["user"] = username
            session["is_admin"] = True  # Mark user as admin
            flash("Admin login successful!", "success")
            return redirect(url_for("index"))
        # Check if the user is a regular user
        else:
            conn = get_db_connection()
            cursor = conn.execute("SELECT * FROM users WHERE name = ? AND password = ?", (username, password))
            user = cursor.fetchone()
            conn.close()

            if user:
                session["user"] = username
                session["is_admin"] = False  # Mark user as non-admin
                flash("Login successful!", "success")
                return redirect(url_for("index"))
            else:
                flash("Invalid credentials", "error")
                return redirect(url_for("login"))

    return render_template("login.html")

# Sign Up Page
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"].upper()
        conn = get_db_connection()
        cursor = conn.execute("SELECT * FROM users WHERE name = ?", (name,))
        user = cursor.fetchone()
        conn.close()

        if user:
            session["temp_user"] = name
            return redirect(url_for("set_password"))
        else:
            flash("Your name is not registered. Please contact the admin.", "error")
            return redirect(url_for("signup"))

    return render_template("signup.html")

# Set Password Page
@app.route("/set_password", methods=["GET", "POST"])
def set_password():
    if "temp_user" not in session:
        flash("You must sign up first.", "error")
        return redirect(url_for("signup"))

    if request.method == "POST":
        password = request.form["password"]
        if len(password) != 6:
            flash("Password must be 6 characters long.", "error")
            return redirect(url_for("set_password"))

        conn = get_db_connection()
        conn.execute("UPDATE users SET password = ? WHERE name = ?", (password, session["temp_user"]))
        conn.commit()
        conn.close()

        session.pop("temp_user", None)
        flash("Password set successfully! Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("set_password.html")

# Admin Login Page
@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"].upper()
        password = request.form["password"]

        if username in {"AGNES", "STANLY"} and password == ADMIN_PASSWORD:
            session["user"] = username
            session["is_admin"] = True
            flash("Admin login successful!", "success")
            return redirect(url_for("index"))
        else:
            flash("Invalid admin credentials.", "error")
            return redirect(url_for("admin_login"))

    return render_template("admin_login.html")

# User Login Page
@app.route("/user_login", methods=["GET", "POST"])
def user_login():
    if request.method == "POST":
        username = request.form["username"].upper()
        password = request.form["password"]

        conn = get_db_connection()
        cursor = conn.execute("SELECT * FROM users WHERE name = ? AND password = ?", (username, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            session["user"] = username
            session["is_admin"] = False
            flash("Login successful!", "success")
            return redirect(url_for("index"))
        else:
            flash("Invalid credentials.", "error")
            return redirect(url_for("user_login"))

    return render_template("user_login.html")

# Home Page
@app.route("/home")
def index():
    if "user" not in session:
        flash("You must log in to access this page", "error")
        return redirect(url_for("login"))

    return render_template("index.html", user=session["user"], is_admin=session.get("is_admin", False))

# Add a License
@app.route("/add", methods=["GET", "POST"])
def add_license():
    if "user" not in session:
        flash("You must log in to add a license", "error")
        return redirect(url_for("login"))

    if has_missing_entry_numbers():
        flash("Cannot add a new license. There are missing entry numbers in the sequence. Please fill in the missing entry first.", "error")
        return redirect(url_for("fill_missing_entry"))

    if request.method == "POST":
        entry_number = get_next_entry_number()  # Get the next sequential entry number
        Business_ID = request.form["Business_ID"].upper()
        Business_name = request.form["Business_name"].upper()
        owner_phone = request.form["owner_phone"]
        Activity = request.form["Activity"].upper()
        business_location = request.form["business_location"]
        date_registered = request.form["date_registered"]
        date_renewed = request.form["date_renewed"]
        status = request.form["status"]
        current_year = datetime.datetime.now().year

        # Insert data into database
        conn = get_db_connection()
        try:
            conn.execute('''
                INSERT INTO licenses (
                    entry_number, Business_name, Business_ID, owner_phone,
                    Activity, business_location, date_registered,
                    date_renewed, status, year
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                entry_number, Business_name, Business_ID, owner_phone,
                Activity, business_location, date_registered,
                date_renewed, status, current_year
            ))
            conn.commit()
            flash("License added successfully!", "success")
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed: licenses.Business_name" in str(e):
                flash("Business name already exists. Please use a unique name.", "error")
            else:
                flash("An error occurred while adding the license.", "error")
        finally:
            conn.close()

        return redirect(url_for("index"))

    return render_template("add_license.html", entry_number=get_next_entry_number(), year=datetime.datetime.now().year)

# Fill Missing Entry
@app.route("/fill_missing_entry", methods=["GET", "POST"])
def fill_missing_entry():
    if "user" not in session:
        flash("You must log in to access this page", "error")
        return redirect(url_for("login"))

    if request.method == "POST":
        entry_number = int(request.form["entry_number"])
        year = int(request.form["year"])
        Business_ID = request.form["Business_ID"].upper()
        Business_name = request.form["Business_name"].upper()
        owner_phone = request.form["owner_phone"]
        Activity = request.form["Activity"].upper()
        business_location = request.form["business_location"]
        date_registered = request.form["date_registered"]
        date_renewed = request.form["date_renewed"]
        status = request.form["status"]

        # Insert data into database
        conn = get_db_connection()
        try:
            conn.execute('''
                INSERT INTO licenses (
                    entry_number, Business_name, Business_ID, owner_phone,
                    Activity, business_location, date_registered,
                    date_renewed, status, year
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                entry_number, Business_name, Business_ID, owner_phone,
                Activity, business_location, date_registered,
                date_renewed, status, year
            ))
            conn.commit()
            flash(f"License with Entry No {entry_number} successfully added!", "success")
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed: licenses.Business_name" in str(e):
                flash("Business name already exists. Please use a unique name.", "error")
            else:
                flash("An error occurred while adding the license.", "error")
        finally:
            conn.close()

        return redirect(url_for("index"))

    # Find the first missing entry number
    current_year = datetime.datetime.now().year
    conn = get_db_connection()
    cursor = conn.execute("SELECT entry_number FROM licenses WHERE year = ? ORDER BY entry_number", (current_year,))
    entry_numbers = [row["entry_number"] for row in cursor.fetchall()]
    conn.close()

    missing_entry = None
    for i in range(1, entry_numbers[-1] + 1):
        if i not in entry_numbers:
            missing_entry = i
            break

    if missing_entry:
        return render_template("fill_missing_entry.html", entry_number=missing_entry, year=current_year)
    else:
        flash("No missing entry numbers found.", "info")
        return redirect(url_for("index"))

# Search License
@app.route("/search", methods=["GET", "POST"])
def search_license():
    if "user" not in session:
        flash("You must log in to search for a license", "error")
        return redirect(url_for("login"))

    if request.method == "POST":
        search_term = request.form["search_term"].upper()  # Ensure search term is uppercase
        conn = get_db_connection()
        cursor = conn.execute('''
            SELECT * FROM licenses 
            WHERE Business_name LIKE ? OR Business_ID LIKE ?
        ''', (f"%{search_term}%", f"%{search_term}%"))
        results = cursor.fetchall()
        conn.close()

        if not results:
            flash("No matching licenses found", "error")
            return render_template("search_license.html", results=None)
        else:
            return render_template("search_license.html", results=results)

    return render_template("search_license.html", results=None)

# Live Search Endpoint
@app.route("/live_search", methods=["POST"])
def live_search():
    search_term = request.form["search_term"].upper()
    conn = get_db_connection()
    cursor = conn.execute('''
        SELECT * FROM licenses 
        WHERE Business_name LIKE ? OR Business_ID LIKE ?
    ''', (f"%{search_term}%", f"%{search_term}%"))
    results = cursor.fetchall()
    conn.close()

    # Convert results to a list of dictionaries for JSON response
    results_list = [dict(row) for row in results]
    return jsonify(results_list)

# Delete License (Admin Only)
@app.route("/delete_license", methods=["GET", "POST"])
def delete_license():
    if "user" not in session or not session.get("is_admin", False):
        flash("You do not have permission to access this page", "error")
        return redirect(url_for("index"))

    if request.method == "POST":
        entry_number = request.form.get("entry_number")
        year = request.form.get("year")
        if not entry_number or not year:
            flash("Invalid request. Please try again.", "error")
            return redirect(url_for("delete_license"))

        conn = get_db_connection()
        try:
            # Fetch the license details before deleting
            cursor = conn.execute("SELECT * FROM licenses WHERE entry_number = ? AND year = ?", (entry_number, year))
            license_details = cursor.fetchone()
            if not license_details:
                flash("License not found.", "error")
                return redirect(url_for("delete_license"))

            # Delete the license
            conn.execute("DELETE FROM licenses WHERE entry_number = ? AND year = ?", (entry_number, year))
            conn.commit()
            flash(f"License with Entry No {entry_number} successfully deleted!", "success")
        except sqlite3.Error as e:
            flash(f"An error occurred while deleting the license: {e}", "error")
        finally:
            conn.close()

        return redirect(url_for("delete_license"))

    # Fetch all licenses to display
    conn = get_db_connection()
    licenses = conn.execute("SELECT * FROM licenses ORDER BY year, entry_number").fetchall()
    conn.close()

    return render_template("delete_license.html", licenses=licenses)

# Add User (Admin Only)
@app.route("/add_user", methods=["GET", "POST"])
def add_user():
    if "user" not in session or not session.get("is_admin", False):
        flash("You do not have permission to access this page", "error")
        return redirect(url_for("index"))

    if request.method == "POST":
        name = request.form["name"].upper()
        conn = get_db_connection()
        try:
            conn.execute("INSERT INTO users (name) VALUES (?)", (name,))
            conn.commit()
            flash(f"User {name} added successfully!", "success")
        except sqlite3.IntegrityError:
            flash(f"User {name} already exists.", "error")
        finally:
            conn.close()

        return redirect(url_for("add_user"))

    return render_template("add_user.html")

# View Users (Admin Only)
@app.route("/view_users")
def view_users():
    if "user" not in session or not session.get("is_admin", False):
        flash("You do not have permission to access this page", "error")
        return redirect(url_for("index"))

    conn = get_db_connection()
    users = conn.execute("SELECT * FROM users").fetchall()
    conn.close()

    return render_template("view_users.html", users=users)

# Delete User (Admin Only)
@app.route("/delete_user/<int:user_id>", methods=["POST"])
def delete_user(user_id):
    if "user" not in session or not session.get("is_admin", False):
        flash("You do not have permission to access this page", "error")
        return redirect(url_for("index"))

    conn = get_db_connection()
    try:
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        flash("User deleted successfully!", "success")
    except sqlite3.Error as e:
        flash(f"An error occurred while deleting the user: {e}", "error")
    finally:
        conn.close()

    return redirect(url_for("view_users"))

# Logout
@app.route("/logout")
def logout():
    session.pop("user", None)
    session.pop("is_admin", None)
    flash("You have been logged out", "success")
    return redirect(url_for("login"))

# Initialize database on startup
if __name__ == '__main__':
    init_db()
    app.run(debug=True)