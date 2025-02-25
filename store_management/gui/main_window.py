# gui/main_window.py
"""
Main application window for the Leatherworking Store Management System.

This module provides the primary interface for the application,
integrating various views and services.
"""

import tkinter as tk
from tkinter import ttk
import logging

# Import views
from gui.leatherworking.pattern_library import PatternLibrary
from gui.order.order_view import OrderView
from gui.storage.storage_view import StorageView
from gui.shopping_list.shopping_list_view import ShoppingListView
from gui.leatherworking.leather_inventory import LeatherInventoryView
from gui.leatherworking.project_dashboard import ProjectDashboard
from gui.reports.report_manager import ReportDialog


class MainWindow:
    """
    Main application window managing multiple views and services.

    Attributes:
        root (tk.Tk): The root Tkinter window
        container (DependencyContainer): Dependency injection container
        logger (logging.Logger): Logger for the main window
    """

    def __init__(self, root, container):
        """
        Initialize the main application window.

        Args:
            root (tk.Tk): The root Tkinter window
            container (DependencyContainer): Dependency injection container
        """
        self.root = root
        self.container = container
        self.logger = logging.getLogger(__name__)

        # Configure window
        self._setup_window()

        # Create notebook (tabbed interface)
        self._create_notebook()

        # Create menubar
        self._create_menu()

        # Optional: Status bar
        self._create_status_bar()

    def _setup_window(self):
        """
        Configure basic window settings.
        """
        self.root.title("Leatherworking Store Management")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)

    def _create_notebook(self):
        """
        Create a notebook with different application views.
        """
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill='both')

        # Define view tabs
        view_configs = [
            ("Pattern Library", PatternLibrary),
            ("Project Dashboard", ProjectDashboard),
            ("Orders", OrderView),
            ("Leather Inventory", LeatherInventoryView),
            ("Storage", StorageView),
            ("Shopping List", ShoppingListView)
        ]

        # Create tabs
        for title, view_class in view_configs:
            try:
                tab = view_class(self.notebook, self)
                self.notebook.add(tab, text=title)
            except Exception as e:
                self.logger.error(f"Failed to create tab {title}: {e}")

    def _create_menu(self):
        """
        Create the main application menu.
        """
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New", command=self._on_new)
        file_menu.add_command(label="Open", command=self._on_open)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # Reports menu
        reports_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Reports", menu=reports_menu)
        reports_menu.add_command(label="Generate Report", command=self._open_report_dialog)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._show_about)

    def _create_status_bar(self):
        """
        Create a status bar at the bottom of the window.
        """
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = tk.Label(
            self.root,
            textvariable=self.status_var,
            bd=1,
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def set_status(self, message):
        """
        Update the status bar message.

        Args:
            message (str): Status message to display
        """
        self.status_var.set(message)

    def _on_new(self):
        """
        Handle New action in the menu.
        Currently a placeholder.
        """
        self.set_status("New action triggered")

    def _on_open(self):
        """
        Handle Open action in the menu.
        Currently a placeholder.
        """
        self.set_status("Open action triggered")

    def _open_report_dialog(self):
        """
        Open the report generation dialog.
        """
        try:
            report_dialog = ReportDialog(self.root)
        except Exception as e:
            self.logger.error(f"Failed to open report dialog: {e}")
            tk.messagebox.showerror("Error", f"Could not open report dialog: {e}")

    def _show_about(self):
        """
        Show About dialog with application information.
        """
        tk.messagebox.showinfo(
            "About Leatherworking Store Management",
            "Leatherworking Store Management System\n\n"
            "Version: 1.0\n"
            "Developed by Your Team\n"
            "© 2025 All Rights Reserved"
        )

    def get_service(self, service_type):
        """
        Get a service from the dependency injection container.

        Args:
            service_type (type): Type of service to retrieve

        Returns:
            The requested service instance
        """
        return self.container.resolve(service_type)