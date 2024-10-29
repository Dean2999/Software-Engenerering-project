import sys
import os
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
                               QTableWidgetItem, QTabWidget, QSizePolicy, QSpacerItem)
from PySide6.QtCore import Qt, Signal
import sqlite3
from datetime import datetime


class StudentDashboard(QMainWindow):
    logout_signal = Signal()

    def __init__(self, student_id):
        super().__init__()
        self.student_id = student_id
        print(f"Initializing StudentDashboard with student_id: {self.student_id}")
        self.setWindowTitle("Student Dashboard")
        self.setGeometry(100, 100, 800, 600)
        self.setup_ui()

    def get_current_semester(self):
        current_date = datetime.now()
        month = current_date.month
        day = current_date.day

        if 1 <= month <= 5 and day <= 15:
            return 'Spring', current_date.year
        elif (month == 5 and day > 15) or (month <= 8 and (month != 8 or day <= 15)):
            return 'Summer', current_date.year
        else:
            return 'Fall', current_date.year

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Header
        header_layout = QHBoxLayout()
        self.student_name_label = QLabel(f"Welcome, Student {self.student_id}")
        self.student_name_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(self.student_name_label)

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

        # Current Courses Tab
        courses_tab = QWidget()
        courses_layout = QVBoxLayout(courses_tab)
        courses_layout.setContentsMargins(10, 10, 10, 10)  # Add some padding around the edges

        # Add semester info label with left alignment
        current_semester, current_year = self.get_current_semester()
        self.semester_label = QLabel(f"Current Semester: {current_semester} {current_year}")
        self.semester_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.semester_label.setAlignment(Qt.AlignLeft)  # Align to the left
        courses_layout.addWidget(self.semester_label)

        # Add some vertical spacing
        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Fixed)
        courses_layout.addItem(spacer)

        # Add no courses message with white text and proper spacing
        self.no_courses_label = QLabel("Student Currently Not Enrolled in classes for this term")
        self.no_courses_label.setStyleSheet("font-size: 14px; color: white; margin: 10px 0;")
        self.no_courses_label.setAlignment(Qt.AlignTop | Qt.AlignCenter)  # Center alignment
        self.no_courses_label.hide()
        courses_layout.addWidget(self.no_courses_label)

        # Add some vertical spacing
        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Fixed)
        courses_layout.addItem(spacer)

        # Add courses table
        self.courses_table = QTableWidget()
        courses_layout.addWidget(self.courses_table)

        tab_widget.addTab(courses_tab, "Courses")

        # Add some vertical spacing
        spacer = QSpacerItem(20, 400, QSizePolicy.Minimum, QSizePolicy.Fixed)
        courses_layout.addItem(spacer)

        # In setup_ui method:

        # GPA Tab
        gpa_tab = QWidget()
        gpa_layout = QVBoxLayout(gpa_tab)

        # Header section
        header_layout = QHBoxLayout()
        self.gpa_label = QLabel()
        self.gpa_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        header_layout.addWidget(self.gpa_label)
        header_layout.addStretch()
        gpa_layout.addLayout(header_layout)

        # Add some vertical spacing
        spacer = QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed)
        gpa_layout.addItem(spacer)

        # Transcript table
        self.transcript_table = QTableWidget()
        gpa_layout.addWidget(self.transcript_table)

        tab_widget.addTab(gpa_tab, "GPA")

        # What-If Analysis Tab
        what_if_tab = QWidget()
        what_if_layout = QVBoxLayout(what_if_tab)
        what_if_label = QLabel("What-If Analysis")
        what_if_layout.addWidget(what_if_label)
        tab_widget.addTab(what_if_tab, "What-If Analysis")

        self.load_student_data()

    def load_transcript_data(self):
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'academic_management.db')
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Get all semesters for this student, ordered by oldest first
            cursor.execute("""
                SELECT DISTINCT semester, year_taken
                FROM student_courses
                WHERE student_id = ?
                ORDER BY year_taken ASC, 
                    CASE semester 
                        WHEN 'S' THEN 1
                        WHEN 'U' THEN 2
                        WHEN 'F' THEN 3
                    END
            """, (self.student_id,))

            semesters = cursor.fetchall()

            # First, calculate all GPAs chronologically
            semester_data = []
            cumulative_points = 0
            cumulative_credits = 0

            for semester, year in semesters:
                # Get courses for this semester
                cursor.execute("""
                    SELECT c.course_prefix, c.course_number, c.credits, sc.grade
                    FROM student_courses sc
                    JOIN courses c ON sc.course_prefix = c.course_prefix 
                        AND sc.course_number = c.course_number
                    WHERE sc.student_id = ? AND sc.semester = ? AND sc.year_taken = ?
                    ORDER BY c.course_prefix, c.course_number
                """, (self.student_id, semester, year))

                courses = cursor.fetchall()

                # Calculate semester GPA
                semester_points = 0
                semester_credits = 0
                semester_courses = []

                for course in courses:
                    prefix, number, credits, grade = course
                    semester_courses.append({
                        'prefix': prefix,
                        'number': number,
                        'credits': credits,
                        'grade': grade
                    })

                    if grade in ['A', 'B', 'C', 'D', 'F']:
                        grade_points = {'A': 4, 'B': 3, 'C': 2, 'D': 1, 'F': 0}[grade]
                        points = grade_points * credits
                        semester_points += points
                        semester_credits += credits

                if semester_credits > 0:
                    semester_gpa = semester_points / semester_credits
                    cumulative_points += semester_points
                    cumulative_credits += semester_credits
                    cumulative_gpa = cumulative_points / cumulative_credits
                else:
                    semester_gpa = 0.0
                    cumulative_gpa = cumulative_points / cumulative_credits if cumulative_credits > 0 else 0.0

                semester_data.append({
                    'term': {'F': 'Fall', 'S': 'Spring', 'U': 'Summer'}[semester],
                    'year': year,
                    'courses': semester_courses,
                    'semester_credits': semester_credits,
                    'semester_gpa': semester_gpa,
                    'cumulative_gpa': cumulative_gpa
                })

            # Now reverse the order for display (newest first)
            semester_data.reverse()

            # Set up the table
            all_rows = []

            for sem_data in semester_data:
                # Add semester header

                all_rows.append([f"{sem_data['term']} {sem_data['year']}", '', '', '', ''])

                # Add courses
                for course in sem_data['courses']:
                    all_rows.append([
                        f"{course['prefix']} {course['number']}",
                        str(course['credits']),
                        course['grade'],
                        '',
                        ''
                    ])

                # Add semester summary
                all_rows.append(['', '', '', '', ''])  # Empty row for spacing
                all_rows.append(['Semester Credits:', str(sem_data['semester_credits']), '', '', ''])
                all_rows.append(['Semester GPA:', f"{sem_data['semester_gpa']:.2f}", '', '', ''])
                all_rows.append(['Cumulative GPA:', f"{sem_data['cumulative_gpa']:.2f}", '', '', ''])
                all_rows.append(['', '', '', '', ''])  # Empty row for spacing

            # Set up and populate the table
            self.transcript_table.setColumnCount(3)
            self.transcript_table.setHorizontalHeaderLabels(
                ["Course", "Credits", "Grade"])
            self.transcript_table.setRowCount(len(all_rows))

            for row_idx, row_data in enumerate(all_rows):
                for col_idx, value in enumerate(row_data):
                    item = QTableWidgetItem(value)
                    if any(sem['term'] in value and str(sem['year']) in value for sem in semester_data):
                        font = item.font()
                        font.setBold(True)
                        item.setFont(font)
                    self.transcript_table.setItem(row_idx, col_idx, item)

            # Adjust column widths
            self.transcript_table.resizeColumnsToContents()

            # When creating table items in the loop, add alignment for the Credits column
            # When creating table items in the loop, add alignment for the Credits column
            for row_idx, row_data in enumerate(all_rows):
                for col_idx, value in enumerate(row_data):
                    item = QTableWidgetItem(value)
                    if any(sem['term'] in value and str(sem['year']) in value for sem in semester_data):
                        font = item.font()
                        font.setBold(True)
                        item.setFont(font)

                    # Center align the Credits column (column index 1)
                    if col_idx == 1 or col_idx == 2 and value.strip():  # If it's the credits column and not empty
                        item.setTextAlignment(Qt.AlignCenter)

                    self.transcript_table.setItem(row_idx, col_idx, item)

        except sqlite3.Error as e:
            print(f"Database error: {e}")
        finally:
            if conn:
                conn.close()

    def load_student_data(self):
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'academic_management.db')
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

            if student_info:
                self.personal_info_table.setColumnCount(3)
                self.personal_info_table.setHorizontalHeaderLabels(["Student ID", "Gender", "Major"])
                self.personal_info_table.setRowCount(1)
                for i, value in enumerate(student_info):
                    self.personal_info_table.setItem(0, i, QTableWidgetItem(str(value)))

            # Get current semester info
            current_semester, current_year = self.get_current_semester()

            # Load current semester courses
            cursor.execute("""
                SELECT c.course_prefix, c.course_number, c.credits, sc.grade
                FROM student_courses sc
                JOIN courses c ON sc.course_prefix = c.course_prefix AND sc.course_number = c.course_number
                WHERE sc.student_id = ? AND sc.semester = ? AND sc.year_taken = ?
            """, (self.student_id, current_semester[0], current_year))  # Using first letter of semester

            current_courses = cursor.fetchall()

            if current_courses:
                self.courses_table.show()
                self.no_courses_label.hide()

                self.courses_table.setColumnCount(4)
                self.courses_table.setHorizontalHeaderLabels(["Course Prefix", "Course Number", "Credits", "Grade"])
                self.courses_table.setRowCount(len(current_courses))

                for row, course in enumerate(current_courses):
                    for col, value in enumerate(course):
                        if col == 3:  # Grade column
                            grade = str(value) if value else "-"
                            self.courses_table.setItem(row, col, QTableWidgetItem(grade))
                        else:
                            self.courses_table.setItem(row, col, QTableWidgetItem(str(value)))
            else:
                self.courses_table.hide()
                self.no_courses_label.show()

            # Calculate overall GPA (for the GPA tab)
            cursor.execute("""
                SELECT c.credits, sc.grade
                FROM student_courses sc
                JOIN courses c ON sc.course_prefix = c.course_prefix AND sc.course_number = c.course_number
                WHERE sc.student_id = ? AND sc.grade IS NOT NULL
            """, (self.student_id,))

            all_courses = cursor.fetchall()

            total_points = 0
            total_credits = 0
            grade_points = {'A': 4, 'B': 3, 'C': 2, 'D': 1, 'F': 0}

            for course in all_courses:
                credits, grade = course
                if grade in grade_points:
                    total_points += grade_points[grade] * credits
                    total_credits += credits

            gpa = total_points / total_credits if total_credits > 0 else 0
            self.gpa_label.setText(f"Current GPA: {gpa:.2f}")

            self.load_transcript_data()

        except sqlite3.Error as e:
            print(f"Database error: {e}")
        finally:
            if conn:
                conn.close()

    def logout(self):
        self.logout_signal.emit()
        self.close()