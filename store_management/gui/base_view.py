# relative path: store_management/gui/base_view.py
"""
Comprehensive Base View module for the Leatherworking Store Management application.

Provides a robust base class for all GUI views with advanced functionality
for service retrieval, error handling, and common UI operations.
"""

import abc
import logging
import tkinter as tk
import tkinter.messagebox
import tkinter.ttk as ttk
from typing import Any, Type, Optional, Callable, List, Dict, Union

# Import all service interfaces for type hinting and service retrieval
from services.interfaces.inventory_service import IInventoryService
from services.interfaces.material_service import IMaterialService
from services.interfaces.order_service import IOrderService
from services.interfaces.project_service import IProjectService
from services.interfaces.storage_service import IStorageService
from services.interfaces.pattern_service import IPatternService

from typing import Any, Type, Optional, Callable, List, Dict, Union, TypeVar

# Define a generic TypeVar for service retrieval
T = TypeVar('T')


class BaseView(ttk.Frame, abc.ABC):
    """
    Advanced base class for all GUI views in the Leatherworking Store Management application.

    Provides comprehensive functionality for:
    - Dependency injection and service retrieval
    - Error handling and user notifications
    - Common UI components and interactions
    - Logging and debugging support

    Attributes:
        parent (tk.Widget): Parent widget
        app (Any): Application instance with dependency container
        _services (Dict[Type, Any]): Cached service instances
        _logger (logging.Logger): View-specific logger
    """

    def __init__(self, parent: tk.Widget, app: Any):
        """
        Initialize the base view with advanced features.

        Args:
            parent (tk.Widget): Parent widget
            app (Any): Application instance with dependency container
        """
        super().__init__(parent)

        # Application and dependency management
        self.app = app
        self._services: Dict[Type, Any] = {}

        # Create a view-specific logger
        self._logger = logging.getLogger(self.__class__.__module__)

        # UI state management
        self._ui_components: Dict[str, tk.Widget] = {}
        self._data_cache: Dict[str, Any] = {}

        # Action tracking
        self._undo_stack: List[Callable] = []
        self._redo_stack: List[Callable] = []

    def get_service(self, service_type: Type[T]) -> T:
        """
        Retrieve a service from the dependency injection container.

        Args:
            service_type (Type[T]): Type of service to retrieve

        Returns:
            T: Instance of the requested service

        Raises:
            ValueError: If no implementation is found for the service
        """
        try:
            # Check cached services first
            if service_type in self._services:
                self._logger.debug(f"Using cached service: {service_type.__name__}")
                return self._services[service_type]

            # Try getting service from app's container
            if hasattr(self.app, 'container') and self.app.container is not None:
                try:
                    service = self.app.container.get(service_type)
                    self._logger.info(f"Successfully retrieved service: {service_type.__name__}")
                    self._services[service_type] = service
                    return service
                except Exception as container_error:
                    self._logger.debug(f"Container.get failed with {service_type.__name__}: {container_error}")

                    # Try with the service name
                    try:
                        service_name = service_type.__name__
                        service = self.app.container.get(service_name)
                        self._logger.info(f"Retrieved service by name: {service_name}")
                        self._services[service_type] = service
                        return service
                    except Exception as name_error:
                        self._logger.debug(f"Container.get failed with name {service_type.__name__}: {name_error}")

            # Try using app as container
            if hasattr(self.app, 'get') and callable(self.app.get):
                try:
                    service = self.app.get(service_type)
                    self._logger.info(f"Retrieved service from app.get: {service_type.__name__}")
                    self._services[service_type] = service
                    return service
                except Exception as app_get_error:
                    self._logger.debug(f"app.get failed: {app_get_error}")

            # Try app's get_service method
            if hasattr(self.app, 'get_service') and callable(self.app.get_service):
                try:
                    service = self.app.get_service(service_type)
                    self._logger.info(f"Retrieved service from app.get_service: {service_type.__name__}")
                    self._services[service_type] = service
                    return service
                except Exception as app_service_error:
                    self._logger.debug(f"app.get_service failed: {app_service_error}")

            # Last resort: Try to import and create the service directly
            try:
                # Derive module and class names
                interface_name = service_type.__name__
                if interface_name.startswith('I'):
                    implementation_name = interface_name[1:]
                else:
                    implementation_name = interface_name

                # Try to import implementation dynamically
                module_name = f"services.implementations.{implementation_name.lower()}"
                class_name = implementation_name

                self._logger.debug(f"Attempting direct import of {module_name}.{class_name}")
                import importlib
                module = importlib.import_module(module_name)
                implementation_class = getattr(module, class_name)

                # Instantiate the service
                service_instance = implementation_class()
                self._logger.info(f"Dynamically created service: {service_type.__name__}")

                # Cache the service
                self._services[service_type] = service_instance
                return service_instance

            except Exception as import_error:
                self._logger.error(f"Failed to retrieve service {service_type.__name__}")
                self._logger.error(f"Import error: {import_error}")
                raise ValueError(f"No implementation found for {service_type.__name__}") from import_error

        except Exception as e:
            self._logger.error(f"Error retrieving service {service_type.__name__}: {e}")
            raise ValueError(f"Service {service_type.__name__} not available") from e

    def show_message(self,
                     message: str,
                     title: str = "Notification",
                     message_type: str = "info") -> None:
        """
        Display a message to the user with configurable type.

        Args:
            message (str): Message content
            title (str, optional): Message window title. Defaults to "Notification".
            message_type (str, optional): Type of message.
                Defaults to "info".
                Options: "info", "warning", "error", "question"

        Returns:
            Optional[bool]: For question dialogs, returns user's choice
        """
        self._logger.info(f"{message_type.upper()}: {message}")

        message_methods = {
            "info": tkinter.messagebox.showinfo,
            "warning": tkinter.messagebox.showwarning,
            "error": tkinter.messagebox.showerror,
            "question": tkinter.messagebox.askyesno
        }

        method = message_methods.get(message_type.lower(), tkinter.messagebox.showinfo)
        return method(title, message)

    def show_error(self, title: str, message: str):
        """Show an error message dialog - for backward compatibility.

        Args:
            title (str): Dialog title
            message (str): Error message to display
        """
        return self.show_message(message, title, "error")

    def show_warning(self, title: str, message: str):
        """Show a warning message dialog - for backward compatibility.

        Args:
            title (str): Dialog title
            message (str): Warning message to display
        """
        return self.show_message(message, title, "warning")

    def show_info(self, title: str, message: str):
        """Show an information message dialog - for backward compatibility.

        Args:
            title (str): Dialog title
            message (str): Information message to display
        """
        return self.show_message(message, title, "info")

    def confirm(self, title: str, message: str) -> bool:
        """Show a confirmation dialog - for backward compatibility.

        Args:
            title (str): Dialog title
            message (str): Confirmation message

        Returns:
            bool: True if confirmed, False otherwise
        """
        return self.show_message(message, title, "question")

    def create_labeled_entry(self,
                             parent: Union[tk.Widget, ttk.Frame],
                             label: str,
                             default_value: str = "",
                             width: int = 30) -> Dict[str, tk.Widget]:
        """
        Create a labeled entry widget with associated components.

        Args:
            parent (Widget): Parent widget
            label (str): Label text
            default_value (str, optional): Default text in entry. Defaults to "".
            width (int, optional): Width of entry widget. Defaults to 30.

        Returns:
            Dict of created widgets
        """
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, padx=5, pady=2)

        label_widget = ttk.Label(frame, text=label, width=15)
        label_widget.pack(side=tk.LEFT, padx=(0, 5))

        entry_widget = ttk.Entry(frame, width=width)
        entry_widget.insert(0, default_value)
        entry_widget.pack(side=tk.LEFT, expand=True, fill=tk.X)

        return {
            "frame": frame,
            "label": label_widget,
            "entry": entry_widget
        }

    def create_toolbar(self,
                       parent: tk.Widget,
                       buttons: List[Dict[str, Any]] = []) -> ttk.Frame:
        """
        Create a configurable toolbar with action buttons.

        Args:
            parent (tk.Widget): Parent widget
            buttons (List[Dict], optional): List of button configurations

        Returns:
            ttk.Frame: Toolbar frame
        """
        toolbar = ttk.Frame(parent)
        toolbar.pack(side=tk.TOP, fill=tk.X)

        default_buttons = [
            {"text": "New", "command": self.on_new},
            {"text": "Save", "command": self.on_save},
            {"text": "Refresh", "command": self.on_refresh}
        ]

        # Combine default and custom buttons
        all_buttons = default_buttons + buttons

        for btn_config in all_buttons:
            button = ttk.Button(
                toolbar,
                text=btn_config.get('text', 'Button'),
                command=btn_config.get('command', lambda: None)
            )
            button.pack(side=tk.LEFT, padx=2, pady=2)

        return toolbar

    def add_undo_action(self, action: Callable):
        """
        Add an action to the undo stack.

        Args:
            action (Callable): Function to be undone
        """
        self._undo_stack.append(action)
        self._redo_stack.clear()  # Clear redo stack when a new action is added

    def undo(self, event=None):
        """
        Undo the last action if possible.
        """
        if self._undo_stack:
            action = self._undo_stack.pop()
            try:
                # Store the current state for potential redo
                self._redo_stack.append(action)
                action()  # Execute the undo action
                self.show_message("Action undone", message_type="info")
            except Exception as e:
                self._logger.error(f"Undo failed: {e}")
                self.show_message(f"Undo failed: {e}", message_type="error")

    def redo(self, event=None):
        """
        Redo the last undone action if possible.
        """
        if self._redo_stack:
            action = self._redo_stack.pop()
            try:
                action()
                self.show_message("Action redone", message_type="info")
            except Exception as e:
                self._logger.error(f"Redo failed: {e}")
                self.show_message(f"Redo failed: {e}", message_type="error")

    def on_new(self):
        """
        Default handler for new item creation.
        To be overridden by specific view implementations.
        """
        self._logger.info("New item action triggered")
        self.show_message("Create new item", message_type="info")

    def on_edit(self):
        """
        Default handler for item editing.
        To be overridden by specific view implementations.
        """
        self._logger.info("Edit item action triggered")
        self.show_message("Edit item", message_type="info")

    def on_delete(self):
        """
        Default handler for item deletion.
        To be overridden by specific view implementations.
        """
        self._logger.info("Delete item action triggered")
        confirm = self.show_message(
            "Are you sure you want to delete this item?",
            message_type="question"
        )
        if confirm:
            self.show_message("Item deleted", message_type="info")

    def on_save(self):
        """
        Default handler for saving data.
        To be overridden by specific view implementations.
        """
        self._logger.info("Save action triggered")
        self.show_message("Data saved", message_type="info")

    def on_refresh(self):
        """
        Default handler for refreshing view data.
        To be overridden by specific view implementations.
        """
        self._logger.info("Refresh action triggered")
        self.show_message("View refreshed", message_type="info")

    def setup_search(self,
                     parent: tk.Widget,
                     search_handler: Optional[Callable[[str], None]] = None) -> Dict[str, tk.Widget]:
        """
        Create a comprehensive search interface.

        Args:
            parent (tk.Widget): Parent widget
            search_handler (Callable, optional): Function to handle search

        Returns:
            Dict of search interface components
        """
        search_frame = ttk.Frame(parent)
        search_frame.pack(fill=tk.X, padx=5, pady=5)

        search_label = ttk.Label(search_frame, text="Search:")
        search_label.pack(side=tk.LEFT, padx=(0, 5))

        search_entry = ttk.Entry(search_frame, width=30)
        search_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))

        def _internal_search():
            query = search_entry.get()
            if search_handler:
                search_handler(query)
            else:
                self._logger.warning("No search handler defined")

        search_button = ttk.Button(search_frame, text="Search", command=_internal_search)
        search_button.pack(side=tk.LEFT)

        return {
            "frame": search_frame,
            "label": search_label,
            "entry": search_entry,
            "button": search_button
        }