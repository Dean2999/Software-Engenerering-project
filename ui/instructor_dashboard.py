import sys
import os
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QPushButton, QTableWidget, QTableWidgetItem,
                               QTabWidget, QComboBox, QMessageBox)
from PySide6.QtCore import Qt, Signal
import sqlite3

class InstructorDashboard(QMainWindow):
    logout_signal = Signal()

    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.instructor_id = self.get_instructor_id()
        print(f"Initializing InstructorDashboard with user_id: {self.user_id}, instructor_id: {self.instructor_id}")
        self.setWindowTitle("Instructor Dashboard")
        self.setGeometry(100, 100, 800, 600)
        self.setup_ui()

    def get_instructor_id(self):
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'academic_management.db')
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT instructor_id FROM instructors WHERE user_id = ?", (self.user_id,))
            result = cursor.fetchone()
            if result:
                return result[0]
            else:
                print(f"No instructor found for user_id: {self.user_id}")
                return None
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Header
        header_layout = QHBoxLayout()
        self.instructor_name_label = QLabel(f"Welcome, Instructor {self.instructor_id}")
        self.instructor_name_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(self.instructor_name_label)

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

        # Assigned Courses Tab
        assigned_courses_tab = QWidget()
        assigned_courses_layout = QVBoxLayout(assigned_courses_tab)
        self.assigned_courses_table = QTableWidget()
        assigned_courses_layout.addWidget(self.assigned_courses_table)
        tab_widget.addTab(assigned_courses_tab, "Assigned Courses")

        # Student List Tab
        student_list_tab = QWidget()
        student_list_layout = QVBoxLayout(student_list_tab)
        self.course_selector = QComboBox()
        self.course_selector.currentIndexChanged.connect(self.load_student_list)
        student_list_layout.addWidget(self.course_selector)
        self.student_list_table = QTableWidget()
        student_list_layout.addWidget(self.student_list_table)
        tab_widget.addTab(student_list_tab, "Student List")

        # Update Course Info Tab
        update_course_tab = QWidget()
        update_course_layout = QVBoxLayout(update_course_tab)
        self.update_course_selector = QComboBox()
        update_course_layout.addWidget(self.update_course_selector)
        self.update_course_table = QTableWidget()
        update_course_layout.addWidget(self.update_course_table)
        self.update_course_button = QPushButton("Update Course Info")
        self.update_course_button.clicked.connect(self.update_course_info)
        update_course_layout.addWidget(self.update_course_button)
        tab_widget.addTab(update_course_tab, "Update Course Info")

        self.load_instructor_data()

    def load_instructor_data(self):
        if not self.instructor_id:
            print("No valid instructor_id, cannot load data.")
            return

        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'academic_management.db')
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Load assigned courses
            cursor.execute("""
                SELECT c.course_prefix, c.course_number, c.credits, ic.semester, ic.year_taught
                FROM instructor_courses ic
                JOIN courses c ON ic.course_prefix = c.course_prefix AND ic.course_number = c.course_number
                WHERE ic.instructor_id = ?
                ORDER BY ic.year_taught DESC, ic.semester DESC
            """, (self.instructor_id,))
            courses = cursor.fetchall()

            print(f"Fetched {len(courses)} courses for instructor {self.instructor_id}")  # Debug print

            self.assigned_courses_table.setColumnCount(5)
            self.assigned_courses_table.setHorizontalHeaderLabels(["Prefix", "Number", "Credits", "Semester", "Year"])
            self.assigned_courses_table.setRowCount(len(courses))
            for row, course in enumerate(courses):
                for col, value in enumerate(course):
                    self.assigned_courses_table.setItem(row, col, QTableWidgetItem(str(value)))

            # Populate course selectors
            self.course_selector.clear()
            self.update_course_selector.clear()
            for course in courses:
                course_str = f"{course[0]} {course[1]} - {course[3]} {course[4]}"
                self.course_selector.addItem(course_str, (course[0], course[1], course[3], course[4]))
                self.update_course_selector.addItem(course_str, (course[0], course[1], course[3], course[4]))

        except sqlite3.Error as e:
            print(f"Database error: {e}")
        finally:
            if conn:
                conn.close()

    def load_student_list(self):
        selected_course = self.course_selector.currentData()
        if not selected_course:
            return

        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'academic_management.db')
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT s.student_id, s.gender, s.major, sc.grade
                FROM student_courses sc
                JOIN students s ON sc.student_id = s.student_id
                WHERE sc.course_prefix = ? AND sc.course_number = ? AND sc.semester = ? AND sc.year_taken = ?
            """, selected_course)
            students = cursor.fetchall()

            self.student_list_table.setColumnCount(4)
            self.student_list_table.setHorizontalHeaderLabels(["Student ID", "Gender", "Major", "Grade"])
            self.student_list_table.setRowCount(len(students))
            for row, student in enumerate(students):
                for col, value in enumerate(student):
                    self.student_list_table.setItem(row, col, QTableWidgetItem(str(value)))

        except sqlite3.Error as e:
            print(f"Database error: {e}")
        finally:
            if conn:
                conn.close()

    def update_course_info(self):
        selected_course = self.update_course_selector.currentData()
        if not selected_course:
            return

        # In a real application, you would implement the logic to update course information here
        # For this example, we'll just show a message box
        QMessageBox.information(self, "Update Course Info", "Course information updated successfully!")

    def logout(self):
        self.logout_signal.emit()
        self.close()