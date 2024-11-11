import os
import sqlite3
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QComboBox, QSpinBox, QDoubleSpinBox, QPushButton,
                               QTableWidget, QTableWidgetItem, QGroupBox,
                               QScrollArea, QMessageBox)
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
        type_group.setFixedHeight(60)
        type_layout = QVBoxLayout()
        type_layout.setAlignment(Qt.AlignTop)
        self.analysis_type = QComboBox()
        self.analysis_type.addItems(["GPA Impact of Future Courses", "Courses Needed for Target GPA"])
        self.analysis_type.currentIndexChanged.connect(self.on_analysis_type_changed)
        type_layout.addWidget(self.analysis_type)
        type_group.setLayout(type_layout)
        layout.addWidget(type_group)

        # Future Courses Input Section
        self.courses_group = QGroupBox("Future Courses")
        courses_layout = QVBoxLayout()

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        scroll_content = QWidget()
        self.courses_container = QVBoxLayout(scroll_content)
        self.courses_container.setAlignment(Qt.AlignTop)
        scroll_area.setWidget(scroll_content)
        courses_layout.addWidget(scroll_area)

        add_course_btn = QPushButton("Add Course")
        add_course_btn.clicked.connect(self.add_course_entry)
        courses_layout.addWidget(add_course_btn)

        self.courses_group.setLayout(courses_layout)
        layout.addWidget(self.courses_group)

        # Target GPA Input Section
        self.target_group = QGroupBox("Target GPA")
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
        results_layout = QVBoxLayout()
        results_group.setFixedHeight(80)
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

        credits_spin = QSpinBox()
        credits_spin.setRange(1, 4)
        credits_spin.setValue(3)
        course_layout.addWidget(QLabel("Credits:"))
        course_layout.addWidget(credits_spin)

        grade_combo = QComboBox()
        grade_combo.addItems(['A', 'B', 'C', 'D', 'F'])
        course_layout.addWidget(QLabel("Grade:"))
        course_layout.addWidget(grade_combo)

        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(lambda: self.remove_course_entry(course_widget))
        course_layout.addWidget(remove_btn)

        self.courses_container.addWidget(course_widget)
        self.course_list.append((credits_spin, grade_combo))

    def remove_course_entry(self, widget):
        widget.deleteLater()
        for i, (credits_spin, grade_combo) in enumerate(self.course_list):
            if credits_spin.parent() == widget:
                self.course_list.pop(i)
                break

    def on_analysis_type_changed(self, index):
        is_impact_analysis = index == 0
        self.courses_group.setVisible(is_impact_analysis)
        self.target_group.setVisible(not is_impact_analysis)

    def get_gpa_data(self, student_id):
        try:
            current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            db_path = os.path.join(current_dir, 'data', 'academic_management.db')

            if not os.path.exists(db_path):
                print(f"Database file not found at: {db_path}")
                return 0, 0, 0

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

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
            return 0, 0, 0
        finally:
            if conn:
                conn.close()

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

        points_needed = (target_gpa * total_credits) - total_points
        credits_needed = points_needed / (4 - target_gpa)  # Assuming all A's
        courses_needed = credits_needed / 3  # Assuming 3-credit courses

        return round(courses_needed, 1)

    def calculate_analysis(self):
        pass  # To be implemented by derived classes