import cv2
import os
import sqlite3
import numpy as np


# --------------------------------
# PATHS
# --------------------------------

dataset_path = "dataset"
model_path = "trainer.yml"
database_path = "biotrackerxr.db"


# --------------------------------
# DATABASE
# --------------------------------

def get_student_id(register_no):

    connection = sqlite3.connect(
        database_path
    )

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id
        FROM students
        WHERE register_no=?
        """,
        (register_no,)
    )

    result = cursor.fetchone()

    connection.close()

    if result:
        return result[0]

    return None


# --------------------------------
# FACE RECOGNIZER
# --------------------------------

recognizer = (
    cv2.face.LBPHFaceRecognizer_create()
)


faces = []
labels = []


# --------------------------------
# CHECK DATASET
# --------------------------------

if not os.path.exists(dataset_path):

    print("Dataset folder not found.")

    exit()


# --------------------------------
# GET STUDENT FOLDERS
# --------------------------------

student_folders = os.listdir(
    dataset_path
)


# --------------------------------
# READ FACE SAMPLES
# --------------------------------

for register_no in student_folders:

    folder = os.path.join(
        dataset_path,
        register_no
    )


    if not os.path.isdir(folder):

        continue


    # Get student ID from database

    student_id = get_student_id(
        register_no
    )


    if student_id is None:

        print(
            "Skipping:",
            register_no,
            "- student not found in database."
        )

        continue


    print(
        "Training:",
        register_no,
        "-> Student ID:",
        student_id
    )


    # Read images

    for filename in os.listdir(folder):

        if not filename.lower().endswith(
            ".jpg"
        ):

            continue


        image_path = os.path.join(
            folder,
            filename
        )


        image = cv2.imread(
            image_path,
            cv2.IMREAD_GRAYSCALE
        )


        if image is not None:

            faces.append(image)

            labels.append(
                student_id
            )


# --------------------------------
# CHECK SAMPLES
# --------------------------------

print()

print(
    "Total face samples:",
    len(faces)
)

print(
    "Total labels:",
    len(labels)
)

print()


if len(faces) == 0:

    print(
        "No face samples found."
    )

    exit()


# --------------------------------
# TRAIN MODEL
# --------------------------------

print(
    "Training face model..."
)


recognizer.train(
    faces,
    np.array(labels)
)


# --------------------------------
# SAVE MODEL
# --------------------------------

recognizer.write(
    model_path
)


print()

print(
    "Training completed successfully!"
)

print(
    "Model saved as:",
    model_path
)