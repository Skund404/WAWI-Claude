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

# Now proceed with your other imports
from database.database_setup import ensure_database
ensure_database()



from database.db_manager import DatabaseManager
from utils.logger import logger, log_error
from utils.error_handler import ErrorHandler, check_database_connection, DatabaseError
from config import DATABASE_PATH, TABLES, COLORS

from config import APP_NAME, WINDOW_SIZE, DATABASE_PATH
from gui.shelf_view import ShelfView
from gui.recipe_view import RecipeView
from gui.storage_view import StorageView
from gui.sorting_system_view import SortingSystemView
from gui.order.incoming_goods_view import IncomingGoodsView
from gui.order.shopping_list_view import ShoppingListView
from gui.supplier_view import SupplierView  # Corrected import


class MainWindow:
    def show_add_item_dialog(self):
        """Show dialog for adding item to recipe"""
        if not self.current_recipe:
            messagebox.showwarning("Warning", "Please select a recipe first")
            return

        dialog = tk.Toplevel(self)
        dialog.title("Add Item to Recipe")
        dialog.transient(self)
        dialog.grab_set()
        dialog.geometry("600x500")

        # Create main frame with padding
        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Get parts and leather items
        self.db.connect()
        parts = self.db.execute_query(
            "SELECT unique_id_parts, name, color, in_storage FROM sorting_system ORDER BY name"
        )
        leather = self.db.execute_query(
            "SELECT unique_id_leather, name, color, size FROM shelf ORDER BY name"
        )
        self.db.disconnect()

        # Dropdown frame
        dropdown_frame = ttk.LabelFrame(main_frame, text="Select Item")
        dropdown_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(dropdown_frame, text="Item:").pack(side=tk.LEFT, padx=5)

        # Create list of items for dropdown
        items = []
        items.append(("create part", "Add New Part"))
        items.append(("create leather", "Add New Leather"))
        items.extend((p[0], f"{p[0]} - {p[1]}") for p in parts)
        items.extend((l[0], f"{l[0]} - {l[1]}") for l in leather)

        item_var = tk.StringVar()
        item_combo = ttk.Combobox(
            dropdown_frame,
            textvariable=item_var,
            width=50
        )
        item_combo['values'] = [item[1] for item in items]
        item_combo.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        # Preview frame
        preview_frame = ttk.LabelFrame(main_frame, text="Item Preview")
        preview_frame.pack(fill=tk.X, pady=(0, 10))

        # Create preview labels with grid layout
        preview_labels = {}
        preview_fields = ['name', 'color', 'size', 'in_storage']
        for i, field in enumerate(preview_fields):
            ttk.Label(preview_frame, text=f"{field.title()}:").grid(
                row=i, column=0, sticky='w', padx=5, pady=2
            )
            preview_labels[field] = ttk.Label(preview_frame, text="")
            preview_labels[field].grid(
                row=i, column=1, sticky='w', padx=5, pady=2
            )

        # Details frame
        details_frame = ttk.LabelFrame(main_frame, text="Details")
        details_frame.pack(fill=tk.X, pady=(0, 10))

        # Create entry fields
        entries = {}
        required_fields = {'amount': 'Amount', 'size': 'Size', 'pattern_id': 'Pattern ID', 'notes': 'Notes'}

        for i, (field, label) in enumerate(required_fields.items()):
            ttk.Label(details_frame, text=f"{label}:").grid(
                row=i, column=0, sticky='w', padx=5, pady=2
            )
            entries[field] = ttk.Entry(details_frame)
            entries[field].grid(
                row=i, column=1, sticky='ew', padx=5, pady=2
            )

            # Add required field indicator
            if field in ['amount', 'size']:
                ttk.Label(details_frame, text="*", foreground="red").grid(
                    row=i, column=2, sticky='w'
                )

        # Configure grid weights
        details_frame.columnconfigure(1, weight=1)

        def update_preview(*args):
            """Update preview when item selection changes"""
            selection = item_var.get()

            # Clear preview fields
            for label in preview_labels.values():
                label.configure(text="")

            # Handle special cases
            def show_add_item_dialog(self):
                # ... existing code ...

                # Handle special cases
                if selection.startswith("Add New"):
                    if selection == "Add New Part":
                        # Call ADD function from sorting system
                        dialog.withdraw()
                        # Get the sorting system view and call its add dialog
                        sorting_view = self.views.get('sorting')
                        if sorting_view:
                            sorting_view.show_add_part_dialog()
                        else:
                            messagebox.showerror("Error", "Sorting System view not found")
                        dialog.deiconify()
                    elif selection == "Add New Leather":
                        # Call ADD function from shelf
                        dialog.withdraw()
                        # Get the shelf view and call its add dialog
                        shelf_view = self.views.get('shelf')
                        if shelf_view:
                            shelf_view.show_add_leather_dialog()
                        else:
                            messagebox.showerror("Error", "Shelf view not found")
                        dialog.deiconify()
                    return

            # Get selected item ID
            selected_id = None
            for item_id, item_text in items:
                if item_text == selection:
                    selected_id = item_id
                    break

            if not selected_id:
                return

            # Query database for item details
            self.db.connect()
            try:
                if selected_id.startswith('L'):  # Leather item
                    result = self.db.execute_query("""
                        SELECT name, color, size, NULL as in_storage
                        FROM shelf 
                        WHERE unique_id_leather = ?
                    """, (selected_id,))
                else:  # Part item
                    result = self.db.execute_query("""
                        SELECT name, color, NULL as size, in_storage
                        FROM sorting_system 
                        WHERE unique_id_parts = ?
                    """, (selected_id,))

                if result:
                    # Update preview labels
                    for field, value in zip(preview_fields, result[0]):
                        preview_labels[field].configure(
                            text=str(value) if value is not None else "N/A"
                        )

            finally:
                self.db.disconnect()

        # Bind preview update to combobox selection
        item_var.trace('w', update_preview)

        def save_item():
            """Save the new recipe item"""
            try:
                # Validate selection
                if not item_var.get() or item_var.get().startswith("Add New"):
                    messagebox.showerror("Error", "Please select an item")
                    return

                # Get selected item ID
                selected_id = None
                for item_id, item_text in items:
                    if item_text == item_var.get():
                        selected_id = item_id
                        break

                if not selected_id:
                    return

                # Validate required fields
                if not entries['amount'].get():
                    messagebox.showerror("Error", "Amount is required")
                    return

                try:
                    amount = int(entries['amount'].get())
                    if amount <= 0:
                        raise ValueError("Amount must be positive")
                except ValueError as e:
                    messagebox.showerror("Error", str(e))
                    return

                # Prepare data
                data = {
                    'recipe_id': self.current_recipe,
                    'unique_id_parts': selected_id,
                    'name': preview_labels['name'].cget('text'),
                    'color': preview_labels['color'].cget('text'),
                    'amount': amount,
                    'size': entries['size'].get(),
                    'in_storage': preview_labels['in_storage'].cget('text'),
                    'pattern_id': entries['pattern_id'].get(),
                    'notes': entries['notes'].get()
                }

                # Check storage availability
                in_storage = preview_labels['in_storage'].cget('text')
                if in_storage != "N/A" and int(in_storage) < amount:
                    if not messagebox.askyesno(
                            "Warning",
                            "Required amount exceeds available stock. Continue anyway?"
                    ):
                        return

                # Save to database
                self.db.connect()
                if self.db.insert_record(TABLES['RECIPE_DETAILS'], data):
                    self.undo_stack.append(('add_item', self.current_recipe, data))
                    self.redo_stack.clear()
                    self.load_recipe_details(self.current_recipe)
                    dialog.destroy()

            except Exception as e:
                messagebox.showerror("Error", f"Failed to add item: {str(e)}")
            finally:
                self.db.disconnect()

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)

        ttk.Button(
            button_frame,
            text="Add Item",
            command=save_item
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            button_frame,
            text="Cancel",
            command=dialog.destroy
        ).pack(side=tk.LEFT, padx=5)

        # Add required fields note
        ttk.Label(
            main_frame,
            text="* Required fields",
            foreground="red"
        ).pack(anchor='w', pady=(5, 0))

        # Set focus to combobox
        item_combo.focus_set()
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
        self.views['storage'].pack(expand=True, fill='both')  # Pack the Storage view

        # Add Recipe view under Product
        recipe_frame = ttk.Frame(product_notebook)
        product_notebook.add(recipe_frame, text='Recipe')
        self.views['recipe'] = RecipeView(recipe_frame)
        self.views['recipe'].pack(expand=True, fill='both')  # Pack the Recipe view

        # Storage group
        storage_notebook = ttk.Notebook(self.notebook)
        self.notebook.add(storage_notebook, text='Storage')

        # Add Shelf view under Storage
        shelf_frame = ttk.Frame(storage_notebook)
        storage_notebook.add(shelf_frame, text='Shelf')
        self.views['shelf'] = ShelfView(shelf_frame)
        self.views['shelf'].pack(expand=True, fill='both')  # Pack the Shelf view

        # Add Sorting System view under Storage
        sorting_frame = ttk.Frame(storage_notebook)
        storage_notebook.add(sorting_frame, text='Sorting System')
        self.views['sorting'] = SortingSystemView(sorting_frame)
        self.views['sorting'].pack(expand=True, fill='both')  # Pack the Sorting System view

        # Order group
        order_notebook = ttk.Notebook(self.notebook)
        self.notebook.add(order_notebook, text='Order')

        # Add Incoming Goods view
        incoming_frame = ttk.Frame(order_notebook)
        order_notebook.add(incoming_frame, text='Incoming Goods')
        self.views['incoming'] = IncomingGoodsView(incoming_frame)
        self.views['incoming'].pack(expand=True, fill='both')  # Pack the Incoming Goods view

        # Add Shopping List view
        shopping_frame = ttk.Frame(order_notebook)
        order_notebook.add(shopping_frame, text='Shopping List')
        self.views['shopping'] = ShoppingListView(shopping_frame)
        self.views['shopping'].pack(expand=True, fill='both')  # Pack the Shopping List view

        # Add Supplier view
        supplier_frame = ttk.Frame(order_notebook)
        order_notebook.add(supplier_frame, text='Supplier')
        self.views['supplier'] = SupplierView(supplier_frame)
        self.views['supplier'].pack(expand=True, fill='both')  # Pack the Supplier view

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