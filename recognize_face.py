import cv2
import sqlite3
from datetime import datetime


# --------------------------------
# DATABASE
# --------------------------------

conn = sqlite3.connect(
    "biotrackerxr.db"
)

cursor = conn.cursor()


# --------------------------------
# FACE RECOGNIZER
# --------------------------------

recognizer = (
    cv2.face.LBPHFaceRecognizer_create()
)

recognizer.read(
    "trainer.yml"
)


# --------------------------------
# FACE DETECTOR
# --------------------------------

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades +
    "haarcascade_frontalface_default.xml"
)


# --------------------------------
# CAMERA
# --------------------------------

camera = cv2.VideoCapture(
    0,
    cv2.CAP_DSHOW
)


if not camera.isOpened():

    print("Could not open camera.")

    conn.close()

    exit()


print()
print("--------------------------------")
print("Bio Tracker XR")
print("Multi-Student Face Attendance")
print("--------------------------------")
print()
print("Press Q or ESC to stop.")
print()


# Students already processed
marked_students = set()


# --------------------------------
# CAMERA LOOP
# --------------------------------

while True:

    success, frame = camera.read()


    if not success:

        print(
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


    for (x, y, w, h) in faces:

        face = gray[
            y:y+h,
            x:x+w
        ]


        # Predict student
        label, confidence = (
            recognizer.predict(face)
        )


        # --------------------------------
        # FIND STUDENT USING DATABASE ID
        # --------------------------------

        cursor.execute(
            """
            SELECT
                id,
                register_no,
                name
            FROM students
            WHERE id=?
            """,
            (label,)
        )


        student = cursor.fetchone()


        # --------------------------------
        # RECOGNIZED STUDENT
        # --------------------------------

        if student and confidence < 70:

            student_id = student[0]

            register_no = student[1]

            name = student[2]


            # Green rectangle

            cv2.rectangle(
                frame,
                (x, y),
                (x+w, y+h),
                (0, 255, 0),
                2
            )


            cv2.putText(
                frame,
                name,
                (x, y-35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2
            )


            cv2.putText(
                frame,
                register_no,
                (x, y-10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2
            )


            # --------------------------------
            # MARK ATTENDANCE
            # --------------------------------

            if student_id not in marked_students:

                today = datetime.now().strftime(
                    "%Y-%m-%d"
                )

                current_time = datetime.now().strftime(
                    "%H:%M:%S"
                )


                try:

                    cursor.execute(
                        """
                        INSERT INTO attendance
                        (
                            student_id,
                            date,
                            time,
                            status
                        )
                        VALUES (?, ?, ?, 'Present')
                        """,
                        (
                            student_id,
                            today,
                            current_time
                        )
                    )


                    conn.commit()


                    print(
                        "Attendance marked:",
                        name,
                        "-",
                        register_no
                    )


                except sqlite3.IntegrityError:

                    print(
                        "Already marked today:",
                        name
                    )


                marked_students.add(
                    student_id
                )


        # --------------------------------
        # UNKNOWN FACE
        # --------------------------------

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
                0.8,
                (0, 0, 255),
                2
            )


    # --------------------------------
    # DISPLAY CAMERA
    # --------------------------------

    cv2.imshow(
        "Bio Tracker XR - Multi Student Recognition",
        frame
    )


    key = cv2.waitKey(1) & 0xFF


    if key == ord("q") or key == 27:

        break


# --------------------------------
# CLOSE
# --------------------------------

camera.release()

conn.close()

cv2.destroyAllWindows()


print()
print(
    "Face recognition stopped."
)