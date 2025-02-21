# store_management/gui/main_window.py

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
from pathlib import Path
from ..application import Application
from .storage.storage_view import StorageView
from .product.product_view import ProductView
from .order.order_view import OrderView
from .shopping_list.shopping_list_view import ShoppingListView


class MainWindow:
    """Main application window"""

    def __init__(self, root, app: Application):
        self.root = root
        self.app = app

        self.root.title("Store Management")
        self.root.geometry("1024x768")

        self.setup_ui()
        self.bind_shortcuts()

    def setup_ui(self):
        """Set up the main UI components"""

        # Create the tab control
        self.tab_control = ttk.Notebook(self.root)

        # Create tabs for each section
        self.storage_tab = ttk.Frame(self.tab_control)
        self.product_tab = ttk.Frame(self.tab_control)
        self.order_tab = ttk.Frame(self.tab_control)
        self.shopping_list_tab = ttk.Frame(self.tab_control)

        # Add tabs to notebook
        self.tab_control.add(self.storage_tab, text="Storage")
        self.tab_control.add(self.product_tab, text="Products")
        self.tab_control.add(self.order_tab, text="Orders")
        self.tab_control.add(self.shopping_list_tab, text="Shopping Lists")

        # Pack the tab control
        self.tab_control.pack(expand=1, fill="both")

        # Create views for each tab
        self.storage_view = StorageView(self.storage_tab, self.app)
        self.product_view = ProductView(self.product_tab, self.app)
        self.order_view = OrderView(self.order_tab, self.app)
        self.shopping_list_view = ShoppingListView(self.shopping_list_tab, self.app)

        # Pack views
        self.storage_view.pack(expand=1, fill="both")
        self.product_view.pack(expand=1, fill="both")
        self.order_view.pack(expand=1, fill="both")
        self.shopping_list_view.pack(expand=1, fill="both")

        # Create status bar
        self.status_bar = ttk.Label(self.root, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def bind_shortcuts(self):
        """Bind global keyboard shortcuts"""
        self.root.bind("<Control-s>", self.save)
        self.root.bind("<Control-o>", self.load)
        self.root.bind("<Control-f>", self.search)
        self.root.bind("<Control-z>", self.undo)
        self.root.bind("<Control-y>", self.redo)

    def save(self, event=None):
        """Global save function"""
        current_view = self.get_current_view()
        if hasattr(current_view, "save"):
            current_view.save()

    def load(self, event=None):
        """Global load function"""
        current_view = self.get_current_view()
        if hasattr(current_view, "load_data"):
            current_view.load_data()

    def search(self, event=None):
        """Global search function"""
        current_view = self.get_current_view()
        if hasattr(current_view, "show_search_dialog"):
            current_view.show_search_dialog()

    def undo(self, event=None):
        """Global undo function"""
        current_view = self.get_current_view()
        if hasattr(current_view, "undo"):
            current_view.undo()

    def redo(self, event=None):
        """Global redo function"""
        current_view = self.get_current_view()
        if hasattr(current_view, "redo"):
            current_view.redo()

    def get_current_view(self):
        """Get the currently active view"""
        current_tab = self.tab_control.index(self.tab_control.select())
        if current_tab == 0:
            return self.storage_view
        elif current_tab == 1:
            return self.product_view
        elif current_tab == 2:
            return self.order_view
        elif current_tab == 3:
            return self.shopping_list_view
        return None

    def set_status(self, message):
        """Set status bar message"""
        self.status_bar.config(text=message)

    def run(self):
        """Start the application main loop"""
        self.root.mainloop()