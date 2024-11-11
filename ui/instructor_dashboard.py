import sys
import os
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QPushButton, QTableWidget, QTableWidgetItem,
                               QTabWidget, QComboBox, QMessageBox)
from PySide6.QtCore import Qt, Signal
import sqlite3
from datetime import datetime
from ui.common.system_logger import SystemLogger, UserRole, OperationType


class InstructorDashboard(QMainWindow):
    logout_signal = Signal()

    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.instructor_id = self.get_instructor_id()
        print(f"Initializing InstructorDashboard with user_id: {self.user_id}, instructor_id: {self.instructor_id}")
        self.setWindowTitle("Instructor Dashboard")
        self.setGeometry(100, 100, 800, 600)

        # Initialize the logger
        self.logger = SystemLogger(self.user_id, UserRole.INSTRUCTOR)

        self.setup_ui()

        # Log the login session
        self.logger.log_session(OperationType.LOGIN)

    def get_instructor_id(self):
        """Get the instructor_id from the database based on user_id"""
        try:
            conn = sqlite3.connect(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                '..', 'data', 'academic_management.db'))
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
        """Initialize the user interface"""
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

        # Add semester selector
        semester_layout = QHBoxLayout()
        semester_layout.addWidget(QLabel("Select Semester:"))
        self.semester_selector = QComboBox()
        semester_layout.addWidget(self.semester_selector)
        semester_layout.addStretch()
        assigned_courses_layout.addLayout(semester_layout)

        self.assigned_courses_table = QTableWidget()
        self.assigned_courses_table.setColumnCount(5)
        self.assigned_courses_table.setHorizontalHeaderLabels([
            "Course", "Credits", "Semester", "Year", "Enrolled Students"
        ])
        assigned_courses_layout.addWidget(self.assigned_courses_table)
        tab_widget.addTab(assigned_courses_tab, "Assigned Courses")

        # Student List Tab
        student_list_tab = QWidget()
        student_list_layout = QVBoxLayout(student_list_tab)

        # Course selection for student list
        course_selection_layout = QHBoxLayout()
        course_selection_layout.addWidget(QLabel("Select Course:"))
        self.course_selector = QComboBox()
        self.course_selector.currentIndexChanged.connect(self.load_student_list)
        course_selection_layout.addWidget(self.course_selector)
        course_selection_layout.addStretch()
        student_list_layout.addLayout(course_selection_layout)

        # Student list table
        self.student_list_table = QTableWidget()
        self.student_list_table.setColumnCount(5)
        self.student_list_table.setHorizontalHeaderLabels([
            "Student ID", "Gender", "Major", "Grade", "Status"
        ])
        student_list_layout.addWidget(self.student_list_table)
        tab_widget.addTab(student_list_tab, "Student List")

        # Connect tab change event
        tab_widget.currentChanged.connect(self.on_tab_changed)

        self.load_instructor_data()

    def load_instructor_data(self):
        """Load all instructor-related data"""
        if not self.instructor_id:
            print("No valid instructor_id, cannot load data.")
            return

        try:
            conn = sqlite3.connect(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                '..', 'data', 'academic_management.db'))
            cursor = conn.cursor()

            # Log the data access attempt
            self.logger.log_data_access(
                "instructor_courses",
                "view assigned courses",
                {"instructor_id": self.instructor_id}
            )

            # Load unique semesters for the semester selector
            cursor.execute("""
                SELECT DISTINCT semester, year_taught 
                FROM instructor_courses 
                WHERE instructor_id = ?
                ORDER BY year_taught DESC, 
                    CASE semester 
                        WHEN 'F' THEN 1
                        WHEN 'S' THEN 2
                        WHEN 'U' THEN 3
                    END DESC
            """, (self.instructor_id,))

            semesters = cursor.fetchall()
            self.semester_selector.clear()
            self.semester_selector.addItem("All Semesters", ("all", "all"))
            for semester, year in semesters:
                semester_name = {'F': 'Fall', 'S': 'Spring', 'U': 'Summer'}[semester]
                display_text = f"{semester_name} {year}"
                self.semester_selector.addItem(display_text, (semester, year))

            # Connect semester selector to update method
            self.semester_selector.currentIndexChanged.connect(self.update_course_table)

            # Load all courses for the student list tab
            self.load_all_courses_for_selector()

            # Initial load of course data for assigned courses tab
            self.update_course_table()

        except sqlite3.Error as e:
            error_msg = f"Database error while loading instructor data: {str(e)}"
            self.logger.log_operation(
                OperationType.ERROR,
                error_msg
            )
            print(error_msg)
            QMessageBox.critical(self, "Error", "Failed to load instructor data")
        finally:
            if conn:
                conn.close()

    def load_all_courses_for_selector(self):
        """Load all courses for the student list tab's course selector"""
        try:
            conn = sqlite3.connect(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                '..', 'data', 'academic_management.db'))
            cursor = conn.cursor()

            cursor.execute("""
                SELECT DISTINCT 
                    c.course_prefix || ' ' || c.course_number as course,
                    ic.semester,
                    ic.year_taught
                FROM instructor_courses ic
                JOIN courses c ON ic.course_prefix = c.course_prefix 
                    AND ic.course_number = c.course_number
                WHERE ic.instructor_id = ?
                ORDER BY ic.year_taught DESC, ic.semester DESC, course
            """, (self.instructor_id,))

            courses = cursor.fetchall()

            self.course_selector.clear()
            self.course_selector.addItem("Select Course", None)

            for course, semester, year in courses:
                semester_name = {'F': 'Fall', 'S': 'Spring', 'U': 'Summer'}[semester]
                display_text = f"{course} - {semester_name} {year}"
                course_parts = course.split()
                self.course_selector.addItem(display_text,
                                             (course_parts[0], course_parts[1], semester, year))

        except sqlite3.Error as e:
            error_msg = f"Database error while loading course selector: {str(e)}"
            self.logger.log_operation(
                OperationType.ERROR,
                error_msg
            )
            print(error_msg)
        finally:
            if conn:
                conn.close()

    def on_tab_changed(self, index):
        """Handle tab change events"""
        if index == 1:  # Student List tab
            self.load_all_courses_for_selector()

    def update_course_table(self):
        """Update the courses table based on selected semester"""
        selected_data = self.semester_selector.currentData()
        if not selected_data:
            return

        semester, year = selected_data

        try:
            conn = sqlite3.connect(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                '..', 'data', 'academic_management.db'))
            cursor = conn.cursor()

            # Build query based on semester selection
            query = """
                SELECT 
                    c.course_prefix || ' ' || c.course_number,
                    c.credits,
                    ic.semester,
                    ic.year_taught,
                    COUNT(DISTINCT sc.student_id) as enrolled_students
                FROM instructor_courses ic
                JOIN courses c ON ic.course_prefix = c.course_prefix 
                    AND ic.course_number = c.course_number
                LEFT JOIN student_courses sc ON c.course_prefix = sc.course_prefix 
                    AND c.course_number = sc.course_number
                    AND sc.semester = ic.semester 
                    AND sc.year_taken = ic.year_taught
                WHERE ic.instructor_id = ?
            """

            params = [self.instructor_id]

            if semester != "all":
                query += " AND ic.semester = ? AND ic.year_taught = ?"
                params.extend([semester, year])

            query += """
                GROUP BY c.course_prefix, c.course_number, ic.semester, ic.year_taught
                ORDER BY ic.year_taught DESC, ic.semester DESC
            """

            cursor.execute(query, params)
            courses = cursor.fetchall()

            # Update the course table
            self.assigned_courses_table.setRowCount(len(courses))
            for row, course in enumerate(courses):
                for col, value in enumerate(course):
                    if col == 2:  # Format semester
                        value = {'F': 'Fall', 'S': 'Spring', 'U': 'Summer'}[value]
                    self.assigned_courses_table.setItem(row, col, QTableWidgetItem(str(value)))

        except sqlite3.Error as e:
            error_msg = f"Database error while updating course table: {str(e)}"
            self.logger.log_operation(
                OperationType.ERROR,
                error_msg
            )
            print(error_msg)
            QMessageBox.critical(self, "Error", "Failed to update course information")
        finally:
            if conn:
                conn.close()

    def load_student_list(self):
        """Load student list for selected course"""
        selected_course = self.course_selector.currentData()
        if not selected_course:
            self.student_list_table.setRowCount(0)
            return

        prefix, number, semester, year = selected_course

        try:
            conn = sqlite3.connect(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                '..', 'data', 'academic_management.db'))
            cursor = conn.cursor()

            # Log the data access
            self.logger.log_data_access(
                "student_list",
                "viewed student list",
                {
                    "course": f"{prefix} {number}",
                    "semester": f"{semester} {year}"
                }
            )

            # Modified query to use DISTINCT and ensure we only get one record per student
            cursor.execute("""
                SELECT DISTINCT 
                    s.student_id,
                    s.gender,
                    s.major,
                    MAX(sc.grade) as grade,  -- Take the latest grade if there are duplicates
                    CASE 
                        WHEN MAX(sc.grade) IS NOT NULL THEN 'Completed'
                        ELSE 'In Progress'
                    END as status
                FROM student_courses sc
                JOIN students s ON sc.student_id = s.student_id
                WHERE sc.course_prefix = ? 
                    AND sc.course_number = ? 
                    AND sc.semester = ? 
                    AND sc.year_taken = ?
                GROUP BY s.student_id, s.gender, s.major  -- Group by student information
                ORDER BY s.student_id
            """, (prefix, number, semester, year))

            students = cursor.fetchall()
            self.student_list_table.setRowCount(len(students))

            for row, student in enumerate(students):
                for col, value in enumerate(student):
                    self.student_list_table.setItem(row, col, QTableWidgetItem(str(value or 'N/A')))

        except sqlite3.Error as e:
            error_msg = f"Database error while loading student list: {str(e)}"
            self.logger.log_operation(
                OperationType.ERROR,
                error_msg
            )
            print(error_msg)
            QMessageBox.critical(self, "Error", "Failed to load student list")
        finally:
            if conn:
                conn.close()

    def logout(self):
        """Handle instructor logout"""
        self.logger.log_session(OperationType.LOGOUT)
        self.logout_signal.emit()
        self.close()

    def closeEvent(self, event):
        """Override closeEvent to log when instructor exits the system"""
        self.logger.log_operation(
            "exit",
            "Instructor exited the system",
            include_role_prefix=False
        )
        event.accept()