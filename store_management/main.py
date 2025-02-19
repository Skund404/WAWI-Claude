# main.py
import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
from typing import Dict

# Determine the absolute path to the project root
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)

# Ensure the project root is in the Python path
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from store_management.config import APP_NAME, WINDOW_SIZE, TABLES, get_database_path

# Ensure the database is initialized before other modules are imported
from database.database_setup import ensure_database
ensure_database()

from store_management.gui.storage.shelf_view import ShelfView
from store_management.gui.product.recipe_view import RecipeView
from store_management.gui.product.storage_view import StorageView
from store_management.gui.storage.sorting_system_view import SortingSystemView
from store_management.gui.order.incoming_goods_view import IncomingGoodsView
from store_management.gui.order.shopping_list_view import ShoppingListView
from store_management.gui.order.supplier_view import SupplierView


class MainWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(APP_NAME)
        self.root.geometry(WINDOW_SIZE)

        # Create main notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill='both')

        # Initialize views
        self.views: Dict[str, ttk.Frame] = {}
        self.setup_views()

        # Bind keyboard shortcuts
        self.bind_shortcuts()

    def setup_views(self):
        """Setup all view tabs"""
        # Product group
        product_notebook = ttk.Notebook(self.notebook)
        self.notebook.add(product_notebook, text='Product')

        # Add Storage view under Product
        storage_frame = ttk.Frame(product_notebook)
        product_notebook.add(storage_frame, text='Storage')
        self.views['storage'] = StorageView(storage_frame)
        self.views['storage'].pack(expand=True, fill='both')

        # Add Recipe view under Product
        recipe_frame = ttk.Frame(product_notebook)
        product_notebook.add(recipe_frame, text='Recipe')
        self.views['recipe'] = RecipeView(recipe_frame)  # Corrected line
        self.views['recipe'].pack(expand=True, fill='both')

        # Storage group
        storage_notebook = ttk.Notebook(self.notebook)
        self.notebook.add(storage_notebook, text='Storage')

        # Add Shelf view under Storage
        shelf_frame = ttk.Frame(storage_notebook)
        storage_notebook.add(shelf_frame, text='Shelf')
        self.views['shelf'] = ShelfView(shelf_frame)
        self.views['shelf'].pack(expand=True, fill='both')

        # Add Sorting System view under Storage
        sorting_frame = ttk.Frame(storage_notebook)
        storage_notebook.add(sorting_frame, text='Sorting System')
        self.views['sorting'] = SortingSystemView(sorting_frame)
        self.views['sorting'].pack(expand=True, fill='both')

        # Order group
        order_notebook = ttk.Notebook(self.notebook)
        self.notebook.add(order_notebook, text='Order')

        # Add Incoming Goods view
        incoming_frame = ttk.Frame(order_notebook)
        order_notebook.add(incoming_frame, text='Incoming Goods')
        self.views['incoming'] = IncomingGoodsView(incoming_frame)
        self.views['incoming'].pack(expand=True, fill='both')

        # Add Shopping List view
        shopping_frame = ttk.Frame(order_notebook)
        order_notebook.add(shopping_frame, text='Shopping List')
        self.views['shopping'] = ShoppingListView(shopping_frame)
        self.views['shopping'].pack(expand=True, fill='both')

        # Add Supplier view
        supplier_frame = ttk.Frame(order_notebook)
        order_notebook.add(supplier_frame, text='Supplier')
        self.views['supplier'] = SupplierView(supplier_frame)
        self.views['supplier'].pack(expand=True, fill='both')

    def bind_shortcuts(self):
        """Bind global keyboard shortcuts"""
        self.root.bind('<Control-z>', self.undo)
        self.root.bind('<Control-y>', self.redo)
        self.root.bind('<Control-s>', self.save)
        self.root.bind('<Control-o>', self.load)
        self.root.bind('<Control-f>', self.search)

    def undo(self, event=None):
        """Global undo function"""
        current_view = self.get_current_view()
        if current_view and hasattr(current_view, 'undo'):
            current_view.undo()

    def redo(self, event=None):
        """Global redo function"""
        current_view = self.get_current_view()
        if current_view and hasattr(current_view, 'redo'):
            current_view.redo()

    def save(self, event=None):
        """Global save function"""
        current_view = self.get_current_view()
        if current_view and hasattr(current_view, 'save'):
            current_view.save()

    def load(self, event=None):
        """Global load function"""
        current_view = self.get_current_view()
        if current_view and hasattr(current_view, 'load'):
            current_view.load()

    def search(self, event=None):
        """Global search function"""
        current_view = self.get_current_view()
        if current_view and hasattr(current_view, 'show_search_dialog'):
            current_view.show_search_dialog()

    def get_current_view(self):
        """Get the currently active view"""
        current_tab = self.notebook.select()
        if current_tab:
            tab_id = self.notebook.index(current_tab)

            # Get the notebook widget for the current tab
            notebook = self.notebook.nametowidget(current_tab)

            # If it's a nested notebook, get the current subtab
            if isinstance(notebook, ttk.Notebook):
                current_subtab = notebook.select()
                if current_subtab:
                    subtab_id = notebook.index(current_subtab)
                    subtab_name = notebook.tab(subtab_id, 'text').lower().replace(' ', '_')
                    return self.views.get(subtab_name)

            # If it's not a nested notebook, get the view directly
            tab_name = self.notebook.tab(tab_id, 'text').lower()
            return self.views.get(tab_name)

        return None

    def run(self):
        """Start the application"""
        self.root.mainloop()


if __name__ == "__main__":
    app = MainWindow()
    app.run()