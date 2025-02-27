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

    def get_service(self, service_type: Type[Any]) -> Any:
        """
        Retrieve a service from the application's dependency container with advanced caching.

        Args:
            service_type (Type): The type/interface of the service to retrieve

        Returns:
            The requested service instance

        Raises:
            ValueError: If the service cannot be retrieved
        """
        try:
            # Check cached services first
            if service_type in self._services:
                return self._services[service_type]

            # Multiple retrieval methods
            service = None
            retrieval_methods = [
                lambda: getattr(self.app, 'get_service', None)(service_type) if hasattr(self.app,
                                                                                        'get_service') else None,
                lambda: getattr(self.app, 'container', None).get(service_type) if hasattr(self.app,
                                                                                          'container') else None,
                lambda: getattr(self, '_get_service_fallback', None)(service_type) if hasattr(self,
                                                                                              '_get_service_fallback') else None
            ]

            for method in retrieval_methods:
                try:
                    service = method()
                    if service is not None:
                        break
                except Exception:
                    continue

            if service is None:
                raise ValueError(f"No implementation found for {service_type.__name__}")

            # Cache the service
            self._services[service_type] = service
            return service

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

    def undo(self):
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

    def redo(self):
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