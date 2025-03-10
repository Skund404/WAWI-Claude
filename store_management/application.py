# application.py
"""
Main application entry point for the Leatherworking application.
This module initializes the DI container and provides access to services.
"""

import logging
import tkinter as tk
from typing import Any, Dict, Optional, Type, TypeVar

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import DI components
from di.setup import initialize, verify_container
from di.provider import get_container, set_container
from di.container import Container, ResolutionError

# Type variable for generic service resolution
T = TypeVar('T')


class Application:
    """
    Main application class that configures and manages the application.
    """

    def __init__(self):
        """Initialize the application and set up dependencies."""
        self.container = None
        self.root = None

    def initialize(self) -> bool:
        """
        Initialize the application.

        Returns:
            True if initialization succeeded, False otherwise
        """
        try:
            # Initialize DI container
            logger.info("Initializing application")
            self.container = initialize()

            # Verify critical services
            if not verify_container(self.container):
                logger.error("Application initialization failed: container verification failed")
                return False

            logger.info("Application initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Application initialization failed: {str(e)}")
            return False

    def get_service(self, service_type: Type[T]) -> Optional[T]:
        """
        Get a service from the DI container.

        Args:
            service_type: Type of service to get

        Returns:
            Service instance or None if resolution fails
        """
        try:
            return self.container.resolve(service_type)
        except ResolutionError as e:
            logger.error(f"Failed to resolve service {service_type.__name__}: {str(e)}")
            return None

    def start_gui(self) -> None:
        """Start the graphical user interface."""
        try:
            # Create Tkinter root window
            self.root = tk.Tk()
            self.root.title("Leatherworking Management System")
            self.root.geometry("1200x800")

            # Initialize main window
            from gui.main_window import MainWindow
            main_window = MainWindow(self.root)

            # Run the application
            logger.info("Starting GUI application")
            self.root.mainloop()
        except Exception as e:
            logger.error(f"Error starting GUI: {str(e)}")
            raise


# Global application instance
app = Application()


def get_app() -> Application:
    """
    Get the global application instance.

    Returns:
        Application instance
    """
    return app


def get_service(service_type: Type[T]) -> Optional[T]:
    """
    Get a service instance from the global application.

    Args:
        service_type: Type of service to get

    Returns:
        Service instance or None if resolution fails
    """
    return app.get_service(service_type)


# Initialize application when module is imported
if not app.initialize():
    logger.error("Application initialization failed!")

# gui/main_window.py
"""
Main window implementation for the Leatherworking application.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from typing import Dict, Optional, List

# Import from our application
from application import get_app, get_service
from di.inject import inject

# Import service interfaces
from services.interfaces.customer_service import ICustomerService
from services.interfaces.project_service import IProjectService
from services.interfaces.inventory_service import IInventoryService

# Import views
from gui.base.base_view import BaseView
from gui.customers.customer_view import CustomerView
from gui.projects.project_view import ProjectView
from gui.inventory.material_inventory import MaterialInventoryView


class MainWindow:
    """Main application window implementation."""

    @inject
    def __init__(self, root: tk.Tk,
                 customer_service: ICustomerService,
                 project_service: IProjectService,
                 inventory_service: IInventoryService):
        """
        Initialize the main window with dependencies.

        Args:
            root: Tkinter root window
            customer_service: Customer service for customer operations
            project_service: Project service for project operations
            inventory_service: Inventory service for inventory operations
        """
        self.root = root
        self.customer_service = customer_service
        self.project_service = project_service
        self.inventory_service = inventory_service
        self.logger = logging.getLogger(__name__)

        # Initialize view containers
        self.current_view: Optional[BaseView] = None
        self.views: Dict[str, BaseView] = {}

        # Set up UI components
        self._setup_ui()

        # Start with dashboard
        self._show_dashboard()

    def _setup_ui(self) -> None:
        """Set up UI components."""
        # Create main layout frames
        self.sidebar = ttk.Frame(self.root, width=200, style='Sidebar.TFrame')
        self.content = ttk.Frame(self.root)

        # Configure grid layout
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)

        # Place frames
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.content.grid(row=0, column=1, sticky="nsew")

        # Configure sidebar
        self.sidebar.grid_propagate(False)  # Keep fixed width

        # Add sidebar buttons
        self._create_sidebar_buttons()

    def _create_sidebar_buttons(self) -> None:
        """Create sidebar navigation buttons."""
        # Add application title
        title_label = ttk.Label(self.sidebar, text="Leatherworking\nManagement",
                                font=("Helvetica", 12, "bold"))
        title_label.pack(pady=20)

        # Create navigation buttons
        buttons = [
            ("Dashboard", self._show_dashboard),
            ("Customers", self._show_customers),
            ("Projects", self._show_projects),
            ("Inventory", self._show_inventory),
            ("Sales", self._show_sales),
            ("Purchases", self._show_purchases),
            ("Tools", self._show_tools),
            ("Settings", self._show_settings)
        ]

        # Add buttons to sidebar
        for text, command in buttons:
            btn = ttk.Button(self.sidebar, text=text, command=command, width=18)
            btn.pack(pady=5)

        # Add exit button at bottom
        exit_btn = ttk.Button(self.sidebar, text="Exit", command=self.root.destroy, width=18)
        exit_btn.pack(side=tk.BOTTOM, pady=20)

    def _show_view(self, view_name: str, view_class, *args, **kwargs) -> None:
        """
        Show a view, creating it if needed.

        Args:
            view_name: Name of the view
            view_class: Class of the view
            *args: Arguments for view constructor
            **kwargs: Keyword arguments for view constructor
        """
        # Hide current view if any
        if self.current_view:
            self.current_view.hide()

        # Create view if it doesn't exist
        if view_name not in self.views:
            try:
                self.views[view_name] = view_class(self.content, *args, **kwargs)
            except Exception as e:
                self.logger.error(f"Error creating view {view_name}: {str(e)}")
                messagebox.showerror("Error", f"Failed to load {view_name} view: {str(e)}")
                return

        # Show the view
        self.current_view = self.views[view_name]
        self.current_view.show()

    # View handlers
    def _show_dashboard(self) -> None:
        """Show the dashboard view."""
        # In a real application, this would load a dashboard view
        # For now, just show a placeholder
        for widget in self.content.winfo_children():
            widget.destroy()

        # Create placeholder dashboard
        frame = ttk.Frame(self.content)
        frame.pack(fill=tk.BOTH, expand=True)

        label = ttk.Label(frame, text="Dashboard\nWelcome to the Leatherworking Management System",
                          font=("Helvetica", 14))
        label.pack(pady=50)

        # Show some stats
        try:
            # Get some basic stats
            customer_count = len(self.customer_service.get_all())
            project_count = len(self.project_service.get_all())

            # Create stats frame
            stats_frame = ttk.Frame(frame)
            stats_frame.pack(pady=20)

            # Add stat cards
            self._create_stat_card(stats_frame, "Customers", customer_count, 0)
            self._create_stat_card(stats_frame, "Projects", project_count, 1)
            self._create_stat_card(stats_frame, "Active Projects",
                                   len(self.project_service.get_by_status("IN_PROGRESS")), 2)
        except Exception as e:
            self.logger.error(f"Error loading dashboard stats: {str(e)}")

    def _create_stat_card(self, parent: ttk.Frame, title: str, value: int, column: int) -> None:
        """
        Create a statistics card for the dashboard.

        Args:
            parent: Parent frame
            title: Card title
            value: Statistic value
            column: Grid column
        """
        card = ttk.Frame(parent, borderwidth=1, relief="solid", padding=10)
        card.grid(row=0, column=column, padx=10)

        ttk.Label(card, text=title, font=("Helvetica", 10)).pack()
        ttk.Label(card, text=str(value), font=("Helvetica", 18, "bold")).pack(pady=5)

    def _show_customers(self) -> None:
        """Show the customers view."""
        from gui.customers.customer_view import CustomerView
        self._show_view("customers", CustomerView)

    def _show_projects(self) -> None:
        """Show the projects view."""
        from gui.projects.project_view import ProjectView
        self._show_view("projects", ProjectView)

    def _show_inventory(self) -> None:
        """Show the inventory view."""
        from gui.inventory.material_inventory import MaterialInventoryView
        self._show_view("inventory", MaterialInventoryView)

    def _show_sales(self) -> None:
        """Show the sales view."""
        # Placeholder for future implementation
        messagebox.showinfo("Not Implemented", "Sales view is not yet implemented")

    def _show_purchases(self) -> None:
        """Show the purchases view."""
        # Placeholder for future implementation
        messagebox.showinfo("Not Implemented", "Purchases view is not yet implemented")

    def _show_tools(self) -> None:
        """Show the tools view."""
        # Placeholder for future implementation
        messagebox.showinfo("Not Implemented", "Tools view is not yet implemented")

    def _show_settings(self) -> None:
        """Show the settings view."""
        # Placeholder for future implementation
        messagebox.showinfo("Not Implemented", "Settings view is not yet implemented")