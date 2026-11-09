import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from analytics import build_section_summary, build_student_summary, build_subject_summary
from database import execute_query, fetch_data, initialize_database


st.set_page_config(page_title="Student Performance", page_icon="📚", layout="wide")

st.markdown(
    """
    <style>
    :root { --ink: #172b2b; --muted: #607675; --line: #d9e4df; --mint: #dcefe5; --coral: #ef795f; }
    .stApp { background: linear-gradient(135deg, #f6f8f1 0%, #eef5f0 48%, #f8f3eb 100%); color: var(--ink); }
    [data-testid="stSidebar"] { background: #193a38; }
    [data-testid="stSidebar"] * { color: #f6f8f1; }
    h1, h2, h3 { color: var(--ink); font-family: Georgia, 'Times New Roman', serif; }
    [data-testid="stMetric"] { background: rgba(255,255,255,.78); border: 1px solid var(--line); border-radius: 6px; padding: 14px 16px; }
    div[data-testid="stForm"] { background: rgba(255,255,255,.72); border: 1px solid var(--line); border-radius: 6px; padding: 18px; }
    .stButton button[kind="primary"] { background: #c95e49; border-color: #c95e49; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(ttl=5)
def load_students():
    return fetch_data("SELECT student_id, roll_no, name, section FROM students ORDER BY section, roll_no")


@st.cache_data(ttl=5)
def load_subjects():
    return fetch_data("SELECT subject_id, subject_name, max_marks, pass_marks FROM subjects ORDER BY subject_name")


@st.cache_data(ttl=5)
def load_marks():
    return fetch_data(
        """SELECT m.mark_id, m.student_id, s.roll_no, s.name, s.section,
                  m.subject_id, sub.subject_name, sub.max_marks, sub.pass_marks,
                  m.assessment, m.marks_obtained,
                  (m.marks_obtained >= sub.pass_marks) AS passed,
                  (m.marks_obtained / sub.max_marks * 100) AS percentage
           FROM marks m
           JOIN students s ON s.student_id = m.student_id
           JOIN subjects sub ON sub.subject_id = m.subject_id
           ORDER BY s.section, s.roll_no, sub.subject_name, m.assessment"""
    )


def refresh_data():
    load_students.clear()
    load_subjects.clear()
    load_marks.clear()


def show_database_error(error):
    st.error("Could not connect to MySQL. Check that the server is running and that `.env` has the correct connection settings.")
    with st.expander("Connection details"):
        st.code(str(error))
    st.stop()


try:
    initialize_database()
except Exception as exc:
    show_database_error(exc)

try:
    students = load_students()
    subjects = load_subjects()
    marks = load_marks()
except Exception as exc:
    show_database_error(exc)

st.sidebar.title("Student records")
st.sidebar.caption("Academic performance overview")
page = st.sidebar.radio("Workspace", ["Dashboard", "Students", "Subjects", "Marks", "Reports"], label_visibility="collapsed")
support_threshold = st.sidebar.number_input("Support threshold (%)", min_value=0, max_value=100, value=60, step=5)


def plot_bar(data, x, y, title, ylabel, color="#c95e49"):
    fig, ax = plt.subplots(figsize=(8, 3.5))
    ax.bar(data[x].astype(str), data[y], color=color, width=0.62)
    ax.set_title(title, loc="left", fontsize=14, color="#193a38", pad=14)
    ax.set_ylabel(ylabel, color="#607675")
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color("#d9e4df")
    ax.tick_params(axis="x", rotation=25, colors="#405c59")
    ax.tick_params(axis="y", colors="#607675")
    ax.grid(axis="y", alpha=0.2)
    fig.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)


if page == "Dashboard":
    st.title("Student performance")
    st.caption("A live view of recorded marks, outcomes, and areas needing attention.")
    student_summary = build_student_summary(marks)
    subject_summary = build_subject_summary(marks)
    section_summary = build_section_summary(student_summary)
    overall_average = float(student_summary["percentage"].mean()) if not student_summary.empty else 0
    overall_pass_rate = float(marks["passed"].mean() * 100) if not marks.empty else 0

    metric_cols = st.columns(4)
    metric_cols[0].metric("Students", len(students))
    metric_cols[1].metric("Mark records", len(marks))
    metric_cols[2].metric("Class average", f"{overall_average:.1f}%")
    metric_cols[3].metric("Pass rate", f"{overall_pass_rate:.1f}%")

    left, right = st.columns([1.3, 1])
    with left:
        if not subject_summary.empty:
            plot_bar(subject_summary, "subject_name", "average_percentage", "Average by subject", "Average (%)", "#367c70")
        else:
            st.info("Add marks to see subject averages.")
    with right:
        if not marks.empty:
            fig, ax = plt.subplots(figsize=(6, 3.5))
            ax.hist(marks["marks_obtained"], bins=10, color="#e59b58", edgecolor="white")
            ax.set_title("Marks distribution", loc="left", fontsize=14, color="#193a38", pad=14)
            ax.set_xlabel("Marks obtained")
            ax.set_ylabel("Assessments")
            ax.spines[["top", "right", "left"]].set_visible(False)
            ax.grid(axis="y", alpha=0.2)
            fig.tight_layout()
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)
        else:
            st.info("The marks distribution will appear when records are added.")

    st.subheader("Section overview")
    if section_summary.empty:
        st.info("Add student and mark records to build a section overview.")
    else:
        st.dataframe(section_summary, use_container_width=True, hide_index=True)

elif page == "Students":
    st.title("Students")
    with st.expander("Add student", expanded=students.empty):
        with st.form("add_student", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            roll_no = col1.text_input("Roll number")
            name = col2.text_input("Student name")
            section = col3.text_input("Section", placeholder="e.g. 10-A")
            submitted = st.form_submit_button("Add student", type="primary")
            if submitted:
                if not all(value.strip() for value in [roll_no, name, section]):
                    st.error("Enter a roll number, name, and section.")
                else:
                    try:
                        execute_query("INSERT INTO students (roll_no, name, section) VALUES (%s, %s, %s)", (roll_no.strip(), name.strip(), section.strip()))
                        refresh_data()
                        st.success("Student added.")
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Could not add student. Roll numbers must be unique. Details: {exc}")

    if students.empty:
        st.info("No student records yet.")
    else:
        st.dataframe(students.drop(columns="student_id"), use_container_width=True, hide_index=True)
        st.subheader("Update or remove a student")
        selected_student_id = st.selectbox(
            "Student", students["student_id"], format_func=lambda value: f"{students.loc[students.student_id == value, 'roll_no'].iloc[0]} · {students.loc[students.student_id == value, 'name'].iloc[0]}",
        )
        selected_student = students.loc[students.student_id == selected_student_id].iloc[0]
        with st.form("edit_student"):
            col1, col2, col3 = st.columns(3)
            edited_roll = col1.text_input("Roll number", value=selected_student.roll_no)
            edited_name = col2.text_input("Student name", value=selected_student["name"])
            edited_section = col3.text_input("Section", value=selected_student.section)
            save_col, delete_col = st.columns(2)
            save = save_col.form_submit_button("Save changes", type="primary")
            remove = delete_col.form_submit_button("Delete student")
            if save:
                try:
                    execute_query("UPDATE students SET roll_no = %s, name = %s, section = %s WHERE student_id = %s", (edited_roll.strip(), edited_name.strip(), edited_section.strip(), int(selected_student_id)))
                    refresh_data()
                    st.rerun()
                except Exception as exc:
                    st.error(f"Could not update student: {exc}")
            if remove:
                try:
                    execute_query("DELETE FROM students WHERE student_id = %s", (int(selected_student_id),))
                    refresh_data()
                    st.rerun()
                except Exception as exc:
                    st.error(f"Could not delete student: {exc}")

elif page == "Subjects":
    st.title("Subjects")
    with st.expander("Add subject", expanded=subjects.empty):
        with st.form("add_subject", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            subject_name = col1.text_input("Subject name")
            max_marks = col2.number_input("Maximum marks", min_value=1, value=100, step=1)
            pass_marks = col3.number_input("Pass marks", min_value=0, value=40, step=1)
            submitted = st.form_submit_button("Add subject", type="primary")
            if submitted:
                if not subject_name.strip() or pass_marks > max_marks:
                    st.error("Enter a subject name and make sure pass marks do not exceed maximum marks.")
                else:
                    try:
                        execute_query("INSERT INTO subjects (subject_name, max_marks, pass_marks) VALUES (%s, %s, %s)", (subject_name.strip(), int(max_marks), int(pass_marks)))
                        refresh_data()
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Could not add subject: {exc}")

    if subjects.empty:
        st.info("No subjects yet. Add a subject before entering marks.")
    else:
        st.dataframe(subjects.drop(columns="subject_id"), use_container_width=True, hide_index=True)
        st.subheader("Update or remove a subject")
        selected_subject_id = st.selectbox(
            "Subject", subjects["subject_id"], format_func=lambda value: subjects.loc[subjects.subject_id == value, "subject_name"].iloc[0],
        )
        selected_subject = subjects.loc[subjects.subject_id == selected_subject_id].iloc[0]
        with st.form("edit_subject"):
            col1, col2, col3 = st.columns(3)
            edited_subject_name = col1.text_input("Subject name", value=selected_subject.subject_name)
            edited_max_marks = col2.number_input("Maximum marks", min_value=1, value=int(selected_subject.max_marks), step=1)
            edited_pass_marks = col3.number_input("Pass marks", min_value=0, value=int(selected_subject.pass_marks), step=1)
            save = st.form_submit_button("Save subject", type="primary")
            if save:
                if edited_pass_marks > edited_max_marks:
                    st.error("Pass marks cannot exceed maximum marks.")
                else:
                    try:
                        execute_query("UPDATE subjects SET subject_name = %s, max_marks = %s, pass_marks = %s WHERE subject_id = %s", (edited_subject_name.strip(), int(edited_max_marks), int(edited_pass_marks), int(selected_subject_id)))
                        refresh_data()
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Could not update subject: {exc}")
        if st.button("Delete selected subject"):
            try:
                execute_query("DELETE FROM subjects WHERE subject_id = %s", (int(selected_subject_id),))
                refresh_data()
                st.rerun()
            except Exception as exc:
                st.error(f"Could not delete subject while it has mark records: {exc}")

elif page == "Marks":
    st.title("Assessment marks")
    if students.empty or subjects.empty:
        st.info("Add at least one student and one subject before recording marks.")
    else:
        with st.expander("Add assessment mark", expanded=marks.empty):
            with st.form("add_mark", clear_on_submit=True):
                col1, col2 = st.columns(2)
                student_id = col1.selectbox("Student", students.student_id, format_func=lambda value: f"{students.loc[students.student_id == value, 'roll_no'].iloc[0]} · {students.loc[students.student_id == value, 'name'].iloc[0]}")
                subject_id = col2.selectbox("Subject", subjects.subject_id, format_func=lambda value: subjects.loc[subjects.subject_id == value, "subject_name"].iloc[0])
                assessment = st.text_input("Assessment", placeholder="e.g. Midterm")
                subject_max = int(subjects.loc[subjects.subject_id == subject_id, "max_marks"].iloc[0])
                obtained = st.number_input("Marks obtained", min_value=0, max_value=subject_max, value=0, step=1)
                submitted = st.form_submit_button("Save mark", type="primary")
                if submitted:
                    if not assessment.strip():
                        st.error("Enter an assessment name.")
                    elif obtained < 0 or obtained > subject_max:
                        st.error(f"Marks must be between 0 and {subject_max} for this subject.")
                    else:
                        try:
                            execute_query("INSERT INTO marks (student_id, subject_id, assessment, marks_obtained) VALUES (%s, %s, %s, %s)", (int(student_id), int(subject_id), assessment.strip(), int(obtained)))
                            refresh_data()
                            st.rerun()
                        except Exception as exc:
                            st.error(f"Could not save this assessment. The same student, subject, and assessment name may already exist. Details: {exc}")

    if not marks.empty:
        st.dataframe(marks[["roll_no", "name", "section", "subject_name", "assessment", "marks_obtained", "max_marks", "passed"]], use_container_width=True, hide_index=True)
        st.subheader("Update or remove a mark")
        mark_ids = marks.mark_id.tolist()
        selected_mark_id = st.selectbox("Mark record", mark_ids, format_func=lambda value: f"{marks.loc[marks.mark_id == value, 'roll_no'].iloc[0]} · {marks.loc[marks.mark_id == value, 'subject_name'].iloc[0]} · {marks.loc[marks.mark_id == value, 'assessment'].iloc[0]}")
        selected_mark = marks.loc[marks.mark_id == selected_mark_id].iloc[0]
        with st.form("edit_mark"):
            col1, col2 = st.columns(2)
            edited_student = col1.selectbox("Student", students.student_id, index=students.student_id.tolist().index(int(selected_mark.student_id)), format_func=lambda value: f"{students.loc[students.student_id == value, 'roll_no'].iloc[0]} · {students.loc[students.student_id == value, 'name'].iloc[0]}")
            edited_subject = col2.selectbox("Subject", subjects.subject_id, index=subjects.subject_id.tolist().index(int(selected_mark.subject_id)), format_func=lambda value: subjects.loc[subjects.subject_id == value, "subject_name"].iloc[0])
            edited_assessment = st.text_input("Assessment", value=selected_mark.assessment)
            edited_max = int(subjects.loc[subjects.subject_id == edited_subject, "max_marks"].iloc[0])
            edited_marks = st.number_input("Marks obtained", min_value=0, max_value=edited_max, value=min(int(selected_mark.marks_obtained), edited_max), step=1)
            save, remove = st.columns(2)
            save_mark = save.form_submit_button("Save changes", type="primary")
            delete_mark = remove.form_submit_button("Delete mark")
            if save_mark:
                if not edited_assessment.strip():
                    st.error("Enter an assessment name.")
                elif edited_marks < 0 or edited_marks > edited_max:
                    st.error(f"Marks must be between 0 and {edited_max} for this subject.")
                else:
                    try:
                        execute_query("UPDATE marks SET student_id = %s, subject_id = %s, assessment = %s, marks_obtained = %s WHERE mark_id = %s", (int(edited_student), int(edited_subject), edited_assessment.strip(), int(edited_marks), int(selected_mark_id)))
                        refresh_data()
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Could not update this assessment. Check for duplicate student, subject, and assessment names. Details: {exc}")
            if delete_mark:
                try:
                    execute_query("DELETE FROM marks WHERE mark_id = %s", (int(selected_mark_id),))
                    refresh_data()
                    st.rerun()
                except Exception as exc:
                    st.error(f"Could not delete this assessment. Details: {exc}")

elif page == "Reports":
    st.title("Performance reports")
    st.caption("Grades use the configured academic rules. A student passes when every recorded assessment meets that subject's pass marks.")
    student_summary = build_student_summary(marks)
    subject_summary = build_subject_summary(marks)
    section_summary = build_section_summary(student_summary)
    if student_summary.empty:
        st.info("Record marks to generate performance reports.")
    else:
        st.subheader("Student performance report")
        report = student_summary.copy()
        report["support_needed"] = report["percentage"] < support_threshold
        st.dataframe(report, use_container_width=True, hide_index=True)
        st.download_button("Download report as CSV", report.to_csv(index=False), "student_performance_report.csv", "text/csv")

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Top performers")
            st.dataframe(student_summary.head(10), use_container_width=True, hide_index=True)
        with col2:
            st.subheader(f"Students below {support_threshold}%")
            support_list = student_summary[student_summary.percentage < support_threshold]
            if support_list.empty:
                st.success("No students are below the selected threshold.")
            else:
                st.dataframe(support_list, use_container_width=True, hide_index=True)

        if not subject_summary.empty:
            plot_bar(subject_summary, "subject_name", "pass_percentage", "Pass percentage by subject", "Pass rate (%)", "#367c70")
            st.subheader("Subject summary")
            st.dataframe(subject_summary, use_container_width=True, hide_index=True)
        st.subheader("Class / section summary")
        st.dataframe(section_summary, use_container_width=True, hide_index=True)