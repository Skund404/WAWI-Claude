# gui/utils/error_manager.py
"""
Centralized error handling and logging utility for the Leatherworking ERP.
"""

import logging
import traceback
import tkinter.messagebox as messagebox


class ErrorManager:
    """
    Centralized error handling with consistent user feedback and logging.
    Provides methods for standardized error management across the application.
    """

    @staticmethod
    def handle_exception(view, exception, context=None):
        """
        Handle exceptions with consistent logging and user feedback.

        Args:
            view: The view or context where the exception occurred
            exception: The exception object
            context: Optional additional context information
        """
        # Extract exception details
        error_type = type(exception).__name__
        error_message = str(exception)

        # Log the full traceback for debugging
        logging.error(f"Error in {view.__class__.__name__}: {error_type}")
        logging.error(f"Context: {context or 'N/A'}")
        logging.error(traceback.format_exc())

        # Provide user-friendly error message
        user_message = f"An error occurred: {error_message}"

        # Try to provide more specific guidance based on exception type
        if isinstance(exception, ValueError):
            user_message += "\nPlease check your input and try again."
        elif isinstance(exception, PermissionError):
            user_message += "\nYou do not have permission to perform this action."
        elif isinstance(exception, ConnectionError):
            user_message += "\nThere was a problem connecting to the database or service."

        # Show error message to the user
        messagebox.showerror("Error", user_message)

    @staticmethod
    def log_error(exception, context=None):
        """
        Log an error with optional context.

        Args:
            exception: The exception object to log
            context: Optional additional context information
        """
        error_type = type(exception).__name__
        error_message = str(exception)

        logging.error(f"Error Type: {error_type}")
        logging.error(f"Error Message: {error_message}")
        logging.error(f"Context: {context or 'N/A'}")
        logging.error(traceback.format_exc())

    @staticmethod
    def show_validation_error(message):
        """
        Show a validation error message to the user.

        Args:
            message: The validation error message to display
        """
        messagebox.showwarning("Validation Error", message)

    @staticmethod
    def show_info(title, message):
        """
        Show an informational message to the user.

        Args:
            title: The title of the message box
            message: The message to display
        """
        messagebox.showinfo(title, message)

    @staticmethod
    def confirm_action(title, message):
        """
        Show a confirmation dialog to the user.

        Args:
            title: The title of the confirmation dialog
            message: The confirmation message

        Returns:
            bool: True if user confirms, False otherwise
        """
        return messagebox.askyesno(title, message)