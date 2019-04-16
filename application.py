import os

from datetime import datetime
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, good, bad, improve

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached


@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///project.db")

@app.route("/home")
@login_required
def home():
    """Return to home page"""
    return redirect("/")

@app.route("/position")
@login_required
def position():
    success_extra = db.execute("SELECT SUM(suc_counter) FROM activity WHERE id = :id", id=session["user_id"])
    failure_extra = db.execute("SELECT SUM(fail_counter) FROM activity WHERE id = :id", id=session["user_id"])
    success_count = success_extra[0]["SUM(suc_counter)"]
    failure_count = failure_extra[0]["SUM(fail_counter)"]

    if success_count > failure_count:
        return good("Good going! More successes than failures!")
    elif success_count < failure_count:
        return bad("Failures more than successes. Time to focus!")
    elif success_count == failure_count:
        return improve("Can improve. Successes equal to failures.")

@app.route("/")
@login_required
def index():
    """Home page"""
    date_time = []
    date_time.append(datetime.now())
    return render_template("index.html", dt=date_time)

@app.route("/suggestion")
@login_required
def suggestion():
    """Show suggestions"""
    tasks = db.execute("SELECT task FROM activity WHERE id = :id", id=session["user_id"])
    row = db.execute("SELECT task,priority,status FROM activity WHERE id = :id GROUP BY task ", id=session["user_id"])
    count = 0
    task_left = []
    priority = []
    status = []

    for task in tasks:
        if row[count]["status"] == "failure" or (row[count]["status"] == "in progress" and row[count]["priority"] == "high"):
            task_left.append(row[count]["task"])
            priority.append(row[count]["priority"])
            status.append(row[count]["status"])
        count += 1

    return render_template("suggestion.html", counter=count, task_pass=task_left, priority_pass=priority,status_pass=status)

@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    """Add Task"""
    if request.method == "POST":
        if not request.form.get("task"):
            return apology("Enter Task!")
        elif not request.form.get("status"):
            return apology("Enter status!")
        elif not request.form.get("priority"):
            return apology("Assign priority!")

        success = 0
        failure = 0
        if request.form.get("status") == "success":
            success += 1
        elif request.form.get("status") == "failure":
            failure += 1

        db.execute("INSERT INTO activity(task,status,priority,suc_counter,fail_counter,id) VALUES(:task,:status,:priority,:suc_counter,:fail_counter,:id)", task=request.form.get("task"), status=request.form.get("status"), priority=request.form.get("priority"), suc_counter=success, fail_counter=failure, id=session["user_id"])
        # redirect user to home page
        return redirect("/")
    else:
        return render_template("add.html")

@app.route("/history")
@login_required
def history():
    """Show history of tasks"""
    success_extra = db.execute("SELECT SUM(suc_counter) FROM activity WHERE id = :id", id=session["user_id"])
    failure_extra = db.execute("SELECT SUM(fail_counter) FROM activity WHERE id = :id", id=session["user_id"])
    success_count = success_extra[0]["SUM(suc_counter)"]
    failure_count = failure_extra[0]["SUM(fail_counter)"]

    information = db.execute("SELECT * FROM activity WHERE id = :id", id=session["user_id"])
    return render_template("history.html", info=information, successes=success_count, failures=failure_count)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("Provide username!", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("Provide password!", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["password"], request.form.get("password")):
            return apology("Invalid username and/or password!", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/update", methods=["GET", "POST"])
@login_required
def update():
    """Update task status."""
    if request.method == "POST":
        rows = db.execute("SELECT * FROM activity WHERE id = :id AND task = :task", id=session["user_id"], task=request.form.get("task"))
        if rows[0]["status"] == "in progress" and request.form.get("status") == "success":
            db.execute("UPDATE activity SET suc_counter = :success WHERE id = :id AND task = :task", success = rows[0]["suc_counter"] + 1, id=session["user_id"], task=request.form.get("task"))
        elif rows[0]["status"] == "in progress" and request.form.get("status") == "failure":
            db.execute("UPDATE activity SET fail_counter = :fail WHERE id = :id AND task = :task", fail = rows[0]["fail_counter"] + 1, id=session["user_id"], task=request.form.get("task"))

        db.execute("UPDATE activity SET status = :status WHERE id = :id AND task = :task", status=request.form.get("status"), id=session["user_id"], task=request.form.get("task"))
        db.execute("UPDATE activity SET priority = :priority WHERE id = :id and task = :task", priority=request.form.get("priority"), id=session["user_id"], task=request.form.get("task"))
        return redirect("/")
    else:
        row = db.execute("SELECT * FROM activity WHERE id = :id", id=session["user_id"])
        return render_template("update.html", tasks=row)

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    if request.method == "POST":
        if not request.form.get("username"):
            return apology("Missing username!")
        elif not request.form.get("password"):
            return apology("Missing password!")
        elif not request.form.get("confirmation"):
            return apology("Missing confirmation!")
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("Password and confirmation do not match!")
        # introduce additional checks that will force user to enter stronger password having at least 5 characters, one digit, one letter and one special character
        # PERSONAL TOUCH
        elif len(request.form.get("password")) < 5:
            return apology("Password must have at least five charcters!")
        elif request.form.get("password").isdigit():
            return apology("Password must have at least one alphabet and special symbol!")
        elif request.form.get("password").isalpha():
            return apology("Password must have at least one digit and special symbol!")
        elif request.form.get("password").isalnum():
            return apology("Password must have a special symbol!")

        hash = generate_password_hash(request.form.get("password"))
        result = db.execute("INSERT INTO users(username,password) VALUES(:username,:password)", username = request.form.get("username"), password=hash)

        if not result:
            return apology("Could not store data in database!")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                              username=request.form.get("username"))
        session["user_id"] = rows[0]["id"]

        # Return user to home page
        return redirect("/")

    else:
        return render_template("register.html")

def errorhandler(e):
    """Handle error"""
    return apology(e.name, e.code)


# listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)