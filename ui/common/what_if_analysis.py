import os
import sqlite3
from PySide6.QtWidgets import QMessageBox, QGroupBox, QVBoxLayout, QComboBox
from ui.common.what_if_analysis_base import WhatIfAnalysisBase
from PySide6.QtCore import Qt


class StudentWhatIfAnalysis(WhatIfAnalysisBase):
    def __init__(self, student_id):
        super().__init__()
        self.student_id = student_id
        self.load_student_data()

    def load_student_data(self):
        """Load the student's GPA data on initialization"""
        self.current_gpa, self.total_credits, self.total_points = self.get_gpa_data(self.student_id)

    def calculate_analysis(self):
        """Perform the what-if analysis based on selected type"""
        if self.analysis_type.currentIndex() == 0:  # GPA Impact
            new_gpa = self.calculate_gpa_impact(self.current_gpa, self.total_credits, self.total_points)
            self.results_label.setText(
                f"Current GPA: {self.current_gpa:.2f}\n"
                f"Projected GPA: {new_gpa:.2f}\n"
                f"With current total credits: {self.total_credits}"
            )
        else:  # Target GPA
            target_gpa = self.target_gpa_input.value()
            courses_needed = self.calculate_target_courses(
                self.current_gpa, self.total_credits, self.total_points, target_gpa
            )
            if courses_needed:
                self.results_label.setText(
                    f"Current GPA: {self.current_gpa:.2f}\n"
                    f"To reach target GPA of {target_gpa:.2f}, "
                    f"you need approximately {courses_needed} courses with A grades\n"
                    f"(Assuming 3-credit courses)"
                )
            else:
                self.results_label.setText(
                    "Target GPA must be higher than current GPA and not exceed 4.0"
                )


class AdvisorWhatIfAnalysis(WhatIfAnalysisBase):
    def __init__(self, advisor_id):
        super().__init__()
        self.advisor_id = advisor_id
        self.setup_student_selector()

    def setup_student_selector(self):
        # Add student selector at the top
        student_group = QGroupBox("Select Student")
        student_group.setFixedHeight(60)
        student_layout = QVBoxLayout()
        student_layout.setAlignment(Qt.AlignTop)
        self.student_selector = QComboBox()
        self.load_advisor_students()
        student_layout.addWidget(self.student_selector)
        student_group.setLayout(student_layout)
        self.layout().insertWidget(0, student_group)

        # Connect student change to update current GPA
        self.student_selector.currentIndexChanged.connect(self.on_student_changed)

        # Initialize with the first student if available
        if self.student_selector.count() > 0:
            self.on_student_changed(0)
        else:
            self.current_gpa = 0.0
            self.total_credits = 0
            self.total_points = 0

    def on_student_changed(self, index):
        """Update GPA data when student selection changes"""
        if index >= 0:
            student_id = self.student_selector.currentData()
            if student_id:
                self.current_gpa, self.total_credits, self.total_points = self.get_gpa_data(student_id)
            else:
                self.current_gpa = 0.0
                self.total_credits = 0
                self.total_points = 0

    def load_advisor_students(self):
        """Load all students assigned to this advisor through their departments"""
        try:
            # Get the absolute path to the database file
            current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            db_path = os.path.join(current_dir, 'data', 'academic_management.db')

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Query to get students based on advisor's departments and student majors
            cursor.execute("""
                SELECT DISTINCT s.student_id, s.major
                FROM students s
                JOIN department_majors dm ON s.major = dm.major_name
                JOIN advisor_departments ad ON dm.department_id = ad.department_id
                WHERE ad.advisor_id = ?
                ORDER BY s.student_id
            """, (self.advisor_id,))

            students = cursor.fetchall()

            # Clear existing items
            self.student_selector.clear()

            # Add a default "Select Student" option
            self.student_selector.addItem("Select Student", None)

            # Add students to the combo box
            for student_id, major in students:
                display_text = f"{student_id} - {major}"
                self.student_selector.addItem(display_text, student_id)

        except sqlite3.Error as e:
            print(f"Database error while loading advisor students: {e}")
            print(f"Using database path: {db_path}")
        except Exception as e:
            print(f"Unexpected error while loading advisor students: {e}")
        finally:
            if conn:
                conn.close()

    def calculate_analysis(self):
        if self.student_selector.currentData() is None:
            self.results_label.setText("Please select a student first")
            return

        if not hasattr(self, 'current_gpa'):
            # Reload student data if attributes are missing
            self.on_student_changed(self.student_selector.currentIndex())

        if self.analysis_type.currentIndex() == 0:  # GPA Impact
            new_gpa = self.calculate_gpa_impact(self.current_gpa, self.total_credits, self.total_points)
            self.results_label.setText(
                f"Student: {self.student_selector.currentText()}\n"
                f"Current GPA: {self.current_gpa:.2f}\n"
                f"Projected GPA: {new_gpa:.2f}\n"
                f"With current total credits: {self.total_credits}"
            )
        else:  # Target GPA
            target_gpa = self.target_gpa_input.value()
            courses_needed = self.calculate_target_courses(
                self.current_gpa, self.total_credits, self.total_points, target_gpa
            )
            if courses_needed:
                self.results_label.setText(
                    f"Student: {self.student_selector.currentText()}\n"
                    f"Current GPA: {self.current_gpa:.2f}\n"
                    f"To reach target GPA of {target_gpa:.2f}, "
                    f"student needs approximately {courses_needed} courses with A grades\n"
                    f"(Assuming 3-credit courses)"
                )
            else:
                self.results_label.setText(
                    "Target GPA must be higher than current GPA and not exceed 4.0"
                )