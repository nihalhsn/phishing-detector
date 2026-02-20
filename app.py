import random
import re
from email_db import SAFE_EMAILS, PHISHING_EMAILS
import sqlite3
from datetime import date
import json
from flask import Flask, render_template, session, redirect, url_for, jsonify, request

def init_db():
    conn = sqlite3.connect("database.db")
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


ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "nihal123"


app = Flask(__name__)
app.secret_key = "super-secret-training-key"

SAFE_SENDERS = [
    "hr@company.com",
    "accounts@company.com",
    "noreply@google.com",
    "alerts@bank.com",
    "support@amazon.com"
]

PHISHING_DOMAINS = [
    "g00gle-security.xyz",
    "amaz0n-billing.net",
    "secure-login-paypal.xyz",
    "bank-verification.info",
    "micr0soft-alerts.top"
]

NAMES = ["User", "Employee", "Customer"]
LOCATIONS = ["Russia", "China", "Germany", "USA"]
SEVERITY_LEVELS = ["Low", "Medium", "High"]

BADGES = [
    {"name": "Sharp Eye", "condition": lambda: session["score"] >= 70},
    {"name": "Phishing Expert", "condition": lambda: session["score"] == 100},
    {"name": "Resilient Defender", "condition": lambda: session["streak"] >= 5}
]

def init_db():
    conn = sqlite3.connect("database.db")
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

# ---------------- UTILITIES ----------------

def make_links_clickable(text, email_id):
    url_pattern = r'(http[s]?://[^\s]+)'
    return re.sub(url_pattern,
                  lambda m: f'<a href="/action/{email_id}/click" class="email-link">{m.group(0)}</a>',
                  text)


def get_difficulty():
    score = session["score"]
    if score < 30:
        return "Easy"
    elif score < 70:
        return "Medium"
    else:
        return "Hard"


def check_badges():
    unlocked = session.get("badges", [])
    for badge in BADGES:
        if badge["name"] not in unlocked and badge["condition"]():
            unlocked.append(badge["name"])
    session["badges"] = unlocked


# ---------------- EMAIL GENERATION ----------------

def fetch_random_email(email_type):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    try:
        c.execute("SELECT * FROM emails WHERE type=?", (email_type,))
        rows = c.fetchall()
    except:
        conn.close()
        return None

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





def generate_inbox(count=50):
    emails = []

    for _ in range(count):
        if random.random() > 0.5:
            email = fetch_random_email("Phishing")
        else:
            email = fetch_random_email("Safe")

        if email:
            emails.append(email)

    random.shuffle(emails)
    return emails

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    if request.method == "POST":

        conn = sqlite3.connect("database.db")
        c = conn.cursor()

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
        conn.close()

        return redirect(url_for("admin"))

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT * FROM emails")
    all_emails = c.fetchall()
    conn.close()

    return render_template("admin.html", emails=all_emails)

@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            return redirect(url_for("admin"))
        else:
            return render_template("admin_login.html", error="Invalid credentials")

    return render_template("admin_login.html")


# ---------------- SESSION INIT ----------------

@app.before_request
def init():
    session.setdefault("score", 50)
    session.setdefault("streak", 0)
    session.setdefault("badges", [])
    session.setdefault("timer_mode", False)
    session.setdefault("trash", [])
    session.setdefault("daily_attempt", None)
    if "emails" not in session:
        session["emails"] = generate_inbox()


@app.route("/admin-import", methods=["POST"])
def admin_import():

    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    file = request.files["file"]

    if not file:
        return "No file uploaded"

    data = json.load(file)

    conn = sqlite3.connect("database.db")
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
# ---------------- ROUTES ----------------

@app.route("/")
def intro():
    return render_template("index.html")


@app.route("/toggle_timer")
def toggle_timer():
    session["timer_mode"] = not session["timer_mode"]
    return redirect(url_for("inbox"))


@app.route("/inbox")
def inbox():

    if "emails" not in session or not session["emails"]:
        session["emails"] = generate_inbox()

    return render_template(
        "inbox.html",
        emails=session["emails"],
        score=session["score"],
        streak=session["streak"],
        badges=session.get("badges", []),
        timer=session.get("timer_mode", False)
    )



@app.route("/trash")
def trash():
    return render_template(
        "trash.html",
        emails=session["trash"],
        score=session["score"],
        streak=session["streak"]
    )


@app.route("/daily")
def daily():
    today = str(date.today())
    if session["daily_attempt"] == today:
        return "Daily challenge already attempted today."

    session["daily_attempt"] = today
    session["emails"] = generate_inbox(20)
    return redirect(url_for("inbox"))


@app.route("/new_email")
def new_email():

    # Get highest existing ID
    if session["emails"]:
        max_id = max(e["id"] for e in session["emails"])
    else:
        max_id = 0

    new_id = max_id + 1

    # Generate new email properly
    if random.random() > 0.5:
        new = generate_phishing_email(new_id)
    else:
        new = generate_safe_email(new_id)

    # Add to session
    session["emails"].insert(0, new)

    return jsonify(new)



@app.route("/email/<int:email_id>")
def open_email(email_id):
    email = next((e for e in session["emails"] if e["id"] == email_id), None)

    if not email:
        return redirect(url_for("inbox"))

    email_copy = email.copy()
    email_copy["body"] = make_links_clickable(email["body"], email_id)
    return render_template("email.html", email=email_copy, timer=session["timer_mode"])



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
    email = next(e for e in session["emails"] if e["id"] == email_id)

    result = ""
    training = ""
    score_change = 0

    if email["type"] == "Phishing":
        if action in ["click", "download", "reply"]:
            penalty = -15 if email["severity"] == "Low" else -20
            score_change = penalty
            update_score(penalty)
            result = "❌ You interacted with a phishing attack!"
            training = "This was a malicious email. Always verify links."
        elif action == "report":
            score_change = 15
            update_score(15)
            result = "🛡 Excellent! You reported a phishing email."
            training = "Correct action."
    else:
        if action == "report":
            score_change = -5
            update_score(-5)
            result = "⚠ False report."
            training = "This was legitimate communication."
        else:
            score_change = 5
            update_score(5)
            result = "✅ Safe interaction."
            training = "Handled properly."

    # Move to trash
    session["emails"].remove(email)
    session["trash"].append(email)

    return render_template("result.html",
                           result=result,
                           training=training,
                           score=session["score"],
                           streak=session["streak"],
                           score_change=score_change,
                           badges=session["badges"])
@app.route("/reset")
def reset():
    session["score"] = 50
    session["streak"] = 0
    session["badges"] = []
    session["trash"] = []
    session["emails"] = generate_inbox()
    return redirect(url_for("inbox"))

@app.route("/admin-delete/<int:email_id>")
def admin_delete(email_id):

    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("DELETE FROM emails WHERE id=?", (email_id,))
    conn.commit()
    conn.close()

    return redirect(url_for("admin"))



init_db()

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)


