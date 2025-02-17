# main.py
import os
import sys
import tkinter as tk
from tkinter import ttk
from pathlib import Path

# Add the project root directory to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

try:
    # Import configuration
    from config import APP_NAME, WINDOW_SIZE, DATABASE_PATH

    # Import database initialization
    from database.database_init import init_database

    # Import views
    from gui.supplier_view import SupplierView
    from gui.storage_view import StorageView
    from gui.shelf_view import ShelfView
    from gui.sorting_system_view import SortingSystemView
    from gui.recipe_view import RecipeView
    from gui.order.incoming_goods_view import IncomingGoodsView
    from gui.order.shopping_list_view import ShoppingListView

except ImportError as e:
    print(f"Import Error: {e}")
    print(f"Current Python path: {sys.path}")
    print(f"Current directory: {os.getcwd()}")
    sys.exit(1)


class MainApplication(tk.Tk):
    def __init__(self):
        super().__init__()

        # Configure main window
        self.title(APP_NAME)
        self.geometry(WINDOW_SIZE)

        # Create notebook for tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill='both', padx=5, pady=5)

        # Initialize database
        init_database()

        # Setup UI
        self.setup_ui()

    def setup_ui(self):
        """Setup the main user interface"""
        # Product group
        product_notebook = ttk.Notebook(self.notebook)
        self.notebook.add(product_notebook, text='Product')

        # Storage view
        storage_frame = ttk.Frame(product_notebook)
        product_notebook.add(storage_frame, text='Storage')
        StorageView(storage_frame)

        # Recipe view
        recipe_frame = ttk.Frame(product_notebook)
        product_notebook.add(recipe_frame, text='Recipe')
        RecipeView(recipe_frame)

        # Storage group
        storage_notebook = ttk.Notebook(self.notebook)
        self.notebook.add(storage_notebook, text='Storage')

        # Shelf view
        shelf_frame = ttk.Frame(storage_notebook)
        storage_notebook.add(shelf_frame, text='Shelf')
        ShelfView(shelf_frame)

        # Sorting system view
        sorting_frame = ttk.Frame(storage_notebook)
        storage_notebook.add(sorting_frame, text='Sorting System')
        SortingSystemView(sorting_frame)

        # Order group
        order_notebook = ttk.Notebook(self.notebook)
        self.notebook.add(order_notebook, text='Order')

        # Incoming Goods view
        incoming_frame = ttk.Frame(order_notebook)
        order_notebook.add(incoming_frame, text='Incoming Goods')
        IncomingGoodsView(incoming_frame)

        # Shopping List view
        shopping_frame = ttk.Frame(order_notebook)
        order_notebook.add(shopping_frame, text='Shopping List')
        ShoppingListView(shopping_frame)

        # Supplier view
        supplier_frame = ttk.Frame(self.notebook)
        self.notebook.add(supplier_frame, text='Supplier')
        SupplierView(supplier_frame)


def main():
    try:
        app = MainApplication()
        app.mainloop()
    except Exception as e:
        print(f"Error starting application: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()