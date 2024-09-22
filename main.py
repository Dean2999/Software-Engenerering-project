import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QSize
from ui.login_screen import LoginScreen


class AcademicManagementSystem:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.login_screen = LoginScreen()
        self.set_default_window_size()

    def set_default_window_size(self):
        default_size = QSize(1280, 720)
        self.login_screen.resize(default_size)

    def run(self):
        self.login_screen.show()
        return self.app.exec()


if __name__ == "__main__":
    # Change the current working directory to the script's directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    ams = AcademicManagementSystem()
    sys.exit(ams.run())