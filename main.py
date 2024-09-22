import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QSize
from ui.login_screen import LoginScreen
from ui.student_dashboard import StudentDashboard
from ui.instructor_dashboard import InstructorDashboard
from ui.advisor_dashboard import AdvisorDashboard
from ui.staff_dashboard import StaffDashboard

class AcademicManagementSystem:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.login_screen = LoginScreen()
        self.set_default_window_size()
        self.login_screen.login_successful.connect(self.show_dashboard)

    def set_default_window_size(self):
        default_size = QSize(800, 600)
        self.login_screen.resize(default_size)

    def show_dashboard(self, user_id, role):
        print(f"Showing dashboard for user_id: {user_id}, role: {role}")  # Debug print
        if role == 'student':
            self.dashboard = StudentDashboard(user_id)
        elif role == 'instructor':
            self.dashboard = InstructorDashboard(user_id)
        elif role == 'advisor':
            self.dashboard = AdvisorDashboard(user_id)
        elif role == 'staff':
            self.dashboard = StaffDashboard(user_id)
        else:
            print(f"Unknown role: {role}")
            return

        self.dashboard.logout_signal.connect(self.handle_logout)
        self.dashboard.show()
        self.login_screen.hide()

    def handle_logout(self):
        self.dashboard.close()
        self.login_screen.show()
        self.login_screen.username_input.clear()
        self.login_screen.password_input.clear()
        self.login_screen.error_label.clear()

    def run(self):
        self.login_screen.show()
        return self.app.exec()

if __name__ == "__main__":
    # Change the current working directory to the script's directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    print(f"Current working directory: {os.getcwd()}")  # Debug print

    ams = AcademicManagementSystem()
    sys.exit(ams.run())