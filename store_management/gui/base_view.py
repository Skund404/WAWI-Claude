# gui/base_view.py

from typing import Optional, Any, Type
import tkinter as tk
from tkinter import ttk, messagebox
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class BaseView(ttk.Frame, ABC):
    """
    Abstract base class for all views in the application.
    Provides common functionality and interface for views.
    """

    def __init__(self, parent: tk.Widget, app: Any) -> None:
        """
        Initialize the base view.

        Args:
            parent: Parent widget
            app: Application instance for accessing services and configuration
        """
        super().__init__(parent)
        self.parent = parent
        self.app = app
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # Initialize UI elements
        self.setup_ui()

    def get_service(self, service_type: Type) -> Any:
        """
        Get a service instance from the application container.

        Args:
            service_type: Type of service to retrieve

        Returns:
            Service instance
        """
        try:
            return self.app.get_service(service_type)
        except Exception as e:
            self.logger.error(f"Failed to get service {service_type}: {e}")
            raise

    @abstractmethod
    def setup_ui(self) -> None:
        """Set up the user interface elements. Must be implemented by subclasses."""
        pass

    @abstractmethod
    def load_data(self) -> None:
        """Load data into the view. Must be implemented by subclasses."""
        pass

    def show_error(self, title: str, message: str) -> None:
        """
        Display an error message dialog.

        Args:
            title: Dialog title
            message: Error message
        """
        self.logger.error(f"Error: {message}")
        messagebox.showerror(title, message)

    def show_info(self, title: str, message: str) -> None:
        """
        Display an information message dialog.

        Args:
            title: Dialog title
            message: Information message
        """
        messagebox.showinfo(title, message)

    def show_warning(self, title: str, message: str) -> None:
        """
        Display a warning message dialog.

        Args:
            title: Dialog title
            message: Warning message
        """
        self.logger.warning(f"Warning: {message}")
        messagebox.showwarning(title, message)

    def confirm(self, title: str, message: str) -> bool:
        """
        Display a confirmation dialog.

        Args:
            title: Dialog title
            message: Confirmation message

        Returns:
            bool: True if user confirmed, False otherwise
        """
        return messagebox.askyesno(title, message)

    def refresh(self) -> None:
        """Refresh the view's data and update the display."""
        try:
            self.load_data()
        except Exception as e:
            self.logger.error(f"Error refreshing view: {e}")
            self.show_error("Refresh Error", f"Failed to refresh view: {str(e)}")

    def cleanup(self) -> None:
        """Perform cleanup operations before view is destroyed."""
        pass

    def set_status(self, message: str) -> None:
        """Sets the status message in the main window's status bar.

        Args:
            message (str): The status message to display.
        """
        if self.parent and hasattr(self.parent, "set_status"):
            self.parent.set_status(message)
        else:
            logger.warning(
                f"Parent does not have set_status method. Message was: {message}"
            )