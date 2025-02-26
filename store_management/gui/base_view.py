# gui/base_view.py
"""
Base view module that provides common functionality for all views.
Handles service access, error display, and shared UI components.
"""

import abc
import logging
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any, Type

from di.container import DependencyContainer
from services.interfaces.inventory_service import IInventoryService
from services.interfaces.material_service import IMaterialService
from services.interfaces.order_service import IOrderService
from services.interfaces.project_service import IProjectService
from services.interfaces.storage_service import IStorageService

# Configure logger
logger = logging.getLogger(__name__)


class BaseView(ttk.Frame, abc.ABC):
    """Base class for all application views.

    Provides common functionality for service access, error handling, and UI components.
    """

    def __init__(self, parent: tk.Widget, app: Any):
        """Initialize the base view.

        Args:
            parent (tk.Widget): Parent widget
            app (Any): Application instance with dependency container
        """
        super().__init__(parent)
        self.parent = parent
        self.app = app

    def _get_service(self, service_type: Type):
        """Retrieve a service from the dependency container.

        Args:
            service_type (Type): Service interface to retrieve

        Returns:
            Any: Service implementation instance
        """
        try:
            if hasattr(self.app, 'get_service'):
                return self.app.get_service(service_type)
            elif hasattr(self.app, 'container'):
                return self.app.container.get_service(service_type)
            else:
                logger.error(f"Cannot access service: {service_type.__name__}")
                return None
        except Exception as e:
            logger.error(f"Error getting service {service_type.__name__}: {str(e)}", exc_info=True)
            self.show_error("Service Error", f"Error accessing {service_type.__name__}: {str(e)}")
            return None

    @property
    def material_service(self):
        """Lazy-loaded material service property.

        Returns:
            IMaterialService: Material service instance
        """
        if not hasattr(self, '_material_service'):
            self._material_service = self._get_service(IMaterialService)
        return self._material_service

    @property
    def order_service(self):
        """Lazy-loaded order service property.

        Returns:
            IOrderService: Order service instance
        """
        if not hasattr(self, '_order_service'):
            self._order_service = self._get_service(IOrderService)
        return self._order_service

    @property
    def project_service(self):
        """Lazy-loaded project service property.

        Returns:
            IProjectService: Project service instance
        """
        if not hasattr(self, '_project_service'):
            self._project_service = self._get_service(IProjectService)
        return self._project_service

    @property
    def inventory_service(self):
        """Lazy-loaded inventory service property.

        Returns:
            IInventoryService: Inventory service instance
        """
        if not hasattr(self, '_inventory_service'):
            self._inventory_service = self._get_service(IInventoryService)
        return self._inventory_service

    @property
    def storage_service(self):
        """Lazy-loaded storage service property.

        Returns:
            IStorageService: Storage service instance
        """
        if not hasattr(self, '_storage_service'):
            self._storage_service = self._get_service(IStorageService)
        return self._storage_service

    def show_error(self, title: str, message: str):
        """Display an error message dialog.

        Args:
            title (str): Dialog title
            message (str): Error message to display
        """
        messagebox.showerror(title, message, parent=self)

    def show_info(self, title: str, message: str):
        """Display an informational message dialog.

        Args:
            title (str): Dialog title
            message (str): Information message to display
        """
        messagebox.showinfo(title, message, parent=self)

    def show_warning(self, title: str, message: str):
        """Display a warning message dialog.

        Args:
            title (str): Dialog title
            message (str): Warning message to display
        """
        messagebox.showwarning(title, message, parent=self)

    def show_confirmation(self, title: str, message: str) -> bool:
        """Display a confirmation dialog.

        Args:
            title (str): Dialog title
            message (str): Confirmation message

        Returns:
            bool: True if confirmed, False otherwise
        """
        return messagebox.askyesno(title, message, parent=self)

    def set_status(self, message: str):
        """Update the application status bar message.

        Args:
            message (str): Status message to display
        """
        if hasattr(self.app, 'set_status'):
            self.app.set_status(message)

    def create_toolbar(self, parent: tk.Widget):
        """Create a standard toolbar with common buttons.

        Args:
            parent (tk.Widget): Parent widget

        Returns:
            ttk.Frame: Toolbar frame
        """
        toolbar = ttk.Frame(parent)

        # Common buttons
        ttk.Button(toolbar, text="New", command=self.on_new).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Edit", command=self.on_edit).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Delete", command=self.on_delete).pack(side=tk.LEFT, padx=2)

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)

        ttk.Button(toolbar, text="Save", command=self.on_save).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Refresh", command=self.on_refresh).pack(side=tk.LEFT, padx=2)

        return toolbar

    def create_search_box(self, parent: tk.Widget, search_callback=None):
        """Create a standard search box.

        Args:
            parent (tk.Widget): Parent widget
            search_callback: Function to call when search is triggered

        Returns:
            ttk.Frame: Search box frame
        """
        search_frame = ttk.Frame(parent)

        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=2)

        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=20)
        search_entry.pack(side=tk.LEFT, padx=2)

        if search_callback:
            search_entry.bind("<Return>", search_callback)
            ttk.Button(search_frame, text="Search", command=search_callback).pack(side=tk.LEFT, padx=2)

        return search_frame

    # These methods should be overridden by derived classes

    def on_new(self):
        """Handle new item action."""
        pass

    def on_edit(self):
        """Handle edit item action."""
        pass

    def on_delete(self):
        """Handle delete item action."""
        pass

    def on_save(self):
        """Handle save action."""
        pass

    def on_refresh(self):
        """Handle refresh action."""
        pass