import sys
import sqlite3
import os
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QSpacerItem, \
    QSizePolicy
from PySide6.QtCore import Qt, Signal
from werkzeug.security import check_password_hash

class LoginScreen(QWidget):
    login_successful = Signal(str, str)  # Signal to emit user_id and role on successful login

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Academic Management System - Login")
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        login_layout = QVBoxLayout()

        # Title
        title_label = QLabel("Academic Management System")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 20px;")
        login_layout.addWidget(title_label)

        # Username
        username_layout = QHBoxLayout()
        username_layout.addStretch()
        username_label = QLabel("Username:")
        username_label.setFixedWidth(70)
        self.username_input = QLineEdit()
        self.username_input.setFixedWidth(200)
        username_layout.addWidget(username_label)
        username_layout.addWidget(self.username_input)
        username_layout.addStretch()
        login_layout.addLayout(username_layout)

        # Password
        password_layout = QHBoxLayout()
        password_layout.addStretch()
        password_label = QLabel("Password:")
        password_label.setFixedWidth(70)
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFixedWidth(200)
        password_layout.addWidget(password_label)
        password_layout.addWidget(self.password_input)
        password_layout.addStretch()
        login_layout.addLayout(password_layout)

        # Connect Enter key press to login function
        self.password_input.returnPressed.connect(self.login)

        # Login button
        login_button = QPushButton("Login")
        login_button.clicked.connect(self.login)
        login_button.setFixedWidth(280)
        login_button.setStyleSheet("margin-top: 20px;")
        login_layout.addWidget(login_button, alignment=Qt.AlignCenter)

        # Exit button
        exit_button = QPushButton("Exit")
        exit_button.clicked.connect(self.close)
        exit_button.setFixedWidth(280)
        exit_button.setStyleSheet("margin-top: 10px;")
        login_layout.addWidget(exit_button, alignment=Qt.AlignCenter)

        # Error message
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: red; margin-top: 10px;")
        self.error_label.setAlignment(Qt.AlignCenter)
        login_layout.addWidget(self.error_label)

        main_layout.addLayout(login_layout)
        main_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        self.setLayout(main_layout)

    def login(self):
        username = self.username_input.text()
        password = self.password_input.text()

        user_id, role = self.check_credentials(username, password)
        if user_id and role:
            self.error_label.setText("Login successful!")
            self.error_label.setStyleSheet("color: green; margin-top: 10px;")
            print(f"Emitting login_successful signal with user_id: {user_id}, role: {role}")  # Debug print
            self.login_successful.emit(user_id, role)
        else:
            self.error_label.setText("Invalid username or password")
            self.error_label.setStyleSheet("color: red; margin-top: 10px;")

    def check_credentials(self, username, password):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(current_dir, '..', 'data', 'academic_management.db')
        print(f"Attempting to connect to database at: {db_path}")  # Debug print

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT u.id, u.password_hash, u.role, s.student_id 
                FROM users u
                LEFT JOIN students s ON u.id = s.user_id
                WHERE u.username = ?
            """, (username,))
            result = cursor.fetchone()
            conn.close()

            if result and check_password_hash(result[1], password):
                user_id = result[3] if result[3] else str(result[0])
                print(f"Login successful for user: {username}, id: {user_id}, role: {result[2]}")  # Debug print
                return user_id, result[2]  # Return student_id (or user_id if not a student) and role
            print(f"Login failed for user: {username}")  # Debug print
            return None, None
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return None, None