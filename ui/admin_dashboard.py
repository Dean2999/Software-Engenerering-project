import sys
import os
from datetime import datetime
import sqlite3
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QPushButton, QTableWidget, QTableWidgetItem,
                               QComboBox, QMessageBox, QDateEdit, QHeaderView, QTabWidget)
from PySide6.QtCore import Qt, Signal
from ui.common.system_logger import SystemLogger, UserRole, OperationType


class AdminDashboard(QMainWindow):
    logout_signal = Signal()

    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        print(f"Initializing AdminDashboard with user_id: {self.user_id}")
        self.setWindowTitle("System Administrator Dashboard")
        self.setGeometry(100, 100, 1000, 800)  # Made window larger for reports

        # Initialize the universal logger
        self.logger = SystemLogger(self.user_id, UserRole.ADMIN)

        self.setup_ui()
        self.logger.log_session(OperationType.LOGIN)

    def load_logs(self):
        """Load system logs into the logs table"""
        try:
            conn = sqlite3.connect(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                              '..', 'data', 'academic_management.db'))
            cursor = conn.cursor()

            # Log the data access
            self.logger.log_data_access(
                "logs",
                "viewed all system logs"
            )

            cursor.execute("""
                SELECT timestamp, user_id, operation_type, details
                FROM operation_logs
                ORDER BY timestamp DESC
            """)

            logs = cursor.fetchall()
            self.logs_table.setRowCount(len(logs))

            for row, log in enumerate(logs):
                timestamp = QTableWidgetItem(log[0])
                user_id = QTableWidgetItem(str(log[1]))
                operation = QTableWidgetItem(log[2])
                details = QTableWidgetItem(log[3])

                # Get user role from operation type
                role = log[2].split('_')[0] if '_' in log[2] else 'Unknown'
                role_item = QTableWidgetItem(role)

                self.logs_table.setItem(row, 0, timestamp)
                self.logs_table.setItem(row, 1, user_id)
                self.logs_table.setItem(row, 2, role_item)
                self.logs_table.setItem(row, 3, operation)
                self.logs_table.setItem(row, 4, details)

            # Update user ID filter options
            self.update_user_filter_options()

        except sqlite3.Error as e:
            self.logger.log_operation(
                OperationType.ERROR,
                f"Failed to load logs: {str(e)}"
            )
            QMessageBox.critical(self, "Error", "Failed to load system logs")
        finally:
            if conn:
                conn.close()

    def update_user_filter_options(self):
        """Update the user ID filter combo box with available options"""
        user_ids = set()
        for row in range(self.logs_table.rowCount()):
            user_id = self.logs_table.item(row, 1).text()
            user_ids.add(user_id)

        current_text = self.user_id_input.currentText()
        self.user_id_input.clear()
        self.user_id_input.addItems(sorted(user_ids))
        if current_text:
            index = self.user_id_input.findText(current_text)
            if index >= 0:
                self.user_id_input.setCurrentIndex(index)

    def confirm_clear_logs(self):
        """Show confirmation dialog before clearing logs"""
        reply = QMessageBox.question(
            self,
            'Confirm Clear Logs',
            'Are you sure you want to clear all system logs?\nThis action cannot be undone.',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.clear_logs()

    def clear_logs(self):
        """Clear all system logs"""
        try:
            conn = sqlite3.connect(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                              '..', 'data', 'academic_management.db'))
            cursor = conn.cursor()

            # Begin transaction
            cursor.execute("BEGIN TRANSACTION")

            # Log that we're about to clear the logs
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
                INSERT INTO operation_logs (timestamp, user_id, operation_type, details)
                VALUES (?, ?, ?, ?)
            """, (timestamp, self.user_id, "clear", "Administrator cleared all system logs"))

            # Clear all logs except the one we just added
            cursor.execute("DELETE FROM operation_logs WHERE operation_type != 'clear'")

            # Commit transaction
            conn.commit()

            # Log success using the logger
            self.logger.log_operation(
                OperationType.CLEAR,
                "Administrator cleared all system logs"
            )

            # Reload the logs table
            self.load_logs()
            QMessageBox.information(self, "Success", "System logs have been cleared")

        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            self.logger.log_operation(
                OperationType.ERROR,
                f"Failed to clear logs: {str(e)}"
            )
            QMessageBox.critical(self, "Error", "Failed to clear system logs")
        finally:
            if conn:
                conn.close()


    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Header
        header_layout = QHBoxLayout()
        self.admin_label = QLabel("System Administrator Dashboard")
        self.admin_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(self.admin_label)
        header_layout.addStretch()

        # Clear Logs Button
        self.clear_logs_button = QPushButton("Clear Logs")
        self.clear_logs_button.clicked.connect(self.confirm_clear_logs)
        header_layout.addWidget(self.clear_logs_button)

        # Logout button
        self.logout_button = QPushButton("Logout")
        self.logout_button.clicked.connect(self.logout)
        header_layout.addWidget(self.logout_button)

        # Exit button
        self.exit_button = QPushButton("Exit")
        self.exit_button.clicked.connect(self.close)
        header_layout.addWidget(self.exit_button)

        main_layout.addLayout(header_layout)

        # Create tab widget
        self.tab_widget = QTabWidget()

        # System Logs Tab
        self.setup_system_logs_tab()

        # Academic Performance Tab
        self.setup_academic_performance_tab()

        # Departmental Rankings Tab
        self.setup_departmental_rankings_tab()

        # Course Performance Tab
        self.setup_course_performance_tab()

        # Instructor Demographics Tab
        self.setup_instructor_demographics_tab()

        # Student Rankings Tab
        self.setup_student_rankings_tab()

        main_layout.addWidget(self.tab_widget)

        # Load initial data for all tabs
        self.load_logs()
        self.load_academic_performance()
        self.load_departmental_rankings()
        self.load_course_performance()
        self.load_instructor_demographics()
        self.load_student_rankings()

    def setup_system_logs_tab(self):
        """Setup the system logs tab"""
        logs_tab = QWidget()
        logs_layout = QVBoxLayout(logs_tab)

        # Filter Section
        filter_layout = QHBoxLayout()
        self.filter_type = QComboBox()
        self.filter_type.addItems([
            "All Operations",
            "By Date",
            "By User ID",
            "View Operations",
            "Add Operations",
            "Modify Operations",
            "Delete Operations"
        ])
        self.filter_type.currentTextChanged.connect(self.handle_filter_change)
        filter_layout.addWidget(QLabel("Filter:"))
        filter_layout.addWidget(self.filter_type)

        self.date_picker = QDateEdit()
        self.date_picker.setCalendarPopup(True)
        self.date_picker.setDate(datetime.now().date())
        self.date_picker.dateChanged.connect(self.filter_logs)
        self.date_picker.hide()
        filter_layout.addWidget(self.date_picker)

        self.user_id_input = QComboBox()
        self.user_id_input.setEditable(True)
        self.user_id_input.setMinimumWidth(75)
        self.user_id_input.currentTextChanged.connect(self.filter_logs)
        self.user_id_input.hide()
        filter_layout.addWidget(self.user_id_input)

        filter_layout.addStretch()
        logs_layout.addLayout(filter_layout)

        # Logs Table
        self.logs_table = QTableWidget()
        self.logs_table.setColumnCount(5)
        self.logs_table.setHorizontalHeaderLabels([
            "Timestamp", "User ID", "Role", "Operation", "Details"
        ])
        self.setup_table_properties(self.logs_table)
        logs_layout.addWidget(self.logs_table)

        self.tab_widget.addTab(logs_tab, "System Logs")

    def setup_academic_performance_tab(self):
        """Setup the academic performance analysis tab"""
        performance_tab = QWidget()
        layout = QVBoxLayout(performance_tab)

        # Create table for GPA analysis
        self.performance_table = QTableWidget()
        self.performance_table.setColumnCount(4)
        self.performance_table.setHorizontalHeaderLabels([
            "Major", "Highest GPA", "Lowest GPA", "Average GPA"
        ])
        self.setup_table_properties(self.performance_table)
        layout.addWidget(self.performance_table)

        self.tab_widget.addTab(performance_tab, "Academic Performance")

    def setup_departmental_rankings_tab(self):
        """Setup the departmental rankings tab"""
        rankings_tab = QWidget()
        layout = QVBoxLayout(rankings_tab)

        self.rankings_table = QTableWidget()
        self.rankings_table.setColumnCount(3)
        self.rankings_table.setHorizontalHeaderLabels([
            "Rank", "Department", "Average GPA"
        ])
        self.setup_table_properties(self.rankings_table)
        layout.addWidget(self.rankings_table)

        self.tab_widget.addTab(rankings_tab, "Department Rankings")

    def setup_course_performance_tab(self):
        """Setup the course performance trends tab"""
        trends_tab = QWidget()
        layout = QVBoxLayout(trends_tab)

        self.trends_table = QTableWidget()
        self.trends_table.setColumnCount(5)
        self.trends_table.setHorizontalHeaderLabels([
            "Course", "Semester", "Year", "Total Enrollments", "Average Grade"
        ])
        self.setup_table_properties(self.trends_table)
        layout.addWidget(self.trends_table)

        self.tab_widget.addTab(trends_tab, "Course Performance")

    def setup_instructor_demographics_tab(self):
        """Setup the instructor demographics tab"""
        demographics_tab = QWidget()
        layout = QVBoxLayout(demographics_tab)

        self.demographics_table = QTableWidget()
        self.demographics_table.setColumnCount(3)
        self.demographics_table.setHorizontalHeaderLabels([
            "Instructor", "Course", "Students by Major"
        ])
        self.setup_table_properties(self.demographics_table)
        layout.addWidget(self.demographics_table)

        self.tab_widget.addTab(demographics_tab, "Instructor Demographics")

    def setup_student_rankings_tab(self):
        """Setup the student rankings tab"""
        rankings_tab = QWidget()
        layout = QVBoxLayout(rankings_tab)

        self.student_rankings_table = QTableWidget()
        self.student_rankings_table.setColumnCount(3)
        self.student_rankings_table.setHorizontalHeaderLabels([
            "Major", "Student ID", "Total Credits"
        ])
        self.setup_table_properties(self.student_rankings_table)
        layout.addWidget(self.student_rankings_table)

        self.tab_widget.addTab(rankings_tab, "Student Rankings")

    def setup_table_properties(self, table):
        """Set common table properties"""
        table.setAlternatingRowColors(True)
        table.setShowGrid(True)
        header = table.horizontalHeader()
        for i in range(table.columnCount() - 1):
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(table.columnCount() - 1, QHeaderView.Stretch)

    def load_academic_performance(self):
        """Load academic performance analysis data"""
        try:
            conn = sqlite3.connect(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                '..', 'data', 'academic_management.db'))
            cursor = conn.cursor()

            cursor.execute("""
                WITH student_gpas AS (
                    SELECT 
                        s.student_id,
                        s.major,
                        CASE 
                            WHEN SUM(CASE 
                                WHEN sc.grade IN ('A', 'S') THEN 4 * c.credits
                                WHEN sc.grade = 'B' THEN 3 * c.credits
                                WHEN sc.grade = 'C' THEN 2 * c.credits
                                WHEN sc.grade = 'D' THEN 1 * c.credits
                                WHEN sc.grade IN ('F', 'U', 'I') THEN 0
                                ELSE 0
                            END) = 0 THEN 0
                            ELSE ROUND(
                                SUM(CASE 
                                    WHEN sc.grade IN ('A', 'S') THEN 4 * c.credits
                                    WHEN sc.grade = 'B' THEN 3 * c.credits
                                    WHEN sc.grade = 'C' THEN 2 * c.credits
                                    WHEN sc.grade = 'D' THEN 1 * c.credits
                                    WHEN sc.grade IN ('F', 'U', 'I') THEN 0
                                    ELSE 0
                                END) * 1.0 / 
                                SUM(CASE WHEN sc.grade IN ('A', 'B', 'C', 'D', 'F', 'S', 'U', 'I') 
                                    THEN c.credits ELSE 0 END),
                                2
                            )
                        END as gpa
                    FROM students s
                    LEFT JOIN student_courses sc ON s.student_id = sc.student_id
                    LEFT JOIN courses c ON sc.course_prefix = c.course_prefix 
                        AND sc.course_number = c.course_number
                    GROUP BY s.student_id, s.major
                )
                SELECT 
                    major,
                    MAX(gpa) as highest_gpa,
                    MIN(gpa) as lowest_gpa,
                    ROUND(AVG(gpa), 2) as average_gpa
                FROM student_gpas
                GROUP BY major
                ORDER BY average_gpa DESC
            """)

            results = cursor.fetchall()
            self.performance_table.setRowCount(len(results))

            for row, data in enumerate(results):
                for col, value in enumerate(data):
                    item = QTableWidgetItem(str(value))
                    item.setTextAlignment(Qt.AlignCenter)
                    self.performance_table.setItem(row, col, item)

        except sqlite3.Error as e:
            self.logger.log_operation(
                OperationType.ERROR,
                f"Failed to load academic performance data: {str(e)}"
            )
            QMessageBox.critical(self, "Error", "Failed to load academic performance data")
        finally:
            if conn:
                conn.close()

    def load_departmental_rankings(self):
        """Load departmental GPA rankings data"""
        try:
            conn = sqlite3.connect(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                '..', 'data', 'academic_management.db'))
            cursor = conn.cursor()

            cursor.execute("""
                WITH department_gpas AS (
                    SELECT 
                        d.department_id,
                        CASE 
                            WHEN SUM(CASE 
                                WHEN sc.grade IN ('A', 'S') THEN 4 * c.credits
                                WHEN sc.grade = 'B' THEN 3 * c.credits
                                WHEN sc.grade = 'C' THEN 2 * c.credits
                                WHEN sc.grade = 'D' THEN 1 * c.credits
                                WHEN sc.grade IN ('F', 'U', 'I') THEN 0
                                ELSE 0
                            END) = 0 THEN 0
                            ELSE ROUND(
                                SUM(CASE 
                                    WHEN sc.grade IN ('A', 'S') THEN 4 * c.credits
                                    WHEN sc.grade = 'B' THEN 3 * c.credits
                                    WHEN sc.grade = 'C' THEN 2 * c.credits
                                    WHEN sc.grade = 'D' THEN 1 * c.credits
                                    WHEN sc.grade IN ('F', 'U', 'I') THEN 0
                                    ELSE 0
                                END) * 1.0 / 
                                SUM(CASE WHEN sc.grade IN ('A', 'B', 'C', 'D', 'F', 'S', 'U', 'I') 
                                    THEN c.credits ELSE 0 END),
                                2
                            )
                        END as dept_gpa
                    FROM departments d
                    JOIN department_majors dm ON d.department_id = dm.department_id
                    JOIN students s ON dm.major_name = s.major
                    LEFT JOIN student_courses sc ON s.student_id = sc.student_id
                    LEFT JOIN courses c ON sc.course_prefix = c.course_prefix 
                        AND sc.course_number = c.course_number
                    GROUP BY d.department_id
                )
                SELECT 
                    ROW_NUMBER() OVER (ORDER BY dept_gpa DESC) as rank,
                    department_id,
                    dept_gpa
                FROM department_gpas
                ORDER BY dept_gpa DESC
            """)

            results = cursor.fetchall()
            self.rankings_table.setRowCount(len(results))

            for row, data in enumerate(results):
                for col, value in enumerate(data):
                    item = QTableWidgetItem(str(value))
                    item.setTextAlignment(Qt.AlignCenter)
                    self.rankings_table.setItem(row, col, item)

        except sqlite3.Error as e:
            self.logger.log_operation(
                OperationType.ERROR,
                f"Failed to load departmental rankings: {str(e)}"
            )
            QMessageBox.critical(self, "Error", "Failed to load departmental rankings")
        finally:
            if conn:
                conn.close()

    def load_course_performance(self):
        """Load course performance trends data"""
        try:
            conn = sqlite3.connect(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                '..', 'data', 'academic_management.db'))
            cursor = conn.cursor()

            cursor.execute("""
                WITH course_stats AS (
                    SELECT 
                        c.course_prefix || ' ' || c.course_number as course,
                        sc.semester,
                        sc.year_taken,
                        COUNT(sc.student_id) as total_enrollments,
                        ROUND(AVG(CASE 
                            WHEN sc.grade IN ('A', 'S') THEN 4.0
                            WHEN sc.grade = 'B' THEN 3.0
                            WHEN sc.grade = 'C' THEN 2.0
                            WHEN sc.grade = 'D' THEN 1.0
                            WHEN sc.grade IN ('F', 'U', 'I') THEN 0.0
                            ELSE NULL
                        END), 2) as avg_grade
                    FROM student_courses sc
                    JOIN courses c ON sc.course_prefix = c.course_prefix 
                        AND sc.course_number = c.course_number
                    GROUP BY 
                        c.course_prefix,
                        c.course_number,
                        sc.semester,
                        sc.year_taken
                )
                SELECT 
                    course,
                    semester,
                    year_taken,
                    total_enrollments,
                    COALESCE(avg_grade, 'N/A') as avg_grade
                FROM course_stats
                ORDER BY 
                    year_taken DESC,
                    CASE semester
                        WHEN 'F' THEN 1
                        WHEN 'S' THEN 2
                        WHEN 'U' THEN 3
                    END,
                    course
            """)

            results = cursor.fetchall()
            self.trends_table.setRowCount(len(results))

            for row, data in enumerate(results):
                for col, value in enumerate(data):
                    if col == 1:  # Format semester
                        semester_name = {'F': 'Fall', 'S': 'Spring', 'U': 'Summer'}
                        value = semester_name.get(value, value)
                    item = QTableWidgetItem(str(value))
                    item.setTextAlignment(Qt.AlignCenter)
                    self.trends_table.setItem(row, col, item)

        except sqlite3.Error as e:
            self.logger.log_operation(
                OperationType.ERROR,
                f"Failed to load course performance data: {str(e)}"
            )
            QMessageBox.critical(self, "Error", "Failed to load course performance data")
        finally:
            if conn:
                conn.close()

    def load_instructor_demographics(self):
        """Load instructor course demographics data including semester/year information"""
        try:
            conn = sqlite3.connect(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                '..', 'data', 'academic_management.db'))
            cursor = conn.cursor()

            cursor.execute("""
                WITH student_majors AS (
                    SELECT 
                        ic.instructor_id,
                        c.course_prefix || ' ' || c.course_number as course,
                        ic.semester,
                        ic.year_taught,
                        s.major,
                        COUNT(DISTINCT s.student_id) as student_count
                    FROM instructor_courses ic
                    JOIN student_courses sc ON ic.course_prefix = sc.course_prefix 
                        AND ic.course_number = sc.course_number
                        AND ic.semester = sc.semester
                        AND ic.year_taught = sc.year_taken
                    JOIN students s ON sc.student_id = s.student_id
                    JOIN courses c ON ic.course_prefix = c.course_prefix 
                        AND ic.course_number = c.course_number
                    WHERE ic.instructor_id IS NOT NULL
                    GROUP BY 
                        ic.instructor_id,
                        c.course_prefix,
                        c.course_number,
                        ic.semester,
                        ic.year_taught,
                        s.major
                )
                SELECT 
                    instructor_id,
                    course,
                    CASE semester
                        WHEN 'F' THEN 'Fall'
                        WHEN 'S' THEN 'Spring'
                        WHEN 'U' THEN 'Summer'
                    END || ' ' || year_taught as term,
                    GROUP_CONCAT(major || ': ' || student_count) as major_distribution
                FROM student_majors
                GROUP BY instructor_id, course, semester, year_taught
                ORDER BY instructor_id, year_taught DESC, 
                    CASE semester
                        WHEN 'F' THEN 1
                        WHEN 'S' THEN 2
                        WHEN 'U' THEN 3
                    END DESC,
                    course
            """)

            results = cursor.fetchall()

            # Update table structure to include the new term column
            self.demographics_table.setColumnCount(4)
            self.demographics_table.setHorizontalHeaderLabels([
                "Instructor", "Course", "Term", "Students by Major"
            ])

            self.demographics_table.setRowCount(len(results))

            # Set custom column widths
            header = self.demographics_table.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Instructor
            header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Course
            header.setSectionResizeMode(2, QHeaderView.Fixed)  # Term
            self.demographics_table.setColumnWidth(2, 100)  # Set Term column to fixed 100 pixels
            header.setSectionResizeMode(3, QHeaderView.Stretch)  # Students by Major

            for row, data in enumerate(results):
                for col, value in enumerate(data):
                    item = QTableWidgetItem(str(value))
                    if col == 3:  # Major distribution column
                        item.setToolTip(str(value))  # Add tooltip for full text
                    item.setTextAlignment(Qt.AlignCenter)
                    self.demographics_table.setItem(row, col, item)

        except sqlite3.Error as e:
            self.logger.log_operation(
                OperationType.ERROR,
                f"Failed to load instructor demographics: {str(e)}"
            )
            QMessageBox.critical(self, "Error", "Failed to load instructor demographics")
        finally:
            if conn:
                conn.close()

    def load_student_rankings(self):
        """Load student rankings by credits within majors"""
        try:
            conn = sqlite3.connect(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                '..', 'data', 'academic_management.db'))
            cursor = conn.cursor()

            cursor.execute("""
                WITH student_credits AS (
                    SELECT 
                        s.major,
                        s.student_id,
                        COALESCE(SUM(c.credits), 0) as total_credits
                    FROM students s
                    LEFT JOIN student_courses sc ON s.student_id = sc.student_id
                    LEFT JOIN courses c ON sc.course_prefix = c.course_prefix 
                        AND sc.course_number = c.course_number
                    GROUP BY s.major, s.student_id
                ),
                ranked_students AS (
                    SELECT 
                        major,
                        student_id,
                        total_credits,
                        ROW_NUMBER() OVER (
                            PARTITION BY major 
                            ORDER BY total_credits DESC, student_id
                        ) as rank_in_major
                    FROM student_credits
                )
                SELECT 
                    major,
                    student_id,
                    total_credits
                FROM ranked_students
                ORDER BY major, rank_in_major
            """)

            results = cursor.fetchall()
            self.student_rankings_table.setRowCount(len(results))

            current_major = None
            major_start_row = 0
            row_count = 0

            for row, data in enumerate(results):
                major = data[0]

                # Add visual separation between majors
                if current_major != major:
                    if row > 0:
                        # Add an empty row for separation
                        self.student_rankings_table.insertRow(row)
                        for col in range(3):
                            item = QTableWidgetItem("")
                            item.setBackground(Qt.gray)
                            self.student_rankings_table.setItem(row, col, item)
                        row += 1
                    current_major = major
                    major_start_row = row

                # Add the data
                for col, value in enumerate(data):
                    item = QTableWidgetItem(str(value))
                    item.setTextAlignment(Qt.AlignCenter)
                    self.student_rankings_table.setItem(row, col, item)

        except sqlite3.Error as e:
            self.logger.log_operation(
                OperationType.ERROR,
                f"Failed to load student rankings: {str(e)}"
            )
            QMessageBox.critical(self, "Error", "Failed to load student rankings")
        finally:
            if conn:
                conn.close()

    def refresh_all_reports(self):
        """Refresh all report data"""
        self.load_logs()
        self.load_academic_performance()
        self.load_departmental_rankings()
        self.load_course_performance()
        self.load_instructor_demographics()
        self.load_student_rankings()

    def handle_filter_change(self, filter_type):
        """Handle changes to the log filter type"""
        # Hide all filter inputs first
        self.date_picker.hide()
        self.user_id_input.hide()

        # Show appropriate filter input based on selection
        if filter_type == "By Date":
            self.date_picker.show()
        elif filter_type == "By User ID":
            self.user_id_input.show()

        self.filter_logs()

    def filter_logs(self):
        """Apply the selected filter to the logs"""
        filter_type = self.filter_type.currentText()
        filter_criteria = {}

        if filter_type == "By Date":
            selected_date = self.date_picker.date().toPython()
            filter_criteria["date"] = selected_date
        elif filter_type == "By User ID":
            user_id = self.user_id_input.currentText()
            filter_criteria["user_id"] = user_id
        elif filter_type != "All Operations":
            operation = filter_type.split()[0].lower()
            filter_criteria["operation"] = operation

        self._apply_filters(filter_criteria)

    def _apply_filters(self, filter_criteria):
        """Apply filters to the logs table"""
        for row in range(self.logs_table.rowCount()):
            show_row = True

            if "date" in filter_criteria:
                try:
                    log_date = datetime.strptime(
                        self.logs_table.item(row, 0).text().split()[0],
                        "%Y-%m-%d"
                    ).date()
                    show_row = log_date == filter_criteria["date"]
                except (ValueError, AttributeError) as e:
                    show_row = False

            elif "user_id" in filter_criteria:
                user_id = self.logs_table.item(row, 1).text()
                show_row = user_id == filter_criteria["user_id"]

            elif "operation" in filter_criteria:
                operation_type = self.logs_table.item(row, 3).text().lower()
                show_row = operation_type.startswith(filter_criteria["operation"])

            self.logs_table.setRowHidden(row, not show_row)

    def logout(self):
        """Handle admin logout"""
        self.logger.log_session(OperationType.LOGOUT)
        self.logout_signal.emit()
        self.close()

    def closeEvent(self, event):
        """Override closeEvent to log when admin exits the system"""
        self.logger.log_operation(
            "exit",
            "Administrator exited the system"
        )
        event.accept()