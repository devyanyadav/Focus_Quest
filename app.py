import os
import sqlite3
import json
from flask import Flask, redirect, render_template, request, session, url_for
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology, login_required
from datetime import datetime, date, timedelta

app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

def query(sql, *args):
    con = sqlite3.connect("habit.db")
    con.row_factory = sqlite3.Row
    rows = con.execute(sql, args).fetchall()
    con.commit()
    con.close()
    return [dict(row) for row in rows]


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == "POST":
        new_user = request.form.get("username")
        new_psw = request.form.get("password")

        if not new_psw or not new_user:
            return apology('all fields are to be filled', 400)

        existing = query("SELECT * FROM users WHERE username = ?", new_user)
        if existing:
            return apology("Username already taken", 400)

        hashed_password = generate_password_hash(new_psw)
        query("INSERT INTO users (username, password) VALUES (?, ?)", new_user, hashed_password)

        new_user_id = query("SELECT user_id FROM users WHERE username = ?", new_user)[0]["user_id"]
        session["user_id"] = new_user_id

        return redirect("/")

    return render_template("register.html")


@app.route('/login', methods=['POST', 'GET'])
def login():
    session.clear()

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username:
            return apology("must provide username", 403)
        elif not password:
            return apology("must provide password", 403)

        rows = query("SELECT * FROM users WHERE username = ?", username)

        if len(rows) != 1 or not check_password_hash(rows[0]["password"], password):
            return apology("invalid username and/or password", 403)

        session["user_id"] = rows[0]["user_id"]
        return redirect("/")

    return render_template("login.html")


@app.route('/')
@login_required
def index():
    return render_template('index.html')


@app.route('/add-habit', methods=['GET', 'POST'])
@login_required
def add_habit():
    if request.method == "POST":
        habit = request.form.get("habit")
        if not habit or len(habit) == 0:
            return apology("you did not fill it", 400)

        existing = query(
            "SELECT habit FROM habit WHERE user_id = ? AND habit = ?",
            session["user_id"], habit
        )
        if existing:
            return apology("you already have this habit", 400)

        query(
            "INSERT INTO habit(user_id, habit, created_at) VALUES(?, ?, ?)",
            session["user_id"], habit, str(date.today())
        )
        return redirect("/")

    rows = query("SELECT * FROM habit WHERE user_id = ?", session["user_id"])
    habits = [{"habit": row["habit"]} for row in rows]
    return render_template('add-habit.html', habits=habits)


@app.route('/habits', methods=['GET', 'POST'])
@login_required
def habits():
    if request.method == 'POST':
        if 'date' in request.form and 'habit_id' not in request.form:
            selected_date = request.form.get('date')
            return redirect(url_for('habits') + f'?date={selected_date}')

        elif 'habit_id' in request.form:
            habit_id = request.form.get('habit_id')
            selected_date = request.form.get("date")

            habit_check = query(
                "SELECT created_at FROM habit WHERE id = ? AND user_id = ?",
                habit_id, session["user_id"]
            )

            if habit_check and habit_check[0]['created_at'][:10] <= selected_date:
                existing = query(
                    "SELECT * FROM habit_completion WHERE user_id = ? AND habit_id = ? AND date = ?",
                    session["user_id"], habit_id, selected_date
                )

                if existing:
                    new_status = 0 if existing[0]['completed'] == 1 else 1
                    query(
                        "UPDATE habit_completion SET completed = ? WHERE user_id = ? AND habit_id = ? AND date = ?",
                        new_status, session["user_id"], habit_id, selected_date
                    )
                else:
                    query(
                        "INSERT INTO habit_completion(user_id, habit_id, date, completed) VALUES(?, ?, ?, ?)",
                        session["user_id"], habit_id, selected_date, 1
                    )

            return redirect(url_for('habits') + f'?date={selected_date}')

        else:
            selected_date = str(date.today())

    selected_date = request.args.get('date', str(date.today()))

    habits = query("SELECT id, created_at FROM habit WHERE user_id = ?", session["user_id"])

    for habit in habits:
        created_at = date.fromisoformat(habit["created_at"][:10])
        current_date = created_at
        today = date.today()

        while current_date <= today:
            query(
                """INSERT OR IGNORE INTO habit_completion (user_id, habit_id, date, completed)
                   VALUES (?, ?, ?, 0)""",
                session["user_id"], habit["id"], current_date
            )
            current_date += timedelta(days=1)

    habits = query(
        "SELECT * FROM habit WHERE user_id = ? AND created_at <= ?",
        session["user_id"], selected_date
    )

    completions = query(
        "SELECT habit_id FROM habit_completion WHERE user_id = ? AND date = ? AND completed = 1",
        session["user_id"], selected_date
    )

    completed_ids = [c['habit_id'] for c in completions]

    for habit in habits:
        habit['is_completed'] = habit['id'] in completed_ids

    all_completed = len(habits) > 0 and len(completed_ids) == len(habits)

    return render_template('habits.html',
                           habits=habits,
                           selected_date=selected_date,
                           all_completed=all_completed)


@app.route('/stats')
@login_required
def stats():
    total_habits = query(
        "SELECT COUNT(*) as count FROM habit WHERE user_id = ?",
        session["user_id"]
    )[0]['count']

    all_habits = query(
        """SELECT COUNT(habit_id) as ab FROM habit_completion
           WHERE date >= DATE('now', '-30 days') AND user_id = ?""",
        session["user_id"]
    )[0]["ab"]

    completed = query(
        """SELECT SUM(completed) AS completed FROM habit_completion
           WHERE date >= DATE('now', '-30 days') AND user_id = ?""",
        session["user_id"]
    )[0]["completed"]

    if not all_habits or all_habits == 0:
        completion_rate = 0
    else:
        completion_rate = round((completed or 0) / all_habits * 100.0, 1)

    completed_dates = query(
        "SELECT DISTINCT date FROM habit_completion WHERE user_id = ? AND completed = 1 ORDER BY date DESC",
        session["user_id"]
    )

    dates = [date.fromisoformat(row["date"]) for row in completed_dates]

    streak = 0
    today = date.today()

    if dates:
        if dates[0] == today or dates[0] == today - timedelta(days=1):
            streak = 1
            for i in range(1, len(dates)):
                if dates[i] == dates[i - 1] - timedelta(days=1):
                    streak += 1
                else:
                    break

    completion_rate_last_30_days = []
    last_30_days = []

    end_date = date.today()
    last_30_days.append(str(end_date))
    for i in range(1, 31):
        duration = end_date - timedelta(days=i)
        last_30_days.append(str(duration))

    for x in last_30_days:
        day_all = query(
            """SELECT COUNT(habit_id) as ab FROM habit_completion
               WHERE date = ? AND user_id = ?""",
            x, session["user_id"]
        )[0]["ab"]

        day_completed = query(
            """SELECT SUM(completed) AS completed FROM habit_completion
               WHERE date = ? AND user_id = ?""",
            x, session["user_id"]
        )[0]["completed"]

        if not day_all or day_all == 0 or day_completed is None:
            completion_rate_of_day = 0
        else:
            completion_rate_of_day = round(day_completed / day_all * 100.0, 1)

        completion_rate_last_30_days.append(str(completion_rate_of_day))

    habit_stats = query(
        """SELECT h.habit, COUNT(hc.id) as completion_count
           FROM habit h
           LEFT JOIN habit_completion hc ON h.id = hc.habit_id AND hc.completed = 1
           WHERE h.user_id = ?
           GROUP BY h.id, h.habit
           ORDER BY completion_count DESC""",
        session["user_id"]
    )

    habit_names = [str(h['habit']) for h in habit_stats]
    habit_counts = [str(h['completion_count']) for h in habit_stats]

    return render_template("stats.html",
                           total_habits=total_habits,
                           completion_rate=completion_rate,
                           streak=streak,
                           last_30_days=json.dumps(last_30_days),
                           completion_rate_30_days=json.dumps(completion_rate_last_30_days),
                           habit_names=json.dumps(habit_names),
                           habit_counts=json.dumps(habit_counts))


@app.route('/logout')
@login_required
def logout():
    session.clear()
    return redirect("/")