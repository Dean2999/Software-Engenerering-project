import csv
import os
from db_operations import (
    create_connection, create_tables, create_user, create_student,
    create_instructor, create_staff, create_course, get_course_id,
    create_instructor_course, create_student_course,
    create_advisor, create_department, add_advisor_department,
    create_major, add_major_to_department, verify_departments, verify_majors
)

def main():
    """Main function to set up the database and populate it with initial data."""
    conn = create_connection()
    create_tables(conn)

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

    conn.close()

if __name__ == "__main__":
    main()