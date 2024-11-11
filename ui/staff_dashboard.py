import sys
import os
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QPushButton, QTableWidget, QTableWidgetItem,
                               QTabWidget, QComboBox, QMessageBox, QLineEdit, QFormLayout, QDialog)
from PySide6.QtCore import Qt, Signal
import sqlite3
from datetime import datetime
from .common.system_logger import SystemLogger, UserRole, OperationType


class StaffDashboard(QMainWindow):
    logout_signal = Signal()

    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.staff_id = self.get_staff_id()
        self.department_id = self.get_department_id()
        print(f"Initializing StaffDashboard with user_id: {self.user_id}, staff_id: {self.staff_id}, department_id: {self.department_id}")
        self.setWindowTitle("Staff Dashboard")
        self.setGeometry(100, 100, 800, 600)
        self.setup_ui()
        self.logger = SystemLogger(self.user_id, UserRole.STAFF)

    def get_staff_id(self):
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'academic_management.db')
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT staff_id FROM staff WHERE user_id = ?", (self.user_id,))
            result = cursor.fetchone()
            return result[0] if result else None
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def get_department_id(self):
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'academic_management.db')
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT department_id FROM staff WHERE staff_id = ?", (self.staff_id,))
            result = cursor.fetchone()
            return result[0] if result else None
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

        # Courses Tab
        courses_tab = QWidget()
        courses_layout = QVBoxLayout(courses_tab)
        self.courses_table = QTableWidget()
        courses_layout.addWidget(self.courses_table)
        course_buttons_layout = QHBoxLayout()
        self.add_course_button = QPushButton("Add Course")
        self.add_course_button.clicked.connect(self.add_course)
        course_buttons_layout.addWidget(self.add_course_button)
        self.remove_course_button = QPushButton("Remove Course")
        self.remove_course_button.clicked.connect(self.remove_course)
        course_buttons_layout.addWidget(self.remove_course_button)
        self.modify_course_button = QPushButton("Modify Course")
        self.modify_course_button.clicked.connect(self.modify_course)
        course_buttons_layout.addWidget(self.modify_course_button)
        courses_layout.addLayout(course_buttons_layout)
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
        tab_widget.addTab(instructors_tab, "Instructors")

        # Students Tab
        students_tab = QWidget()
        students_layout = QVBoxLayout(students_tab)
        self.students_table = QTableWidget()
        students_layout.addWidget(self.students_table)
        self.modify_student_button = QPushButton("Modify Student")
        self.modify_student_button.clicked.connect(self.modify_student)
        students_layout.addWidget(self.modify_student_button)
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
        tab_widget.addTab(department_tab, "Department Info")

        self.load_staff_data()

    def load_staff_data(self):
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'academic_management.db')
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Load courses
            cursor.execute("""
                SELECT c.course_prefix, c.course_number, c.credits
                FROM courses c
                WHERE c.course_prefix = ?
            """, (self.department_id,))
            courses = cursor.fetchall()
            self.courses_table.setColumnCount(3)
            self.courses_table.setHorizontalHeaderLabels(["Prefix", "Number", "Credits"])
            self.courses_table.setRowCount(len(courses))
            for row, course in enumerate(courses):
                for col, value in enumerate(course):
                    self.courses_table.setItem(row, col, QTableWidgetItem(str(value)))

            # Load instructors
            cursor.execute("""
                SELECT i.instructor_id, i.phone, i.hired_semester
                FROM instructors i
                WHERE i.department_id = ?
            """, (self.department_id,))
            instructors = cursor.fetchall()
            self.instructors_table.setColumnCount(3)
            self.instructors_table.setHorizontalHeaderLabels(["Instructor ID", "Phone", "Hired Semester"])
            self.instructors_table.setRowCount(len(instructors))
            for row, instructor in enumerate(instructors):
                for col, value in enumerate(instructor):
                    self.instructors_table.setItem(row, col, QTableWidgetItem(str(value)))

            # Load students
            cursor.execute("""
                SELECT s.student_id, s.gender, s.major
                FROM students s
                JOIN department_majors dm ON s.major = dm.major_name
                WHERE dm.department_id = ?
            """, (self.department_id,))
            students = cursor.fetchall()
            self.students_table.setColumnCount(3)
            self.students_table.setHorizontalHeaderLabels(["Student ID", "Gender", "Major"])
            self.students_table.setRowCount(len(students))
            for row, student in enumerate(students):
                for col, value in enumerate(student):
                    self.students_table.setItem(row, col, QTableWidgetItem(str(value)))

        except sqlite3.Error as e:
            print(f"Database error: {e}")
        finally:
            if conn:
                conn.close()

        # Load department info
        self.load_department_info()

    def add_course(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Course")
        layout = QFormLayout(dialog)

        prefix_input = QLineEdit(self.department_id)
        prefix_input.setReadOnly(True)
        number_input = QLineEdit()
        credits_input = QLineEdit()

        layout.addRow("Course Prefix:", prefix_input)
        layout.addRow("Course Number:", number_input)
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
            prefix = prefix_input.text()
            number = number_input.text()
            credits = credits_input.text()

            if self.is_duplicate_course(prefix, number):
                QMessageBox.warning(self, "Duplicate Course", "This course already exists.")
                return

            self.save_course(prefix, number, credits)
            self.log_operation("add_course", f"Added course {prefix} {number}")
            self.load_staff_data()

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
        selected_items = self.courses_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select a course to remove.")
            return

        row = selected_items[0].row()
        prefix = self.courses_table.item(row, 0).text()
        number = self.courses_table.item(row, 1).text()

        reply = QMessageBox.question(self, "Confirm Removal", f"Are you sure you want to remove {prefix} {number}?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.delete_course(prefix, number)
            self.log_operation("remove_course", f"Removed course {prefix} {number}")
            self.load_staff_data()

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
        selected_items = self.courses_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select a course to modify.")
            return

        row = selected_items[0].row()
        old_prefix = self.courses_table.item(row, 0).text()
        old_number = self.courses_table.item(row, 1).text()
        old_credits = self.courses_table.item(row, 2).text()

        dialog = QDialog(self)
        dialog.setWindowTitle("Modify Course")
        layout = QFormLayout(dialog)

        prefix_input = QLineEdit(old_prefix)
        prefix_input.setReadOnly(True)
        number_input = QLineEdit(old_number)
        credits_input = QLineEdit(old_credits)

        layout.addRow("Course Prefix:", prefix_input)
        layout.addRow("Course Number:", number_input)
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
            new_prefix = prefix_input.text()
            new_number = number_input.text()
            new_credits = credits_input.text()

            if (new_prefix != old_prefix or new_number != old_number) and self.is_duplicate_course(new_prefix,
                                                                                                   new_number):
                QMessageBox.warning(self, "Duplicate Course", "A course with this prefix and number already exists.")
                return

            self.update_course(old_prefix, old_number, new_prefix, new_number, new_credits)
            self.log_operation("modify_course",
                               f"Modified course from {old_prefix} {old_number} to {new_prefix} {new_number}")
            self.load_staff_data()

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

        # Populate instructor combo box
        for row in range(self.instructors_table.rowCount()):
            instructor_id = self.instructors_table.item(row, 0).text()
            instructor_combo.addItem(instructor_id)

        # Populate course combo box
        for row in range(self.courses_table.rowCount()):
            prefix = self.courses_table.item(row, 0).text()
            number = self.courses_table.item(row, 1).text()
            course_combo.addItem(f"{prefix} {number}")

        layout.addRow("Instructor:", instructor_combo)
        layout.addRow("Course:", course_combo)

        buttons = QHBoxLayout()
        save_button = QPushButton("Assign")
        cancel_button = QPushButton("Cancel")
        buttons.addWidget(save_button)
        buttons.addWidget(cancel_button)
        layout.addRow(buttons)

        save_button.clicked.connect(dialog.accept)
        cancel_button.clicked.connect(dialog.reject)

        if dialog.exec_():
            instructor_id = instructor_combo.currentText()
            course = course_combo.currentText().split()
            course_prefix = course[0]
            course_number = course[1]

            self.save_instructor_course_assignment(instructor_id, course_prefix, course_number)
            self.log_operation("assign_instructor",
                               f"Assigned instructor {instructor_id} to course {course_prefix} {course_number}")

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
            QMessageBox.warning(self, "No Selection", "Please select an instructor to modify.")
            return

        row = selected_items[0].row()
        instructor_id = self.instructors_table.item(row, 0).text()
        old_phone = self.instructors_table.item(row, 1).text()
        old_hired_semester = self.instructors_table.item(row, 2).text()

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

            self.update_instructor(instructor_id, new_phone, new_hired_semester)
            self.log_operation("modify_instructor", f"Modified instructor {instructor_id}")
            self.load_staff_data()

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
            QMessageBox.warning(self, "No Selection", "Please select a student to modify.")
            return

        row = selected_items[0].row()
        student_id = self.students_table.item(row, 0).text()
        old_gender = self.students_table.item(row, 1).text()
        old_major = self.students_table.item(row, 2).text()

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

            self.update_student(student_id, new_gender, new_major)
            self.log_operation("modify_student", f"Modified student {student_id}")
            self.load_staff_data()

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
        dialog = QDialog(self)
        dialog.setWindowTitle("Modify Department")
        layout = QFormLayout(dialog)

        building_input = QLineEdit()
        office_input = QLineEdit()

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

            self.update_department(new_building, new_office)
            self.log_operation("modify_department", f"Modified department {self.department_id}")
            self.load_department_info()

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

    def logout(self):
        self.logout_signal.emit()
        self.close()