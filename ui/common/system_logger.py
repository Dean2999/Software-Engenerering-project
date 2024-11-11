import sqlite3
import os
from datetime import datetime
from typing import Optional, Dict, Any, Union
from enum import Enum, auto


class UserRole(Enum):
    """Enum defining system user roles"""
    STUDENT = auto()
    INSTRUCTOR = auto()
    ADVISOR = auto()
    STAFF = auto()
    ADMIN = auto()


class OperationType(Enum):
    """Enum defining common operation types"""
    LOGIN = "login"
    LOGOUT = "logout"
    VIEW = "view"
    ADD = "add"
    MODIFY = "modify"
    DELETE = "delete"
    REGISTER = "register"
    DROP = "drop"
    ANALYSIS = "analysis"
    CLEAR = "clear"
    FILTER = "filter"
    ERROR = "error"


class SystemLogger:
    """
    Universal logger class for the Academic Management System.
    Handles logging for all user roles and operation types.
    """

    def __init__(self, user_id: str, role: UserRole):
        """
        Initialize the logger with user information.

        Args:
            user_id: The user's ID in the system
            role: UserRole enum indicating the user's role
        """
        self.user_id = user_id
        self.role = role
        self.role_prefix = role.name.lower()
        self.db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                                    'data', 'academic_management.db')

    def log_operation(self, operation_type: Union[OperationType, str],
                      details: str,
                      affected_data: Optional[Dict[str, Any]] = None,
                      include_role_prefix: bool = True) -> bool:
        """
        Log a system operation with detailed information.

        Args:
            operation_type: Type of operation (can be OperationType enum or string)
            details: Human-readable description of the operation
            affected_data: Optional dictionary containing affected data details
            include_role_prefix: Whether to prefix operation type with role

        Returns:
            bool: True if logging successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Format operation type
            if isinstance(operation_type, OperationType):
                op_type = operation_type.value
            else:
                op_type = str(operation_type)

            # Add role prefix if requested
            if include_role_prefix:
                op_type = f"{self.role_prefix}_{op_type}"

            # Format affected data if provided
            if affected_data:
                data_details = self._format_affected_data(affected_data)
                details = f"{details} | Data: {data_details}"

            cursor.execute("""
                INSERT INTO operation_logs 
                (timestamp, user_id, operation_type, details)
                VALUES (?, ?, ?, ?)
            """, (timestamp, self.user_id, op_type, details))

            conn.commit()
            return True

        except sqlite3.Error as e:
            print(f"Database error while logging operation: {e}")
            self._log_error(e, "log_operation")
            return False
        finally:
            if conn:
                conn.close()

    def log_session(self, operation_type: OperationType) -> bool:
        """
        Log session-related operations (login/logout).

        Args:
            operation_type: OperationType.LOGIN or OperationType.LOGOUT

        Returns:
            bool: True if logging successful, False otherwise
        """
        action = operation_type.value.title()
        details = f"{self.role.name.title()} {action}"
        return self.log_operation(operation_type, details)

    def log_data_access(self, data_type: str, action: str,
                        identifiers: Optional[Dict[str, Any]] = None) -> bool:
        """
        Log data access operations.

        Args:
            data_type: Type of data being accessed (e.g., "student", "course")
            action: Action being performed on the data
            identifiers: Optional identifying information

        Returns:
            bool: True if logging successful, False otherwise
        """
        details = f"Accessed {data_type} data - {action}"
        return self.log_operation(
            OperationType.VIEW,
            details,
            affected_data=identifiers
        )

    def log_data_modification(self, data_type: str, action: str,
                              before: Optional[Dict[str, Any]] = None,
                              after: Optional[Dict[str, Any]] = None) -> bool:
        """
        Log data modification operations.

        Args:
            data_type: Type of data being modified
            action: Description of modification
            before: Optional state before modification
            after: Optional state after modification

        Returns:
            bool: True if logging successful, False otherwise
        """
        details = f"Modified {data_type} - {action}"
        affected_data = {}

        if before:
            affected_data["before"] = before
        if after:
            affected_data["after"] = after

        return self.log_operation(
            OperationType.MODIFY,
            details,
            affected_data=affected_data
        )

    def log_course_operation(self, operation_type: OperationType,
                             course_data: Dict[str, Any],
                             student_id: Optional[str] = None) -> bool:
        """
        Log course-related operations.

        Args:
            operation_type: Type of operation (register/drop)
            course_data: Dictionary containing course information
            student_id: Optional student ID for student-related operations

        Returns:
            bool: True if logging successful, False otherwise
        """
        course_str = (f"{course_data.get('prefix', '')} "
                      f"{course_data.get('number', '')}")
        term_str = (f"{course_data.get('semester', '')} "
                    f"{course_data.get('year', '')}")

        details = f"Course: {course_str} | Term: {term_str}"
        if student_id:
            details = f"Student: {student_id} | {details}"

        return self.log_operation(operation_type, details, affected_data=course_data)

    def log_analysis(self, analysis_type: str,
                     parameters: Dict[str, Any],
                     results: Dict[str, Any],
                     student_id: Optional[str] = None) -> bool:
        """
        Log analysis operations.

        Args:
            analysis_type: Type of analysis performed
            parameters: Analysis parameters
            results: Analysis results
            student_id: Optional student ID

        Returns:
            bool: True if logging successful, False otherwise
        """
        details = f"Analysis Type: {analysis_type}"
        if student_id:
            details = f"Student: {student_id} | {details}"

        affected_data = {
            "parameters": parameters,
            "results": results
        }

        return self.log_operation(
            OperationType.ANALYSIS,
            details,
            affected_data=affected_data
        )

    def _log_error(self, error: Exception, context: str) -> None:
        """
        Log system errors.

        Args:
            error: The exception that occurred
            context: Context where the error occurred
        """
        error_details = f"Error in {context}: {str(error)}"
        try:
            self.log_operation(
                OperationType.ERROR,
                error_details,
                include_role_prefix=False
            )
        except Exception as e:
            print(f"Error logging error: {e}")

    def _format_affected_data(self, data: Dict[str, Any]) -> str:
        """
        Format dictionary data into a readable string.

        Args:
            data: Dictionary containing operation data

        Returns:
            str: Formatted string representation of the data
        """
        return " | ".join(f"{k}: {v}" for k, v in data.items())