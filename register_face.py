import cv2
import os
import sys

# --------------------------------
# GET REGISTER NUMBER
# --------------------------------

if len(sys.argv) > 1:

    register_no = sys.argv[1].strip()

else:

    register_no = input(
        "Enter student Register Number: "
    ).strip()


# --------------------------------
# CREATE DATASET FOLDER
# --------------------------------

folder = os.path.join(
    "dataset",
    register_no
)

os.makedirs(
    folder,
    exist_ok=True
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

    sys.exit()


count = 0


print()
print("--------------------------------")
print("Bio Tracker XR")
print("Face Registration")
print("--------------------------------")
print()
print("Student Register Number:")
print(register_no)
print()
print("Look at the camera.")
print("Move your face slightly left and right.")
print("Collecting 30 samples...")
print("Press Q to stop.")
print()


# --------------------------------
# CAPTURE 30 SAMPLES
# --------------------------------

while count < 30:

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

        count += 1


        face = gray[
            y:y+h,
            x:x+w
        ]


        filename = os.path.join(
            folder,
            f"{count}.jpg"
        )


        cv2.imwrite(
            filename,
            face
        )


        cv2.rectangle(
            frame,
            (x, y),
            (x+w, y+h),
            (0, 255, 0),
            2
        )


        cv2.putText(
            frame,
            f"Samples: {count}/30",
            (x, y-10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2
        )


        if count >= 30:

            break


    cv2.imshow(
        "Bio Tracker XR - Face Registration",
        frame
    )


    key = cv2.waitKey(1) & 0xFF


    if key == ord("q") or key == 27:

        break


# --------------------------------
# CLOSE CAMERA
# --------------------------------

camera.release()

cv2.destroyAllWindows()


print()
print("--------------------------------")
print("Face registration completed.")
print("Student:", register_no)
print("Samples saved:", count)
print("Folder:", folder)
print("--------------------------------")