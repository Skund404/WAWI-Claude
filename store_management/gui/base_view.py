# gui/base_view.py
import abc
import logging
from typing import Any, Type

import tkinter as tk
from tkinter import messagebox, ttk

from services.interfaces.inventory_service import IInventoryService
from services.interfaces.material_service import IMaterialService
from services.interfaces.order_service import IOrderService
from services.interfaces.project_service import IProjectService
from services.interfaces.storage_service import IStorageService


class BaseView(ttk.Frame, abc.ABC):
    """Base class for all views in the application.

    Provides common functionality like service access and UI utilities.
    """

    def __init__(self, parent: tk.Widget, app: Any):
        """Initialize the base view.

        Args:
            parent (tk.Widget): Parent widget
            app (Any): Application instance with dependency container
        """
        super().__init__(parent)
        self.app = app  # Store reference to the application
        self._material_service = None
        self._order_service = None
        self._project_service = None
        self._inventory_service = None
        self._storage_service = None

    def _get_service(self, service_type: Type) -> Any:
        """Retrieve a service from the dependency container.

        Args:
            service_type (Type): Service interface to retrieve

        Returns:
            Any: Service implementation instance
        """
        try:
            return self.app.get_service(service_type)
        except Exception as e:
            logging.getLogger(__name__).error(f"Error getting service {service_type.__name__}: {str(e)}")
            raise

    @property
    def material_service(self) -> IMaterialService:
        """Lazy-loaded material service property.

        Returns:
            IMaterialService: Material service instance
        """
        if self._material_service is None:
            self._material_service = self._get_service(IMaterialService)
        return self._material_service

    @property
    def order_service(self) -> IOrderService:
        """Lazy-loaded order service property.

        Returns:
            IOrderService: Order service instance
        """
        if self._order_service is None:
            self._order_service = self._get_service(IOrderService)
        return self._order_service

    @property
    def project_service(self) -> IProjectService:
        """Lazy-loaded project service property.

        Returns:
            IProjectService: Project service instance
        """
        if self._project_service is None:
            self._project_service = self._get_service(IProjectService)
        return self._project_service

    @property
    def inventory_service(self) -> IInventoryService:
        """Lazy-loaded inventory service property.

        Returns:
            IInventoryService: Inventory service instance
        """
        if self._inventory_service is None:
            self._inventory_service = self._get_service(IInventoryService)
        return self._inventory_service

    @property
    def storage_service(self) -> IStorageService:
        """Lazy-loaded storage service property.

        Returns:
            IStorageService: Storage service instance
        """
        if self._storage_service is None:
            self._storage_service = self._get_service(IStorageService)
        return self._storage_service

    def show_error(self, title: str, message: str):
        """Display an error message dialog.

        Args:
            title (str): Dialog title
            message (str): Error message to display
        """
        messagebox.showerror(title, message)

    def show_info(self, title: str, message: str):
        """Display an informational message dialog.

        Args:
            title (str): Dialog title
            message (str): Information message to display
        """
        messagebox.showinfo(title, message)

    def show_warning(self, title: str, message: str):
        """Display a warning message dialog.

        Args:
            title (str): Dialog title
            message (str): Warning message to display
        """
        messagebox.showwarning(title, message)

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

        # Add standard toolbar buttons
        new_btn = ttk.Button(toolbar, text="New", command=self.on_new)
        new_btn.pack(side=tk.LEFT, padx=2)

        edit_btn = ttk.Button(toolbar, text="Edit", command=self.on_edit)
        edit_btn.pack(side=tk.LEFT, padx=2)

        delete_btn = ttk.Button(toolbar, text="Delete", command=self.on_delete)
        delete_btn.pack(side=tk.LEFT, padx=2)

        save_btn = ttk.Button(toolbar, text="Save", command=self.on_save)
        save_btn.pack(side=tk.LEFT, padx=2)

        refresh_btn = ttk.Button(toolbar, text="Refresh", command=self.on_refresh)
        refresh_btn.pack(side=tk.LEFT, padx=2)

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

        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=5)

        search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=search_var, width=20)
        search_entry.pack(side=tk.LEFT, padx=5)

        def on_search():
            if search_callback and search_var.get():
                search_callback(search_var.get())

        search_entry.bind("<Return>", lambda e: on_search())

        search_button = ttk.Button(search_frame, text="Search", command=on_search)
        search_button.pack(side=tk.LEFT, padx=5)

        return search_frame

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