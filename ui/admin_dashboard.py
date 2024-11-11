import sys
import os
from datetime import datetime
import sqlite3
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QPushButton, QTableWidget, QTableWidgetItem,
                               QComboBox, QMessageBox, QDateEdit, QHeaderView)
from PySide6.QtCore import Qt, Signal
from ui.common.system_logger import SystemLogger, UserRole, OperationType


class AdminDashboard(QMainWindow):
    logout_signal = Signal()

    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        print(f"Initializing AdminDashboard with user_id: {self.user_id}")
        self.setWindowTitle("System Administrator Dashboard")
        self.setGeometry(100, 100, 800, 600)

        # Initialize the universal logger
        self.logger = SystemLogger(self.user_id, UserRole.ADMIN)

        self.setup_ui()
        self.logger.log_session(OperationType.LOGIN)

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
        main_layout.addLayout(filter_layout)

        # Logs Table
        self.logs_table = QTableWidget()
        self.logs_table.setColumnCount(5)
        self.logs_table.setHorizontalHeaderLabels([
            "Timestamp", "User ID", "Role", "Operation", "Details"
        ])

        # Set table properties for better display
        self.logs_table.setAlternatingRowColors(True)
        self.logs_table.setShowGrid(True)

        # Configure header behavior
        header = self.logs_table.horizontalHeader()
        for i in range(4):  # First 4 columns (all except Details)
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        # Make the Details column stretch
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)

        main_layout.addWidget(self.logs_table)

        # Load initial data
        self.load_logs()
        self.load_user_ids()

    def load_logs(self):
        try:
            conn = sqlite3.connect(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                '..', 'data', 'academic_management.db'))
            cursor = conn.cursor()

            cursor.execute("""
                SELECT 
                    l.timestamp,
                    l.user_id,
                    CASE 
                        WHEN u.role IS NOT NULL THEN 
                            UPPER(SUBSTR(u.role, 1, 1)) || LOWER(SUBSTR(u.role, 2))
                        ELSE 'Unknown'
                    END as role,
                    l.operation_type,
                    l.details
                FROM operation_logs l
                LEFT JOIN users u ON l.user_id = CAST(u.id AS TEXT)
                ORDER BY l.timestamp DESC
            """)
            logs = cursor.fetchall()

            self.logs_table.setRowCount(len(logs))
            for row, log in enumerate(logs):
                for col, value in enumerate(log):
                    item = QTableWidgetItem(str(value))
                    if col != 4:  # Center align all columns except Details
                        item.setTextAlignment(Qt.AlignCenter)
                    self.logs_table.setItem(row, col, item)

            # Log the view operation
            self.logger.log_data_access("logs", "viewed all system logs")

        except sqlite3.Error as e:
            self.logger.log_operation(OperationType.ERROR, f"Failed to load logs: {str(e)}")
            QMessageBox.critical(self, "Error", "Failed to load logs from database.")
        finally:
            if conn:
                conn.close()

    def load_user_ids(self):
        try:
            conn = sqlite3.connect(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                '..', 'data', 'academic_management.db'))
            cursor = conn.cursor()

            cursor.execute("SELECT DISTINCT user_id FROM operation_logs ORDER BY user_id")
            user_ids = cursor.fetchall()

            self.user_id_input.clear()
            self.user_id_input.addItems([str(uid[0]) for uid in user_ids])

        except sqlite3.Error as e:
            self.logger.log_operation(OperationType.ERROR, f"Failed to load user IDs: {str(e)}")
        finally:
            if conn:
                conn.close()

    def handle_filter_change(self, filter_type):
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

        # Log the filter operation
        self.logger.log_operation(
            OperationType.FILTER,
            f"Filtered logs by {filter_type}",
            affected_data=filter_criteria
        )

        self._apply_filters(filter_criteria)

    def _apply_filters(self, filter_criteria):
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

    def clear_logs(self):
        """Clear all system logs with proper connection and transaction management"""
        conn = None
        try:
            conn = sqlite3.connect(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                '..', 'data', 'academic_management.db'))
            cursor = conn.cursor()

            # Set a timeout for acquiring locks (5 seconds)
            cursor.execute("PRAGMA busy_timeout = 5000")

            # Begin transaction
            cursor.execute("BEGIN TRANSACTION")

            try:
                # Delete all existing logs
                cursor.execute("DELETE FROM operation_logs")

                # Log the clear operation immediately within the same transaction
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute("""
                    INSERT INTO operation_logs (timestamp, user_id, operation_type, details)
                    VALUES (?, ?, ?, ?)
                """, (timestamp, self.user_id, OperationType.CLEAR.value, "Administrator cleared all system logs"))

                # Commit the transaction
                conn.commit()

                # Reload the table
                self.load_logs()
                self.load_user_ids()

                QMessageBox.information(self, "Success", "All logs have been cleared.")

            except sqlite3.Error as e:
                if conn:
                    conn.rollback()
                raise e  # Re-raise to be caught by outer try block

        except sqlite3.Error as e:
            error_msg = f"Failed to clear logs: {str(e)}"
            print(f"Database error: {error_msg}")
            QMessageBox.critical(self, "Error", error_msg)

            # Log the error without trying to access the database again
            print(f"Error while clearing logs: {error_msg}")

        finally:
            if conn:
                try:
                    conn.close()
                except sqlite3.Error as e:
                    print(f"Error closing database connection: {e}")

    def confirm_clear_logs(self):
        """Confirm and handle log clearing with improved error handling"""
        reply = QMessageBox.question(
            self,
            "Confirm Clear Logs",
            "Are you sure you want to clear all logs? This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                self.clear_logs()
            except Exception as e:
                print(f"Unexpected error during log clearing: {e}")
                QMessageBox.critical(self, "Error",
                                     "An unexpected error occurred while clearing logs. Please try again or contact system administrator.")

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