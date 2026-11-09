import os
import re

import mysql.connector
import pandas as pd
from dotenv import load_dotenv


load_dotenv()

DB_HOST = os.getenv("MYSQL_HOST", "localhost")
DB_PORT = int(os.getenv("MYSQL_PORT", "3306"))
DB_USER = os.getenv("MYSQL_USER", "root")
DB_PASSWORD = os.getenv("MYSQL_PASSWORD", "root")
DB_NAME = os.getenv("MYSQL_DATABASE", "student_performance")


def _server_connection():
    return mysql.connector.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD)


def get_connection():
    return mysql.connector.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD, database=DB_NAME)


def initialize_database():
    if not re.fullmatch(r"[A-Za-z0-9_]+", DB_NAME):
        raise ValueError("MYSQL_DATABASE may contain only letters, numbers, and underscores.")

    connection = _server_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        connection.commit()
    finally:
        connection.close()

    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS students (
                student_id INT AUTO_INCREMENT PRIMARY KEY,
                roll_no VARCHAR(30) NOT NULL UNIQUE,
                name VARCHAR(120) NOT NULL,
                section VARCHAR(30) NOT NULL
            ) ENGINE=InnoDB"""
        )
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS subjects (
                subject_id INT AUTO_INCREMENT PRIMARY KEY,
                subject_name VARCHAR(120) NOT NULL UNIQUE,
                max_marks DECIMAL(7,2) NOT NULL,
                pass_marks DECIMAL(7,2) NOT NULL,
                CONSTRAINT chk_subject_marks CHECK (max_marks > 0 AND pass_marks >= 0 AND pass_marks <= max_marks)
            ) ENGINE=InnoDB"""
        )
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS marks (
                mark_id INT AUTO_INCREMENT PRIMARY KEY,
                student_id INT NOT NULL,
                subject_id INT NOT NULL,
                assessment VARCHAR(100) NOT NULL,
                marks_obtained DECIMAL(7,2) NOT NULL,
                CONSTRAINT fk_marks_student FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
                CONSTRAINT fk_marks_subject FOREIGN KEY (subject_id) REFERENCES subjects(subject_id) ON DELETE RESTRICT,
                CONSTRAINT chk_marks_nonnegative CHECK (marks_obtained >= 0),
                UNIQUE KEY uq_student_subject_assessment (student_id, subject_id, assessment)
            ) ENGINE=InnoDB"""
        )
        connection.commit()
    finally:
        connection.close()


def fetch_data(query, params=None):
    connection = get_connection()
    try:
        return pd.read_sql(query, connection, params=params)
    finally:
        connection.close()


def execute_query(query, params=None):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(query, params or ())
        connection.commit()
        return cursor.lastrowid
    finally:
        connection.close()