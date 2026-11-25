from datetime import datetime, timedelta
from functools import wraps
import os
import secrets
import sqlite3

from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
from flask_wtf.csrf import CSRFProtect, CSRFError
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
# The secret key signs the session cookie, so it must never be hardcoded in the source.
# Set TOKA_SECRET_KEY in the environment for a stable key; otherwise a random one is
# generated each time the app starts (users are simply signed out after a restart).
app.config["SECRET_KEY"] = os.environ.get("TOKA_SECRET_KEY") or secrets.token_hex(32)
app.config["DATABASE"] = "toka_fitness.db"
app.config["SESSION_COOKIE_HTTPONLY"] = True    # JavaScript cannot read the session cookie
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"   # cookie is not sent on cross-site POST requests

# CSRF protection: every POST form must include the hidden csrf_token field.
csrf = CSRFProtect(app)


@app.errorhandler(CSRFError)
def handle_csrf_error(error):
    """Show a friendly message if a form token is missing, invalid or has expired."""
    flash("Your form session expired or was invalid. Please try again.", "error")
    return redirect(request.referrer or url_for("home"))

def get_db():
    db = sqlite3.connect(app.config["DATABASE"])
    db.row_factory = sqlite3.Row
    return db


def init_db():
    db = get_db()
    db.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        email TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        membership_status TEXT NOT NULL DEFAULT 'free',
        role TEXT NOT NULL DEFAULT 'member',
        failed_logins INTEGER NOT NULL DEFAULT 0,
        locked_until TEXT
    );
    CREATE TABLE IF NOT EXISTS content (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        summary TEXT NOT NULL,
        body TEXT NOT NULL,
        category TEXT NOT NULL,
        access_level TEXT NOT NULL DEFAULT 'free',
        source TEXT DEFAULT ''
    );
    CREATE TABLE IF NOT EXISTS plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        plan_type TEXT NOT NULL,
        details TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    );
    CREATE TABLE IF NOT EXISTS community_posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        body TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        reported INTEGER NOT NULL DEFAULT 0,
        FOREIGN KEY(user_id) REFERENCES users(id)
    );
    CREATE TABLE IF NOT EXISTS points_ledger (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        completion_id TEXT NOT NULL,
        points INTEGER NOT NULL,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, completion_id)
    );
    """)
    count = db.execute("SELECT COUNT(*) FROM content").fetchone()[0]
    if count == 0:
        db.executemany(
            """INSERT INTO content (title, summary, body, category, access_level, source)
               VALUES (?, ?, ?, ?, ?, ?)""",
            [
                ("Getting started with strength training",
                 "A beginner-friendly introduction to resistance training.",
                 "Start with manageable movements, focus on controlled technique and allow recovery time between sessions. Increase difficulty gradually.",
                 "Strength", "free", "Example content only — replace with a qualified ToKa-approved source."),
                ("Building a balanced weekly routine",
                 "Ideas for combining activity and rest across the week.",
                 "A balanced routine can include strength, cardiovascular activity, mobility and rest. Adapt activity to your own ability and circumstances.",
                 "Healthy living", "free", "Example content only — replace with a qualified ToKa-approved source."),
                ("Progressive overload: member guide",
                 "An example of a paid guide for the prototype.",
                 "Progressive overload means gradually adjusting training demands over time. This example is placeholder content, not personalised medical advice.",
                 "Strength", "paid", "Example content only — replace with a qualified ToKa-approved source.")
            ]
        )
    db.commit()
    db.close()


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please sign in to use that feature.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def require_member(view):
    """Server-side paid-content check adapted from the Task 1 AI-generated snippet."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        uid = session.get("user_id")
        if uid is None:
            return redirect(url_for("login"))
        db = get_db()
        user = db.execute(
            "SELECT membership_status FROM users WHERE id = ?", (uid,)
        ).fetchone()
        db.close()
        if user is None or user["membership_status"] != "active":
            flash("This guide is for active members. View the pricing page to learn more.", "warning")
            return redirect(url_for("pricing"))
        return view(*args, **kwargs)
    return wrapped


@app.route("/")
def home():
    db = get_db()
    guides = db.execute(
        "SELECT * FROM content WHERE access_level='free' ORDER BY id LIMIT 3"
    ).fetchall()
    user = None
    if session.get("user_id"):
        user = db.execute("SELECT * FROM users WHERE id=?", (session["user_id"],)).fetchone()
    db.close()
    return render_template("home.html", guides=guides, user=user)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if len(username) < 3 or "@" not in email or len(password) < 8:
            flash("Enter a username (at least 3 characters), valid email and password (at least 8 characters).", "error")
            return render_template("register.html")
        db = get_db()
        try:
            db.execute(
                "INSERT INTO users (username,email,password_hash) VALUES (?,?,?)",
                (username, email, generate_password_hash(password))
            )
            db.commit()
            flash("Account created. You can now sign in.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("That username or email is already registered.", "error")
        finally:
            db.close()
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        if user and user["locked_until"] and datetime.fromisoformat(user["locked_until"]) > datetime.utcnow():
            db.close()
            flash("This account is temporarily locked. Try again later.", "error")
            return render_template("login.html")
        if user and check_password_hash(user["password_hash"], password):
            db.execute("UPDATE users SET failed_logins=0, locked_until=NULL WHERE id=?", (user["id"],))
            db.commit()
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            db.close()
            return redirect(url_for("home"))
        if user:
            attempts = user["failed_logins"] + 1
            locked = (datetime.utcnow() + timedelta(minutes=15)).isoformat() if attempts >= 5 else None
            db.execute("UPDATE users SET failed_logins=?, locked_until=? WHERE id=?", (attempts, locked, user["id"]))
            db.commit()
        db.close()
        flash("Email or password was not recognised.", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been signed out.", "success")
    return redirect(url_for("home"))


@app.route("/resources")
def resources():
    term = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    db = get_db()
    sql = "SELECT * FROM content WHERE (title LIKE ? OR summary LIKE ?)"
    pattern = f"%{term}%"
    params = [pattern, pattern]
    if category:
        sql += " AND category=?"
        params.append(category)
    sql += " ORDER BY title"
    results = db.execute(sql, params).fetchall()
    categories = db.execute("SELECT DISTINCT category FROM content ORDER BY category").fetchall()
    db.close()
    return render_template("resources.html", guides=results, term=term, categories=categories, selected_category=category)


@app.route("/guide/<int:content_id>")
def guide(content_id):
    db = get_db()
    item = db.execute("SELECT * FROM content WHERE id=?", (content_id,)).fetchone()
    db.close()
    if item is None:
        abort(404)
    if item["access_level"] == "paid":
        return paid_guide(content_id)
    return render_template("guide.html", guide=item)


@app.route("/member-guide/<int:content_id>")
@require_member
def paid_guide(content_id):
    db = get_db()
    item = db.execute("SELECT * FROM content WHERE id=? AND access_level='paid'", (content_id,)).fetchone()
    db.close()
    if item is None:
        abort(404)
    return render_template("guide.html", guide=item)


@app.route("/plans", methods=["GET", "POST"])
@login_required
def plans():
    db = get_db()
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        plan_type = request.form.get("plan_type", "")
        details = request.form.get("details", "").strip()
        if not title or len(title) > 100 or plan_type not in ("workout", "eating") or not details:
            flash("Enter a title, choose a plan type and add some plan details.", "error")
        else:
            db.execute(
                "INSERT INTO plans (user_id,title,plan_type,details) VALUES (?,?,?,?)",
                (session["user_id"], title, plan_type, details)
            )
            db.commit()
            flash("Your plan has been saved.", "success")
    saved = db.execute("SELECT * FROM plans WHERE user_id=? ORDER BY id DESC", (session["user_id"],)).fetchall()
    db.close()
    return render_template("plans.html", plans=saved)


@app.route("/plans/delete/<int:plan_id>", methods=["POST"])
@login_required
def delete_plan(plan_id):
    db = get_db()
    db.execute("DELETE FROM plans WHERE id=? AND user_id=?", (plan_id, session["user_id"]))
    db.commit()
    db.close()
    flash("Plan deleted if it belonged to your account.", "success")
    return redirect(url_for("plans"))


@app.route("/community", methods=["GET", "POST"])
@login_required
def community():
    db = get_db()
    if request.method == "POST":
        body = request.form.get("body", "").strip()
        if body and len(body) <= 500:
            db.execute("INSERT INTO community_posts (user_id,body) VALUES (?,?)", (session["user_id"], body))
            db.commit()
            flash("Post added. Community moderation is a future development task.", "success")
        else:
            flash("Posts must contain 1–500 characters.", "error")
    posts = db.execute(
        """SELECT community_posts.*, users.username FROM community_posts
           JOIN users ON users.id=community_posts.user_id
           WHERE reported=0 ORDER BY community_posts.id DESC"""
    ).fetchall()
    db.close()
    return render_template("community.html", posts=posts)


@app.route("/community/report/<int:post_id>", methods=["POST"])
@login_required
def report_post(post_id):
    db = get_db()
    db.execute("UPDATE community_posts SET reported=1 WHERE id=?", (post_id,))
    db.commit()
    db.close()
    flash("Post hidden from the public feed and flagged for staff review (prototype behaviour).", "success")
    return redirect(url_for("community"))


@app.route("/pricing")
def pricing():
    return render_template("pricing.html")

@app.route("/privacy")
def privacy():
    return render_template("privacy.html")

@app.route("/profile")
@login_required
def profile():
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id=?", (session["user_id"],)).fetchone()
    points = db.execute("SELECT COALESCE(SUM(points),0) FROM points_ledger WHERE user_id=?", (session["user_id"],)).fetchone()[0]
    db.close()
    return render_template("profile.html", user=user, points=points)


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        flash("Example form submitted. Add a database table and staff inbox before using this for real enquiries.", "success")
    return render_template("contact.html")

"""
Award demonstration points for a completion reference.
PROTOTYPE SHORTCUT (deliberate): this uses a GET link and trusts the
reference in the URL, so points are not tied to a verified workout.
Before launch it should be a POST request that checks the session
was really completed.
"""
@app.route("/demo-complete")
@login_required
def demo_complete():
    """Demonstration-only completion endpoint; replace with verified session completion."""
    completion_id = request.args.get("id", "").strip()
    if not completion_id:
        flash("A completion reference is required.", "error")
        return redirect(url_for("profile"))
    db = get_db()
    try:
        db.execute("INSERT INTO points_ledger (user_id,completion_id,points) VALUES (?,?,?)",
                   (session["user_id"], completion_id, 10))
        db.commit()
        flash("10 demonstration points awarded.", "success")
    except sqlite3.IntegrityError:
        db.rollback()
        flash("Points were already awarded for that completion reference.", "warning")
    finally:
        db.close()
    return redirect(url_for("profile"))

"""
PROTOTYPE SHORTCUT (deliberate): any signed-in user can activate
membership without paying, so the paid-guide check can be demonstrated.
Before launch, replace this with a real payment provider and only
activate membership after the payment is confirmed. 
"""
@app.route("/upgrade-demo", methods=["POST"])
@login_required
def upgrade_demo():
    db = get_db()
    db.execute("UPDATE users SET membership_status='active' WHERE id=?", (session["user_id"],))
    db.commit()
    db.close()
    flash("Demo membership activated without payment. Replace with a real payment provider before launch.", "warning")
    return redirect(url_for("pricing"))

if __name__ == "__main__":
    init_db()
    # Debug mode exposes an interactive debugger, so it is off unless TOKA_DEBUG=1 is set.
    app.run(debug=os.environ.get("TOKA_DEBUG") == "1")