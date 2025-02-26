# gui/base_view.py
"""
Base View class for the Leatherworking Store Management Application.

Provides a common base for all GUI views with dependency injection
and service access capabilities.
"""

import abc
import logging
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any, Type

from di.container import DependencyContainer


class BaseView(ttk.Frame, abc.ABC):
    """
    Base class for all GUI views in the application.

    Provides common functionality for service access, error handling,
    and basic view setup.
    """

    def __init__(self, parent: tk.Widget, app: Any):
        """
        Initialize the base view.

        Args:
            parent (tk.Widget): Parent widget
            app (Any): Application instance with dependency container
        """
        super().__init__(parent)

        # Store application reference
        self._app = app
        self._logger = logging.getLogger(self.__class__.__name__)

    def _get_service(self, service_type: Type):
        """
        Retrieve a service from the dependency container.

        Args:
            service_type (Type): Service interface to retrieve

        Returns:
            Any: Service implementation instance
        """
        try:
            # Ensure app has a get_service method (compatible with DependencyContainer)
            return self._app.get_service(service_type)
        except Exception as e:
            self._logger.error(f"Error retrieving service {service_type}: {e}")
            self.show_error("Service Error", f"Could not load {service_type.__name__}")
            return None

    @property
    def material_service(self):
        """
        Lazy-loaded material service property.

        Returns:
            IMaterialService: Material service instance
        """
        from services.interfaces.material_service import IMaterialService
        return self._get_service(IMaterialService)

    @property
    def order_service(self):
        """
        Lazy-loaded order service property.

        Returns:
            IOrderService: Order service instance
        """
        from services.interfaces.order_service import IOrderService
        return self._get_service(IOrderService)

    @property
    def project_service(self):
        """
        Lazy-loaded project service property.

        Returns:
            IProjectService: Project service instance
        """
        from services.interfaces.project_service import IProjectService
        return self._get_service(IProjectService)

    @property
    def inventory_service(self):
        """
        Lazy-loaded inventory service property.

        Returns:
            IInventoryService: Inventory service instance
        """
        from services.interfaces.inventory_service import IInventoryService
        return self._get_service(IInventoryService)

    @property
    def storage_service(self):
        """
        Lazy-loaded storage service property.

        Returns:
            IStorageService: Storage service instance
        """
        from services.interfaces.storage_service import IStorageService
        return self._get_service(IStorageService)

    def show_error(self, title: str, message: str):
        """
        Display an error message dialog.

        Args:
            title (str): Dialog title
            message (str): Error message to display
        """
        messagebox.showerror(title, message)

    def show_info(self, title: str, message: str):
        """
        Display an informational message dialog.

        Args:
            title (str): Dialog title
            message (str): Information message to display
        """
        messagebox.showinfo(title, message)

    def show_warning(self, title: str, message: str):
        """
        Display a warning message dialog.

        Args:
            title (str): Dialog title
            message (str): Warning message to display
        """
        messagebox.showwarning(title, message)

    def confirm(self, title: str, message: str) -> bool:
        """
        Display a confirmation dialog.

        Args:
            title (str): Dialog title
            message (str): Confirmation message to display

        Returns:
            bool: True if user confirms, False otherwise
        """
        return messagebox.askyesno(title, message)