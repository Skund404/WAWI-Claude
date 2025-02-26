# store_management/gui/main_window.py
"""
Main Window for the Leatherworking Store Management Application.

Provides the primary user interface with notebook for different views.
"""

import logging
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any, Optional

# Import views
from gui.inventory.hardware_inventory import HardwareInventoryView
from gui.inventory.product_inventory import ProductInventoryView
from gui.leatherworking.leather_inventory import LeatherInventoryView
from gui.leatherworking.pattern_library import PatternLibrary
from gui.order.order_view import OrderView
from gui.product.project_view import ProjectView
from gui.storage.storage_view import StorageView


class MainWindow:
    """
    Main application window with notebook for different views.

    Manages the primary interface and provides access to various application modules.
    """

    def __init__(self, root: tk.Tk, container: Any):
        """
        Initialize the main window.

        Args:
            root (tk.Tk): The root Tkinter window
            container (Any): Dependency injection container
        """
        try:
            logging.info("Initializing main window")

            # Ensure root window is available
            self.root = root if root else tk.Tk()
            self.container = container

            # Configure root window
            self._setup_window()

            # Create notebook for different views
            self._create_notebook()

            # Create status bar
            self._create_status_bar()

            # Create menu
            self._create_menu()

            logging.info("Main window initialized successfully")

        except Exception as e:
            logging.error(f"Failed to initialize main window: {e}")
            raise

    def _setup_window(self):
        """
        Configure basic window settings.
        """
        try:
            self.root.title("Leatherworking Store Management")
            self.root.geometry("1200x800")
            self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        except Exception as e:
            logging.error(f"Error setting up window: {e}")
            raise

    def _create_notebook(self):
        """
        Create a notebook with tabs for different application modules.
        """
        try:
            # Create notebook
            self.notebook = ttk.Notebook(self.root)
            self.notebook.pack(expand=True, fill='both')

            # Define views to add to notebook
            views = [
                ("Leather Inventory", LeatherInventoryView),
                ("Hardware Inventory", HardwareInventoryView),
                ("Product Inventory", ProductInventoryView),
                ("Pattern Library", PatternLibrary),
                ("Projects", ProjectView),
                ("Orders", OrderView),
                ("Storage", StorageView)
            ]

            # Add tabs dynamically
            for title, view_class in views:
                try:
                    frame = ttk.Frame(self.notebook)
                    view = view_class(frame, self)
                    frame.pack(fill='both', expand=True)
                    self.notebook.add(frame, text=title)
                except Exception as view_error:
                    logging.error(f"Failed to load {title} view: {view_error}")
                    # Create a fallback label if view fails
                    error_label = ttk.Label(
                        frame,
                        text=f"Failed to load {title} view\n{view_error}",
                        foreground='red'
                    )
                    error_label.pack(expand=True, fill='both')
                    self.notebook.add(frame, text=title)

        except Exception as e:
            logging.error(f"Error creating notebook: {e}")
            messagebox.showerror("Initialization Error", f"Could not create application tabs: {e}")
            raise

    def _create_status_bar(self):
        """
        Create a status bar at the bottom of the window.
        """
        try:
            self.status_var = tk.StringVar(value="Ready")
            self.status_bar = ttk.Label(
                self.root,
                textvariable=self.status_var,
                relief=tk.SUNKEN,
                anchor=tk.W
            )
            self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        except Exception as e:
            logging.error(f"Error creating status bar: {e}")

    def _create_menu(self):
        """
        Create the main application menu.
        """
        try:
            # Create main menu bar
            menubar = tk.Menu(self.root)
            self.root.config(menu=menubar)

            # File menu
            file_menu = tk.Menu(menubar, tearoff=0)
            menubar.add_cascade(label="File", menu=file_menu)
            file_menu.add_command(label="New", command=self._on_new)
            file_menu.add_command(label="Open", command=self._on_open)
            file_menu.add_command(label="Save", command=self._on_save)
            file_menu.add_separator()
            file_menu.add_command(label="Exit", command=self._on_closing)

            # Edit menu
            edit_menu = tk.Menu(menubar, tearoff=0)
            menubar.add_cascade(label="Edit", menu=edit_menu)
            edit_menu.add_command(label="Undo", command=self._on_undo)
            edit_menu.add_command(label="Redo", command=self._on_redo)

            # Help menu
            help_menu = tk.Menu(menubar, tearoff=0)
            menubar.add_cascade(label="Help", menu=help_menu)
            help_menu.add_command(label="About", command=self._show_about)

        except Exception as e:
            logging.error(f"Error creating menu: {e}")

    def set_status(self, message: str):
        """
        Update the status bar message.

        Args:
            message (str): Status message to display
        """
        try:
            self.status_var.set(message)
        except Exception as e:
            logging.error(f"Error setting status: {e}")

    def _on_new(self):
        """Handle New action."""
        logging.info("New action triggered")
        self.set_status("Creating new item...")

    def _on_open(self):
        """Handle Open action."""
        logging.info("Open action triggered")
        self.set_status("Opening item...")

    def _on_save(self):
        """Handle Save action."""
        logging.info("Save action triggered")
        self.set_status("Saving...")

    def _on_undo(self):
        """Handle Undo action."""
        logging.info("Undo action triggered")
        self.set_status("Undoing last action...")

    def _on_redo(self):
        """Handle Redo action."""
        logging.info("Redo action triggered")
        self.set_status("Redoing last action...")

    def _on_closing(self):
        """
        Handle application closing.
        Provides confirmation dialog and cleanup.
        """
        try:
            if messagebox.askokcancel("Quit", "Do you want to quit?"):
                logging.info("Application closing")
                self.root.destroy()
        except Exception as e:
            logging.error(f"Error during application closing: {e}")
            self.root.destroy()

    def _show_about(self):
        """
        Show About dialog with application information.
        """
        messagebox.showinfo(
            "About",
            "Leatherworking Store Management\n"
            "Version 1.0\n"
            "Developed for efficient leatherworking project and inventory management."
        )

    def mainloop(self):
        """
        Start the main event loop.
        """
        try:
            # Ensure the window is deiconified and brought to front
            self.root.deiconify()
            self.root.lift()
            self.root.focus_force()

            # Start the main event loop
            self.root.mainloop()
        except Exception as e:
            logging.error(f"Error in main event loop: {e}")
            raise