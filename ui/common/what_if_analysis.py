import os
import sqlite3
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QComboBox, QSpinBox, QDoubleSpinBox, QPushButton,
                               QTableWidget, QTableWidgetItem, QGroupBox,
                               QScrollArea)
from PySide6.QtCore import Qt


class WhatIfAnalysisBase(QWidget):
    def __init__(self):
        super().__init__()
        self.course_list = []
        self.current_gpa = 0.0
        self.total_credits = 0
        self.total_points = 0
        self.setup_base_ui()

    def setup_base_ui(self):
        layout = QVBoxLayout(self)

        # Analysis Type Selection
        type_group = QGroupBox("Analysis Type")
        type_group.setMaximumHeight(60)
        type_layout = QVBoxLayout()
        type_layout.setAlignment(Qt.AlignTop)
        self.analysis_type = QComboBox()
        self.analysis_type.addItems(["GPA Impact of Future Courses", "Courses Needed for Target GPA"])
        self.analysis_type.currentIndexChanged.connect(self.on_analysis_type_changed)
        type_layout.addWidget(self.analysis_type)
        type_group.setLayout(type_layout)
        layout.addWidget(type_group)

        # Future Courses Input Section with Scroll Area
        self.courses_group = QGroupBox("Future Courses")
        self.courses_group.setMaximumHeight(200)
        courses_layout = QVBoxLayout()

        # Create a scroll area and a widget to contain course entries
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        scroll_content = QWidget()
        self.courses_container = QVBoxLayout(scroll_content)
        self.courses_container.setAlignment(Qt.AlignTop)

        # Set a fixed height for 6 courses (approximately 50 pixels per course)
        scroll_area.setMaximumHeight(150)  # 6 courses * 50 pixels
        scroll_area.setWidget(scroll_content)

        courses_layout.addWidget(scroll_area)

        # Add Course Button
        add_course_btn = QPushButton("Add Course")
        add_course_btn.clicked.connect(self.add_course_entry)
        courses_layout.addWidget(add_course_btn)

        self.courses_group.setLayout(courses_layout)
        layout.addWidget(self.courses_group)

        # Target GPA Input Section
        self.target_group = QGroupBox("Target GPA")
        self.target_group.setMaximumHeight(200)
        target_layout = QVBoxLayout()
        self.target_gpa_input = QDoubleSpinBox()
        self.target_gpa_input.setRange(0, 4.0)
        self.target_gpa_input.setDecimals(2)
        self.target_gpa_input.setSingleStep(0.01)
        target_layout.addWidget(self.target_gpa_input)
        self.target_group.setLayout(target_layout)
        layout.addWidget(self.target_group)

        # Calculate Button
        self.calculate_btn = QPushButton("Calculate")
        self.calculate_btn.clicked.connect(self.calculate_analysis)
        layout.addWidget(self.calculate_btn)

        # Results Section
        results_group = QGroupBox("Analysis Results")
        results_group.setMaximumHeight(80)
        results_layout = QVBoxLayout()
        self.results_label = QLabel()
        self.results_label.setWordWrap(True)
        results_layout.addWidget(self.results_label)
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)

        # Initial state
        self.on_analysis_type_changed(0)

    def add_course_entry(self):
        course_widget = QWidget()
        course_layout = QHBoxLayout(course_widget)
        course_layout.setContentsMargins(0, 0, 0, 0)

        # Credits input
        credits_spin = QSpinBox()
        credits_spin.setRange(1, 4)
        credits_spin.setValue(3)
        course_layout.addWidget(QLabel("Credits:"))
        course_layout.addWidget(credits_spin)

        # Grade selection
        grade_combo = QComboBox()
        grade_combo.addItems(['A', 'B', 'C', 'D', 'F'])
        course_layout.addWidget(QLabel("Grade:"))
        course_layout.addWidget(grade_combo)

        # Remove button
        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(lambda: self.remove_course_entry(course_widget))
        course_layout.addWidget(remove_btn)

        self.courses_container.addWidget(course_widget)
        self.course_list.append((credits_spin, grade_combo))


    def remove_course_entry(self, widget):
        widget.deleteLater()
        # Find and remove the corresponding entries from course_list
        for i, (credits_spin, grade_combo) in enumerate(self.course_list):
            if credits_spin.parent() == widget:
                self.course_list.pop(i)
                break

    def on_analysis_type_changed(self, index):
        is_impact_analysis = index == 0
        self.courses_group.setVisible(is_impact_analysis)
        self.target_group.setVisible(not is_impact_analysis)

    def get_gpa_data(self, student_id):
        conn = None  # Initialize conn to None
        try:
            # Get the absolute path to the database file
            current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            db_path = os.path.join(current_dir, 'data', 'academic_management.db')

            # Verify database file exists
            if not os.path.exists(db_path):
                print(f"Database file not found at: {db_path}")
                return 0, 0, 0

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Get completed courses and calculate GPA
            cursor.execute("""
                SELECT c.credits, sc.grade
                FROM student_courses sc
                JOIN courses c ON sc.course_prefix = c.course_prefix 
                    AND sc.course_number = c.course_number
                WHERE sc.student_id = ? AND sc.grade IS NOT NULL
            """, (student_id,))

            courses = cursor.fetchall()
            total_points = 0
            total_credits = 0
            grade_points = {'A': 4, 'B': 3, 'C': 2, 'D': 1, 'F': 0}

            for credits, grade in courses:
                if grade in grade_points:
                    total_points += grade_points[grade] * credits
                    total_credits += credits

            current_gpa = total_points / total_credits if total_credits > 0 else 0

            return current_gpa, total_credits, total_points

        except sqlite3.Error as e:
            print(f"Database error in get_gpa_data: {e}")
            print(f"Using database path: {db_path}")
            return 0, 0, 0
        except Exception as e:
            print(f"Unexpected error in get_gpa_data: {e}")
            return 0, 0, 0
        finally:
            if conn:
                try:
                    conn.close()
                except Exception as e:
                    print(f"Error closing database connection: {e}")

    def calculate_gpa_impact(self, current_gpa, total_credits, total_points):
        additional_points = 0
        additional_credits = 0
        grade_points = {'A': 4, 'B': 3, 'C': 2, 'D': 1, 'F': 0}

        for credits_spin, grade_combo in self.course_list:
            credits = credits_spin.value()
            grade = grade_combo.currentText()
            points = grade_points[grade] * credits
            additional_points += points
            additional_credits += credits

        if additional_credits == 0:
            return current_gpa

        new_gpa = (total_points + additional_points) / (total_credits + additional_credits)
        return new_gpa

    def calculate_target_courses(self, current_gpa, total_credits, total_points, target_gpa):
        if target_gpa <= current_gpa or target_gpa > 4.0:
            return None

        # Calculate points needed to reach target GPA
        points_needed = (target_gpa * total_credits) - total_points
        credits_needed = points_needed / (4 - target_gpa)  # Assuming all A's
        courses_needed = credits_needed / 3  # Assuming 3-credit courses

        return round(courses_needed, 1)

    def calculate_analysis(self):
        # This method should be implemented by derived classes
        pass


class StudentWhatIfAnalysis(WhatIfAnalysisBase):
    def __init__(self, student_id):
        super().__init__()
        self.student_id = student_id
        self.load_student_data()

    class StudentWhatIfAnalysis(WhatIfAnalysisBase):
        def __init__(self, student_id):
            super().__init__()
            self.student_id = student_id
            self.load_student_data()

        def load_student_data(self):
            """Load the student's GPA data on initialization"""
            self.current_gpa, self.total_credits, self.total_points = self.get_gpa_data(self.student_id)

        def calculate_analysis(self):
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
        student_group.setMaximumHeight(60)
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