import sys
import os
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QPushButton, QTableWidget, QTableWidgetItem, QTabWidget)
from PySide6.QtCore import Qt, Signal
import sqlite3

class StudentDashboard(QMainWindow):
    logout_signal = Signal()

    def __init__(self, student_id):
        super().__init__()
        self.student_id = student_id
        print(f"Initializing StudentDashboard with student_id: {self.student_id}")  # Debug print
        self.setWindowTitle("Student Dashboard")
        self.setGeometry(100, 100, 800, 600)
        self.setup_ui()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Header
        header_layout = QHBoxLayout()
        self.student_name_label = QLabel(f"Welcome, Student {self.student_id}")
        self.student_name_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(self.student_name_label)

        # Add a stretch to push the buttons to the right
        header_layout.addStretch()

        # Logout button
        self.logout_button = QPushButton("Logout")
        self.logout_button.clicked.connect(self.logout)
        header_layout.addWidget(self.logout_button)

        # Exit button
        self.exit_button = QPushButton("Exit")
        self.exit_button.clicked.connect(self.close)
        header_layout.addWidget(self.exit_button)

        main_layout.addLayout(header_layout)

        # Tabs
        tab_widget = QTabWidget()
        main_layout.addWidget(tab_widget)

        # Personal Info Tab
        personal_info_tab = QWidget()
        personal_info_layout = QVBoxLayout(personal_info_tab)
        self.personal_info_table = QTableWidget()
        personal_info_layout.addWidget(self.personal_info_table)
        tab_widget.addTab(personal_info_tab, "Personal Info")

        # Courses Tab
        courses_tab = QWidget()
        courses_layout = QVBoxLayout(courses_tab)
        self.courses_table = QTableWidget()
        courses_layout.addWidget(self.courses_table)
        tab_widget.addTab(courses_tab, "Courses")

        # GPA Tab
        gpa_tab = QWidget()
        gpa_layout = QVBoxLayout(gpa_tab)
        self.gpa_label = QLabel("Current GPA: ")
        gpa_layout.addWidget(self.gpa_label)
        tab_widget.addTab(gpa_tab, "GPA")

        # What-If Analysis Tab
        what_if_tab = QWidget()
        what_if_layout = QVBoxLayout(what_if_tab)
        what_if_label = QLabel("What-If Analysis")
        what_if_layout.addWidget(what_if_label)
        # TODO: Add input fields and buttons for what-if analysis
        tab_widget.addTab(what_if_tab, "What-If Analysis")

        self.load_student_data()

    def load_student_data(self):
        # Connect to the database
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'academic_management.db')
        print(f"Attempting to connect to database at: {db_path}")  # Debug print

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Load student info
            cursor.execute("""
                SELECT student_id, gender, major
                FROM students
                WHERE student_id = ?
            """, (self.student_id,))
            student_info = cursor.fetchone()
            print(
                f"Student info query: SELECT student_id, gender, major FROM students WHERE student_id = '{self.student_id}'")
            print(f"Student info result: {student_info}")  # Debug print

            if student_info:
                self.personal_info_table.setColumnCount(3)
                self.personal_info_table.setHorizontalHeaderLabels(["Student ID", "Gender", "Major"])
                self.personal_info_table.setRowCount(1)
                for i, value in enumerate(student_info):
                    self.personal_info_table.setItem(0, i, QTableWidgetItem(str(value)))
            else:
                print(f"No student info found for student_id: {self.student_id}")  # Debug print

            # Load courses
            cursor.execute("""
                SELECT c.course_prefix, c.course_number, c.credits, sc.semester, sc.year_taken, sc.grade
                FROM student_courses sc
                JOIN courses c ON sc.course_prefix = c.course_prefix AND sc.course_number = c.course_number
                WHERE sc.student_id = ?
            """, (self.student_id,))
            courses = cursor.fetchall()
            print(
                f"Courses query: SELECT c.course_prefix, c.course_number, c.credits, sc.semester, sc.year_taken, sc.grade FROM student_courses sc JOIN courses c ON sc.course_prefix = c.course_prefix AND sc.course_number = c.course_number WHERE sc.student_id = '{self.student_id}'")
            print(f"Courses result: {courses}")  # Debug print

            self.courses_table.setColumnCount(6)
            self.courses_table.setHorizontalHeaderLabels(["Prefix", "Number", "Credits", "Semester", "Year", "Grade"])
            self.courses_table.setRowCount(len(courses))
            for row, course in enumerate(courses):
                for col, value in enumerate(course):
                    self.courses_table.setItem(row, col, QTableWidgetItem(str(value)))

            # Calculate GPA
            total_points = 0
            total_credits = 0
            grade_points = {'A': 4, 'B': 3, 'C': 2, 'D': 1, 'F': 0}
            for course in courses:
                if course[5] in grade_points:
                    total_points += grade_points[course[5]] * course[2]
                    total_credits += course[2]
            gpa = total_points / total_credits if total_credits > 0 else 0
            self.gpa_label.setText(f"Current GPA: {gpa:.2f}")

        except sqlite3.Error as e:
            print(f"Database error: {e}")
        finally:
            if conn:
                conn.close()

    def logout(self):
        self.logout_signal.emit()
        self.close()