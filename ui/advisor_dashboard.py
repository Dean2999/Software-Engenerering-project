import sys
import os
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QPushButton, QTableWidget, QTableWidgetItem,
                               QLineEdit, QComboBox, QFrame, QGroupBox,
                               QHeaderView, QSpacerItem, QSizePolicy, QTabWidget,
                               QMessageBox, QScrollArea)
from PySide6.QtCore import Qt, Signal
import sqlite3
from datetime import datetime
from ui.common.what_if_analysis import AdvisorWhatIfAnalysis


class AdvisorDashboard(QMainWindow):
    logout_signal = Signal()

    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.advisor_id = self.get_advisor_id()
        self.departments = self.get_advisor_departments()

        self.setWindowTitle("Advisor Dashboard")
        self.setGeometry(100, 100, 800, 600)
        self.setup_ui()
        self.load_advisor_data()
        self.log_operation("login", "Advisor logged into dashboard")

    def get_advisor_id(self):
        """Get the advisor_id from the database based on user_id"""
        try:
            conn = sqlite3.connect(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                '..', 'data', 'academic_management.db'))
            cursor = conn.cursor()
            cursor.execute("""
                SELECT advisor_id 
                FROM advisors 
                WHERE user_id = ?
            """, (self.user_id,))
            result = cursor.fetchone()
            return result[0] if result else None
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def get_advisor_departments(self):
        """Get the departments associated with this advisor"""
        if not self.advisor_id:
            return []

        try:
            conn = sqlite3.connect(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                '..', 'data', 'academic_management.db'))
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT department_id 
                FROM advisor_departments 
                WHERE advisor_id = ?
            """, (self.advisor_id,))
            return [dept[0] for dept in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def setup_ui(self):
        """Initialize the user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Header
        header = QWidget()
        header_layout = QHBoxLayout(header)
        title_label = QLabel(f"Welcome, Advisor {self.advisor_id}")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # Buttons
        self.logout_button = QPushButton("Logout")
        self.logout_button.clicked.connect(self.logout)
        header_layout.addWidget(self.logout_button)

        self.exit_button = QPushButton("Exit")
        self.exit_button.clicked.connect(self.close)
        header_layout.addWidget(self.exit_button)

        layout.addWidget(header)

        # Tab widget
        self.tab_widget = QTabWidget()
        self.setup_registration_tab()
        self.setup_progress_tab()
        self.setup_analysis_tab()
        layout.addWidget(self.tab_widget)

    def get_current_and_future_semesters(self):
        """Get current and future semesters based on current date"""
        current_date = datetime.now()
        current_year = current_date.year
        current_month = current_date.month

        semesters = []
        # Current semester
        if 1 <= current_month <= 5:
            current_sem = ('S', current_year)  # Spring
            semesters.extend([
                ('S', current_year),
                ('U', current_year),
                ('F', current_year),
                ('S', current_year + 1)
            ])
        elif 6 <= current_month <= 8:
            current_sem = ('U', current_year)  # Summer
            semesters.extend([
                ('U', current_year),
                ('F', current_year),
                ('S', current_year + 1)
            ])
        else:
            current_sem = ('F', current_year)  # Fall
            semesters.extend([
                ('F', current_year),
                ('S', current_year + 1)
            ])

        return current_sem, semesters

    def setup_registration_tab(self):
        """Setup the course registration tab with semester selection"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Student selection
        student_group = QGroupBox("Student Selection")
        student_layout = QHBoxLayout()
        self.student_combo = QComboBox()
        self.student_combo.currentIndexChanged.connect(self.load_student_courses)
        student_layout.addWidget(QLabel("Select Student:"))
        student_layout.addWidget(self.student_combo)
        student_group.setLayout(student_layout)
        layout.addWidget(student_group)

        # Semester selection and course registration group
        reg_group = QGroupBox("Course Registration")
        reg_layout = QVBoxLayout()

        # Add semester selection at the top
        semester_selection_layout = QHBoxLayout()
        self.view_semester_combo = QComboBox()
        _, future_semesters = self.get_current_and_future_semesters()
        for sem, year in future_semesters:
            semester_name = {'S': 'Spring', 'U': 'Summer', 'F': 'Fall'}[sem]
            self.view_semester_combo.addItem(f"{semester_name} {year}", (sem, year))
        self.view_semester_combo.currentIndexChanged.connect(self.load_student_courses)
        semester_selection_layout.addWidget(QLabel("View Semester:"))
        semester_selection_layout.addWidget(self.view_semester_combo)
        semester_selection_layout.addStretch()
        reg_layout.addLayout(semester_selection_layout)

        # Course selection for registration
        course_layout = QHBoxLayout()
        self.course_combo = QComboBox()
        course_layout.addWidget(QLabel("Select Course:"))
        course_layout.addWidget(self.course_combo)
        reg_layout.addLayout(course_layout)

        # Registration semester selection
        semester_layout = QHBoxLayout()
        self.semester_combo = QComboBox()
        for sem, year in future_semesters:
            semester_name = {'S': 'Spring', 'U': 'Summer', 'F': 'Fall'}[sem]
            self.semester_combo.addItem(f"{semester_name} {year}", (sem, year))
        semester_layout.addWidget(QLabel("Register for Semester:"))
        semester_layout.addWidget(self.semester_combo)
        reg_layout.addLayout(semester_layout)

        # Buttons
        button_layout = QHBoxLayout()
        register_button = QPushButton("Register Course")
        register_button.clicked.connect(self.register_course)
        drop_button = QPushButton("Drop Course")
        drop_button.clicked.connect(self.drop_course)
        button_layout.addWidget(register_button)
        button_layout.addWidget(drop_button)
        reg_layout.addLayout(button_layout)

        reg_group.setLayout(reg_layout)
        layout.addWidget(reg_group)

        # Course table
        self.courses_table = QTableWidget()
        self.courses_table.setColumnCount(6)
        self.courses_table.setHorizontalHeaderLabels([
            "Course", "Credits", "Grade", "Semester", "Year", "Status"
        ])
        header = self.courses_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.courses_table)

        tab.setLayout(layout)
        self.tab_widget.addTab(tab, "Course Registration")

    def setup_progress_tab(self):
        """Setup the student progress tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Student selection for progress
        student_group = QGroupBox("Student Selection")
        student_layout = QHBoxLayout()

        self.progress_student_combo = QComboBox()
        self.progress_student_combo.currentIndexChanged.connect(self.load_student_progress)
        student_layout.addWidget(QLabel("Select Student:"))
        student_layout.addWidget(self.progress_student_combo)

        student_group.setLayout(student_layout)
        layout.addWidget(student_group)

        # Progress summary
        summary_group = QGroupBox("Progress Summary")
        summary_layout = QVBoxLayout()
        self.progress_label = QLabel()
        summary_layout.addWidget(self.progress_label)
        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)

        # Course history table
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(6)
        self.history_table.setHorizontalHeaderLabels([
            "Course", "Credits", "Grade", "Semester", "Year", "GPA Impact"
        ])
        header = self.history_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.history_table)

        tab.setLayout(layout)
        self.tab_widget.addTab(tab, "Student Progress")

    def setup_analysis_tab(self):
        """Setup the what-if analysis tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Create What-If Analysis widget
        self.analysis_widget = AdvisorWhatIfAnalysis(self.advisor_id)
        layout.addWidget(self.analysis_widget)

        tab.setLayout(layout)
        self.tab_widget.addTab(tab, "What-If Analysis")

    def load_advisor_data(self):
        """Load all advisor-related data from the database"""
        try:
            conn = sqlite3.connect(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                '..', 'data', 'academic_management.db'))
            cursor = conn.cursor()

            # Load advisees
            cursor.execute("""
                SELECT DISTINCT s.student_id, s.major, dm.department_id,
                       ROUND(AVG(CASE 
                           WHEN sc.grade = 'A' THEN 4.0
                           WHEN sc.grade = 'B' THEN 3.0
                           WHEN sc.grade = 'C' THEN 2.0
                           WHEN sc.grade = 'D' THEN 1.0
                           WHEN sc.grade = 'F' THEN 0.0
                           ELSE NULL
                       END), 2) as gpa
                FROM students s
                JOIN department_majors dm ON s.major = dm.major_name
                JOIN advisor_departments ad ON dm.department_id = ad.department_id
                LEFT JOIN student_courses sc ON s.student_id = sc.student_id
                WHERE ad.advisor_id = ?
                GROUP BY s.student_id
                ORDER BY s.student_id
            """, (self.advisor_id,))

            advisees = cursor.fetchall()

            # Populate student combos
            self.student_combo.clear()
            self.progress_student_combo.clear()
            for advisee in advisees:
                student_text = f"{advisee[0]} - {advisee[1]}"
                self.student_combo.addItem(student_text, advisee[0])
                self.progress_student_combo.addItem(student_text, advisee[0])

            # Load available courses
            cursor.execute("""
                SELECT DISTINCT c.course_prefix, c.course_number, c.credits
                FROM courses c
                JOIN department_majors dm ON c.course_prefix = dm.department_id
                JOIN advisor_departments ad ON dm.department_id = ad.department_id
                WHERE ad.advisor_id = ?
                ORDER BY c.course_prefix, c.course_number
            """, (self.advisor_id,))

            courses = cursor.fetchall()
            self.course_combo.clear()
            for course in courses:
                course_text = f"{course[0]} {course[1]} ({course[2]} credits)"
                self.course_combo.addItem(course_text, (course[0], course[1], course[2]))

        except sqlite3.Error as e:
            print(f"Database error: {e}")
            QMessageBox.critical(self, "Error", "Failed to load advisor data")
        finally:
            if conn:
                conn.close()

    def filter_advisees(self):
        """Filter the advisee table based on search text and department"""
        search_text = self.search_input.text().lower()
        selected_dept = self.department_filter.currentText()

        for row in range(self.advisee_table.rowCount()):
            student_id = self.advisee_table.item(row, 0).text().lower()
            major = self.advisee_table.item(row, 1).text().lower()
            department = self.advisee_table.item(row, 2).text()

            matches_search = search_text in student_id or search_text in major
            matches_dept = selected_dept == "All Departments" or selected_dept == department

            self.advisee_table.setRowHidden(row, not (matches_search and matches_dept))


    def load_student_progress(self):
        """Load progress information for the selected student"""
        student_id = self.progress_student_combo.currentData()
        if not student_id:
            return

        try:
            conn = sqlite3.connect(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                               '..', 'data', 'academic_management.db'))
            cursor = conn.cursor()

            # Get student progress information
            cursor.execute("""
                SELECT s.major, dm.hours_req,
                       COUNT(sc.course_prefix) as courses_taken,
                       SUM(c.credits) as credits_earned,
                       ROUND(AVG(CASE 
                           WHEN sc.grade = 'A' THEN 4.0
                           WHEN sc.grade = 'B' THEN 3.0
                           WHEN sc.grade = 'C' THEN 2.0
                           WHEN sc.grade = 'D' THEN 1.0
                           WHEN sc.grade = 'F' THEN 0.0
                           ELSE NULL
                       END), 2) as gpa
                FROM students s
                JOIN department_majors dm ON s.major = dm.major_name
                LEFT JOIN student_courses sc ON s.student_id = sc.student_id
                LEFT JOIN courses c ON sc.course_prefix = c.course_prefix 
                    AND sc.course_number = c.course_number
                WHERE s.student_id = ?
                GROUP BY s.student_id
            """, (student_id,))

            progress = cursor.fetchone()
            if progress:
                major, hours_req, courses_taken, credits_earned, gpa = progress
                credits_earned = credits_earned or 0
                progress_text = (
                    f"Major: {major}\n"
                    f"Required Credits: {hours_req}\n"
                    f"Credits Earned: {credits_earned}\n"
                    f"Courses Taken: {courses_taken}\n"
                    f"Current GPA: {gpa or 'N/A'}\n"
                    f"Progress: {(credits_earned / hours_req * 100):.1f}% complete"
                )
                self.progress_label.setText(progress_text)

            # Load course history with GPA impact
            cursor.execute("""
                SELECT c.course_prefix || ' ' || c.course_number,
                       c.credits, sc.grade, sc.semester, sc.year_taken,
                       CASE sc.grade
                           WHEN 'A' THEN c.credits * 4.0
                           WHEN 'B' THEN c.credits * 3.0
                           WHEN 'C' THEN c.credits * 2.0
                           WHEN 'D' THEN c.credits * 1.0
                           WHEN 'F' THEN 0.0
                           ELSE NULL
                       END as points
                FROM student_courses sc
                JOIN courses c ON sc.course_prefix = c.course_prefix 
                    AND sc.course_number = c.course_number
                WHERE sc.student_id = ?
                ORDER BY sc.year_taken DESC, sc.semester DESC
            """, (student_id,))

            courses = cursor.fetchall()
            self.history_table.setRowCount(len(courses))

            for row, course in enumerate(courses):
                for col, value in enumerate(course):
                    if col == 5:  # GPA Impact column
                        value = f"{value:.1f} points" if value is not None else 'N/A'
                    item = QTableWidgetItem(str(value if value is not None else 'N/A'))
                    item.setTextAlignment(Qt.AlignCenter)
                    self.history_table.setItem(row, col, item)

        except sqlite3.Error as e:
            print(f"Database error: {e}")
            QMessageBox.critical(self, "Error", "Failed to load student progress")
        finally:
            if conn:
                conn.close()

    def load_student_courses(self):
        """Load courses for the selected student and semester"""
        student_id = self.student_combo.currentData()
        if not student_id:
            return

        # Get selected semester and year
        semester_data = self.view_semester_combo.currentData()
        if not semester_data:
            return

        selected_semester, selected_year = semester_data

        try:
            conn = sqlite3.connect(os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                '..', 'data', 'academic_management.db'
            ))
            cursor = conn.cursor()

            current_sem, _ = self.get_current_and_future_semesters()

            # Modified query to filter by selected semester and year
            cursor.execute("""
                SELECT c.course_prefix || ' ' || c.course_number,
                       c.credits, sc.grade, sc.semester, sc.year_taken,
                       CASE 
                           WHEN sc.grade IS NOT NULL THEN 'Completed'
                           WHEN (sc.year_taken < ? OR (sc.year_taken = ? AND sc.semester < ?)) 
                               THEN 'Completed'
                           WHEN (sc.year_taken = ? AND sc.semester = ?) 
                               THEN 'Current'
                           ELSE 'Future'
                       END as status
                FROM student_courses sc
                JOIN courses c ON sc.course_prefix = c.course_prefix 
                    AND sc.course_number = c.course_number
                WHERE sc.student_id = ?
                AND sc.semester = ?
                AND sc.year_taken = ?
                ORDER BY c.course_prefix, c.course_number
            """, (current_sem[1], current_sem[1], current_sem[0],
                  current_sem[1], current_sem[0], student_id,
                  selected_semester, selected_year))

            courses = cursor.fetchall()
            self.courses_table.setRowCount(len(courses))

            for row, course in enumerate(courses):
                for col, value in enumerate(course):
                    item = QTableWidgetItem(str(value if value is not None else 'N/A'))
                    item.setTextAlignment(Qt.AlignCenter)
                    self.courses_table.setItem(row, col, item)

                    # Color-code the status column
                    if col == 5:  # Status column
                        if value == 'Completed':
                            item.setBackground(Qt.gray)
                        elif value == 'Current':
                            item.setBackground(Qt.green)
                        else:  # Future
                            item.setBackground(Qt.yellow)

        except sqlite3.Error as e:
            print(f"Database error: {e}")
            QMessageBox.critical(self, "Error", "Failed to load student courses")
        finally:
            if conn:
                conn.close()


    def drop_course(self):
        """Drop a student from a selected course with enhanced validation"""
        # Validate student selection
        student_id = self.student_combo.currentData()
        if not student_id:
            QMessageBox.warning(self, "Warning", "Please select a student first")
            return

        # Validate course selection
        selected_items = self.courses_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Warning", "Please select a course to drop")
            return

        # Get course details
        try:
            row = selected_items[0].row()
            status = self.courses_table.item(row, 5).text()
            course_full = self.courses_table.item(row, 0).text()
            course_parts = course_full.split()

            if len(course_parts) != 2:
                QMessageBox.warning(self, "Error", "Invalid course format")
                return

            course_prefix, course_number = course_parts
            semester = self.courses_table.item(row, 3).text()
            year = self.courses_table.item(row, 4).text()

        except (IndexError, AttributeError) as e:
            QMessageBox.critical(self, "Error", "Failed to get course details")
            print(f"Error getting course details: {e}")
            return

        # Validate course status
        if status == 'Completed':
            QMessageBox.warning(
                self,
                "Drop Error",
                "Cannot drop completed courses. Only current or future courses can be dropped."
            )
            return

        # Get current semester for additional validation
        current_sem, _ = self.get_current_and_future_semesters()
        if (int(year) < current_sem[1] or
                (int(year) == current_sem[1] and semester < current_sem[0])):
            QMessageBox.warning(
                self,
                "Drop Error",
                "Cannot drop courses from past semesters."
            )
            return

        # Confirm with user
        reply = QMessageBox.question(
            self,
            'Confirm Drop',
            f'Are you sure you want to drop {course_prefix} {course_number}\n'
            f'for student {student_id} ({semester} {year})?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.No:
            return

        # Perform database operation
        conn = None
        try:
            conn = sqlite3.connect(os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                '..', 'data', 'academic_management.db'
            ))
            cursor = conn.cursor()

            # Begin transaction
            cursor.execute("BEGIN TRANSACTION")

            # Verify the course exists and can be dropped
            cursor.execute("""
                SELECT COUNT(*) FROM student_courses 
                WHERE student_id = ? 
                AND course_prefix = ? 
                AND course_number = ? 
                AND semester = ? 
                AND year_taken = ?
                AND (grade IS NULL OR grade = '')
            """, (student_id, course_prefix, course_number, semester, year))

            if cursor.fetchone()[0] == 0:
                cursor.execute("ROLLBACK")
                QMessageBox.warning(
                    self,
                    "Drop Error",
                    "Course not found or cannot be dropped."
                )
                return

            # Perform the drop
            cursor.execute("""
                DELETE FROM student_courses 
                WHERE student_id = ? 
                AND course_prefix = ? 
                AND course_number = ? 
                AND semester = ? 
                AND year_taken = ?
            """, (student_id, course_prefix, course_number, semester, year))

            # Commit transaction
            conn.commit()

            # Log the operation
            self.log_operation(
                "drop",
                f"Dropped course {course_prefix} {course_number} "
                f"for student {student_id} ({semester} {year})"
            )

            # Refresh the display
            self.load_student_courses()

            QMessageBox.information(
                self,
                "Success",
                f"Successfully dropped {course_prefix} {course_number}"
            )

        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            print(f"Database error: {e}")
            QMessageBox.critical(
                self,
                "Error",
                "Failed to drop course. Please try again or contact system administrator."
            )
        except Exception as e:
            if conn:
                conn.rollback()
            print(f"Unexpected error: {e}")
            QMessageBox.critical(
                self,
                "Error",
                "An unexpected error occurred. Please try again or contact system administrator."
            )
        finally:
            if conn:
                try:
                    conn.close()
                except sqlite3.Error as e:
                    print(f"Error closing database connection: {e}")

    def register_course(self):
        """Register a student for a selected course"""
        # Validate student selection
        student_id = self.student_combo.currentData()
        if not student_id:
            QMessageBox.warning(self, "Warning", "Please select a student first")
            return

        # Get course details from combo box
        course_data = self.course_combo.currentData()
        if not course_data:
            QMessageBox.warning(self, "Warning", "Please select a course to register")
            return

        course_prefix, course_number, credits = course_data
        semester_data = self.semester_combo.currentData()
        if not semester_data:
            QMessageBox.warning(self, "Warning", "Please select a semester")
            return

        semester, year = semester_data

        # Check for duplicate registration
        conn = None
        try:
            conn = sqlite3.connect(os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                '..', 'data', 'academic_management.db'
            ))
            cursor = conn.cursor()

            # Begin transaction
            cursor.execute("BEGIN TRANSACTION")

            # Check if student is already registered for this course in the same semester
            cursor.execute("""
                SELECT COUNT(*) FROM student_courses 
                WHERE student_id = ? 
                AND course_prefix = ? 
                AND course_number = ? 
                AND semester = ? 
                AND year_taken = ?
            """, (student_id, course_prefix, course_number, semester, year))

            if cursor.fetchone()[0] > 0:
                cursor.execute("ROLLBACK")
                QMessageBox.warning(
                    self,
                    "Registration Error",
                    "Student is already registered for this course in the selected semester."
                )
                return

            # Register the student for the course
            cursor.execute("""
                INSERT INTO student_courses 
                (student_id, course_prefix, course_number, semester, year_taken)
                VALUES (?, ?, ?, ?, ?)
            """, (student_id, course_prefix, course_number, semester, year))

            # Commit transaction
            conn.commit()

            # Log the operation
            self.log_operation(
                "register",
                f"Registered student {student_id} for course {course_prefix} {course_number} "
                f"({semester} {year})"
            )

            # Refresh the display
            self.load_student_courses()

            QMessageBox.information(
                self,
                "Success",
                f"Successfully registered for {course_prefix} {course_number}"
            )

        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            print(f"Database error: {e}")
            QMessageBox.critical(
                self,
                "Error",
                "Failed to register for course. Please try again or contact system administrator."
            )
        except Exception as e:
            if conn:
                conn.rollback()
            print(f"Unexpected error: {e}")
            QMessageBox.critical(
                self,
                "Error",
                "An unexpected error occurred. Please try again or contact system administrator."
            )
        finally:
            if conn:
                try:
                    conn.close()
                except sqlite3.Error as e:
                    print(f"Error closing database connection: {e}")


    def log_operation(self, operation_type, details):
        """Log advisor operations to the database"""
        try:
            conn = sqlite3.connect(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                               '..', 'data', 'academic_management.db'))
            cursor = conn.cursor()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            cursor.execute("""
                INSERT INTO operation_logs 
                (timestamp, user_id, operation_type, details)
                VALUES (?, ?, ?, ?)
            """, (timestamp, self.user_id, f"advisor_{operation_type}", details))

            conn.commit()

        except sqlite3.Error as e:
            print(f"Database error while logging operation: {e}")
        finally:
            if conn:
                conn.close()

    def closeEvent(self, event):
        """Handle window close event"""
        self.log_operation("exit", "Advisor exited the system")
        event.accept()

    def logout(self):
        """Handle logout"""
        self.log_operation("logout", "Advisor logged out")
        self.logout_signal.emit()
        self.close()