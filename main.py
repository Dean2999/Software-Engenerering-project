import sys
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QLineEdit, QPushButton, QGridLayout)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon


class LoginScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Project 2 - Login")
        self.setGeometry(100, 100, 800, 600)  # Slightly wider to accommodate the new button
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout()
        form_layout = QGridLayout()

        # Username
        username_label = QLabel("Username:")
        self.username_input = QLineEdit()

        # Password
        password_label = QLabel("Password:")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)

        # Password visibility toggle button
        self.toggle_password_button = QPushButton()
        self.toggle_password_button.setIcon(QIcon.fromTheme("eye-off"))  # You might need to provide your own icons
        self.toggle_password_button.clicked.connect(self.toggle_password_visibility)
        self.toggle_password_button.setFixedSize(30, 30)  # Set a fixed size for the button

        # Set fixed width for input fields
        self.username_input.setFixedWidth(150)
        self.password_input.setFixedWidth(150)

        # Add widgets to form layout
        form_layout.addWidget(username_label, 0, 0, Qt.AlignRight)
        form_layout.addWidget(self.username_input, 0, 1, Qt.AlignLeft)
        form_layout.addWidget(password_label, 1, 0, Qt.AlignRight)

        # Create a horizontal layout for password input and toggle button
        password_layout = QHBoxLayout()
        password_layout.addWidget(self.password_input)
        password_layout.addWidget(self.toggle_password_button)
        password_layout.setAlignment(Qt.AlignLeft)
        password_layout.setSpacing(0)  # Reduce spacing between password field and button

        form_layout.addLayout(password_layout, 1, 1)

        # Login button
        login_button = QPushButton("Login")
        login_button.clicked.connect(self.login)
        login_button.setFixedWidth(100)

        # Create a container widget for the form and center it
        form_container = QWidget()
        form_container.setLayout(form_layout)

        # Add all widgets to the main layout
        main_layout.addWidget(form_container, alignment=Qt.AlignCenter)
        main_layout.addWidget(login_button, alignment=Qt.AlignCenter)

        self.setLayout(main_layout)

    def toggle_password_visibility(self):
        if self.password_input.echoMode() == QLineEdit.Password:
            self.password_input.setEchoMode(QLineEdit.Normal)
            self.toggle_password_button.setIcon(QIcon.fromTheme("eye-on"))
        else:
            self.password_input.setEchoMode(QLineEdit.Password)
            self.toggle_password_button.setIcon(QIcon.fromTheme("eye-off"))

    def login(self):
        username = self.username_input.text()
        password = self.password_input.text()
        # Here you would typically check the credentials against your database
        print(f"Login attempt: Username: {username}, Password: {password}")
        # For now, we'll just print the credentials. In a real application,
        # you'd verify these against your database and proceed accordingly.


if __name__ == "__main__":
    app = QApplication(sys.argv)
    login_screen = LoginScreen()
    login_screen.show()
    sys.exit(app.exec())