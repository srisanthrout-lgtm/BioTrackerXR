from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    send_file
)

import sqlite3
import cv2
from datetime import datetime
import os
import sys
import subprocess
from functools import wraps
from io import BytesIO

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from openpyxl import Workbook


app = Flask(__name__)
app.secret_key = "biotrackerxr-dev-key"

DB = "biotrackerxr.db"


# ---------------- DATABASE ----------------

def get_db():

    c = sqlite3.connect(DB)

    c.row_factory = sqlite3.Row

    return c


def init_db():

    c = get_db()

    c.execute("""
        CREATE TABLE IF NOT EXISTS students(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            register_no TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            department TEXT NOT NULL,
            year TEXT NOT NULL
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS attendance(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            status TEXT NOT NULL,
            UNIQUE(student_id, date)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS admins(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    admin = c.execute(
        "SELECT * FROM admins WHERE username=?",
        ("admin",)
    ).fetchone()

    if admin is None:

        password_hash = generate_password_hash(
            "admin123"
        )

        c.execute(
            """
            INSERT INTO admins(username,password)
            VALUES(?,?)
            """,
            ("admin", password_hash)
        )

    c.commit()

    c.close()


# ---------------- LOGIN PROTECTION ----------------

def login_required(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):

        if "admin_id" not in session:

            return redirect(
                url_for("login")
            )

        return f(*args, **kwargs)

    return decorated_function


# ---------------- LOGIN ----------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if "admin_id" in session:

        return redirect(
            url_for("dashboard")
        )

    if request.method == "POST":

        username = request.form[
            "username"
        ].strip()

        password = request.form[
            "password"
        ]

        c = get_db()

        admin = c.execute(
            """
            SELECT *
            FROM admins
            WHERE username=?
            """,
            (username,)
        ).fetchone()

        c.close()

        if admin and check_password_hash(
            admin["password"],
            password
        ):

            session["admin_id"] = admin["id"]

            session["username"] = admin["username"]

            flash(
                "Login successful."
            )

            return redirect(
                url_for("dashboard")
            )

        flash(
            "Invalid username or password."
        )

    return render_template(
        "login.html"
    )


# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():

    session.clear()

    flash(
        "You have been logged out."
    )

    return redirect(
        url_for("login")
    )


# ---------------- DASHBOARD ----------------

@app.route("/")
@login_required
def dashboard():

    c = get_db()

    total = c.execute(
        "SELECT COUNT(*) FROM students"
    ).fetchone()[0]

    today = datetime.now().strftime(
        "%Y-%m-%d"
    )

    present = c.execute(
        """
        SELECT COUNT(*)
        FROM attendance
        WHERE date=?
        AND status='Present'
        """,
        (today,)
    ).fetchone()[0]

    recent = c.execute("""
        SELECT
            a.date,
            a.time,
            a.status,
            s.register_no,
            s.name
        FROM attendance a
        JOIN students s
            ON a.student_id=s.id
        ORDER BY a.id DESC
        LIMIT 10
    """).fetchall()

    c.close()

    return render_template(
        "dashboard.html",
        total=total,
        present=present,
        absent=max(
            total - present,
            0
        ),
        percentage=round(
            present / total * 100,
            2
        ) if total else 0,
        recent=recent
    )


# ---------------- STUDENTS ----------------

@app.route("/students")
@login_required
def students():

    c = get_db()

    rows = c.execute(
        """
        SELECT *
        FROM students
        ORDER BY id DESC
        """
    ).fetchall()

    c.close()

    return render_template(
        "students.html",
        students=rows
    )


# ---------------- ADD STUDENT ----------------

@app.route(
    "/students/add",
    methods=["GET", "POST"]
)
@login_required
def add_student():

    if request.method == "POST":

        v = [
            request.form[
                "register_no"
            ].strip(),

            request.form[
                "name"
            ].strip(),

            request.form[
                "department"
            ].strip(),

            request.form[
                "year"
            ].strip()
        ]

        c = get_db()

        try:

            c.execute(
                """
                INSERT INTO students
                (register_no,name,department,year)
                VALUES(?,?,?,?)
                """,
                v
            )

            c.commit()

            flash(
                "Student added successfully."
            )

        except sqlite3.IntegrityError:

            flash(
                "Register number already exists."
            )

        c.close()

        return redirect(
            url_for("students")
        )

    return render_template(
        "add_student.html"
    )


# ---------------- EDIT STUDENT ----------------

@app.route(
    "/students/edit/<int:student_id>",
    methods=["GET", "POST"]
)
@login_required
def edit_student(student_id):

    c = get_db()

    student = c.execute(
        """
        SELECT *
        FROM students
        WHERE id=?
        """,
        (student_id,)
    ).fetchone()

    if student is None:

        c.close()

        flash(
            "Student not found."
        )

        return redirect(
            url_for("students")
        )

    if request.method == "POST":

        register_no = request.form[
            "register_no"
        ].strip()

        name = request.form[
            "name"
        ].strip()

        department = request.form[
            "department"
        ].strip()

        year = request.form[
            "year"
        ].strip()

        try:

            c.execute(
                """
                UPDATE students
                SET register_no=?,
                    name=?,
                    department=?,
                    year=?
                WHERE id=?
                """,
                (
                    register_no,
                    name,
                    department,
                    year,
                    student_id
                )
            )

            c.commit()

            flash(
                "Student details updated successfully."
            )

        except sqlite3.IntegrityError:

            flash(
                "Register number already exists."
            )

        c.close()

        return redirect(
            url_for("students")
        )

    c.close()

    return render_template(
        "edit_student.html",
        student=student
    )


# ---------------- DELETE STUDENT ----------------

@app.route(
    "/students/delete/<int:student_id>",
    methods=["POST"]
)
@login_required
def delete_student(student_id):

    c = get_db()

    student = c.execute(
        """
        SELECT register_no, name
        FROM students
        WHERE id=?
        """,
        (student_id,)
    ).fetchone()

    if student is None:

        c.close()

        flash(
            "Student not found."
        )

        return redirect(
            url_for("students")
        )

    c.execute(
        """
        DELETE FROM attendance
        WHERE student_id=?
        """,
        (student_id,)
    )

    c.execute(
        """
        DELETE FROM students
        WHERE id=?
        """,
        (student_id,)
    )

    c.commit()

    c.close()

    flash(
        f"Student {student['name']} "
        "deleted successfully."
    )

    return redirect(
        url_for("students")
    )


# ---------------- REGISTER FACE ----------------

@app.route(
    "/students/register-face/<int:student_id>"
)
@login_required
def register_face(student_id):

    c = get_db()

    student = c.execute(
        """
        SELECT *
        FROM students
        WHERE id=?
        """,
        (student_id,)
    ).fetchone()

    c.close()

    if student is None:

        flash(
            "Student not found."
        )

        return redirect(
            url_for("students")
        )

    script_path = os.path.join(
        os.path.dirname(
            os.path.abspath(__file__)
        ),
        "register_face.py"
    )

    if not os.path.exists(script_path):

        flash(
            "register_face.py was not found."
        )

        return redirect(
            url_for("students")
        )

    try:

        # Send register number to
        # register_face.py

        subprocess.Popen(
            [
                sys.executable,
                script_path,
                student["register_no"]
            ]
        )

        flash(
            f"Face registration started "
            f"for {student['name']}."
        )

    except Exception as e:

        flash(
            "Could not start face registration: "
            + str(e)
        )

    return redirect(
        url_for("students")
    )


# ---------------- ATTENDANCE ----------------

@app.route(
    "/attendance",
    methods=["GET", "POST"]
)
@login_required
def attendance():

    c = get_db()

    students = c.execute(
        """
        SELECT *
        FROM students
        ORDER BY name
        """
    ).fetchall()

    if request.method == "POST":

        sid = request.form[
            "student_id"
        ]

        d = datetime.now().strftime(
            "%Y-%m-%d"
        )

        t = datetime.now().strftime(
            "%H:%M:%S"
        )

        try:

            c.execute(
                """
                INSERT INTO attendance
                (student_id,date,time,status)
                VALUES(?,?,?,'Present')
                """,
                (
                    sid,
                    d,
                    t
                )
            )

            c.commit()

            flash(
                "Attendance marked successfully."
            )

        except sqlite3.IntegrityError:

            flash(
                "Attendance already marked "
                "for this student today."
            )

        c.close()

        return redirect(
            url_for("attendance")
        )

    c.close()

    return render_template(
        "attendance.html",
        students=students
    )


# ---------------- FACE ATTENDANCE ----------------

@app.route("/face-attendance")
@login_required
def face_attendance():

    # Check trained model

    if not os.path.exists(
        "trainer.yml"
    ):

        flash(
            "trainer.yml was not found. "
            "Please train the face model first."
        )

        return redirect(
            url_for("attendance")
        )


    # ---------------- DATABASE ----------------

    c = get_db()


    # ---------------- FACE RECOGNIZER ----------------

    recognizer = (
        cv2.face.LBPHFaceRecognizer_create()
    )

    recognizer.read(
        "trainer.yml"
    )


    # ---------------- FACE DETECTOR ----------------

    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades +
        "haarcascade_frontalface_default.xml"
    )


    # ---------------- CAMERA ----------------

    camera = cv2.VideoCapture(
        0,
        cv2.CAP_DSHOW
    )


    if not camera.isOpened():

        c.close()

        flash(
            "Could not open camera."
        )

        return redirect(
            url_for("attendance")
        )


    # Keep track of students
    # already processed in this session

    marked_students = set()


    msg = (
        "Look at camera. "
        "Press Q or Esc to stop."
    )


    # ---------------- CAMERA LOOP ----------------

    while True:

        success, frame = camera.read()


        if not success:

            msg = (
                "Could not read camera."
            )

            break


        gray = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2GRAY
        )


        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(80, 80)
        )


        # ---------------- PROCESS EVERY FACE ----------------

        for x, y, w, h in faces:

            face = gray[
                y:y+h,
                x:x+w
            ]


            # Predict face

            label, confidence = (
                recognizer.predict(face)
            )


            # Find student using
            # model label = student ID

            student = c.execute(
                """
                SELECT
                    id,
                    register_no,
                    name
                FROM students
                WHERE id=?
                """,
                (label,)
            ).fetchone()


            # ---------------- RECOGNIZED STUDENT ----------------

            if student and confidence < 70:

                student_id = student["id"]

                register_no = student["register_no"]

                name = student["name"]


                # Green rectangle

                cv2.rectangle(
                    frame,
                    (x, y),
                    (x+w, y+h),
                    (0, 255, 0),
                    2
                )


                # Student name

                cv2.putText(
                    frame,
                    name,
                    (x, y-35),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2
                )


                # Register number

                cv2.putText(
                    frame,
                    register_no,
                    (x, y-10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55,
                    (0, 255, 0),
                    2
                )


                # ---------------- MARK ATTENDANCE ----------------

                if student_id not in marked_students:

                    d = datetime.now().strftime(
                        "%Y-%m-%d"
                    )

                    t = datetime.now().strftime(
                        "%H:%M:%S"
                    )


                    try:

                        c.execute(
                            """
                            INSERT INTO attendance
                            (
                                student_id,
                                date,
                                time,
                                status
                            )
                            VALUES (
                                ?,
                                ?,
                                ?,
                                'Present'
                            )
                            """,
                            (
                                student_id,
                                d,
                                t
                            )
                        )


                        c.commit()


                        msg = (
                            f"Attendance marked "
                            f"for {name}."
                        )


                    except sqlite3.IntegrityError:

                        msg = (
                            f"{name} is already "
                            "marked present today."
                        )


                    marked_students.add(
                        student_id
                    )


            # ---------------- UNKNOWN FACE ----------------

            else:

                cv2.rectangle(
                    frame,
                    (x, y),
                    (x+w, y+h),
                    (0, 0, 255),
                    2
                )


                cv2.putText(
                    frame,
                    "Unknown Face",
                    (x, y-10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 0, 255),
                    2
                )


        # ---------------- DISPLAY CAMERA ----------------

        cv2.imshow(
            "Bio Tracker XR - AI Face Attendance",
            frame
        )


        key = cv2.waitKey(1) & 0xFF


        if key in (
            ord("q"),
            27
        ):

            break


    # ---------------- CLOSE CAMERA ----------------

    camera.release()

    cv2.destroyAllWindows()

    c.close()


    flash(msg)


    return redirect(
        url_for("dashboard")
    )


# ---------------- ATTENDANCE HISTORY ----------------

@app.route("/attendance-history")
@login_required
def attendance_history():

    c = get_db()

    rows = c.execute("""
        SELECT
            a.id,
            a.date,
            a.time,
            a.status,
            s.register_no,
            s.name,
            s.department,
            s.year
        FROM attendance a
        JOIN students s
            ON a.student_id = s.id
        ORDER BY a.date DESC, a.time DESC
    """).fetchall()

    c.close()

    return render_template(
        "attendance_history.html",
        rows=rows
    )


# ---------------- EXCEL EXPORT ----------------

@app.route("/export-attendance")
@login_required
def export_attendance():

    c = get_db()

    rows = c.execute("""
        SELECT
            a.date,
            a.time,
            s.register_no,
            s.name,
            s.department,
            s.year,
            a.status
        FROM attendance a
        JOIN students s
            ON a.student_id = s.id
        ORDER BY a.date DESC, a.time DESC
    """).fetchall()

    c.close()

    workbook = Workbook()

    sheet = workbook.active

    sheet.title = "Attendance History"

    headers = [
        "Date",
        "Time",
        "Register No",
        "Name",
        "Department",
        "Year",
        "Status"
    ]

    sheet.append(headers)

    for row in rows:

        sheet.append([
            row["date"],
            row["time"],
            row["register_no"],
            row["name"],
            row["department"],
            row["year"],
            row["status"]
        ])

    widths = {
        "A": 15,
        "B": 12,
        "C": 22,
        "D": 25,
        "E": 18,
        "F": 15,
        "G": 12
    }

    for column, width in widths.items():

        sheet.column_dimensions[
            column
        ].width = width

    output = BytesIO()

    workbook.save(output)

    output.seek(0)

    filename = (
        "BioTrackerXR_Attendance_"
        + datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )
        + ".xlsx"
    )

    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype=(
            "application/vnd.openxmlformats-"
            "officedocument.spreadsheetml.sheet"
        )
    )


# ---------------- REPORTS ----------------

@app.route("/reports")
@login_required
def reports():

    c = get_db()

    rows = c.execute("""
        SELECT
            s.register_no,
            s.name,
            s.department,
            s.year,

            SUM(
                CASE
                    WHEN a.status='Present'
                    THEN 1
                    ELSE 0
                END
            ) present_days,

            COUNT(a.id) recorded_days

        FROM students s

        LEFT JOIN attendance a
            ON s.id=a.student_id

        GROUP BY s.id

        ORDER BY s.name

    """).fetchall()

    c.close()

    data = []

    for r in rows:

        n = r["recorded_days"] or 0

        p = r["present_days"] or 0

        data.append(
            dict(
                r,
                percentage=round(
                    p / n * 100,
                    2
                ) if n else 0
            )
        )

    return render_template(
        "reports.html",
        rows=data
    )


# ---------------- START APPLICATION ----------------

if __name__ == "__main__":

    init_db()

    app.run(
        debug=True
    )