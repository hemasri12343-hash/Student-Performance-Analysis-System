# Student Performance Analysis System

A beginner-friendly Streamlit application for maintaining students, subjects, and assessment marks in MySQL. The dashboard analyzes persisted records with Pandas and NumPy and plots summaries with Matplotlib.

## Requirements

- Python 3.10 or newer
- MySQL Server running locally

## Setup

1. Create and activate a virtual environment:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

2. Install the dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env` and set your MySQL connection values. The provided defaults use `localhost`, user `root`, and password `root`.

4. Start the application:

   ```powershell
   python -m streamlit run app.py
   ```

The application creates the `student_performance` database and its tables the first time it connects. The MySQL user needs permission to create a database and tables.

## Features

- Create, view, update, and delete student and subject records.
- Create, view, update, and delete assessment marks.
- Reject marks outside `0` to the subject's maximum marks; subject pass marks must be between `0` and maximum marks.
- View overall, subject, and section summaries, a marks distribution, subject averages, and pass percentages.
- Export the student report as CSV and identify top performers and students below the configurable support threshold.

## Calculation rules

- A mark record passes when its marks are greater than or equal to that subject's pass marks.
- A student passes when every recorded assessment passes. Students with no marks do not appear in performance reports.
- Student percentage is total marks divided by the sum of maximum marks for recorded assessments, multiplied by 100. Average marks is the arithmetic mean of recorded marks.
- Grades are A (90% and above), B (80-89.99%), C (70-79.99%), D (60-69.99%), and F (below 60%).
- Subject pass percentage is the proportion of assessment records meeting the subject's pass marks. Section average is the mean of student percentages; section pass percentage is the proportion of reported students passing.

## Run calculation tests

```powershell
python -m unittest discover -s tests -v
```