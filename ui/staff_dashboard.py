import sys
import os
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QPushButton, QTableWidget, QTableWidgetItem,
                               QTabWidget, QComboBox, QMessageBox, QLineEdit, QFormLayout, QDialog)
from PySide6.QtCore import Qt, Signal
import sqlite3
from datetime import datetime
from ui.common.system_logger import SystemLogger, UserRole, OperationType
from ui.staff_course_management import CourseManagementDialog


class StaffDashboard(QMainWindow):
    logout_signal = Signal()

    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id

        # Initialize the system logger first
        self.logger = SystemLogger(self.user_id, UserRole.STAFF)

        # Then get staff_id and department_id
        self.staff_id = self.get_staff_id()
        self.department_id = self.get_department_id()

        print(
            f"Initializing StaffDashboard with user_id: {self.user_id}, "
            f"staff_id: {self.staff_id}, department_id: {self.department_id}"
        )

        self.setWindowTitle("Staff Dashboard")
        self.setGeometry(100, 100, 800, 600)
        self.setup_ui()

        # Log the login session
        self.logger.log_session(OperationType.LOGIN)

    def get_staff_id(self):
        try:
            conn = sqlite3.connect(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                '..', 'data', 'academic_management.db'))
            cursor = conn.cursor()
            cursor.execute("SELECT staff_id FROM staff WHERE user_id = ?", (self.user_id,))
            result = cursor.fetchone()

            # Log the data access
            if result:
                self.logger.log_data_access(
                    "staff",
                    "retrieved staff ID",
                    {"user_id": self.user_id, "staff_id": result[0]}
                )
            return result[0] if result else None

        except sqlite3.Error as e:
            self.logger.log_operation(
                OperationType.ERROR,
                f"Failed to get staff ID: {str(e)}"
            )
            return None
        finally:
            if conn:
                conn.close()

    def get_department_id(self):
        try:
            conn = sqlite3.connect(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                '..', 'data', 'academic_management.db'))
            cursor = conn.cursor()
            cursor.execute("SELECT department_id FROM staff WHERE staff_id = ?", (self.staff_id,))
            result = cursor.fetchone()

            # Log the data access
            if result:
                self.logger.log_data_access(
                    "staff",
                    "retrieved department ID",
                    {"staff_id": self.staff_id, "department_id": result[0]}
                )
            return result[0] if result else None

        except sqlite3.Error as e:
            self.logger.log_operation(
                OperationType.ERROR,
                f"Failed to get department ID: {str(e)}"
            )
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
        self.staff_name_label = QLabel(f"Welcome, Staff {self.staff_id}")
        self.staff_name_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(self.staff_name_label)
        header_layout.addStretch()
        self.logout_button = QPushButton("Logout")
        self.logout_button.clicked.connect(self.logout)
        header_layout.addWidget(self.logout_button)
        self.exit_button = QPushButton("Exit")
        self.exit_button.clicked.connect(self.close)
        header_layout.addWidget(self.exit_button)
        main_layout.addLayout(header_layout)

        # Tabs
        tab_widget = QTabWidget()
        main_layout.addWidget(tab_widget)

        # Courses Tab with subtabs
        courses_tab = QWidget()
        courses_layout = QVBoxLayout(courses_tab)

        # Create subtabs for courses
        courses_subtabs = QTabWidget()

        # Catalog Management Subtab
        catalog_tab = QWidget()
        catalog_layout = QVBoxLayout(catalog_tab)

        # Initialize the catalog table
        self.catalog_table = QTableWidget()
        self.catalog_table.setColumnCount(3)
        self.catalog_table.setHorizontalHeaderLabels(["Prefix", "Number", "Credits"])
        catalog_layout.addWidget(self.catalog_table)

        # Catalog buttons
        catalog_buttons_layout = QHBoxLayout()
        self.add_catalog_course_button = QPushButton("Add Course")
        self.add_catalog_course_button.clicked.connect(self.add_course)
        catalog_buttons_layout.addWidget(self.add_catalog_course_button)

        self.remove_catalog_course_button = QPushButton("Remove Course")
        self.remove_catalog_course_button.clicked.connect(self.remove_course)
        catalog_buttons_layout.addWidget(self.remove_catalog_course_button)

        self.modify_catalog_course_button = QPushButton("Modify Course")
        self.modify_catalog_course_button.clicked.connect(self.modify_course)
        catalog_buttons_layout.addWidget(self.modify_catalog_course_button)

        catalog_layout.addLayout(catalog_buttons_layout)
        catalog_tab.setLayout(catalog_layout)
        courses_subtabs.addTab(catalog_tab, "Course Catalog")

        # Semester Schedule Subtab
        schedule_tab = QWidget()
        schedule_layout = QVBoxLayout(schedule_tab)

        # Semester selector
        semester_layout = QHBoxLayout()
        semester_layout.addWidget(QLabel("Select Semester:"))
        self.semester_selector = QComboBox()
        current_sem, future_sems = self.get_current_and_future_semesters()
        for sem, year in future_sems:
            semester_name = {'F': 'Fall', 'S': 'Spring', 'U': 'Summer'}[sem]
            self.semester_selector.addItem(f"{semester_name} {year}", (sem, year))
        self.semester_selector.currentIndexChanged.connect(self.load_semester_courses)
        semester_layout.addWidget(self.semester_selector)
        semester_layout.addStretch()
        schedule_layout.addLayout(semester_layout)

        # Semester courses table
        self.semester_courses_table = QTableWidget()
        self.semester_courses_table.setColumnCount(4)
        self.semester_courses_table.setHorizontalHeaderLabels(
            ["Course", "Credits", "Instructor", "Status"]
        )
        schedule_layout.addWidget(self.semester_courses_table)

        # Schedule management buttons
        schedule_buttons_layout = QHBoxLayout()
        self.add_schedule_button = QPushButton("Add to Schedule")
        self.add_schedule_button.clicked.connect(self.add_to_schedule)
        schedule_buttons_layout.addWidget(self.add_schedule_button)

        self.remove_schedule_button = QPushButton("Remove from Schedule")
        self.remove_schedule_button.clicked.connect(self.remove_from_schedule)
        schedule_buttons_layout.addWidget(self.remove_schedule_button)

        self.modify_schedule_button = QPushButton("Modify Schedule")
        self.modify_schedule_button.clicked.connect(self.modify_schedule)
        schedule_buttons_layout.addWidget(self.modify_schedule_button)

        schedule_layout.addLayout(schedule_buttons_layout)
        schedule_tab.setLayout(schedule_layout)
        courses_subtabs.addTab(schedule_tab, "Semester Schedule")

        courses_layout.addWidget(courses_subtabs)
        courses_tab.setLayout(courses_layout)
        tab_widget.addTab(courses_tab, "Courses")

        # Instructors Tab
        instructors_tab = QWidget()
        instructors_layout = QVBoxLayout(instructors_tab)
        self.instructors_table = QTableWidget()
        instructors_layout.addWidget(self.instructors_table)
        instructor_buttons_layout = QHBoxLayout()
        self.assign_instructor_button = QPushButton("Assign Instructor to Course")
        self.assign_instructor_button.clicked.connect(self.assign_instructor_to_course)
        instructor_buttons_layout.addWidget(self.assign_instructor_button)
        self.modify_instructor_button = QPushButton("Modify Instructor")
        self.modify_instructor_button.clicked.connect(self.modify_instructor)
        instructor_buttons_layout.addWidget(self.modify_instructor_button)
        instructors_layout.addLayout(instructor_buttons_layout)
        instructors_tab.setLayout(instructors_layout)
        tab_widget.addTab(instructors_tab, "Instructors")

        # Students Tab
        students_tab = QWidget()
        students_layout = QVBoxLayout(students_tab)
        self.students_table = QTableWidget()
        students_layout.addWidget(self.students_table)
        self.modify_student_button = QPushButton("Modify Student")
        self.modify_student_button.clicked.connect(self.modify_student)
        students_layout.addWidget(self.modify_student_button)
        students_tab.setLayout(students_layout)
        tab_widget.addTab(students_tab, "Students")

        # Department Info Tab
        department_tab = QWidget()
        department_layout = QVBoxLayout(department_tab)
        self.department_info_label = QLabel()
        department_layout.addWidget(self.department_info_label)
        self.department_majors_table = QTableWidget()
        department_layout.addWidget(self.department_majors_table)
        self.modify_department_button = QPushButton("Modify Department Info")
        self.modify_department_button.clicked.connect(self.modify_department)
        department_layout.addWidget(self.modify_department_button)
        department_tab.setLayout(department_layout)
        tab_widget.addTab(department_tab, "Department Info")

        self.load_staff_data()
        self.load_initial_data()

    def load_initial_data(self):
        """Load all initial data for the dashboard"""
        print("Loading initial dashboard data...")
        self.load_staff_data()
        # Load initial semester courses if a semester is selected
        if self.semester_selector.count() > 0:
            print(f"Initial semester selected: {self.semester_selector.currentText()}")
            self.load_semester_courses()
        else:
            print("No semesters available in selector")


    def load_staff_data(self):
        try:
            conn = sqlite3.connect(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                '..', 'data', 'academic_management.db'))
            cursor = conn.cursor()

            # ========== Load Courses Tab ==========
            self.catalog_table.clear()
            self.catalog_table.setRowCount(0)

            # Modified query to use department_course_prefixes table
            cursor.execute("""
                SELECT DISTINCT c.course_prefix, c.course_number, c.credits
                FROM courses c
                JOIN department_course_prefixes dcp ON c.course_prefix = dcp.course_prefix
                WHERE dcp.department_id = ?
                ORDER BY c.course_prefix, c.course_number
            """, (self.department_id,))

            courses = cursor.fetchall()
            print(f"Found {len(courses)} courses for department {self.department_id}")  # Debug print

            # Populate courses table
            self.catalog_table.setRowCount(len(courses))
            for row, course in enumerate(courses):
                for col, value in enumerate(course):
                    item = QTableWidgetItem(str(value))
                    item.setTextAlignment(Qt.AlignCenter)
                    self.catalog_table.setItem(row, col, item)

            self.catalog_table.resizeColumnsToContents()

            # ========== Load Instructors Tab ==========
            self.instructors_table.clear()
            self.instructors_table.setRowCount(0)

            # Set up instructors table headers
            self.instructors_table.setColumnCount(3)
            self.instructors_table.setHorizontalHeaderLabels(["Instructor ID", "Phone", "Hired Semester"])

            # Get instructors for the department
            cursor.execute("""
                        SELECT i.instructor_id, i.phone, i.hired_semester
                        FROM instructors i
                        WHERE i.department_id = ?
                        ORDER BY i.instructor_id
                    """, (self.department_id,))

            instructors = cursor.fetchall()

            # Log instructor data access
            self.logger.log_data_access(
                "instructors",
                "retrieved department instructors",
                {
                    "department_id": self.department_id,
                    "instructor_count": len(instructors)
                }
            )

            # Populate instructors table
            self.instructors_table.setRowCount(len(instructors))
            for row, instructor in enumerate(instructors):
                for col, value in enumerate(instructor):
                    item = QTableWidgetItem(str(value))
                    item.setTextAlignment(Qt.AlignCenter)
                    self.instructors_table.setItem(row, col, item)

            self.instructors_table.resizeColumnsToContents()

            # ========== Load Students Tab ==========
            self.students_table.clear()
            self.students_table.setRowCount(0)

            # Set up students table headers
            self.students_table.setColumnCount(3)
            self.students_table.setHorizontalHeaderLabels(["Student ID", "Gender", "Major"])

            # Get students for the department's majors
            cursor.execute("""
                        SELECT DISTINCT s.student_id, s.gender, s.major
                        FROM students s
                        JOIN department_majors dm ON s.major = dm.major_name
                        WHERE dm.department_id = ?
                        ORDER BY s.student_id
                    """, (self.department_id,))

            students = cursor.fetchall()

            # Log student data access
            self.logger.log_data_access(
                "students",
                "retrieved department students",
                {
                    "department_id": self.department_id,
                    "student_count": len(students)
                }
            )

            # Populate students table
            self.students_table.setRowCount(len(students))
            for row, student in enumerate(students):
                for col, value in enumerate(student):
                    item = QTableWidgetItem(str(value))
                    item.setTextAlignment(Qt.AlignCenter)
                    self.students_table.setItem(row, col, item)

            self.students_table.resizeColumnsToContents()

            # ========== Load Department Info Tab ==========
            # Get department information
            cursor.execute("""
                        SELECT d.department_id, d.building, d.office
                        FROM departments d
                        WHERE d.department_id = ?
                    """, (self.department_id,))

            dept_info = cursor.fetchone()

            if dept_info:
                self.department_info_label.setText(
                    f"Department ID: {dept_info[0]}\n"
                    f"Building: {dept_info[1]}\n"
                    f"Office: {dept_info[2]}"
                )
            else:
                self.department_info_label.setText("No department information available.")

            # Load department majors
            self.department_majors_table.clear()
            self.department_majors_table.setRowCount(0)
            self.department_majors_table.setColumnCount(2)
            self.department_majors_table.setHorizontalHeaderLabels(["Major", "Required Hours"])

            cursor.execute("""
                        SELECT major_name, hours_req
                        FROM department_majors
                        WHERE department_id = ?
                        ORDER BY major_name
                    """, (self.department_id,))

            majors = cursor.fetchall()

            # Log department data access
            self.logger.log_data_access(
                "department_majors",
                "retrieved department majors",
                {
                    "department_id": self.department_id,
                    "major_count": len(majors)
                }
            )

            # Populate majors table
            self.department_majors_table.setRowCount(len(majors))
            for row, major in enumerate(majors):
                for col, value in enumerate(major):
                    item = QTableWidgetItem(str(value))
                    item.setTextAlignment(Qt.AlignCenter)
                    self.department_majors_table.setItem(row, col, item)

            self.department_majors_table.resizeColumnsToContents()

        except sqlite3.Error as e:
            self.logger.log_operation(
                OperationType.ERROR,
                f"Database error while loading staff data: {str(e)}"
            )
            QMessageBox.critical(self, "Error", "Failed to load staff data")
            print(f"Database error: {e}")  # For debugging
        finally:
            if conn:
                conn.close()

    def get_allowed_prefixes(self):
        """Get the course prefixes that this staff member's department can manage"""
        try:
            conn = sqlite3.connect(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                '..', 'data', 'academic_management.db'))
            cursor = conn.cursor()

            cursor.execute("""
                SELECT course_prefix, is_primary 
                FROM department_course_prefixes
                WHERE department_id = ?
                ORDER BY is_primary DESC, course_prefix
            """, (self.department_id,))

            return cursor.fetchall()
        except sqlite3.Error as e:
            self.logger.log_operation(
                OperationType.ERROR,
                f"Database error while getting allowed prefixes: {str(e)}"
            )
            return []
        finally:
            if conn:
                conn.close()

    def add_course(self):
        """Add a new course to the catalog"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Course")
        layout = QFormLayout(dialog)

        # Course prefix input with validation
        prefix_layout = QHBoxLayout()
        prefix_input = QLineEdit()
        prefix_input.setMaxLength(3)
        prefix_input.setPlaceholderText("3 letters (e.g., CIS)")
        prefix_layout.addWidget(prefix_input)
        layout.addRow("Course Prefix:", prefix_layout)

        # Course number and credits inputs
        number_input = QLineEdit()
        number_input.setPlaceholderText("e.g., 4930")
        layout.addRow("Course Number:", number_input)

        credits_input = QLineEdit()
        credits_input.setPlaceholderText("1-4")
        layout.addRow("Credits:", credits_input)

        # Dialog buttons
        buttons = QHBoxLayout()
        save_button = QPushButton("Save")
        cancel_button = QPushButton("Cancel")
        buttons.addWidget(save_button)
        buttons.addWidget(cancel_button)
        layout.addRow(buttons)

        save_button.clicked.connect(dialog.accept)
        cancel_button.clicked.connect(dialog.reject)

        if dialog.exec_():
            prefix = prefix_input.text().strip().upper()
            number = number_input.text().strip()

            try:
                credits = int(credits_input.text().strip())
            except ValueError:
                self.logger.log_operation(
                    OperationType.ERROR,
                    "Invalid credits value",
                    {"value": credits_input.text().strip()}
                )
                QMessageBox.warning(self, "Error", "Credits must be a number between 1 and 4")
                return

            # Validate inputs
            if not prefix or len(prefix) != 3 or not prefix.isalpha():
                self.logger.log_operation(
                    OperationType.ERROR,
                    "Invalid course prefix format",
                    {"prefix": prefix, "reason": "Prefix must be exactly 3 uppercase letters"}
                )
                QMessageBox.warning(self, "Error", "Course prefix must be exactly 3 letters")
                return

            if not number or not number.isdigit():
                self.logger.log_operation(
                    OperationType.ERROR,
                    "Invalid course number format",
                    {"number": number}
                )
                QMessageBox.warning(self, "Error", "Course number must be numeric")
                return

            if credits < 1 or credits > 4:
                self.logger.log_operation(
                    OperationType.ERROR,
                    "Invalid credits value",
                    {"credits": credits}
                )
                QMessageBox.warning(self, "Error", "Credits must be between 1 and 4")
                return

            try:
                conn = sqlite3.connect(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                    '..', 'data', 'academic_management.db'))
                cursor = conn.cursor()

                # Check if the prefix is already assigned to another department
                cursor.execute("""
                    SELECT d.department_id 
                    FROM department_course_prefixes d
                    WHERE d.course_prefix = ?
                """, (prefix,))

                existing_dept = cursor.fetchone()

                if existing_dept and existing_dept[0] != self.department_id:
                    self.logger.log_operation(
                        OperationType.ERROR,
                        "Attempted to add course with prefix belonging to another department",
                        {"prefix": prefix, "owning_department": existing_dept[0]}
                    )
                    QMessageBox.warning(self, "Error",
                                        "This course prefix belongs to another department")
                    return

                # Check for duplicate course
                cursor.execute("""
                    SELECT COUNT(*) FROM courses
                    WHERE course_prefix = ? AND course_number = ?
                """, (prefix, number))

                if cursor.fetchone()[0] > 0:
                    self.logger.log_operation(
                        OperationType.ERROR,
                        "Attempted to add duplicate course",
                        {"prefix": prefix, "number": number}
                    )
                    QMessageBox.warning(self, "Error", "This course already exists")
                    return

                # Begin transaction
                cursor.execute("BEGIN TRANSACTION")

                # If this is a new prefix, add it to department_course_prefixes
                if not existing_dept:
                    cursor.execute("""
                        INSERT INTO department_course_prefixes 
                        (department_id, course_prefix, is_primary, added_date)
                        VALUES (?, ?, 0, datetime('now'))
                    """, (self.department_id, prefix))

                # Add the course
                cursor.execute("""
                    INSERT INTO courses (course_prefix, course_number, credits)
                    VALUES (?, ?, ?)
                """, (prefix, number, credits))

                cursor.execute("COMMIT")

                self.logger.log_operation(
                    OperationType.ADD,
                    "Successfully added new course",
                    {"prefix": prefix, "number": number, "credits": credits}
                )

                self.load_staff_data()
                QMessageBox.information(self, "Success", "Course added successfully")

            except sqlite3.Error as e:
                if conn:
                    cursor.execute("ROLLBACK")
                self.logger.log_operation(
                    OperationType.ERROR,
                    f"Database error while adding course: {str(e)}"
                )
                QMessageBox.warning(self, "Error", "Failed to add course")
            finally:
                if conn:
                    conn.close()

    def on_prefix_selection_changed(index):
        if prefix_combo.currentText() == "New Prefix...":
            prefix_input.show()
        else:
            prefix_input.hide()

        prefix_combo.currentIndexChanged.connect(on_prefix_selection_changed)

        layout.addRow("Course Prefix:", prefix_layout)
        layout.addRow("Course Number:", QLineEdit())
        layout.addRow("Credits:", QLineEdit())


        if dialog.exec_():
            # Get prefix (either selected or new)
            if prefix_combo.currentText() == "New Prefix...":
                prefix = prefix_input.text().strip().upper()
                is_new_prefix = True
            else:
                prefix = prefix_combo.currentData()
                is_new_prefix = False

            # Validate new prefix
            if is_new_prefix:
                if not prefix or len(prefix) != 3 or not prefix.isalpha():
                    QMessageBox.warning(self, "Error", "New prefix must be exactly 3 letters.")
                    return

                # Confirm adding new prefix
                reply = QMessageBox.question(
                    self,
                    "Confirm New Prefix",
                    f"Do you want to add '{prefix}' as a new course prefix for your department?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )

                if reply == QMessageBox.Yes:
                    try:
                        conn = sqlite3.connect(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                            '..', 'data', 'academic_management.db'))
                        cursor = conn.cursor()

                        # Add new prefix to department_course_prefixes
                        cursor.execute("""
                            INSERT INTO department_course_prefixes (department_id, course_prefix, is_primary)
                            VALUES (?, ?, 0)
                        """, (self.department_id, prefix))

                        conn.commit()

                        self.logger.log_operation(
                            OperationType.ADD,
                            f"Added new course prefix {prefix} to department {self.department_id}"
                        )
                    except sqlite3.Error as e:
                        self.logger.log_operation(
                            OperationType.ERROR,
                            f"Failed to add new prefix: {str(e)}"
                        )
                        QMessageBox.warning(self, "Error", "Failed to add new prefix.")
                        return
                    finally:
                        if conn:
                            conn.close()
                else:
                    return


    def is_duplicate_course(self, prefix, number):
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'academic_management.db')
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM courses WHERE course_prefix = ? AND course_number = ?", (prefix, number))
            count = cursor.fetchone()[0]
            return count > 0
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def save_course(self, prefix, number, credits):
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'academic_management.db')
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO courses (course_prefix, course_number, credits) VALUES (?, ?, ?)",
                           (prefix, number, credits))
            conn.commit()
            QMessageBox.information(self, "Success", "Course added successfully.")
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            QMessageBox.warning(self, "Error", "Failed to add course.")
        finally:
            if conn:
                conn.close()

    def remove_course(self):
        """Remove a course from the catalog"""
        selected_items = self.catalog_table.selectedItems()
        if not selected_items:
            self.logger.log_operation(
                OperationType.ERROR,
                "Attempted to remove course without selection"
            )
            QMessageBox.warning(self, "No Selection", "Please select a course to remove")
            return

        row = selected_items[0].row()
        prefix = self.catalog_table.item(row, 0).text()
        number = self.catalog_table.item(row, 1).text()

        try:
            conn = sqlite3.connect(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                '..', 'data', 'academic_management.db'))
            cursor = conn.cursor()

            # Check for existing enrollments
            cursor.execute("""
                SELECT COUNT(*) FROM student_courses
                WHERE course_prefix = ? AND course_number = ?
            """, (prefix, number))

            if cursor.fetchone()[0] > 0:
                self.logger.log_operation(
                    OperationType.ERROR,
                    "Attempted to remove course with existing enrollments",
                    {"course": f"{prefix} {number}"}
                )
                QMessageBox.warning(self, "Error", "Cannot remove course with existing enrollments")
                return

            reply = QMessageBox.question(
                self,
                "Confirm Removal",
                f"Are you sure you want to remove {prefix} {number}?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                cursor.execute("""
                    DELETE FROM courses
                    WHERE course_prefix = ? AND course_number = ?
                """, (prefix, number))

                conn.commit()

                self.logger.log_operation(
                    OperationType.DELETE,
                    "Successfully removed course",
                    {"course": f"{prefix} {number}"}
                )

                self.load_staff_data()
                QMessageBox.information(self, "Success", "Course removed successfully")

        except sqlite3.Error as e:
            self.logger.log_operation(
                OperationType.ERROR,
                f"Database error while removing course: {str(e)}"
            )
            QMessageBox.warning(self, "Error", "Failed to remove course")
        finally:
            if conn:
                conn.close()

    def delete_course(self, prefix, number):
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'academic_management.db')
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM courses WHERE course_prefix = ? AND course_number = ?", (prefix, number))
            conn.commit()
            QMessageBox.information(self, "Success", "Course removed successfully.")
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            QMessageBox.warning(self, "Error", "Failed to remove course.")
        finally:
            if conn:
                conn.close()

    def modify_course(self):
        """Modify an existing course"""
        selected_items = self.catalog_table.selectedItems()
        if not selected_items:
            self.logger.log_operation(
                OperationType.ERROR,
                "Attempted to modify course without selection"
            )
            QMessageBox.warning(self, "No Selection", "Please select a course to modify")
            return

        row = selected_items[0].row()
        prefix = self.catalog_table.item(row, 0).text()
        number = self.catalog_table.item(row, 1).text()
        credits = self.catalog_table.item(row, 2).text()

        # Log access to course data
        self.logger.log_data_access(
            "courses",
            "retrieving course for modification",
            {"course": f"{prefix} {number}", "current_credits": credits}
        )

        dialog = QDialog(self)
        dialog.setWindowTitle("Modify Course")
        layout = QFormLayout(dialog)

        # Course prefix (read-only)
        prefix_input = QLineEdit(prefix)
        prefix_input.setReadOnly(True)
        layout.addRow("Course Prefix:", prefix_input)

        # Course number (read-only as well to prevent inconsistencies)
        number_input = QLineEdit(number)
        number_input.setReadOnly(True)
        layout.addRow("Course Number:", number_input)

        # Credits can be modified
        credits_input = QLineEdit(credits)
        layout.addRow("Credits:", credits_input)

        buttons = QHBoxLayout()
        save_button = QPushButton("Save")
        cancel_button = QPushButton("Cancel")
        buttons.addWidget(save_button)
        buttons.addWidget(cancel_button)
        layout.addRow(buttons)

        save_button.clicked.connect(dialog.accept)
        cancel_button.clicked.connect(dialog.reject)

        if dialog.exec_():
            try:
                new_credits = int(credits_input.text().strip())
                if new_credits < 1 or new_credits > 4:
                    self.logger.log_operation(
                        OperationType.ERROR,
                        "Invalid credits value",
                        {"credits": new_credits}
                    )
                    QMessageBox.warning(self, "Error", "Credits must be between 1 and 4")
                    return

                conn = sqlite3.connect(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                    '..', 'data', 'academic_management.db'))
                cursor = conn.cursor()

                # Log the modification
                self.logger.log_operation(
                    OperationType.MODIFY,
                    "Modified course - modifying course details",
                    {
                        "before": {"prefix": prefix, "number": number, "credits": credits},
                        "after": {"prefix": prefix, "number": number, "credits": str(new_credits)}
                    }
                )

                cursor.execute("""
                    UPDATE courses 
                    SET credits = ?
                    WHERE course_prefix = ? AND course_number = ?
                """, (new_credits, prefix, number))

                conn.commit()
                self.load_staff_data()
                QMessageBox.information(self, "Success", "Course updated successfully")

            except ValueError:
                self.logger.log_operation(
                    OperationType.ERROR,
                    "Invalid credits format",
                    {"value": credits_input.text().strip()}
                )
                QMessageBox.warning(self, "Error", "Credits must be a number")
            except sqlite3.Error as e:
                self.logger.log_operation(
                    OperationType.ERROR,
                    f"Database error while modifying course: {str(e)}"
                )
                QMessageBox.warning(self, "Error", "Failed to update course")
            finally:
                if conn:
                    conn.close()


    def update_course(self, old_prefix, old_number, new_prefix, new_number, new_credits):
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'academic_management.db')
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE courses 
                SET course_prefix = ?, course_number = ?, credits = ?
                WHERE course_prefix = ? AND course_number = ?
            """, (new_prefix, new_number, new_credits, old_prefix, old_number))
            conn.commit()
            QMessageBox.information(self, "Success", "Course updated successfully.")
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            QMessageBox.warning(self, "Error", "Failed to update course.")
        finally:
            if conn:
                conn.close()

    def assign_instructor_to_course(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Assign Instructor to Course")
        layout = QFormLayout(dialog)

        instructor_combo = QComboBox()
        course_combo = QComboBox()

        try:
            # Load instructors and courses
            conn = sqlite3.connect(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                '..', 'data', 'academic_management.db'))
            cursor = conn.cursor()

            # Log data access for loading instructors
            self.logger.log_data_access(
                "instructors",
                "retrieving department instructors for assignment",
                {"department_id": self.department_id}
            )

            cursor.execute("""
                SELECT instructor_id 
                FROM instructors 
                WHERE department_id = ?
            """, (self.department_id,))

            instructors = cursor.fetchall()
            for instructor in instructors:
                instructor_combo.addItem(instructor[0])

            # Log data access for loading courses
            self.logger.log_data_access(
                "courses",
                "retrieving department courses for assignment",
                {"department_id": self.department_id}
            )

            cursor.execute("""
                SELECT course_prefix, course_number 
                FROM courses 
                WHERE course_prefix = ?
            """, (self.department_id,))

            courses = cursor.fetchall()
            for course in courses:
                course_combo.addItem(f"{course[0]} {course[1]}")

        except sqlite3.Error as e:
            self.logger.log_operation(
                OperationType.ERROR,
                f"Error loading data for instructor assignment: {str(e)}"
            )
            QMessageBox.warning(self, "Error", "Failed to load instructor/course data.")
            return
        finally:
            if conn:
                conn.close()

        layout.addRow("Instructor:", instructor_combo)
        layout.addRow("Course:", course_combo)

        buttons = QHBoxLayout()
        assign_button = QPushButton("Assign")
        cancel_button = QPushButton("Cancel")
        buttons.addWidget(assign_button)
        buttons.addWidget(cancel_button)
        layout.addRow(buttons)

        assign_button.clicked.connect(dialog.accept)
        cancel_button.clicked.connect(dialog.reject)

        if dialog.exec_():
            instructor_id = instructor_combo.currentText()
            course = course_combo.currentText().split()
            course_prefix = course[0]
            course_number = course[1]

            try:
                conn = sqlite3.connect(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                    '..', 'data', 'academic_management.db'))
                cursor = conn.cursor()

                # Check instructor credit hours
                self.logger.log_data_access(
                    "instructor_courses",
                    "checking instructor credit load",
                    {"instructor_id": instructor_id}
                )

                cursor.execute("""
                    SELECT SUM(c.credits)
                    FROM instructor_courses ic
                    JOIN courses c ON ic.course_prefix = c.course_prefix 
                        AND ic.course_number = c.course_number
                    WHERE ic.instructor_id = ?
                """, (instructor_id,))

                current_credits = cursor.fetchone()[0] or 0
                new_course_credits = int(self.courses_table.item(
                    course_combo.currentIndex(), 2).text())

                if current_credits + new_course_credits > 12:
                    self.logger.log_operation(
                        OperationType.ERROR,
                        "Instructor credit hour limit exceeded",
                        {
                            "instructor_id": instructor_id,
                            "current_credits": current_credits,
                            "attempted_add_credits": new_course_credits
                        }
                    )
                    QMessageBox.warning(self, "Error",
                                        "Instructor cannot exceed 12 credit hours per semester.")
                    return

                # Log the assignment attempt
                self.logger.log_operation(
                    OperationType.ADD,
                    "Assigning instructor to course",
                    {
                        "instructor_id": instructor_id,
                        "course": f"{course_prefix} {course_number}"
                    }
                )

                cursor.execute("""
                    INSERT INTO instructor_courses (instructor_id, course_prefix, course_number)
                    VALUES (?, ?, ?)
                """, (instructor_id, course_prefix, course_number))

                conn.commit()

                self.logger.log_operation(
                    OperationType.ADD,
                    "Successfully assigned instructor to course",
                    {
                        "instructor_id": instructor_id,
                        "course": f"{course_prefix} {course_number}"
                    }
                )

                QMessageBox.information(self, "Success",
                                        "Instructor assigned to course successfully.")

            except sqlite3.Error as e:
                self.logger.log_operation(
                    OperationType.ERROR,
                    f"Database error while assigning instructor: {str(e)}",
                    {
                        "instructor_id": instructor_id,
                        "course": f"{course_prefix} {course_number}"
                    }
                )
                QMessageBox.warning(self, "Error", "Failed to assign instructor to course.")
            finally:
                if conn:
                    conn.close()

    def save_instructor_course_assignment(self, instructor_id, course_prefix, course_number):
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'academic_management.db')
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO instructor_courses (instructor_id, course_prefix, course_number)
                VALUES (?, ?, ?)
            """, (instructor_id, course_prefix, course_number))
            conn.commit()
            QMessageBox.information(self, "Success", "Instructor assigned to course successfully.")
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            QMessageBox.warning(self, "Error", "Failed to assign instructor to course.")
        finally:
            if conn:
                conn.close()

    def modify_instructor(self):
        selected_items = self.instructors_table.selectedItems()
        if not selected_items:
            self.logger.log_operation(
                OperationType.ERROR,
                "Attempted to modify instructor without selection"
            )
            QMessageBox.warning(self, "No Selection", "Please select an instructor to modify.")
            return

        row = selected_items[0].row()
        instructor_id = self.instructors_table.item(row, 0).text()
        old_phone = self.instructors_table.item(row, 1).text()
        old_hired_semester = self.instructors_table.item(row, 2).text()

        # Log data access
        self.logger.log_data_access(
            "instructors",
            "retrieving instructor details for modification",
            {
                "instructor_id": instructor_id,
                "department_id": self.department_id
            }
        )

        dialog = QDialog(self)
        dialog.setWindowTitle("Modify Instructor")
        layout = QFormLayout(dialog)

        phone_input = QLineEdit(old_phone)
        hired_semester_input = QLineEdit(old_hired_semester)

        layout.addRow("Phone:", phone_input)
        layout.addRow("Hired Semester:", hired_semester_input)

        buttons = QHBoxLayout()
        save_button = QPushButton("Save")
        cancel_button = QPushButton("Cancel")
        buttons.addWidget(save_button)
        buttons.addWidget(cancel_button)
        layout.addRow(buttons)

        save_button.clicked.connect(dialog.accept)
        cancel_button.clicked.connect(dialog.reject)

        if dialog.exec_():
            new_phone = phone_input.text()
            new_hired_semester = hired_semester_input.text()

            try:
                conn = sqlite3.connect(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                    '..', 'data', 'academic_management.db'))
                cursor = conn.cursor()

                # Log modification attempt
                self.logger.log_data_modification(
                    "instructor",
                    "modifying instructor details",
                    before={
                        "instructor_id": instructor_id,
                        "phone": old_phone,
                        "hired_semester": old_hired_semester
                    },
                    after={
                        "instructor_id": instructor_id,
                        "phone": new_phone,
                        "hired_semester": new_hired_semester
                    }
                )

                cursor.execute("""
                    UPDATE instructors 
                    SET phone = ?, hired_semester = ?
                    WHERE instructor_id = ? AND department_id = ?
                """, (new_phone, new_hired_semester, instructor_id, self.department_id))

                conn.commit()

                self.logger.log_operation(
                    OperationType.MODIFY,
                    "Successfully modified instructor",
                    {"instructor_id": instructor_id}
                )

                self.load_staff_data()
                QMessageBox.information(self, "Success", "Instructor updated successfully.")

            except sqlite3.Error as e:
                self.logger.log_operation(
                    OperationType.ERROR,
                    f"Database error while modifying instructor: {str(e)}",
                    {"instructor_id": instructor_id}
                )
                QMessageBox.warning(self, "Error", "Failed to update instructor.")
            finally:
                if conn:
                    conn.close()

    def update_instructor(self, instructor_id, new_phone, new_hired_semester):
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'academic_management.db')
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE instructors 
                SET phone = ?, hired_semester = ?
                WHERE instructor_id = ?
            """, (new_phone, new_hired_semester, instructor_id))
            conn.commit()
            QMessageBox.information(self, "Success", "Instructor updated successfully.")
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            QMessageBox.warning(self, "Error", "Failed to update instructor.")
        finally:
            if conn:
                conn.close()

    def modify_student(self):
        selected_items = self.students_table.selectedItems()
        if not selected_items:
            self.logger.log_operation(
                OperationType.ERROR,
                "Attempted to modify student without selection"
            )
            QMessageBox.warning(self, "No Selection", "Please select a student to modify.")
            return

        row = selected_items[0].row()
        student_id = self.students_table.item(row, 0).text()
        old_gender = self.students_table.item(row, 1).text()
        old_major = self.students_table.item(row, 2).text()

        # Log data access
        self.logger.log_data_access(
            "students",
            "retrieving student details for modification",
            {"student_id": student_id}
        )

        # Verify student's major belongs to staff's department
        try:
            conn = sqlite3.connect(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                '..', 'data', 'academic_management.db'))
            cursor = conn.cursor()

            cursor.execute("""
                SELECT COUNT(*)
                FROM department_majors
                WHERE department_id = ? AND major_name = ?
            """, (self.department_id, old_major))

            if cursor.fetchone()[0] == 0:
                self.logger.log_operation(
                    OperationType.ERROR,
                    "Attempted to modify student from different department",
                    {
                        "student_id": student_id,
                        "major": old_major,
                        "staff_department": self.department_id
                    }
                )
                QMessageBox.warning(self, "Error",
                                    "Cannot modify student from different department.")
                return

            dialog = QDialog(self)
            dialog.setWindowTitle("Modify Student")
            layout = QFormLayout(dialog)

            gender_input = QLineEdit(old_gender)
            major_input = QLineEdit(old_major)

            layout.addRow("Gender:", gender_input)
            layout.addRow("Major:", major_input)

            buttons = QHBoxLayout()
            save_button = QPushButton("Save")
            cancel_button = QPushButton("Cancel")
            buttons.addWidget(save_button)
            buttons.addWidget(cancel_button)
            layout.addRow(buttons)

            save_button.clicked.connect(dialog.accept)
            cancel_button.clicked.connect(dialog.reject)

            if dialog.exec_():
                new_gender = gender_input.text()
                new_major = major_input.text()

                # Validate new major belongs to department
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM department_majors
                    WHERE department_id = ? AND major_name = ?
                """, (self.department_id, new_major))

                if cursor.fetchone()[0] == 0:
                    self.logger.log_operation(
                        OperationType.ERROR,
                        "Attempted to assign invalid major",
                        {
                            "student_id": student_id,
                            "invalid_major": new_major,
                            "department_id": self.department_id
                        }
                    )
                    QMessageBox.warning(self, "Error",
                                        "New major must belong to your department.")
                    return

                # Log modification attempt
                self.logger.log_data_modification(
                    "student",
                    "modifying student details",
                    before={
                        "student_id": student_id,
                        "gender": old_gender,
                        "major": old_major
                    },
                    after={
                        "student_id": student_id,
                        "gender": new_gender,
                        "major": new_major
                    }
                )

                cursor.execute("""
                    UPDATE students 
                    SET gender = ?, major = ?
                    WHERE student_id = ?
                """, (new_gender, new_major, student_id))

                conn.commit()

                self.logger.log_operation(
                    OperationType.MODIFY,
                    "Successfully modified student",
                    {"student_id": student_id}
                )

                self.load_staff_data()
                QMessageBox.information(self, "Success", "Student updated successfully.")

        except sqlite3.Error as e:
            self.logger.log_operation(
                OperationType.ERROR,
                f"Database error while modifying student: {str(e)}",
                {"student_id": student_id}
            )
            QMessageBox.warning(self, "Error", "Failed to update student.")
        finally:
            if conn:
                conn.close()

    def update_student(self, student_id, new_gender, new_major):
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'academic_management.db')
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE students 
                SET gender = ?, major = ?
                WHERE student_id = ?
            """, (new_gender, new_major, student_id))
            conn.commit()
            QMessageBox.information(self, "Success", "Student updated successfully.")
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            QMessageBox.warning(self, "Error", "Failed to update student.")
        finally:
            if conn:
                conn.close()

    def load_department_info(self):
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'academic_management.db')
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Load department info
            cursor.execute("""
                SELECT d.department_id, d.building, d.office
                FROM departments d
                WHERE d.department_id = ?
            """, (self.department_id,))
            department_info = cursor.fetchone()
            if department_info:
                self.department_info_label.setText(f"Department ID: {department_info[0]}\n"
                                                   f"Building: {department_info[1]}\n"
                                                   f"Office: {department_info[2]}")
            else:
                self.department_info_label.setText("No department information available.")

            # Load department majors
            cursor.execute("""
                SELECT major_name, hours_req
                FROM department_majors
                WHERE department_id = ?
            """, (self.department_id,))
            majors = cursor.fetchall()

            self.department_majors_table.setColumnCount(2)
            self.department_majors_table.setHorizontalHeaderLabels(["Major", "Required Hours"])
            self.department_majors_table.setRowCount(len(majors))
            for row, major in enumerate(majors):
                self.department_majors_table.setItem(row, 0, QTableWidgetItem(major[0]))
                self.department_majors_table.setItem(row, 1, QTableWidgetItem(str(major[1])))

        except sqlite3.Error as e:
            print(f"Database error: {e}")
        finally:
            if conn:
                conn.close()

    def modify_department(self):
        try:
            conn = sqlite3.connect(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                '..', 'data', 'academic_management.db'))
            cursor = conn.cursor()

            # Get current department info
            cursor.execute("""
                SELECT building, office
                FROM departments
                WHERE department_id = ?
            """, (self.department_id,))

            result = cursor.fetchone()
            if not result:
                self.logger.log_operation(
                    OperationType.ERROR,
                    "Department not found",
                    {"department_id": self.department_id}
                )
                QMessageBox.warning(self, "Error", "Department information not found.")
                return

            old_building, old_office = result

            # Log data access
            self.logger.log_data_access(
                "departments",
                "retrieving department details for modification",
                {
                    "department_id": self.department_id,
                    "current_building": old_building,
                    "current_office": old_office
                }
            )

            dialog = QDialog(self)
            dialog.setWindowTitle("Modify Department")
            layout = QFormLayout(dialog)

            building_input = QLineEdit(old_building)
            office_input = QLineEdit(old_office)

            layout.addRow("Building:", building_input)
            layout.addRow("Office:", office_input)

            buttons = QHBoxLayout()
            save_button = QPushButton("Save")
            cancel_button = QPushButton("Cancel")
            buttons.addWidget(save_button)
            buttons.addWidget(cancel_button)
            layout.addRow(buttons)

            save_button.clicked.connect(dialog.accept)
            cancel_button.clicked.connect(dialog.reject)

            if dialog.exec_():
                new_building = building_input.text()
                new_office = office_input.text()

                # Log modification attempt
                self.logger.log_data_modification(
                    "department",
                    "modifying department details",
                    before={
                        "department_id": self.department_id,
                        "building": old_building,
                        "office": old_office
                    },
                    after={
                        "department_id": self.department_id,
                        "building": new_building,
                        "office": new_office
                    }
                )

                cursor.execute("""
                    UPDATE departments 
                    SET building = ?, office = ?
                    WHERE department_id = ?
                """, (new_building, new_office, self.department_id))

                conn.commit()

                self.logger.log_operation(
                    OperationType.MODIFY,
                    "Successfully modified department",
                    {"department_id": self.department_id}
                )

                self.load_department_info()
                QMessageBox.information(self, "Success", "Department updated successfully.")

        except sqlite3.Error as e:
            self.logger.log_operation(
                OperationType.ERROR,
                f"Database error while modifying department: {str(e)}",
                {"department_id": self.department_id}
            )
            QMessageBox.warning(self, "Error", "Failed to update department.")
        finally:
            if conn:
                conn.close()

    def update_department(self, new_building, new_office):
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'academic_management.db')
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE departments 
                SET building = ?, office = ?
                WHERE department_id = ?
            """, (new_building, new_office, self.department_id))
            conn.commit()
            QMessageBox.information(self, "Success", "Department updated successfully.")
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            QMessageBox.warning(self, "Error", "Failed to update department.")
        finally:
            if conn:
                conn.close()


    def log_operation(self, operation_type, details):
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'academic_management.db')
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
                INSERT INTO operation_logs (timestamp, user_id, operation_type, details)
                VALUES (?, ?, ?, ?)
            """, (timestamp, self.user_id, operation_type, details))
            conn.commit()
        except sqlite3.Error as e:
            print(f"Database error while logging operation: {e}")
        finally:
            if conn:
                conn.close()

    def setup_course_management_ui(self):
        """Add course management button to courses tab"""
        # Find the existing course_buttons_layout in your courses tab
        self.manage_courses_button = QPushButton("Manage Courses")
        self.manage_courses_button.clicked.connect(self.show_course_management)
        course_buttons_layout.addWidget(self.manage_courses_button)

    def show_course_management(self):
        """Show the course management dialog"""
        dialog = CourseManagementDialog(self)
        dialog.exec_()

    def get_current_and_future_semesters(self):
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

    def load_semester_courses(self):
        """Load courses for the selected semester"""
        semester_data = self.semester_selector.currentData()
        if not semester_data:
            return

        semester, year = semester_data
        try:
            conn = sqlite3.connect(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                '..', 'data', 'academic_management.db'))
            cursor = conn.cursor()

            # Log the data access
            self.logger.log_data_access(
                "instructor_courses",
                "retrieving semester course schedule",
                {
                    "semester": semester,
                    "year": year,
                    "department": self.department_id
                }
            )

            # Modified query to correctly join with department_course_prefixes
            cursor.execute("""
                SELECT 
                    c.course_prefix || ' ' || c.course_number as course,
                    c.credits,
                    COALESCE(i.instructor_id, 'TBA') as instructor,
                    CASE 
                        WHEN ic.instructor_id IS NULL THEN 'Unassigned'
                        ELSE 'Assigned'
                    END as status
                FROM instructor_courses ic
                JOIN courses c ON ic.course_prefix = c.course_prefix 
                    AND ic.course_number = c.course_number
                JOIN department_course_prefixes dcp ON c.course_prefix = dcp.course_prefix
                LEFT JOIN instructors i ON ic.instructor_id = i.instructor_id
                WHERE dcp.department_id = ?
                    AND ic.semester = ? 
                    AND ic.year_taught = ?
                ORDER BY c.course_prefix, c.course_number
            """, (self.department_id, semester, year))

            courses = cursor.fetchall()

            # Debug print
            print(f"Found {len(courses)} courses for {semester} {year} in department {self.department_id}")

            self.semester_courses_table.setRowCount(len(courses))
            for row, course in enumerate(courses):
                for col, value in enumerate(course):
                    item = QTableWidgetItem(str(value))
                    item.setTextAlignment(Qt.AlignCenter)
                    self.semester_courses_table.setItem(row, col, item)

            self.semester_courses_table.resizeColumnsToContents()

        except sqlite3.Error as e:
            error_msg = f"Failed to load semester courses: {str(e)}"
            self.logger.log_operation(
                "error",
                error_msg
            )
            print(error_msg)  # Debug print
            QMessageBox.warning(self, "Error", "Failed to load semester courses")
        finally:
            if conn:
                conn.close()

    def add_to_schedule(self):
        """Add a course to the semester schedule"""
        # Create the dialog with a reference to the current semester
        current_semester_data = self.semester_selector.currentData()
        dialog = CourseManagementDialog(self, current_semester_data)
        # Connect the signal before showing the dialog
        dialog.course_scheduled.connect(self.load_semester_courses)
        dialog.exec_()

    def remove_from_schedule(self):
        """Remove a course from the semester schedule"""
        selected_items = self.semester_courses_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select a course to remove from schedule.")
            return

        row = selected_items[0].row()
        course = self.semester_courses_table.item(row, 0).text()
        semester_data = self.semester_selector.currentData()

        if not semester_data:
            return

        semester, year = semester_data

        reply = QMessageBox.question(
            self,
            "Confirm Removal",
            f"Are you sure you want to remove {course} from {semester} {year}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                course_prefix, course_number = course.split()
                conn = sqlite3.connect(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                    '..', 'data', 'academic_management.db'))
                cursor = conn.cursor()

                cursor.execute("""
                    DELETE FROM instructor_courses 
                    WHERE course_prefix = ? 
                    AND course_number = ? 
                    AND semester = ? 
                    AND year_taught = ?
                """, (course_prefix, course_number, semester, year))

                conn.commit()

                self.logger.log_operation(
                    "delete",
                    f"Removed course {course} from schedule ({semester} {year})"
                )

                self.load_semester_courses()
                QMessageBox.information(self, "Success", "Course removed from schedule successfully.")

            except sqlite3.Error as e:
                self.logger.log_operation(
                    "error",
                    f"Failed to remove course from schedule: {str(e)}"
                )
                QMessageBox.warning(self, "Error", "Failed to remove course from schedule")
            finally:
                if conn:
                    conn.close()

    def modify_schedule(self):
        """Modify a scheduled course (e.g., change instructor)"""
        selected_items = self.semester_courses_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select a course to modify.")
            return

        # Create and show the modification dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Modify Course Schedule")
        layout = QFormLayout(dialog)

        row = selected_items[0].row()
        course = self.semester_courses_table.item(row, 0).text()
        current_instructor = self.semester_courses_table.item(row, 2).text()

        # Create instructor selection combo box
        instructor_combo = QComboBox()
        instructor_combo.addItem("TBA", None)

        try:
            conn = sqlite3.connect(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                '..', 'data', 'academic_management.db'))
            cursor = conn.cursor()

            cursor.execute("""
                SELECT instructor_id
                FROM instructors
                WHERE department_id = ?
                ORDER BY instructor_id
            """, (self.department_id,))

            instructors = cursor.fetchall()
            for instructor in instructors:
                instructor_combo.addItem(str(instructor[0]), instructor[0])
                if str(instructor[0]) == current_instructor:
                    instructor_combo.setCurrentText(current_instructor)

        except sqlite3.Error as e:
            self.logger.log_operation(
                "error",
                f"Failed to load instructors: {str(e)}"
            )
        finally:
            if conn:
                conn.close()

        layout.addRow("Course:", QLabel(course))
        layout.addRow("Instructor:", instructor_combo)

        buttons = QHBoxLayout()
        save_button = QPushButton("Save")
        cancel_button = QPushButton("Cancel")
        buttons.addWidget(save_button)
        buttons.addWidget(cancel_button)
        layout.addRow(buttons)

        save_button.clicked.connect(dialog.accept)
        cancel_button.clicked.connect(dialog.reject)

        if dialog.exec_():
            try:
                course_prefix, course_number = course.split()
                semester_data = self.semester_selector.currentData()
                if not semester_data:
                    return

                semester, year = semester_data
                new_instructor = instructor_combo.currentData()

                conn = sqlite3.connect(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                    '..', 'data', 'academic_management.db'))
                cursor = conn.cursor()

                cursor.execute("""
                    UPDATE instructor_courses 
                    SET instructor_id = ?
                    WHERE course_prefix = ? 
                    AND course_number = ? 
                    AND semester = ? 
                    AND year_taught = ?
                """, (new_instructor, course_prefix, course_number, semester, year))

                conn.commit()

                self.logger.log_operation(
                    "modify",
                    f"Updated instructor for {course} to {new_instructor or 'TBA'}"
                )

                self.load_semester_courses()
                QMessageBox.information(self, "Success", "Schedule updated successfully.")

            except sqlite3.Error as e:
                self.logger.log_operation(
                    "error",
                    f"Failed to update course schedule: {str(e)}"
                )
                QMessageBox.warning(self, "Error", "Failed to update schedule")
            finally:
                if conn:
                    conn.close()

    def logout(self):
        """Handle staff logout"""
        self.logger.log_session(OperationType.LOGOUT)
        self.logout_signal.emit()
        self.close()

    def closeEvent(self, event):
        """Override closeEvent to log when staff exits the system"""
        self.logger.log_operation(
            "exit",
            "Staff member exited the system",
            include_role_prefix=False
        )
        event.accept()