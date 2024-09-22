import sys
import os
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QPushButton, QTableWidget, QTableWidgetItem,
                               QTabWidget, QComboBox, QMessageBox, QLineEdit)
from PySide6.QtCore import Qt, Signal
import sqlite3


class AdvisorDashboard(QMainWindow):
    logout_signal = Signal()

    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.advisor_id = self.get_advisor_id()
        print(f"Initializing AdvisorDashboard with user_id: {self.user_id}, advisor_id: {self.advisor_id}")
        self.setWindowTitle("Advisor Dashboard")
        self.setGeometry(100, 100, 800, 600)
        self.setup_ui()

    def get_advisor_id(self):
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'academic_management.db')
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT advisor_id FROM advisors WHERE user_id = ?", (self.user_id,))
            result = cursor.fetchone()
            if result:
                return result[0]
            else:
                print(f"No advisor found for user_id: {self.user_id}")
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
        self.advisor_name_label = QLabel(f"Welcome, Advisor {self.advisor_id}")
        self.advisor_name_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(self.advisor_name_label)

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

        # Advisees Tab
        advisees_tab = QWidget()
        advisees_layout = QVBoxLayout(advisees_tab)
        self.advisees_table = QTableWidget()
        advisees_layout.addWidget(self.advisees_table)
        tab_widget.addTab(advisees_tab, "Advisees")

        # Course Registration Tab
        course_reg_tab = QWidget()
        course_reg_layout = QVBoxLayout(course_reg_tab)
        self.student_selector = QComboBox()
        course_reg_layout.addWidget(QLabel("Select Student:"))
        course_reg_layout.addWidget(self.student_selector)
        self.course_selector = QComboBox()
        course_reg_layout.addWidget(QLabel("Select Course:"))
        course_reg_layout.addWidget(self.course_selector)
        self.register_button = QPushButton("Register Student for Course")
        self.register_button.clicked.connect(self.register_student_for_course)
        course_reg_layout.addWidget(self.register_button)
        self.drop_button = QPushButton("Drop Student from Course")
        self.drop_button.clicked.connect(self.drop_student_from_course)
        course_reg_layout.addWidget(self.drop_button)
        tab_widget.addTab(course_reg_tab, "Course Registration")

        # What-If Analysis Tab
        what_if_tab = QWidget()
        what_if_layout = QVBoxLayout(what_if_tab)
        self.what_if_student_selector = QComboBox()
        what_if_layout.addWidget(QLabel("Select Student:"))
        what_if_layout.addWidget(self.what_if_student_selector)
        self.scenario_selector = QComboBox()
        self.scenario_selector.addItems(["GPA Impact", "GPA Goal"])
        what_if_layout.addWidget(QLabel("Select Scenario:"))
        what_if_layout.addWidget(self.scenario_selector)
        self.input_field = QLineEdit()
        what_if_layout.addWidget(QLabel("Input:"))
        what_if_layout.addWidget(self.input_field)
        self.analyze_button = QPushButton("Perform What-If Analysis")
        self.analyze_button.clicked.connect(self.perform_what_if_analysis)
        what_if_layout.addWidget(self.analyze_button)
        self.analysis_result = QLabel()
        what_if_layout.addWidget(self.analysis_result)
        tab_widget.addTab(what_if_tab, "What-If Analysis")

        self.load_advisor_data()

    def load_advisor_data(self):
        if not self.advisor_id:
            print("No valid advisor_id, cannot load data.")
            return

        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'academic_management.db')
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Load advisees
            cursor.execute("""
                SELECT s.student_id, s.gender, s.major
                FROM students s
                JOIN department_majors dm ON s.major = dm.major_name
                JOIN advisor_departments ad ON dm.department_id = ad.department_id
                WHERE ad.advisor_id = ?
            """, (self.advisor_id,))
            advisees = cursor.fetchall()

            self.advisees_table.setColumnCount(3)
            self.advisees_table.setHorizontalHeaderLabels(["Student ID", "Gender", "Major"])
            self.advisees_table.setRowCount(len(advisees))
            for row, advisee in enumerate(advisees):
                for col, value in enumerate(advisee):
                    self.advisees_table.setItem(row, col, QTableWidgetItem(str(value)))

            # Populate student selectors
            self.student_selector.clear()
            self.what_if_student_selector.clear()
            for advisee in advisees:
                self.student_selector.addItem(f"{advisee[0]} - {advisee[2]}", advisee[0])
                self.what_if_student_selector.addItem(f"{advisee[0]} - {advisee[2]}", advisee[0])

            # Load courses
            cursor.execute("""
                SELECT DISTINCT c.course_prefix, c.course_number, c.credits
                FROM courses c
                JOIN department_majors dm ON c.course_prefix = dm.major_name
                JOIN advisor_departments ad ON dm.department_id = ad.department_id
                WHERE ad.advisor_id = ?
            """, (self.advisor_id,))
            courses = cursor.fetchall()

            self.course_selector.clear()
            for course in courses:
                self.course_selector.addItem(f"{course[0]} {course[1]} - {course[2]} credits", (course[0], course[1]))

        except sqlite3.Error as e:
            print(f"Database error: {e}")
        finally:
            if conn:
                conn.close()

    def register_student_for_course(self):
        student_id = self.student_selector.currentData()
        course = self.course_selector.currentData()
        if not student_id or not course:
            return

        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'academic_management.db')
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Check if the student is already registered for the course
            cursor.execute("""
                SELECT * FROM student_courses
                WHERE student_id = ? AND course_prefix = ? AND course_number = ?
            """, (student_id, course[0], course[1]))
            if cursor.fetchone():
                QMessageBox.warning(self, "Registration Failed", "Student is already registered for this course.")
                return

            # Register the student for the course
            cursor.execute("""
                INSERT INTO student_courses (student_id, course_prefix, course_number, semester, year_taken)
                VALUES (?, ?, ?, ?, ?)
            """, (student_id, course[0], course[1], 'F', 2023))  # Assuming Fall 2023 for this example
            conn.commit()
            QMessageBox.information(self, "Registration Successful", "Student has been registered for the course.")

        except sqlite3.Error as e:
            print(f"Database error: {e}")
            QMessageBox.critical(self, "Registration Error", "An error occurred while registering the student.")
        finally:
            if conn:
                conn.close()

    def drop_student_from_course(self):
        student_id = self.student_selector.currentData()
        course = self.course_selector.currentData()
        if not student_id or not course:
            return

        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'academic_management.db')
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Check if the student is registered for the course
            cursor.execute("""
                DELETE FROM student_courses
                WHERE student_id = ? AND course_prefix = ? AND course_number = ?
            """, (student_id, course[0], course[1]))

            if cursor.rowcount > 0:
                conn.commit()
                QMessageBox.information(self, "Drop Successful", "Student has been dropped from the course.")
            else:
                QMessageBox.warning(self, "Drop Failed", "Student is not registered for this course.")

        except sqlite3.Error as e:
            print(f"Database error: {e}")
            QMessageBox.critical(self, "Drop Error", "An error occurred while dropping the student from the course.")
        finally:
            if conn:
                conn.close()

    def perform_what_if_analysis(self):
        student_id = self.what_if_student_selector.currentData()
        scenario = self.scenario_selector.currentText()
        input_value = self.input_field.text()

        if not student_id or not input_value:
            QMessageBox.warning(self, "Invalid Input", "Please select a student and provide input.")
            return

        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'academic_management.db')
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Get current GPA and total credits
            cursor.execute("""
                SELECT SUM(CASE
                    WHEN sc.grade = 'A' THEN 4 * c.credits
                    WHEN sc.grade = 'B' THEN 3 * c.credits
                    WHEN sc.grade = 'C' THEN 2 * c.credits
                    WHEN sc.grade = 'D' THEN 1 * c.credits
                    ELSE 0
                END) as total_points,
                SUM(c.credits) as total_credits
                FROM student_courses sc
                JOIN courses c ON sc.course_prefix = c.course_prefix AND sc.course_number = c.course_number
                WHERE sc.student_id = ? AND sc.grade IN ('A', 'B', 'C', 'D', 'F')
            """, (student_id,))
            result = cursor.fetchone()

            if result and result[1] > 0:
                current_gpa = result[0] / result[1]
                total_credits = result[1]
            else:
                current_gpa = 0
                total_credits = 0

            if scenario == "GPA Impact":
                try:
                    new_courses = int(input_value)
                    new_credits = new_courses * 3  # Assuming 3 credits per course
                    new_points = new_credits * 4  # Assuming all A's
                    new_gpa = (result[0] + new_points) / (total_credits + new_credits)
                    self.analysis_result.setText(
                        f"Current GPA: {current_gpa:.2f}\nProjected GPA after {new_courses} courses with all A's: {new_gpa:.2f}")
                except ValueError:
                    QMessageBox.warning(self, "Invalid Input", "Please enter a valid number of courses.")

            elif scenario == "GPA Goal":
                try:
                    target_gpa = float(input_value)
                    if target_gpa < current_gpa or target_gpa > 4.0:
                        raise ValueError

                    additional_points_needed = (target_gpa * total_credits) - result[0]
                    additional_credits_needed = additional_points_needed / (4 - target_gpa)
                    courses_needed = additional_credits_needed / 3  # Assuming 3 credits per course

                    self.analysis_result.setText(f"Current GPA: {current_gpa:.2f}\nTo reach a GPA of {target_gpa:.2f}, "
                                                 f"you need approximately {courses_needed:.1f} courses with all A's.")
                except ValueError:
                    QMessageBox.warning(self, "Invalid Input",
                                        "Please enter a valid target GPA between your current GPA and 4.0.")

        except sqlite3.Error as e:
            print(f"Database error: {e}")
            QMessageBox.critical(self, "Analysis Error", "An error occurred while performing the analysis.")
        finally:
            if conn:
                conn.close()

    def logout(self):
        self.logout_signal.emit()
        self.close()