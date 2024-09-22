import sys
import sqlite3
import os
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QSpacerItem, \
    QSizePolicy
from PySide6.QtCore import Qt
from werkzeug.security import check_password_hash


class LoginScreen(QWidget):
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

        # Login button
        login_button = QPushButton("Login")
        login_button.clicked.connect(self.login)
        login_button.setFixedWidth(280)
        login_button.setStyleSheet("margin-top: 20px;")
        login_layout.addWidget(login_button, alignment=Qt.AlignCenter)

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

        if self.check_credentials(username, password):
            self.error_label.setText("Login successful!")
            self.error_label.setStyleSheet("color: green; margin-top: 10px;")
            # TODO: Proceed to the main application window
        else:
            self.error_label.setText("Invalid username or password")
            self.error_label.setStyleSheet("color: red; margin-top: 10px;")

    def check_credentials(self, username, password):
        # Get the absolute path to the database file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(current_dir, '..', 'data', 'academic_management.db')

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
            result = cursor.fetchone()
            conn.close()

            if result:
                stored_password_hash = result[0]
                return check_password_hash(stored_password_hash, password)
            return False
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return False