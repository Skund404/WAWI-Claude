# File: store_management/gui/base_view.py
# Description: Base View Component for GUI Applications

import tkinter as tk
import tkinter.ttk as ttk
import tkinter.messagebox as messagebox
from typing import Any, Optional, Type

from application import Application
from services.interfaces.base_service import IBaseService


class BaseView(ttk.Frame):
    """
    Base class for all view components in the application.

    Provides common functionality for GUI views:
    - Service resolution
    - Basic error handling
    - Message dialogs
    - Lifecycle management methods

    Attributes:
        _app (Application): Reference to the main application instance
        _parent (tk.Widget): Parent widget for this view
    """

    def __init__(self, parent: tk.Widget, app: Application):
        """
        Initialize the base view.

        Args:
            parent: Parent widget
            app: Main application instance
        """
        super().__init__(parent)

        # Store references to parent and application
        self._parent = parent
        self._app = app

    def get_service(self, service_type: Type[IBaseService]) -> IBaseService:
        """
        Retrieve a service from the application's dependency container.

        Args:
            service_type: Type of service to retrieve

        Returns:
            Resolved service instance

        Raises:
            ValueError: If service cannot be resolved
        """
        return self._app.get_service(service_type)

    def load_data(self) -> None:
        """
        Load initial data for the view.

        Subclasses should override this method to implement
        data loading logic specific to the view.
        """
        pass

    def save(self) -> None:
        """
        Save current view data.

        Subclasses should override this method to implement
        data saving logic specific to the view.
        """
        pass

    def undo(self) -> None:
        """
        Undo the last action in the view.

        Subclasses should override this method to implement
        undo functionality specific to the view.
        """
        pass

    def redo(self) -> None:
        """
        Redo the last undone action in the view.

        Subclasses should override this method to implement
        redo functionality specific to the view.
        """
        pass

    def show_error(self, title: str, message: str) -> None:
        """
        Display an error message dialog.

        Args:
            title: Title of the error dialog
            message: Error message to display
        """
        messagebox.showerror(title, message)

    def show_info(self, title: str, message: str) -> None:
        """
        Display an information message dialog.

        Args:
            title: Title of the info dialog
            message: Information message to display
        """
        messagebox.showinfo(title, message)

    def show_warning(self, title: str, message: str) -> None:
        """
        Display a warning message dialog.

        Args:
            title: Title of the warning dialog
            message: Warning message to display
        """
        messagebox.showwarning(title, message)

    def confirm(self, title: str, message: str) -> bool:
        """
        Show a confirmation dialog with Yes/No options.

        Args:
            title: Title of the confirmation dialog
            message: Confirmation message to display

        Returns:
            True if user clicks Yes, False otherwise
        """
        return messagebox.askyesno(title, message)

    def set_status(self, message: str) -> None:
        """
        Set status message in the main window.

        Args:
            message: Status message to display
        """
        if hasattr(self._parent, 'set_status'):
            self._parent.set_status(message)