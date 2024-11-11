import csv
import os
from datetime import datetime
from db_operations import (
    create_connection, create_tables, create_user, create_student,
    create_instructor, create_staff, create_course, get_course_id,
    create_instructor_course, create_student_course,
    create_advisor, create_department, add_advisor_department,
    create_major, add_major_to_department, verify_departments, verify_majors
)


def create_operation_logs_table(conn):
    """Create the operation_logs table."""
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS operation_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME NOT NULL,
        user_id INTEGER NOT NULL,
        operation_type TEXT NOT NULL,
        details TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')

    # Create index for faster querying
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON operation_logs(timestamp)
    ''')

    conn.commit()


def create_admin_user(conn):
    """Create the system administrator user."""
    cursor = conn.cursor()

    # Insert the system administrator
    admin_data = {
        'username': 'SA01',
        'password_hash': 'scrypt:32768:8:1$vWTDwVNX6CXc6rgL$d87e008085e2e71203d1e2938c8e326966e248e373ade5eff02d4b7ff7558fbfc10c4f6271c591e1a79793748f44c4dd1f00d2606e95fe0afbcd560a68f44e3c',
        'role': 'admin'
    }

    # Check if admin user already exists
    cursor.execute('SELECT id FROM users WHERE username = ?', (admin_data['username'],))
    existing_admin = cursor.fetchone()

    if not existing_admin:
        cursor.execute('''
        INSERT INTO users (username, password_hash, role)
        VALUES (?, ?, ?)
        ''', (admin_data['username'], admin_data['password_hash'], admin_data['role']))

        # Add initial log entry
        admin_id = cursor.lastrowid
        cursor.execute('''
        INSERT INTO operation_logs (timestamp, user_id, operation_type, details)
        VALUES (?, ?, ?, ?)
        ''', (
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            admin_id,
            'system_setup',
            'Database initialized with admin user'
        ))

        conn.commit()


def main():
    """Main function to set up the database and populate it with initial data."""
    conn = create_connection()

    # Create all tables
    create_tables(conn)

    # Create admin user before other operations
    create_admin_user(conn)

    # Create operation_logs table
    create_operation_logs_table(conn)


    with open(os.path.join('csvfiles', 'students.csv'), 'r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            if 'StudentID' in row and row['StudentID']:
                user_id = create_user(conn, row['StudentID'], "student")
                gender = row.get('Gender', '')
                major = row.get('Major', '')
                create_student(conn, user_id, row['StudentID'], gender, major)

    # Create students from CSV
    with open(os.path.join('csvfiles', 'students.csv'), 'r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            if 'StudentID' in row and row['StudentID']:
                user_id = create_user(conn, row['StudentID'], "student")
                gender = row.get('Gender', '')
                major = row.get('Major', '')
                create_student(conn, user_id, row['StudentID'], gender, major)

    # Create instructors from CSV
    with open(os.path.join('csvfiles', 'instructors.csv'), 'r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            if 'InstructorID' in row and row['InstructorID']:
                user_id = create_user(conn, row['InstructorID'], "instructor")
                phone = row.get('InstructorPhone', '')
                dept_id = row.get('DepartmentID', '')
                hired = row.get('HiredSemester', '')
                create_instructor(conn, user_id, row['InstructorID'], phone, dept_id, hired)

    # Create staff from CSV
    with open(os.path.join('csvfiles', 'staff.csv'), 'r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            if 'StaffID' in row and row['StaffID']:
                user_id = create_user(conn, row['StaffID'], "staff")
                dept_id = row.get('DepartmentID', '')
                phone = row.get('Phone', '')
                create_staff(conn, user_id, row['StaffID'], dept_id, phone)

    # Create departments, majors, and advisors from CSV
    with open(os.path.join('csvfiles', 'Departments.csv'), 'r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            if 'DepartmentID' in row and row['DepartmentID']:
                dept_id = row['DepartmentID']
                building = row.get('Building', '')
                office = row.get('Office', '')
                create_department(conn, dept_id, building, office)

                major_offered = row.get('MajorOffered', '')
                total_hours_req = row.get('TotalHoursReq', '')
                if major_offered and total_hours_req:
                    create_major(conn, major_offered, int(total_hours_req))
                    add_major_to_department(conn, dept_id, major_offered, int(total_hours_req))

                advisor_id = row.get('AdvisorID')
                if advisor_id:
                    phone = row.get('AdvisorPhone', '')
                    create_advisor(conn, advisor_id, phone)
                    add_advisor_department(conn, advisor_id, dept_id)

    # Create courses and instructor_courses from CSV
    with open(os.path.join('csvfiles', 'InstructorCourse.csv'), 'r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            if 'InstructorID' in row and row['InstructorID']:
                prefix = row.get('CoursePrefix', '')
                number = row.get('CourseNumber', '')
                credits = row.get('Credits', '')

                # Create the course (this will either create a new course or return the existing one)
                create_course(conn, prefix, number, credits)

                semester = row.get('Semester', '')
                year = row.get('YearTaught', '')
                create_instructor_course(conn, row['InstructorID'], prefix, number, credits, semester, year)

    # Create student_courses from CSV
    with open(os.path.join('csvfiles', 'StudentCourse.csv'), 'r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            if 'StudentID' in row and row['StudentID']:
                prefix = row.get('CoursePrefix', '')
                number = row.get('CourseNumber', '')
                semester = row.get('Semester', '')
                year = row.get('YearTaken', '')
                grade = row.get('Grade', '')

                create_student_course(conn, row['StudentID'], prefix, number, semester, year, grade)

    print("Database setup and population completed successfully.")

    # # Verify departments and their majors
    # print("\nVerifying departments and their majors in the database:")
    # verify_departments(conn)

    # # Verify majors
    # print("\nVerifying majors and their default hours required:")
    # verify_majors(conn)

    print("Database setup and population completed successfully.")
    print("System administrator account created (Username: SA01)")

    conn.close()

if __name__ == "__main__":
    main()