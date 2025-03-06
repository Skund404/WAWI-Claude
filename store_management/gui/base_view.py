# gui/base_view.py
import abc
import importlib
import logging
import tkinter as tk
import tkinter.messagebox
import tkinter.ttk as ttk
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union

from services.interfaces.inventory_service import IInventoryService
from services.interfaces.material_service import IMaterialService
from services.interfaces.sale_service import ISaleService
from services.interfaces.pattern_service import IPatternService
from services.interfaces.project_service import IProjectService
from services.interfaces.storage_service import IStorageService
from services.base_service import BaseApplicationException, NotFoundError, ValidationError

# Type variable for generic services
T = TypeVar('T')


class BaseView(ttk.Frame, abc.ABC):
    """Base class for all application views.

    Provides common functionality for handling user interactions, error management,
    displaying messages, and performing undo/redo operations.
    """

    def __init__(self, parent: tk.Widget, app: Any):
        """Initialize the base view with advanced features.

        Args:
            parent (tk.Widget): Parent widget
            app (Any): Application instance with dependency container
        """
        super().__init__(parent)
        self.parent = parent
        self.app = app
        self.logger = logging.getLogger(self.__class__.__name__)

        # Initialize undo/redo stacks
        self._undo_stack = []
        self._redo_stack = []

        # Set up keyboard shortcuts
        self.bind_all("<Control-z>", self.undo)
        self.bind_all("<Control-y>", self.redo)

        # Set up basic service injections if available
        self._material_service = None
        self._inventory_service = None
        self._order_service = None
        self._project_service = None
        self._pattern_service = None
        self._storage_service = None

        # Try to get services from app container
        if hasattr(app, 'get_service'):
            try:
                self._material_service = app.get_service(IMaterialService)
            except Exception as e:
                self.logger.debug(f"Material service not available: {str(e)}")

            try:
                self._inventory_service = app.get_service(IInventoryService)
            except Exception as e:
                self.logger.debug(f"Inventory service not available: {str(e)}")

            try:
                self._order_service = app.get_service(ISaleService)
            except Exception as e:
                self.logger.debug(f"Order service not available: {str(e)}")

            try:
                self._project_service = app.get_service(IProjectService)
            except Exception as e:
                self.logger.debug(f"Project service not available: {str(e)}")

            try:
                self._pattern_service = app.get_service(IPatternService)
            except Exception as e:
                self.logger.debug(f"Pattern service not available: {str(e)}")

            try:
                self._storage_service = app.get_service(IStorageService)
            except Exception as e:
                self.logger.debug(f"Storage service not available: {str(e)}")

        # Internal search state
        self._search_query = ""
        self._search_filter = {}

    def show_error(self, title: str, message: str):
        """Show an error message dialog - for backward compatibility.

        Args:
            title (str): Dialog title
            message (str): Error message to display
        """
        self.logger.error(f"{title}: {message}")
        tkinter.messagebox.showerror(title, message)

    def show_warning(self, title: str, message: str):
        """Show a warning message dialog - for backward compatibility.

        Args:
            title (str): Dialog title
            message (str): Warning message to display
        """
        self.logger.warning(f"{title}: {message}")
        tkinter.messagebox.showwarning(title, message)

    def show_info(self, title: str, message: str):
        """Show an information message dialog - for backward compatibility.

        Args:
            title (str): Dialog title
            message (str): Information message to display
        """
        self.logger.info(f"{title}: {message}")
        tkinter.messagebox.showinfo(title, message)

    def handle_service_error(self, error: Exception, context: str = "") -> bool:
        """Handle service layer errors consistently.

        Args:
            error (Exception): The error that occurred
            context (str, optional): Additional context for the error. Defaults to "".

        Returns:
            bool: True if error was handled, False if unknown error
        """
        error_message = str(error)
        if context:
            error_message = f"{context}: {error_message}"

        if isinstance(error, ValidationError):
            # Handle validation errors
            self.show_error("Validation Error", error_message)
            return True
        elif isinstance(error, NotFoundError):
            # Handle not found errors
            self.show_error("Not Found", error_message)
            return True
        elif isinstance(error, BaseApplicationException):
            # Handle other application errors
            self.show_error("Application Error", error_message)
            return True
        else:
            # Unknown error, log full details
            self.logger.exception(f"Unhandled error in {self.__class__.__name__}: {error_message}")
            self.show_error("Unexpected Error",
                            "An unexpected error occurred. Please check the logs for details.")
            return False

    def validate_input(self, input_data: Dict[str, Any]) -> Dict[str, str]:
        """Validate input data before sending to service layer.

        Args:
            input_data (Dict[str, Any]): Data to validate

        Returns:
            Dict[str, str]: Dictionary of field errors, empty if valid
        """
        errors = {}

        # Perform basic validations
        for key, value in input_data.items():
            if isinstance(value, str) and 'required' in key.lower() and not value.strip():
                errors[key] = "This field is required"

        return errors

    def add_undo_action(self, action: Callable):
        """Add an action to the undo stack.

        Args:
            action (Callable): Function to be undone
        """
        self._undo_stack.append(action)
        # Clear redo stack when a new action is performed
        self._redo_stack = []

    def undo(self, event=None):
        """Undo the last action if possible."""
        if not self._undo_stack:
            self.logger.debug("No actions to undo")
            return

        action = self._undo_stack.pop()
        try:
            # Store the inverse action for redo
            inverse_action = action()
            if inverse_action:
                self._redo_stack.append(inverse_action)
        except Exception as e:
            self.logger.error(f"Error undoing action: {str(e)}")
            self.show_error("Undo Failed", f"Failed to undo action: {str(e)}")

    def redo(self, event=None):
        """Redo the last undone action if possible."""
        if not self._redo_stack:
            self.logger.debug("No actions to redo")
            return

        action = self._redo_stack.pop()
        try:
            # Store the inverse action for undo
            inverse_action = action()
            if inverse_action:
                self._undo_stack.append(inverse_action)
        except Exception as e:
            self.logger.error(f"Error redoing action: {str(e)}")
            self.show_error("Redo Failed", f"Failed to redo action: {str(e)}")

    def on_new(self):
        """Default handler for new item creation.
        To be overridden by specific view implementations."""
        self.logger.debug("on_new called in base class")
        pass

    def on_edit(self):
        """Default handler for item editing.
        To be overridden by specific view implementations."""
        self.logger.debug("on_edit called in base class")
        pass

    def on_delete(self):
        """Default handler for item deletion.
        To be overridden by specific view implementations."""
        self.logger.debug("on_delete called in base class")
        pass

    def on_save(self):
        """Default handler for saving data.
        To be overridden by specific view implementations."""
        self.logger.debug("on_save called in base class")
        pass

    def on_refresh(self):
        """Default handler for refreshing view data.
        To be overridden by specific view implementations."""
        self.logger.debug("on_refresh called in base class")
        pass

    def execute_with_error_handling(self, func: Callable, error_context: str = "",
                                    success_message: Optional[str] = None) -> Optional[Any]:
        """Execute a function with standard error handling.

        Args:
            func (Callable): Function to execute
            error_context (str, optional): Context for error messages. Defaults to "".
            success_message (Optional[str], optional): Message to show on success. Defaults to None.

        Returns:
            Optional[Any]: Result of the function or None if error occurred
        """
        try:
            result = func()
            if success_message:
                self.show_info("Success", success_message)
            return result
        except Exception as e:
            self.handle_service_error(e, error_context)
            return None

    def search(self, query: str, **filters):
        """Perform a search with filters.

        Args:
            query (str): Text search query
            **filters: Additional filters to apply

        Returns:
            List[Any]: Search results
        """
        self._search_query = query
        self._search_filter = filters
        return self._internal_search()

    def _internal_search(self):
        """Internal search implementation.
        To be overridden by specific view implementations.

        Returns:
            List[Any]: Search results
        """
        self.logger.debug(f"Internal search called with query: {self._search_query}, filters: {self._search_filter}")
        return []

    def get_service(self, service_type: Type[T]) -> Optional[T]:
        """Get a service from the application's dependency container.

        Args:
            service_type (Type[T]): Type of service to get

        Returns:
            Optional[T]: Service instance or None if not available
        """
        if not hasattr(self.app, 'get_service'):
            self.logger.error("App does not provide get_service method")
            return None

        try:
            return self.app.get_service(service_type)
        except Exception as e:
            self.logger.error(f"Error getting service {service_type.__name__}: {str(e)}")
            return None

    def confirm_action(self, title: str, message: str) -> bool:
        """Ask for confirmation before proceeding with an action.

        Args:
            title (str): Dialog title
            message (str): Confirmation message

        Returns:
            bool: True if confirmed, False otherwise
        """
        return tkinter.messagebox.askyesno(title, message)

    def cleanup(self):
        """Clean up resources before destroying the view.
        Can be overridden by specific views to perform custom cleanup.
        """
        self.logger.debug("Cleanup called in base view")
        # Default implementation does nothing
        pass