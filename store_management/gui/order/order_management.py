import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Optional

from database.db_manager import DatabaseManager
from config import DATABASE_PATH, TABLES, COLORS
from gui.order.incoming_goods_view import IncomingGoodsView
from gui.order.shopping_list_view import ShoppingListView
from gui.supplier_view import SupplierView


class OrderManagementSystem(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.db = DatabaseManager(DATABASE_PATH)

        # Initialize views dictionary
        self.views: Dict[str, Optional[ttk.Frame]] = {}

        # Setup UI
        self.setup_ui()

        # Bind events
        self.bind_shortcuts()

    def setup_ui(self):
        """Setup the main user interface"""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill='both')

        # Create frames for each view
        incoming_frame = ttk.Frame(self.notebook)
        shopping_frame = ttk.Frame(self.notebook)
        supplier_frame = ttk.Frame(self.notebook)

        # Add frames to notebook
        self.notebook.add(incoming_frame, text='Incoming Goods')
        self.notebook.add(shopping_frame, text='Shopping Lists')
        self.notebook.add(supplier_frame, text='Suppliers')

        # Initialize views
        self.views['incoming'] = IncomingGoodsView(incoming_frame)
        self.views['shopping'] = ShoppingListView(shopping_frame)
        self.views['supplier'] = SupplierView(supplier_frame)

        # Setup communication between views
        self.setup_view_communication()

    def setup_view_communication(self):
        """Setup communication channels between views"""

        # Add supplier callback
        def add_supplier_callback():
            """Switch to supplier view and show add dialog"""
            self.notebook.select(2)  # Switch to supplier tab
            if hasattr(self.views['supplier'], 'show_add_dialog'):
                self.views['supplier'].show_add_dialog()

        # Add callbacks to views that need them
        if hasattr(self.views['incoming'], 'set_add_supplier_callback'):
            self.views['incoming'].set_add_supplier_callback(add_supplier_callback)

        if hasattr(self.views['shopping'], 'set_add_supplier_callback'):
            self.views['shopping'].set_add_supplier_callback(add_supplier_callback)

    def bind_shortcuts(self):
        """Bind global keyboard shortcuts"""
        self.bind_all('<Control-s>', self.save_current_view)
        self.bind_all('<Control-z>', self.undo_current_view)
        self.bind_all('<Control-y>', self.redo_current_view)
        self.bind_all('<Control-f>', self.search_current_view)
        self.bind_all('<F5>', self.refresh_current_view)

    def get_current_view(self) -> Optional[ttk.Frame]:
        """Get the currently active view"""
        current_tab = self.notebook.select()
        if current_tab:
            tab_id = self.notebook.index(current_tab)
            if tab_id == 0:
                return self.views.get('incoming')
            elif tab_id == 1:
                return self.views.get('shopping')
            elif tab_id == 2:
                return self.views.get('supplier')
        return None

    def save_current_view(self, event=None):
        """Save current view state"""
        current_view = self.get_current_view()
        if current_view and hasattr(current_view, 'save_table'):
            current_view.save_table()

    def undo_current_view(self, event=None):
        """Undo in current view"""
        current_view = self.get_current_view()
        if current_view and hasattr(current_view, 'undo'):
            current_view.undo()

    def redo_current_view(self, event=None):
        """Redo in current view"""
        current_view = self.get_current_view()
        if current_view and hasattr(current_view, 'redo'):
            current_view.redo()

    def search_current_view(self, event=None):
        """Search in current view"""
        current_view = self.get_current_view()
        if current_view and hasattr(current_view, 'show_search_dialog'):
            current_view.show_search_dialog()

    def refresh_current_view(self, event=None):
        """Refresh current view"""
        current_view = self.get_current_view()
        if current_view and hasattr(current_view, 'reset_view'):
            current_view.reset_view()

    def refresh_all_views(self):
        """Refresh all views"""
        for view in self.views.values():
            if view and hasattr(view, 'reset_view'):
                view.reset_view()


class OrderManagementStatusBar(ttk.Frame):
    """Status bar for order management system"""

    def __init__(self, parent):
        super().__init__(parent)

        # Create status labels
        self.status_label = ttk.Label(self, text="Ready")
        self.status_label.pack(side=tk.LEFT, padx=5)

        # Create count labels
        self.order_count = ttk.Label(self, text="Orders: 0")
        self.order_count.pack(side=tk.RIGHT, padx=5)

        self.list_count = ttk.Label(self, text="Shopping Lists: 0")
        self.list_count.pack(side=tk.RIGHT, padx=5)

        self.supplier_count = ttk.Label(self, text="Suppliers: 0")
        self.supplier_count.pack(side=tk.RIGHT, padx=5)

        # Update counts
        self.update_counts()

    def update_counts(self):
        """Update the count displays"""
        db = DatabaseManager(DATABASE_PATH)
        db.connect()
        try:
            # Get order count
            orders = db.execute_query("SELECT COUNT(*) FROM orders")
            self.order_count.configure(text=f"Orders: {orders[0][0]}")

            # Get shopping list count
            lists = db.execute_query(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name LIKE 'shopping_list_%'"
            )
            self.list_count.configure(text=f"Shopping Lists: {lists[0][0]}")

            # Get supplier count
            suppliers = db.execute_query("SELECT COUNT(*) FROM supplier")
            self.supplier_count.configure(text=f"Suppliers: {suppliers[0][0]}")

        finally:
            db.disconnect()

    def set_status(self, message: str):
        """Update status message"""
        self.status_label.configure(text=message)
        self.after(3000, lambda: self.status_label.configure(text="Ready"))


class OrderManagementToolbar(ttk.Frame):
    """Toolbar for order management system"""

    def __init__(self, parent, callback_handler):
        super().__init__(parent)

        # Save reference to callback handler
        self.callback_handler = callback_handler

        # Create buttons
        ttk.Button(self, text="Refresh All",
                   command=self.callback_handler.refresh_all_views).pack(side=tk.LEFT, padx=2)

        ttk.Button(self, text="Export Data",
                   command=self.export_data).pack(side=tk.LEFT, padx=2)

        ttk.Button(self, text="Import Data",
                   command=self.import_data).pack(side=tk.LEFT, padx=2)

        # Add separator
        ttk.Separator(self, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)

        # Add quick access buttons
        ttk.Button(self, text="New Order",
                   command=self.new_order).pack(side=tk.LEFT, padx=2)

        ttk.Button(self, text="New Shopping List",
                   command=self.new_shopping_list).pack(side=tk.LEFT, padx=2)

        ttk.Button(self, text="New Supplier",
                   command=self.new_supplier).pack(side=tk.LEFT, padx=2)

    def export_data(self):
        """Export all order management data"""
        # To be implemented
        pass

    def import_data(self):
        """Import order management data"""
        # To be implemented
        pass

    def new_order(self):
        """Quick access to new order creation"""
        current_view = self.callback_handler.get_current_view()
        if isinstance(current_view, IncomingGoodsView):
            current_view.show_add_dialog()
        else:
            self.callback_handler.notebook.select(0)  # Switch to incoming goods tab
            self.after(100, lambda: self.callback_handler.views['incoming'].show_add_dialog())

    def new_shopping_list(self):
        """Quick access to new shopping list creation"""
        current_view = self.callback_handler.get_current_view()
        if isinstance(current_view, ShoppingListView):
            current_view.create_new_list()
        else:
            self.callback_handler.notebook.select(1)  # Switch to shopping lists tab
            self.after(100, lambda: self.callback_handler.views['shopping'].create_new_list())

    def new_supplier(self):
        """Quick access to new supplier creation"""
        current_view = self.callback_handler.get_current_view()
        if isinstance(current_view, SupplierView):
            current_view.show_add_dialog()
        else:
            self.callback_handler.notebook.select(2)  # Switch to suppliers tab
            self.after(100, lambda: self.callback_handler.views['supplier'].show_add_dialog())