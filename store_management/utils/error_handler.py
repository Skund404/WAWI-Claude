import tkinter as tk
from tkinter import messagebox
from functools import wraps
from .logger import log_error, logger
import traceback


class ErrorHandler:
    @staticmethod
    def show_error(title, message, error=None):
        """Show error message to user and log it"""
        if error:
            log_error(error, message)
            error_message = f"{message}\n\nError: {str(error)}"
        else:
            logger.error(message)
            error_message = message

        messagebox.showerror(title, error_message)

    @staticmethod
    def show_warning(title, message):
        """Show warning message to user and log it"""
        logger.warning(message)
        messagebox.showwarning(title, message)

    @staticmethod
    def handle_error(func):
        """Decorator for handling errors in functions"""

        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_msg = f"Error in {func.__name__}: {str(e)}"
                log_error(e, error_msg)
                messagebox.showerror("Error", f"{error_msg}\n\nCheck logs for details.")
                return None

        return wrapper


def check_database_connection(func):
    """Decorator to check database connection before executing database operations"""

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            if not hasattr(self, 'db') or not self.db:
                raise Exception("Database connection not initialized")
            return func(self, *args, **kwargs)
        except Exception as e:
            error_msg = f"Database error in {func.__name__}"
            log_error(e, error_msg)
            messagebox.showerror("Database Error", f"{error_msg}\n\nError: {str(e)}")
            return None

    return wrapper


class ApplicationError(Exception):
    """Base class for application-specific errors"""

    def __init__(self, message, details=None):
        super().__init__(message)
        self.details = details
        log_error(self, message)


class DatabaseError(ApplicationError):
    """Error raised for database-related issues"""
    pass


class ValidationError(ApplicationError):
    """Error raised for data validation issues"""
    pass


def get_error_context():
    """Get current error context including stack trace"""
    return traceback.format_exc()