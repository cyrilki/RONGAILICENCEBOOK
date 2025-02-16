from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import datetime

app = Flask(__name__)
app.secret_key = "securekey2025"  # Secret key for sessions

# Predefined login users
USERS = {"JOY", "WILL", "STAN", "CYRIL", "MIKE", "BRAYO", "MARIA", "AGNES"}
PASSWORD = "RONGAI2025"

# Database connection
def get_db_connection():
    conn = sqlite3.connect('license_database.db', timeout=300)  # 5-minute timeout
    conn.row_factory = sqlite3.Row
    return conn

# Initialize database
def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS licenses (
            entry_number INTEGER,
            license_number TEXT NOT NULL UNIQUE,
            owner_name TEXT NOT NULL CHECK(owner_name = UPPER(owner_name)),
            owner_phone TEXT NOT NULL CHECK(length(owner_phone) = 10 AND owner_phone LIKE '07%'),
            business_name TEXT NOT NULL CHECK(business_name = UPPER(business_name)),
            business_location TEXT,
            date_registered TEXT NOT NULL,
            date_renewed TEXT,
            status TEXT,
            year INTEGER NOT NULL,
            PRIMARY KEY(entry_number, year)
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

# Login Page
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].upper()
        password = request.form["password"]

        if username in USERS and password == PASSWORD:
            session["user"] = username
            flash("Login successful!", "success")
            return redirect(url_for("index"))
        else:
            flash("Invalid credentials", "error")
            return redirect(url_for("login"))
    
    return render_template("login.html")

# Home Page
@app.route("/home")
def index():
    if "user" not in session:
        flash("You must log in to access this page", "error")
        return redirect(url_for("login"))
    
    return render_template("index.html", user=session["user"])

# Add a License
@app.route("/add", methods=["GET", "POST"])
def add_license():
    if "user" not in session:
        flash("You must log in to add a license", "error")
        return redirect(url_for("login"))

    if request.method == "POST":
        entry_number = get_next_entry_number()
        license_number = request.form["license_number"].upper()
        owner_name = request.form["owner_name"].upper()
        owner_phone = request.form["owner_phone"]
        business_name = request.form["business_name"].upper()
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
                    entry_number, license_number, owner_name, owner_phone,
                    business_name, business_location, date_registered,
                    date_renewed, status, year
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                entry_number, license_number, owner_name, owner_phone,
                business_name, business_location, date_registered,
                date_renewed, status, current_year
            ))
            conn.commit()
            flash("License added successfully!", "success")
        except sqlite3.IntegrityError:
            flash("License number already exists", "error")
        finally:
            conn.close()

        return redirect(url_for("index"))

    return render_template("add_license.html", entry_number=get_next_entry_number(), year=datetime.datetime.now().year)

# Search License
@app.route("/search", methods=["GET", "POST"])
def search_license():
    if "user" not in session:
        flash("You must log in to search for a license", "error")
        return redirect(url_for("login"))

    results = None
    if request.method == "POST":
        search_term = request.form["search_term"]
        conn = get_db_connection()
        cursor = conn.execute('''
            SELECT * FROM licenses 
            WHERE license_number = ? OR owner_name = ? OR business_name = ?
        ''', (search_term, search_term, search_term))
        results = cursor.fetchall()
        conn.close()

        if not results:
            flash("No matching licenses found", "error")

    return render_template("search_license.html", results=results)

# Logout
@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("You have been logged out", "success")
    return redirect(url_for("login"))

# Initialize database on startup
if __name__ == '__main__':
    init_db()
    app.run(debug=True)