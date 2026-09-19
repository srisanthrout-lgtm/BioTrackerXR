from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "biotrackerxr-dev-key"
DB = "biotrackerxr.db"

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""CREATE TABLE IF NOT EXISTS students(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        register_no TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        department TEXT NOT NULL,
        year TEXT NOT NULL
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS attendance(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        time TEXT NOT NULL,
        status TEXT NOT NULL,
        UNIQUE(student_id, date),
        FOREIGN KEY(student_id) REFERENCES students(id)
    )""")
    conn.commit()
    conn.close()

@app.route("/")
def dashboard():
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    today = datetime.now().strftime("%Y-%m-%d")
    present = conn.execute(
        "SELECT COUNT(*) FROM attendance WHERE date=? AND status='Present'", (today,)
    ).fetchone()[0]
    recent = conn.execute("""
        SELECT a.date,a.time,a.status,s.register_no,s.name
        FROM attendance a JOIN students s ON a.student_id=s.id
        ORDER BY a.id DESC LIMIT 10
    """).fetchall()
    conn.close()
    absent = max(total - present, 0)
    percentage = round((present / total) * 100, 2) if total else 0
    return render_template("dashboard.html", total=total, present=present,
                           absent=absent, percentage=percentage, recent=recent)

@app.route("/students")
def students():
    conn = get_db()
    rows = conn.execute("SELECT * FROM students ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("students.html", students=rows)

@app.route("/students/add", methods=["GET","POST"])
def add_student():
    if request.method == "POST":
        reg = request.form["register_no"].strip()
        name = request.form["name"].strip()
        dept = request.form["department"].strip()
        year = request.form["year"].strip()
        if not all([reg,name,dept,year]):
            flash("All fields are required.")
            return redirect(url_for("add_student"))
        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO students(register_no,name,department,year) VALUES(?,?,?,?)",
                (reg,name,dept,year)
            )
            conn.commit()
            flash("Student added successfully.")
        except sqlite3.IntegrityError:
            flash("Register number already exists.")
        finally:
            conn.close()
        return redirect(url_for("students"))
    return render_template("add_student.html")

@app.route("/attendance", methods=["GET","POST"])
def attendance():
    conn = get_db()
    students = conn.execute("SELECT * FROM students ORDER BY name").fetchall()
    if request.method == "POST":
        student_id = request.form["student_id"]
        today = datetime.now().strftime("%Y-%m-%d")
        now = datetime.now().strftime("%H:%M:%S")
        try:
            conn.execute(
                "INSERT INTO attendance(student_id,date,time,status) VALUES(?,?,?,'Present')",
                (student_id,today,now)
            )
            conn.commit()
            flash("Attendance marked successfully.")
        except sqlite3.IntegrityError:
            flash("Attendance already marked for this student today.")
        conn.close()
        return redirect(url_for("attendance"))
    conn.close()
    return render_template("attendance.html", students=students)

@app.route("/reports")
def reports():
    conn = get_db()
    rows = conn.execute("""
        SELECT s.register_no,s.name,s.department,s.year,
               SUM(CASE WHEN a.status='Present' THEN 1 ELSE 0 END) AS present_days,
               COUNT(a.id) AS recorded_days
        FROM students s LEFT JOIN attendance a ON s.id=a.student_id
        GROUP BY s.id ORDER BY s.name
    """).fetchall()
    conn.close()
    data=[]
    for r in rows:
        recorded=r["recorded_days"] or 0
        present=r["present_days"] or 0
        pct=round(present/recorded*100,2) if recorded else 0
        data.append(dict(r, percentage=pct))
    return render_template("reports.html", rows=data)

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
