import numpy as np
import pandas as pd


def grade_for_percentage(percentage):
    if percentage >= 90:
        return "A"
    if percentage >= 80:
        return "B"
    if percentage >= 70:
        return "C"
    if percentage >= 60:
        return "D"
    return "F"


def build_student_summary(marks):
    columns = ["student_id", "roll_no", "name", "section", "total_marks", "average_marks", "percentage", "grade", "status"]
    if marks.empty:
        return pd.DataFrame(columns=columns)

    summary = marks.groupby(["student_id", "roll_no", "name", "section"], as_index=False).agg(
        total_marks=("marks_obtained", "sum"),
        average_marks=("marks_obtained", "mean"),
        total_possible=("max_marks", "sum"),
        passed=("passed", "all"),
    )
    summary["percentage"] = np.where(summary.total_possible > 0, summary.total_marks / summary.total_possible * 100, 0)
    summary["grade"] = summary.percentage.map(grade_for_percentage)
    summary["status"] = np.where(summary.passed, "Pass", "Fail")
    summary = summary.drop(columns=["total_possible", "passed"])
    summary["total_marks"] = summary.total_marks.round(2)
    summary["average_marks"] = summary.average_marks.round(2)
    summary["percentage"] = summary.percentage.round(2)
    return summary.sort_values(["percentage", "total_marks"], ascending=False).reset_index(drop=True)


def build_subject_summary(marks):
    columns = ["subject_name", "assessment_count", "average_marks", "average_percentage", "pass_count", "pass_percentage", "minimum", "maximum", "median"]
    if marks.empty:
        return pd.DataFrame(columns=columns)

    summary = marks.groupby("subject_name").agg(
        assessment_count=("marks_obtained", "size"),
        average_marks=("marks_obtained", "mean"),
        average_percentage=("percentage", "mean"),
        pass_count=("passed", "sum"),
        minimum=("marks_obtained", "min"),
        maximum=("marks_obtained", "max"),
        median=("marks_obtained", "median"),
    ).reset_index()
    summary["pass_percentage"] = summary.pass_count / summary.assessment_count * 100
    numeric_columns = ["average_marks", "average_percentage", "pass_percentage", "minimum", "maximum", "median"]
    summary[numeric_columns] = summary[numeric_columns].round(2)
    return summary.sort_values("subject_name").reset_index(drop=True)


def build_section_summary(student_summary):
    columns = ["section", "students", "average_percentage", "pass_percentage"]
    if student_summary.empty:
        return pd.DataFrame(columns=columns)

    summary = student_summary.groupby("section").agg(
        students=("student_id", "nunique"),
        average_percentage=("percentage", "mean"),
        pass_percentage=("status", lambda values: (values == "Pass").mean() * 100),
    ).reset_index()
    summary[["average_percentage", "pass_percentage"]] = summary[["average_percentage", "pass_percentage"]].round(2)
    return summary.sort_values("section").reset_index(drop=True)