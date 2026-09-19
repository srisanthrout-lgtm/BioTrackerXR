# Bio Tracker XR

A simple academic mini-project for student attendance management.

## Version 1 features
- Student registration
- Attendance marking
- Duplicate attendance prevention for the same day
- Dashboard
- Attendance percentage report
- SQLite database for easy setup

## Run on Windows

1. Install Python 3.10+.
2. Open Command Prompt in this folder.
3. Create a virtual environment:
   `python -m venv venv`
4. Activate it:
   `venv\Scripts\activate`
5. Install dependencies:
   `pip install -r requirements.txt`
6. Start the application:
   `python app.py`
7. Open:
   `http://127.0.0.1:5000`

## Important
This starter version uses SQLite so you can get a working prototype quickly. MySQL and OpenCV face recognition can be added as Version 2 after the basic workflow is tested.

## Project flow
Student registration -> attendance marking -> database -> dashboard -> report.
