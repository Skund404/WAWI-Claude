# tests/leatherwork_gui_tests/utils/test_error_manager.py
"""
Unit tests for the ErrorManager utility in the Leatherworking ERP.
"""

import unittest
import logging
import tkinter as tk
import tkinter.messagebox as messagebox
from unittest.mock import patch, MagicMock

# Lazy import to resolve potential circular dependencies
from utils.circular_import_resolver import lazy_import

# Lazy import the ErrorManager
ErrorManager = lazy_import('gui.utils.error_manager', 'ErrorManager')


class DummyView:
    """
    A dummy view class for testing error handling.
    Simulates a view context in the Leatherworking ERP.
    """

    def __init__(self, name="DummyView"):
        self.__class__.__name__ = name


class TestErrorManager(unittest.TestCase):
    """
    Test suite for the ErrorManager utility class.
    Covers various error handling and logging scenarios.
    """

    def setUp(self):
        """
        Set up the test environment before each test method.
        Configures logging and creates a hidden root Tkinter window.
        """
        # Configure logging
        logging.basicConfig(level=logging.ERROR)
        self.log_handler = logging.StreamHandler()
        self.log_handler.setLevel(logging.ERROR)
        logging.getLogger().addHandler(self.log_handler)

        # Create a hidden root window for Tkinter message boxes
        self.root = tk.Tk()
        self.root.withdraw()

    def tearDown(self):
        """
        Clean up the test environment after each test method.
        Removes log handlers and destroys the Tkinter root window.
        """
        # Remove the log handler
        logging.getLogger().removeHandler(self.log_handler)

        # Destroy the root window
        self.root.destroy()

    @patch('tkinter.messagebox.showerror')
    @patch('logging.error')
    def test_handle_exception_generic(self, mock_log_error, mock_showerror):
        """
        Test the handle_exception method with a generic exception.
        Verifies logging and error message display.
        """
        view = DummyView()
        exception = Exception("Generic error occurred")
        context = "Test context"

        # Call the method being tested
        ErrorManager.handle_exception(view, exception, context)

        # Verify logging calls (3 calls for full traceback and error details)
        self.assertEqual(mock_log_error.call_count, 3)

        # Verify error message box
        mock_showerror.assert_called_once_with(
            "Error",
            "An error occurred: Generic error occurred"
        )

    @patch('tkinter.messagebox.showerror')
    @patch('logging.error')
    def test_handle_exception_value_error(self, mock_log_error, mock_showerror):
        """
        Test the handle_exception method with a ValueError.
        Verifies input validation guidance is provided.
        """
        view = DummyView()
        exception = ValueError("Invalid input")

        # Call the method being tested
        ErrorManager.handle_exception(view, exception)

        # Verify error message box includes input validation guidance
        mock_showerror.assert_called_once_with(
            "Error",
            "An error occurred: Invalid input\nPlease check your input and try again."
        )

    @patch('tkinter.messagebox.showerror')
    @patch('logging.error')
    def test_handle_exception_permission_error(self, mock_log_error, mock_showerror):
        """
        Test the handle_exception method with a PermissionError.
        Verifies permission-related guidance is provided.
        """
        view = DummyView()
        exception = PermissionError("Access denied")

        # Call the method being tested
        ErrorManager.handle_exception(view, exception)

        # Verify error message box includes permission guidance
        mock_showerror.assert_called_once_with(
            "Error",
            "An error occurred: Access denied\nYou do not have permission to perform this action."
        )

    @patch('logging.error')
    def test_log_error(self, mock_log_error):
        """
        Test the log_error method.
        Verifies error logging with optional context.
        """
        exception = ValueError("Test error")
        context = "Logging test"

        # Call the method being tested
        ErrorManager.log_error(exception, context)

        # Verify logging calls
        self.assertEqual(mock_log_error.call_count, 4)
        mock_log_error.assert_any_call(f"Error Type: ValueError")
        mock_log_error.assert_any_call(f"Error Message: Test error")
        mock_log_error.assert_any_call(f"Context: Logging test")
        # The 4th call is typically the full traceback

    @patch('tkinter.messagebox.showwarning')
    def test_show_validation_error(self, mock_showwarning):
        """
        Test the show_validation_error method.
        Verifies validation error message display.
        """
        error_message = "Invalid input detected"

        # Call the method being tested
        ErrorManager.show_validation_error(error_message)

        # Verify warning message box
        mock_showwarning.assert_called_once_with(
            "Validation Error",
            error_message
        )

    @patch('tkinter.messagebox.showinfo')
    def test_show_info(self, mock_showinfo):
        """
        Test the show_info method.
        Verifies informational message display.
        """
        title = "Information"
        message = "Test information message"

        # Call the method being tested
        ErrorManager.show_info(title, message)

        # Verify info message box
        mock_showinfo.assert_called_once_with(title, message)

    @patch('tkinter.messagebox.askyesno')
    def test_confirm_action(self, mock_askyesno):
        """
        Test the confirm_action method.
        Verifies confirmation dialog with both positive and negative responses.
        """
        title = "Confirm Action"
        message = "Are you sure you want to proceed?"

        # Test when user confirms
        mock_askyesno.return_value = True
        result = ErrorManager.confirm_action(title, message)
        self.assertTrue(result)
        mock_askyesno.assert_called_once_with(title, message)

        # Reset mock for second test
        mock_askyesno.reset_mock()
        mock_askyesno.return_value = False

        # Test when user cancels
        result = ErrorManager.confirm_action(title, message)
        self.assertFalse(result)
        mock_askyesno.assert_called_once_with(title, message)


if __name__ == '__main__':
    unittest.main()