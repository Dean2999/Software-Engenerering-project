import os
import sqlite3
from datetime import datetime
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QComboBox, QMessageBox, QFormLayout,
                              QLineEdit, QSpinBox, QTabWidget, QWidget)
from PySide6.QtCore import Qt, Signal


class CourseManagementDialog(QDialog):
    course_scheduled = Signal()  # Signal to emit when a course is scheduled

    def __init__(self, parent=None, initial_semester=None):
        super().__init__(parent)
        self.parent = parent
        self.initial_semester = initial_semester
        self.setWindowTitle("Schedule Course")
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Create main layout for scheduling
        schedule_layout = QFormLayout()

        # Course selection
        self.course_combo = QComboBox()
        self.load_course_catalogue()
        schedule_layout.addRow("Select Course:", self.course_combo)

        # Semester selection
        self.semester_combo = QComboBox()
        current_sem, future_sems = self.get_available_semesters()
        for sem, year in future_sems:
            semester_name = {'F': 'Fall', 'S': 'Spring', 'U': 'Summer'}[sem]
            self.semester_combo.addItem(f"{semester_name} {year}", (sem, year))
        schedule_layout.addRow("Semester:", self.semester_combo)

        # Instructor selection (optional)
        self.instructor_combo = QComboBox()
        self.load_department_instructors()
        self.instructor_combo.addItem("TBA", None)
        schedule_layout.addRow("Instructor:", self.instructor_combo)

        # Schedule button
        button_layout = QHBoxLayout()
        schedule_button = QPushButton("Schedule Course")
        schedule_button.clicked.connect(self.schedule_course)
        button_layout.addWidget(schedule_button)

        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        button_layout.addWidget(close_button)

        # Add layouts to main layout
        layout.addLayout(schedule_layout)
        layout.addLayout(button_layout)

        # If initial semester was provided, set it in the combo box
        if self.initial_semester:
            index = self.semester_combo.findData(self.initial_semester)
            if index >= 0:
                self.semester_combo.setCurrentIndex(index)

    def load_course_catalogue(self):
        """Load existing courses from the catalogue"""
        try:
            conn = sqlite3.connect(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                '..', 'data', 'academic_management.db'))
            cursor = conn.cursor()

            # Modified query to use department_course_prefixes table
            cursor.execute("""
                SELECT DISTINCT c.course_prefix, c.course_number, c.credits
                FROM courses c
                JOIN department_course_prefixes dcp ON c.course_prefix = dcp.course_prefix
                WHERE dcp.department_id = ?
                ORDER BY c.course_prefix, c.course_number
            """, (self.parent.department_id,))

            courses = cursor.fetchall()
            self.course_combo.clear()
            for course in courses:
                self.course_combo.addItem(
                    f"{course[0]} {course[1]} ({course[2]} credits)",
                    (course[0], course[1], course[2])
                )

            # Log the data access
            self.parent.logger.log_data_access(
                "courses",
                "retrieved department courses for scheduling",
                {
                    "department_id": self.parent.department_id,
                    "courses_found": len(courses)
                }
            )

        except sqlite3.Error as e:
            self.parent.logger.log_operation(
                "error",
                f"Failed to load course catalogue: {str(e)}"
            )
            QMessageBox.warning(self, "Error", "Failed to load course catalogue")
        finally:
            if conn:
                conn.close()

    def load_department_instructors(self):
        """Load instructors from the department"""
        try:
            conn = sqlite3.connect(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                '..', 'data', 'academic_management.db'))
            cursor = conn.cursor()

            cursor.execute("""
                SELECT instructor_id
                FROM instructors
                WHERE department_id = ?
                ORDER BY instructor_id
            """, (self.parent.department_id,))

            instructors = cursor.fetchall()
            for instructor in instructors:
                self.instructor_combo.addItem(str(instructor[0]), instructor[0])

            # Log the data access
            self.parent.logger.log_data_access(
                "instructors",
                "retrieved department instructors for scheduling",
                {
                    "department_id": self.parent.department_id,
                    "instructors_found": len(instructors)
                }
            )

        except sqlite3.Error as e:
            self.parent.logger.log_operation(
                "error",
                f"Failed to load instructors: {str(e)}"
            )
            QMessageBox.warning(self, "Error", "Failed to load instructors")
        finally:
            if conn:
                conn.close()

    def get_available_semesters(self):
        """Get current and future semesters"""
        current_date = datetime.now()
        current_year = current_date.year
        current_month = current_date.month

        if 1 <= current_month <= 5:
            current_sem = ('S', current_year)
            future_sems = [
                ('S', current_year),
                ('U', current_year),
                ('F', current_year)
            ]
        elif 6 <= current_month <= 8:
            current_sem = ('U', current_year)
            future_sems = [
                ('U', current_year),
                ('F', current_year),
                ('S', current_year + 1)
            ]
        else:
            current_sem = ('F', current_year)
            future_sems = [
                ('F', current_year),
                ('S', current_year + 1)
            ]

        return current_sem, future_sems

    def schedule_course(self):
        """Schedule an existing course for a semester"""
        course_data = self.course_combo.currentData()
        if not course_data:
            QMessageBox.warning(self, "Error", "Please select a course")
            return

        semester_data = self.semester_combo.currentData()
        if not semester_data:
            QMessageBox.warning(self, "Error", "Please select a semester")
            return

        prefix, number, credits = course_data
        semester, year = semester_data
        instructor_id = self.instructor_combo.currentData()

        try:
            conn = sqlite3.connect(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                '..', 'data', 'academic_management.db'))
            cursor = conn.cursor()

            # Check if course is already scheduled for this semester
            cursor.execute("""
                SELECT COUNT(*) FROM instructor_courses
                WHERE course_prefix = ? AND course_number = ?
                AND semester = ? AND year_taught = ?
            """, (prefix, number, semester, year))

            if cursor.fetchone()[0] > 0:
                self.parent.logger.log_operation(
                    "error",
                    "Attempted to schedule duplicate course",
                    {
                        "course": f"{prefix} {number}",
                        "semester": f"{semester} {year}"
                    }
                )
                QMessageBox.warning(self, "Error",
                                    "This course is already scheduled for the selected semester")
                return

            # If instructor is selected, verify their credit load
            if instructor_id:
                cursor.execute("""
                    SELECT SUM(c.credits)
                    FROM instructor_courses ic
                    JOIN courses c ON ic.course_prefix = c.course_prefix 
                        AND ic.course_number = c.course_number
                    WHERE ic.instructor_id = ? 
                    AND ic.semester = ? AND ic.year_taught = ?
                """, (instructor_id, semester, year))

                current_credits = cursor.fetchone()[0] or 0
                if current_credits + credits > 12:
                    self.parent.logger.log_operation(
                        "error",
                        "Instructor credit hour limit exceeded",
                        {
                            "instructor_id": instructor_id,
                            "current_credits": current_credits,
                            "attempted_add": credits
                        }
                    )
                    QMessageBox.warning(self, "Error",
                                        "Instructor would exceed 12 credit hours for the semester")
                    return

            # Schedule the course
            cursor.execute("""
                INSERT INTO instructor_courses 
                (course_prefix, course_number, instructor_id, semester, year_taught)
                VALUES (?, ?, ?, ?, ?)
            """, (prefix, number, instructor_id, semester, year))

            conn.commit()

            self.parent.logger.log_operation(
                "add",
                f"Scheduled course {prefix} {number} for {semester} {year}",
                {
                    "course": f"{prefix} {number}",
                    "semester": semester,
                    "year": year,
                    "instructor": instructor_id or "TBA"
                }
            )

            QMessageBox.information(self, "Success", "Course scheduled successfully")

            # Emit the signal to notify that a course was scheduled
            self.course_scheduled.emit()

            self.close()

        except sqlite3.Error as e:
            self.parent.logger.log_operation(
                "error",
                f"Failed to schedule course: {str(e)}"
            )
            QMessageBox.warning(self, "Error", "Failed to schedule course")
        finally:
            if conn:
                conn.close()

