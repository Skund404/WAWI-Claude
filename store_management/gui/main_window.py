import tkinter as tk
from tkinter import ttk
from typing import Dict
from pathlib import Path
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from store_management.config import APP_NAME, WINDOW_SIZE, DATABASE_PATH
from store_management.gui.storage.shelf_view import ShelfView
from store_management.gui.product.recipe_view import RecipeView
from store_management.gui.product.storage_view import StorageView
from store_management.gui.storage.sorting_system_view import SortingSystemView
from store_management.gui.order.incoming_goods_view import IncomingGoodsView
from store_management.gui.order.shopping_list_view import ShoppingListView
from store_management.gui.order.supplier_view import SupplierView


class MainWindow:
    def get_part_dialog(self, parent):
        """
        Open the add part dialog from the sorting system view

        Args:
            parent (tk.Toplevel): Parent dialog window

        Returns:
            tk.Toplevel: Dialog for adding a new part
        """
        sorting_system_view = self.get_view('sorting_system')
        if sorting_system_view:
            dialog = tk.Toplevel(parent)
            dialog.title("Add New Part")
            dialog.geometry("600x400")
            dialog.transient(parent)
            dialog.grab_set()

            # Main frame
            main_frame = ttk.Frame(dialog, padding="10")
            main_frame.pack(fill=tk.BOTH, expand=True)

            # Entry fields dictionary
            entries = {}
            fields = [
                ('name', 'Part Name', True),
                ('color', 'Color', False),
                ('in_storage', 'Initial Stock', True),
                ('warning_threshold', 'Warning Threshold', True),
                ('bin', 'Bin Location', True),
                ('notes', 'Notes', False)
            ]

            for i, (field, label, required) in enumerate(fields):
                ttk.Label(main_frame, text=f"{label}:").grid(row=i, column=0, sticky='w', padx=5, pady=2)

                if field in ['in_storage', 'warning_threshold']:
                    entries[field] = ttk.Spinbox(main_frame, from_=0, to=1000, width=20)
                    if field == 'warning_threshold':
                        entries[field].insert(0, "5")  # Default warning threshold
                else:
                    entries[field] = ttk.Entry(main_frame, width=40)

                entries[field].grid(row=i, column=1, sticky='ew', padx=5, pady=2)

                if required:
                    ttk.Label(main_frame, text="*", foreground="red").grid(row=i, column=2, sticky='w')

            # Configure grid
            main_frame.columnconfigure(1, weight=1)

            def save_part():
                """Save the new part to the database"""
                try:
                    # Collect input data
                    data = {}
                    required_fields = [
                        ('name', 'Part Name'),
                        ('bin', 'Bin Location'),
                        ('in_storage', 'Initial Stock'),
                        ('warning_threshold', 'Warning Threshold')
                    ]

                    for field, label in required_fields:
                        value = entries[field].get().strip()
                        if not value:
                            messagebox.showerror("Error", f"{label} is required")
                            return
                        data[field] = value

                    # Collect optional fields
                    data['color'] = entries['color'].get().strip() or None
                    data['notes'] = entries['notes'].get().strip() or None

                    # Validate numeric inputs
                    try:
                        data['in_storage'] = int(data['in_storage'])
                        data['warning_threshold'] = int(data['warning_threshold'])

                        if data['in_storage'] < 0:
                            raise ValueError("Stock cannot be negative")
                        if data['warning_threshold'] < 0:
                            raise ValueError("Warning threshold cannot be negative")
                    except ValueError as e:
                        messagebox.showerror("Error", str(e))
                        return

                    # Generate Part ID
                    import uuid
                    prefix = ''.join(word[0].upper() for word in data['name'].split()[:2])
                    unique_id = f"P{prefix}{str(uuid.uuid4())[:8]}"
                    data['unique_id_parts'] = unique_id

                    # Attempt to insert record
                    sorting_system_view.add_item(data)

                    messagebox.showinfo(
                        "Success",
                        f"Part added successfully\nPart ID: {unique_id}"
                    )
                    dialog.destroy()

                except Exception as e:
                    messagebox.showerror("Error", f"An error occurred: {str(e)}")

            # Add buttons
            button_frame = ttk.Frame(main_frame)
            button_frame.grid(row=len(fields), column=0, columnspan=3, pady=10)
            ttk.Button(button_frame, text="Save", command=save_part).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)

            # Required fields note
            ttk.Label(
                main_frame,
                text="* Required fields",
                foreground="red"
            ).grid(row=len(fields) + 1, column=0, columnspan=3, sticky='w', pady=(5, 0))

            # Set focus
            entries['name'].focus_set()

            return dialog
        return None

    def get_leather_dialog(self, parent):
        """
        Open the add leather dialog from the shelf view

        Args:
            parent (tk.Toplevel): Parent dialog window

        Returns:
            tk.Toplevel: Dialog for adding a new leather item
        """
        shelf_view = self.get_view('shelf')
        if shelf_view:
            dialog = tk.Toplevel(parent)
            dialog.title("Add New Leather")
            dialog.geometry("600x400")
            dialog.transient(parent)
            dialog.grab_set()

            # Main frame
            main_frame = ttk.Frame(dialog, padding="10")
            main_frame.pack(fill=tk.BOTH, expand=True)

            # Entry fields
            entries = {}
            fields = [
                ('name', 'Leather Name', True),
                ('color', 'Color', True),
                ('thickness', 'Thickness', True),
                ('size_ft', 'Size (ft)', True),
                ('shelf', 'Shelf Location', False),
                ('notes', 'Notes', False)
            ]

            for i, (field, label, required) in enumerate(fields):
                ttk.Label(main_frame, text=f"{label}:").grid(row=i, column=0, sticky='w', padx=5, pady=2)

                if field in ['thickness', 'size_ft']:
                    entries[field] = ttk.Entry(main_frame, width=20)
                else:
                    entries[field] = ttk.Entry(main_frame, width=40)

                entries[field].grid(row=i, column=1, sticky='ew', padx=5, pady=2)

                # Add required field indicator
                if required:
                    ttk.Label(main_frame, text="*", foreground="red").grid(row=i, column=2, sticky='w')

            # Configure grid
            main_frame.columnconfigure(1, weight=1)

            def save_leather():
                """Save the new leather item to the database"""
                # Validate required fields
                try:
                    # Collect input data
                    data = {}
                    required_fields = [
                        ('name', 'Leather Name'),
                        ('color', 'Color'),
                        ('thickness', 'Thickness'),
                        ('size_ft', 'Size')
                    ]

                    for field, label in required_fields:
                        value = entries[field].get().strip()
                        if not value:
                            messagebox.showerror("Error", f"{label} is required")
                            return
                        data[field] = value

                    # Collect optional fields
                    data['shelf'] = entries['shelf'].get().strip() or None
                    data['notes'] = entries['notes'].get().strip() or None

                    # Validate numeric inputs
                    try:
                        thickness = float(data['thickness'])
                        size_ft = float(data['size_ft'])
                        data['area_sqft'] = thickness * size_ft

                        if thickness <= 0 or size_ft <= 0:
                            raise ValueError("Thickness and size must be positive")
                    except ValueError as e:
                        messagebox.showerror("Error", str(e))
                        return

                    # Call shelf view's add method
                    result = shelf_view.add_item(data)

                    if result:
                        messagebox.showinfo("Success", "Leather item added successfully")
                        dialog.destroy()

                except Exception as e:
                    messagebox.showerror("Error", f"An error occurred: {str(e)}")

            # Add buttons
            button_frame = ttk.Frame(main_frame)
            button_frame.grid(row=len(fields), column=0, columnspan=3, pady=10)

            ttk.Button(button_frame, text="Save", command=save_leather).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)

            # Add required fields note
            ttk.Label(
                main_frame,
                text="* Required fields",
                foreground="red"
            ).grid(row=len(fields) + 1, column=0, columnspan=3, sticky='w', pady=(5, 0))

            # Set focus
            entries['name'].focus_set()

            return dialog
        return None
    def get_view(self, view_name):
        """
        Get a specific view by name

        Args:
            view_name (str): Name of the view (e.g., 'sorting', 'shelf')

        Returns:
            ttk.Frame or None: The requested view or None if not found
        """
        return self.views.get(view_name)

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