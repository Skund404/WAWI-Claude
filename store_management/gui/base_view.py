# gui/base_view.py
"""
Base view class for all GUI views in the leatherworking store management application.
"""

import tkinter as tk
from tkinter import messagebox, ttk
import logging
from abc import ABC, abstractmethod
from typing import Any, Type

from di.container import DependencyContainer
from services.interfaces.inventory_service import IInventoryService
from services.interfaces.material_service import IMaterialService
from services.interfaces.order_service import IOrderService
from services.interfaces.project_service import IProjectService
from services.interfaces.storage_service import IStorageService

# Configure logger
logger = logging.getLogger(__name__)


class BaseView(ttk.Frame, ABC):
    """Base class for all views in the application."""

    def __init__(self, parent: tk.Widget, app: Any):
        """
        Initialize the base view.

        Args:
            parent (tk.Widget): Parent widget
            app (Any): Application instance
        """
        super().__init__(parent)
        self.parent = parent
        self.app = app

        # Create or get the singleton container
        self.container = DependencyContainer()

        # Get commonly used services
        # Note: Subclasses should use these properties or get_service for specific needs
        self._material_service = None
        self._project_service = None
        self._order_service = None
        self._inventory_service = None
        self._storage_service = None

        logger.debug(f"Initialized {self.__class__.__name__}")

    @property
    def material_service(self):
        """Lazy-loaded MaterialService property."""
        if self._material_service is None:
            self._material_service = self.get_service(IMaterialService)
        return self._material_service

    @property
    def project_service(self):
        """Lazy-loaded ProjectService property."""
        if self._project_service is None:
            self._project_service = self.get_service(IProjectService)
        return self._project_service

    @property
    def order_service(self):
        """Lazy-loaded OrderService property."""
        if self._order_service is None:
            self._order_service = self.get_service(IOrderService)
        return self._order_service

    @property
    def inventory_service(self):
        """Lazy-loaded InventoryService property."""
        if self._inventory_service is None:
            self._inventory_service = self.get_service(IInventoryService)
        return self._inventory_service

    @property
    def storage_service(self):
        """Lazy-loaded StorageService property."""
        if self._storage_service is None:
            self._storage_service = self.get_service(IStorageService)
        return self._storage_service

    def get_service(self, service_type: Type) -> Any:
        """
        Get a service from the dependency injection container.

        Args:
            service_type (Type): Service interface class

        Returns:
            Any: Service implementation instance
        """
        # First try to get from parent app if it has get_service method
        if hasattr(self.app, 'get_service') and callable(getattr(self.app, 'get_service')):
            try:
                service = self.app.get_service(service_type)
                logger.debug(f"Got {service_type.__name__} from app.get_service")

                # Debug the obtained service
                if service:
                    logger.debug(f"Service type: {type(service)}")
                    logger.debug(f"Service dir: {dir(service)}")

                return service
            except Exception as e:
                logger.warning(f"Error getting {service_type.__name__} from app: {str(e)}")

        # Fall back to container resolve
        try:
            service = self.container.resolve(service_type)
            logger.debug(f"Got {service_type.__name__} from container.resolve")

            # Debug the obtained service
            if service:
                logger.debug(f"Service type: {type(service)}")
                logger.debug(f"Service dir: {dir(service)}")

            return service
        except Exception as e:
            logger.error(f"Error resolving {service_type.__name__} from container: {str(e)}")
            return None

    @abstractmethod
    def setup_ui(self) -> None:
        """
        Set up the user interface.
        This method must be implemented by subclasses.
        """
        pass

    def load_data(self) -> None:
        """
        Load data for the view.
        Subclasses should override this method to load their specific data.
        """
        pass

    def show_error(self, title: str, message: str) -> None:
        """
        Show an error message dialog.

        Args:
            title (str): Dialog title
            message (str): Error message
        """
        logger.error(f"{title}: {message}")
        messagebox.showerror(title, message)

    def show_info(self, title: str, message: str) -> None:
        """
        Show an information message dialog.

        Args:
            title (str): Dialog title
            message (str): Information message
        """
        logger.info(f"{title}: {message}")
        messagebox.showinfo(title, message)

    def show_warning(self, title: str, message: str) -> None:
        """
        Show a warning message dialog.

        Args:
            title (str): Dialog title
            message (str): Warning message
        """
        logger.warning(f"{title}: {message}")
        messagebox.showwarning(title, message)

    def confirm(self, title: str, message: str) -> bool:
        """
        Show a confirmation dialog.

        Args:
            title (str): Dialog title
            message (str): Confirmation message

        Returns:
            bool: True if user confirmed, False otherwise
        """
        return messagebox.askyesno(title, message)

    def set_status(self, message: str) -> None:
        """
        Set status message if the view has a status bar.

        Args:
            message (str): Status message
        """
        if hasattr(self, 'status_bar') and self.status_bar:
            self.status_bar.config(text=message)
        elif hasattr(self, 'status_label') and self.status_label:
            self.status_label.config(text=message)
        else:
            logger.debug(f"Status: {message}")