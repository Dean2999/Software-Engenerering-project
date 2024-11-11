import sqlite3
from werkzeug.security import generate_password_hash

# Database setup
DB_NAME = 'academic_management.db'

def create_connection():
    """Create and return a database connection."""
    return sqlite3.connect(DB_NAME)

def create_tables(conn):
    """Create necessary tables in the database if they don't exist."""
    cursor = conn.cursor()

    # Create users table with role_description column included from the start
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT CHECK (role IN ('student', 'instructor', 'advisor', 'staff', 'admin')) NOT NULL,
        role_description TEXT
    )
    ''')

    # Create operation_logs table
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

    # Create index for faster querying of logs
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON operation_logs(timestamp)
    ''')
    """Create necessary tables in the database if they don't exist."""
    cursor = conn.cursor()

    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT CHECK (role IN ('student', 'instructor', 'advisor', 'staff', 'admin')) NOT NULL
    )
    ''')

    # Create students table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS students (
        user_id INTEGER PRIMARY KEY,
        student_id TEXT UNIQUE NOT NULL,
        gender TEXT,
        major TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')

    # Create instructors table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS instructors (
        user_id INTEGER PRIMARY KEY,
        instructor_id TEXT UNIQUE NOT NULL,
        phone TEXT,
        department_id TEXT,
        hired_semester TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')

    # Create courses table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS courses (
        course_id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_prefix TEXT,
        course_number TEXT,
        credits INTEGER,
        UNIQUE(course_prefix, course_number)
    )
    ''')

    # Create instructor_courses table (many-to-many relationship)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS instructor_courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        instructor_id TEXT,
        course_prefix TEXT,
        course_number TEXT,
        credits INTEGER,
        semester TEXT,
        year_taught INTEGER,
        FOREIGN KEY (instructor_id) REFERENCES instructors (instructor_id)
    )
    ''')

    # Create student_courses table (many-to-many relationship)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS student_courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT,
        course_prefix TEXT,
        course_number TEXT,
        semester TEXT,
        year_taken INTEGER,
        grade TEXT,
        FOREIGN KEY (student_id) REFERENCES students (student_id)
    )
    ''')

    # Create staff table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS staff (
        user_id INTEGER PRIMARY KEY,
        staff_id TEXT UNIQUE NOT NULL,
        department_id TEXT,
        phone TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')

    # Create advisors table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS advisors (
        user_id INTEGER PRIMARY KEY,
        advisor_id TEXT UNIQUE NOT NULL,
        phone TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')

    # Create departments table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS departments (
        department_id TEXT PRIMARY KEY,
        building TEXT,
        office TEXT
    )
    ''')

    # Create majors table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS majors (
        major_name TEXT PRIMARY KEY,
        default_hours_req INTEGER
    )
    ''')

    # Create department_majors table (many-to-many relationship) with a unique constraint
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS department_majors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        department_id TEXT,
        major_name TEXT,
        hours_req INTEGER,
        FOREIGN KEY (department_id) REFERENCES departments (department_id),
        FOREIGN KEY (major_name) REFERENCES majors (major_name),
        UNIQUE(department_id, major_name)
    )
    ''')

    # Create advisor_departments table (many-to-many relationship)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS advisor_departments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        advisor_id TEXT,
        department_id TEXT,
        FOREIGN KEY (advisor_id) REFERENCES advisors (advisor_id),
        FOREIGN KEY (department_id) REFERENCES departments (department_id)
    )
    ''')

    conn.commit()


def user_exists(conn, username):
    """Check if a user with the given username exists in the database."""
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
    return cursor.fetchone() is not None


def get_user_id(conn, username):
    """Get the user ID for a given username."""
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
    result = cursor.fetchone()
    return result[0] if result else None


def create_user(conn, username, role):
    """Create a new user or return the ID of an existing user."""
    if user_exists(conn, username):
        return get_user_id(conn, username)

    cursor = conn.cursor()
    password_hash = generate_password_hash('password')
    cursor.execute('INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)',
                   (username, password_hash, role))
    conn.commit()
    return cursor.lastrowid


def create_student(conn, user_id, student_id, gender, major):
    """Create a new student record or update an existing one."""
    cursor = conn.cursor()
    cursor.execute('''
    INSERT OR REPLACE INTO students (user_id, student_id, gender, major)
    VALUES (?, ?, ?, ?)
    ''', (user_id, student_id, gender, major))
    conn.commit()


def create_instructor(conn, user_id, instructor_id, phone, department_id, hired_semester):
    """Create a new instructor record or update an existing one."""
    cursor = conn.cursor()
    cursor.execute('''
    INSERT OR REPLACE INTO instructors (user_id, instructor_id, phone, department_id, hired_semester)
    VALUES (?, ?, ?, ?, ?)
    ''', (user_id, instructor_id, phone, department_id, hired_semester))
    conn.commit()


def create_course(conn, course_prefix, course_number, credits):
    """Create a new course record if it doesn't exist, or return the existing course ID."""
    cursor = conn.cursor()

    # First, check if the course already exists
    cursor.execute('''
    SELECT course_id FROM courses
    WHERE course_prefix = ? AND course_number = ?
    ''', (course_prefix, course_number))

    existing_course = cursor.fetchone()

    if existing_course:
        return existing_course[0]  # Return the existing course ID

    # If the course doesn't exist, create a new one
    cursor.execute('''
    INSERT INTO courses (course_prefix, course_number, credits)
    VALUES (?, ?, ?)
    ''', (course_prefix, course_number, credits))
    conn.commit()
    return cursor.lastrowid


def get_course_id(conn, course_prefix, course_number):
    """Get the course ID for an existing course."""
    cursor = conn.cursor()
    cursor.execute('''
    SELECT course_id FROM courses
    WHERE course_prefix = ? AND course_number = ?
    ''', (course_prefix, course_number))
    result = cursor.fetchone()
    return result[0] if result else None


def create_instructor_course(conn, instructor_id, course_prefix, course_number, credits, semester, year_taught):
    """Create a new instructor course record."""
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO instructor_courses (instructor_id, course_prefix, course_number, credits, semester, year_taught)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (instructor_id, course_prefix, course_number, credits, semester, year_taught))
    conn.commit()


def create_student_course(conn, student_id, course_prefix, course_number, semester, year_taken, grade):
    """Create a new student course record."""
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO student_courses (student_id, course_prefix, course_number, semester, year_taken, grade)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (student_id, course_prefix, course_number, semester, year_taken, grade))
    conn.commit()


def create_staff(conn, user_id, staff_id, department_id, phone):
    """Create a new staff record or update an existing one."""
    cursor = conn.cursor()
    cursor.execute('''
    INSERT OR REPLACE INTO staff (user_id, staff_id, department_id, phone)
    VALUES (?, ?, ?, ?)
    ''', (user_id, staff_id, department_id, phone))
    conn.commit()


def create_advisor(conn, advisor_id, phone):
    """Create a new advisor record or update an existing one, ensuring they're in the users table."""
    cursor = conn.cursor()

    # First, ensure the advisor is in the users table
    user_id = create_user(conn, advisor_id, "advisor")

    cursor.execute('''
    INSERT OR REPLACE INTO advisors (user_id, advisor_id, phone)
    VALUES (?, ?, ?)
    ''', (user_id, advisor_id, phone))
    conn.commit()
    return user_id


def create_department(conn, department_id, building, office):
    """Create a new department record or update an existing one."""
    cursor = conn.cursor()
    cursor.execute('''
    INSERT OR REPLACE INTO departments (department_id, building, office)
    VALUES (?, ?, ?)
    ''', (department_id, building, office))
    conn.commit()


def create_major(conn, major_name, default_hours_req):
    """Create a new major record if it doesn't exist."""
    cursor = conn.cursor()
    cursor.execute('''
    INSERT OR REPLACE INTO majors (major_name, default_hours_req)
    VALUES (?, ?)
    ''', (major_name, default_hours_req))
    conn.commit()


def add_major_to_department(conn, department_id, major_name, hours_req=None):
    """Add a major to a department or update if it already exists."""
    cursor = conn.cursor()

    # If hours_req is not provided, get the default from the majors table
    if hours_req is None:
        cursor.execute('SELECT default_hours_req FROM majors WHERE major_name = ?', (major_name,))
        result = cursor.fetchone()
        if result:
            hours_req = result[0]
        else:
            raise ValueError(f"Major {major_name} not found in majors table")

    cursor.execute('''
    INSERT OR REPLACE INTO department_majors (department_id, major_name, hours_req)
    VALUES (?, ?, ?)
    ''', (department_id, major_name, hours_req))
    conn.commit()


def add_advisor_department(conn, advisor_id, department_id):
    """Add a department to an advisor's list of departments."""
    cursor = conn.cursor()
    cursor.execute('''
    INSERT OR IGNORE INTO advisor_departments (advisor_id, department_id)
    VALUES (?, ?)
    ''', (advisor_id, department_id))
    conn.commit()


def get_department_majors(conn, department_id):
    """Get all majors offered by a department."""
    cursor = conn.cursor()
    cursor.execute('''
    SELECT major_name, hours_req
    FROM department_majors
    WHERE department_id = ?
    ''', (department_id,))
    return cursor.fetchall()


def verify_departments(conn):
    """Verify the contents of the departments table and their majors."""
    cursor = conn.cursor()
    cursor.execute('SELECT department_id, building, office FROM departments')
    departments = cursor.fetchall()
    for dept in departments:
        majors = get_department_majors(conn, dept[0])
        print(f"Department ID: {dept[0]}, Building: {dept[1]}, Office: {dept[2]}")
        if majors:
            for major in majors:
                print(f"  Major: {major[0]}, Hours Required: {major[1]}")
        else:
            print("  No majors offered")
        print()


def verify_majors(conn):
    """Verify the contents of the majors table."""
    cursor = conn.cursor()
    cursor.execute('SELECT major_name, default_hours_req FROM majors')
    majors = cursor.fetchall()
    print("Majors and their default hours required:")
    for major in majors:
        print(f"  {major[0]}: {major[1]} hours")
    print()