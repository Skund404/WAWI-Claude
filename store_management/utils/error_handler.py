import tkinter
import tkinter.messagebox
import functools
from functools import wraps
from store_management.utils.logger import log_error, logger #modified
import traceback

class ErrorHandler:
    """
    """

    def log_database_action(action, details):
        """Log database-related actions"""
        logger.info(f"Database {action}: {details}")

    def validate_positive_integer(value, field_name):
        """Validate that a value is a positive integer"""
        if not isinstance(value, int) or value <= 0:
            raise ValueError(f"{field_name} must be a positive integer")

    def show_error(self, title, message, error=None):
        """Show error message to user and log it"""
        logger.error(f"{title}: {message} - {str(error)}")
        tkinter.messagebox.showerror(title, message)

    def show_warning(self, title, message):
        """Show warning message to user and log it"""
        logger.warning(f"{title}: {message}")
        tkinter.messagebox.showwarning(title, message)

    def handle_error(self, func):
        """Decorator for handling errors in functions"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as error:
                error_context = get_error_context()
                log_error(error, context=error_context)
                self.show_error("Error", f"An error occurred: {str(error)}", error)
                return None

        return wrapper


class ApplicationError(Exception):
    """Base class for application-specific errors"""

    def __init__(self, message="Application Error", details=None):
        self.message = message
        self.details = details
        super().__init__(self.message)


class DatabaseError(ApplicationError):
    """Error raised for database-related issues"""
    pass


class ValidationError(ApplicationError):
    """Error raised for data validation issues"""
    pass


def check_database_connection(func):
    """Decorator to check database connection before executing database operations"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            # Replace this with your actual database connection check logic
            # For example, attempt to connect to the database
            # If the connection fails, raise a DatabaseError
            return func(*args, **kwargs)
        except Exception as e:
            log_error(e, context="Database Connection Check Failed")
            tkinter.messagebox.showerror("Database Error", "Failed to connect to the database.")
            return None

    return wrapper


def get_error_context():
    """Get current error context including stack trace"""
    import traceback
    stack_summary = traceback.extract_stack()
    # Get the last few entries for context
    relevant_stack = stack_summary[-3:]
    formatted_context = " | ".join([f"{f.filename}:{f.lineno} ({f.name})" for f in relevant_stack])
    return formatted_context