import random
import re
import sqlite3
import os
from datetime import date
import json
from flask import Flask, render_template, session, redirect, url_for, jsonify, request

# ==============================
# APP SETUP
# ==============================

app = Flask(__name__)
app.secret_key = "super-secret-training-key"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "nihal123"

# ==============================
# DATABASE INIT
# ==============================

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT,
            sender TEXT,
            subject TEXT,
            body TEXT,
            attachment TEXT,
            severity TEXT
        )
    """)

    conn.commit()
    conn.close()

# ==============================
# UTILITIES
# ==============================

def make_links_clickable(text, email_id):
    url_pattern = r'(http[s]?://[^\s]+)'
    return re.sub(
        url_pattern,
        lambda m: f'<a href="/action/{email_id}/click" class="email-link">{m.group(0)}</a>',
        text
    )

def check_badges():
    unlocked = session.get("badges", [])
    if session["score"] >= 70 and "Sharp Eye" not in unlocked:
        unlocked.append("Sharp Eye")
    if session["score"] == 100 and "Phishing Expert" not in unlocked:
        unlocked.append("Phishing Expert")
    if session["streak"] >= 5 and "Resilient Defender" not in unlocked:
        unlocked.append("Resilient Defender")
    session["badges"] = unlocked

# ==============================
# EMAIL FETCHING
# ==============================

def fetch_random_email(email_type):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT * FROM emails WHERE type=?", (email_type,))
    rows = c.fetchall()
    conn.close()

    if not rows:
        return None

    row = random.choice(rows)

    return {
        "id": row[0],
        "type": row[1],
        "sender": row[2],
        "subject": row[3],
        "body": row[4],
        "attachment": row[5],
        "severity": row[6]
    }

def generate_inbox(count=30):
    emails = []

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM emails")
    rows = c.fetchall()
    conn.close()

    if not rows:
        return []

    for _ in range(count):
        row = random.choice(rows)

        email = {
            "id": row[0],
            "type": row[1],
            "sender": row[2],
            "subject": row[3],
            "body": row[4],
            "attachment": row[5],
            "severity": row[6]
        }

        emails.append(email)

    random.shuffle(emails)
    return emails

# ==============================
# SESSION INIT
# ==============================

@app.before_request
def init_session():
    session.setdefault("score", 50)
    session.setdefault("streak", 0)
    session.setdefault("badges", [])
    session.setdefault("timer_mode", False)
    session.setdefault("trash", [])
    session.setdefault("daily_attempt", None)

    if "emails" not in session:
        session["emails"] = generate_inbox()

# ==============================
# ROUTES
# ==============================

@app.route("/")
def intro():
    return render_template("index.html")

@app.route("/inbox")
def inbox():
    if not session["emails"]:
        session["emails"] = generate_inbox()

    return render_template(
        "inbox.html",
        emails=session["emails"],
        score=session["score"],
        streak=session["streak"],
        badges=session["badges"],
        timer=session["timer_mode"]
    )

@app.route("/trash")
def trash():
    return render_template(
        "trash.html",
        emails=session["trash"],
        score=session["score"],
        streak=session["streak"]
    )

@app.route("/toggle_timer")
def toggle_timer():
    session["timer_mode"] = not session["timer_mode"]
    return redirect(url_for("inbox"))

@app.route("/daily")
def daily():
    today = str(date.today())
    if session["daily_attempt"] == today:
        return "Daily challenge already attempted today."

    session["daily_attempt"] = today
    session["emails"] = generate_inbox(20)
    return redirect(url_for("inbox"))

@app.route("/email/<int:email_id>")
def open_email(email_id):
    email = next((e for e in session["emails"] if e["id"] == email_id), None)

    if not email:
        return redirect(url_for("inbox"))

    email_copy = email.copy()
    email_copy["body"] = make_links_clickable(email["body"], email_id)

    return render_template(
        "email.html",
        email=email_copy,
        timer=session["timer_mode"]
    )

@app.route("/new_email")
def new_email():
    email = fetch_random_email("Phishing") or fetch_random_email("Safe")

    if not email:
        return jsonify({})

    session["emails"].insert(0, email)
    return jsonify(email)

# ==============================
# ACTION HANDLER
# ==============================

def update_score(points):
    session["score"] += points
    session["score"] = max(0, min(100, session["score"]))

    if points > 0:
        session["streak"] += 1
    else:
        session["streak"] = 0

    check_badges()

@app.route("/action/<int:email_id>/<action>")
def take_action(email_id, action):
    email = next((e for e in session["emails"] if e["id"] == email_id), None)

    if not email:
        return redirect(url_for("inbox"))

    score_change = 0

    if email["type"] == "Phishing":
        if action in ["click", "download", "reply"]:
            score_change = -20
        elif action == "report":
            score_change = 15
    else:
        if action == "report":
            score_change = -5
        else:
            score_change = 5

    update_score(score_change)

    session["emails"].remove(email)
    session["trash"].append(email)

    result = "Correct!" if score_change > 0 else "Incorrect action."
    training = "Always verify sender and links before interacting."

    return render_template(
        "result.html",
        result=result,
        training=training,
        score=session["score"],
        streak=session["streak"],
        score_change=score_change,
        badges=session["badges"]
    )

# ==============================
# ADMIN PANEL
# ==============================

@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if request.form["username"] == ADMIN_USERNAME and request.form["password"] == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            return redirect(url_for("admin"))
        return render_template("admin_login.html", error="Invalid credentials")

    return render_template("admin_login.html")

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    if request.method == "POST":
        c.execute("""
            INSERT INTO emails (type, sender, subject, body, attachment, severity)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            request.form["type"],
            request.form["sender"],
            request.form["subject"],
            request.form["body"],
            request.form["attachment"],
            request.form["severity"]
        ))
        conn.commit()

    c.execute("SELECT * FROM emails")
    emails = c.fetchall()
    conn.close()

    return render_template("admin.html", emails=emails)

# ==============================
# ADMIN BULK IMPORT
# ==============================

@app.route("/admin-import", methods=["POST"])
def admin_import():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    file = request.files.get("file")

    if not file:
        return "No file uploaded"

    try:
        data = json.load(file)
    except Exception as e:
        return f"Invalid JSON file: {e}"

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    for email in data:
        c.execute("""
            INSERT INTO emails (type, sender, subject, body, attachment, severity)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            email["type"],
            email["sender"],
            email["subject"],
            email["body"],
            email.get("attachment"),
            email["severity"]
        ))

    conn.commit()
    conn.close()

    return redirect(url_for("admin"))

@app.route("/admin-delete/<int:email_id>")
def admin_delete(email_id):
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM emails WHERE id=?", (email_id,))
    conn.commit()
    conn.close()

    return redirect(url_for("admin"))

# ==============================
# RESET
# ==============================

@app.route("/reset")
def reset():
    session["score"] = 50
    session["streak"] = 0
    session["badges"] = []
    session["trash"] = []
    session["emails"] = generate_inbox()
    return redirect(url_for("inbox"))

# ==============================
# START
# ==============================

init_db()

if __name__ == "__main__":
    app.run(debug=True)