import tkinter as tk
from tkinter import ttk
from typing import Dict
from pathlib import Path
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import APP_NAME, WINDOW_SIZE, DATABASE_PATH
from gui.shelf_view import ShelfView
from gui.recipe_view import RecipeView
from gui.storage_view import StorageView
from gui.sorting_system_view import SortingSystemView
from gui.order.incoming_goods_view import IncomingGoodsView
from gui.order.shopping_list_view import ShoppingListView
from gui.order.supplier_view import SupplierView


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

        # Add Recipe view under Product
        recipe_frame = ttk.Frame(product_notebook)
        product_notebook.add(recipe_frame, text='Recipe')
        self.views['recipe'] = RecipeView(recipe_frame)

        # Storage group
        storage_notebook = ttk.Notebook(self.notebook)
        self.notebook.add(storage_notebook, text='Storage')

        # Add Shelf view under Storage
        shelf_frame = ttk.Frame(storage_notebook)
        storage_notebook.add(shelf_frame, text='Shelf')
        self.views['shelf'] = ShelfView(shelf_frame)

        # Add Sorting System view under Storage
        sorting_frame = ttk.Frame(storage_notebook)
        storage_notebook.add(sorting_frame, text='Sorting System')
        self.views['sorting'] = SortingSystemView(sorting_frame)

        # Order group
        order_notebook = ttk.Notebook(self.notebook)
        self.notebook.add(order_notebook, text='Order')

        # Add Incoming Goods view
        incoming_frame = ttk.Frame(order_notebook)
        order_notebook.add(incoming_frame, text='Incoming Goods')
        self.views['incoming'] = IncomingGoodsView(incoming_frame)

        # Add Shopping List view
        shopping_frame = ttk.Frame(order_notebook)
        order_notebook.add(shopping_frame, text='Shopping List')
        self.views['shopping'] = ShoppingListView(shopping_frame)

        # Add Supplier view
        supplier_frame = ttk.Frame(order_notebook)
        order_notebook.add(supplier_frame, text='Supplier')
        self.views['supplier'] = SupplierView(supplier_frame)

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