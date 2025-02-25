# Relative path: store_management/views/main_window.py

"""
Main window module for the application.

Provides the main application window with tabbed interface for different functionalities.
"""

import logging
import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING, List, Tuple, Type

from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService

# Import view classes - add proper imports for your actual views
# These are placeholder imports that would need to be updated with your actual view classes
if TYPE_CHECKING:
    from application import Application
    from views.project_view import LeatherworkingProjectView
    from views.order_view import OrderView
    from views.pattern_view import PatternView
    from views.storage_view import StorageView
    from views.shopping_list_view import ShoppingListView
    from views.supplier_view import SupplierView
else:
    # This is a placeholder for runtime imports
    # In a real application, you would import these properly
    from views.placeholder import (
        LeatherworkingProjectView, OrderView, PatternView,
        StorageView, ShoppingListView, SupplierView
    )


class MainWindow(ttk.Frame):
    """
    Main application window that manages multiple views and provides
    a tabbed interface for different application functionalities.
    """

    def __init__(self, root: tk.Tk, app: 'Application'):
        """
        Initialize the main window with a tabbed interface.

        Args:
            root (tk.Tk): The root Tkinter window
            app (Application): The main application instance
        """
        super().__init__(root)
        self.root = root
        self.app = app
        self._setup_window()
        self._create_menu()
        self._create_notebook()
        self._create_status_bar()
        logging.info('Main window initialized')

    def _setup_window(self):
        """
        Configure basic window settings.
        """
        self.pack(fill=tk.BOTH, expand=True)
        self.root.minsize(800, 600)

    def _create_menu(self):
        """
        Create the main application menu.
        """
        menu_bar = tk.Menu(self.root)
        self.root.config(menu=menu_bar)

        # File menu
        file_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label='File', menu=file_menu)
        file_menu.add_command(label='New', command=self._on_new)
        file_menu.add_command(label='Open', command=self._on_open)
        file_menu.add_command(label='Save', command=self._on_save)
        file_menu.add_separator()
        file_menu.add_command(label='Exit', command=self._on_exit)

        # Edit menu
        edit_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label='Edit', menu=edit_menu)
        edit_menu.add_command(label='Undo', command=self._on_undo)
        edit_menu.add_command(label='Redo', command=self._on_redo)

        # View menu
        view_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label='View', menu=view_menu)
        view_menu.add_command(label='Refresh', command=self._on_refresh)

    def _create_notebook(self):
        """
        Create a notebook (tabbed interface) with different application views.
        """
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        views = [
            ('Projects', LeatherworkingProjectView),
            ('Orders', OrderView),
            ('Patterns', PatternView),
            ('Storage', StorageView),
            ('Shopping Lists', ShoppingListView),
            ('Suppliers', SupplierView)
        ]

        for title, view_class in views:
            try:
                view = view_class(self.notebook, self.app)
                self.notebook.add(view, text=title)
            except Exception as e:
                logging.error(f'Failed to load {title} view: {e}')

    def _create_status_bar(self):
        """
        Create a status bar at the bottom of the window.
        """
        self.status_var = tk.StringVar()
        self.status_var.set('Ready')
        status_bar = ttk.Label(
            self, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def set_status(self, message: str):
        """
        Update the status bar message.

        Args:
            message (str): Status message to display
        """
        self.status_var.set(message)

    def _on_new(self):
        """Handle New action"""
        logging.info('New action triggered')

    def _on_open(self):
        """Handle Open action"""
        logging.info('Open action triggered')

    def _on_save(self):
        """Handle Save action"""
        logging.info('Save action triggered')

    def _on_undo(self):
        """Handle Undo action"""
        logging.info('Undo action triggered')

    def _on_redo(self):
        """Handle Redo action"""
        logging.info('Redo action triggered')

    def _on_refresh(self):
        """Handle Refresh action"""
        logging.info('Refresh action triggered')

    def _on_exit(self):
        """
        Handle application exit.
        Performs cleanup and closes the application.
        """
        logging.info('Exiting application')
        try:
            self.app.quit()
        except Exception as e:
            logging.error(f'Error during application exit: {e}')
        self.root.quit()