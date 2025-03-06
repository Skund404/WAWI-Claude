# incoming_goods_view.py
import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Dict, Any, Optional, Tuple
import logging

from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
from models.order import Order
from managers.order_manager import OrderManager

logger = logging.getLogger(__name__)


class BaseView(tk.Frame):
    """Base view for application views."""

    def __init__(self, parent):
        super().__init__(parent)


class IncomingGoodsView(BaseView):
    """
    View for managing incoming goods and orders
    """

    @inject(MaterialService)
    def __init__(self, parent, session):
        """
        Initialize Incoming Goods View

        Args:
            parent: Parent widget
            session: SQLAlchemy database session
        """
        super().__init__(parent)
        self.session = session
        self.order_manager = OrderManager(session)
        self.current_order: Optional[Order] = None
        self.modified = False
        self.undo_stack: List[tuple] = []
        self.redo_stack: List[tuple] = []
        self._setup_ui()
        self._load_initial_data()

    @inject(MaterialService)
    def _setup_ui(self):
        """Setup the entire user interface"""
        self._create_toolbar()
        self._create_content_area()
        self._create_status_bar()

    @inject(MaterialService)
    def _create_toolbar(self):
        """Create the main toolbar with action buttons"""
        toolbar_actions = [
            ('Add Order', self.show_add_order_dialog),
            ('Search', self.show_search_dialog),
            ('Filter', self.show_filter_dialog),
            ('Finish Order', self.finish_order),
            ('Export', self.show_export_dialog),
            ('Import', self.show_import_dialog),
            ('Undo', self.undo_action),
            ('Redo', self.redo_action),
            ('Save', self.save_changes),
            ('Reset View', self.reset_view)
        ]
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        for text, command in toolbar_actions:
            ttk.Button(toolbar, text=text, command=command).pack(side=tk.LEFT, padx=2)

    @inject(MaterialService)
    def _create_content_area(self):
        """Create main content area with orders and details tables"""
        paned_window = ttk.PanedWindow(self, orient=tk.VERTICAL)
        paned_window.pack(expand=True, fill='both', padx=5, pady=5)

        orders_frame = ttk.LabelFrame(paned_window, text='Orders')
        self.orders_tree = self._create_treeview(
            orders_frame,
            ['Order Number', 'Supplier', 'Date', 'Status', 'Payment', 'Total'],
            self._on_order_select
        )
        paned_window.add(orders_frame, weight=1)

        details_frame = ttk.LabelFrame(paned_window, text='Order Details')
        details_frame.pack(expand=True, fill='both')
        ttk.Button(details_frame, text='Add Item', command=self.show_add_item_dialog).pack(side=tk.TOP, pady=5)
        self.details_tree = self._create_treeview(
            details_frame,
            ['Article', 'Unique ID', 'Price', 'Amount', 'Total', 'Notes']
        )
        paned_window.add(details_frame, weight=1)

    def _create_status_bar(self):
        """Create status bar at the bottom of the view"""
        status_bar = ttk.Frame(self)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM, padx=5, pady=2)
        self.status_label = ttk.Label(status_bar, text="Ready")
        self.status_label.pack(side=tk.LEFT)

    @staticmethod
    def _create_treeview(parent, columns, select_callback=None):
        """
        Create a standardized treeview

        Args:
            parent: Parent widget
            columns: List of column names
            select_callback: Optional selection callback

        Returns:
            Configured Treeview widget
        """
        tree = ttk.Treeview(parent, columns=columns, show='headings')
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, anchor='center')

        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.pack(expand=True, fill='both')

        if select_callback:
            tree.bind('<<TreeviewSelect>>', select_callback)

        return tree

    @inject(MaterialService)
    def _load_initial_data(self):
        """Load initial orders data"""
        try:
            orders = self.order_manager.get_all_sales()
            self._populate_orders_tree(orders)
        except Exception as e:
            messagebox.showerror('Load Error', str(e))
            logger.error(f"Failed to load initial data: {e}")

    @inject(MaterialService)
    def _populate_orders_tree(self, orders):
        """
        Populate orders treeview

        Args:
            orders: List of Order objects
        """
        for item in self.orders_tree.get_children():
            self.orders_tree.delete(item)

        for order in orders:
            values = (
                order.order_number,
                order.supplier,
                order.date_of_order.strftime('%Y-%m-%d'),
                order.status.value,
                order.payed.value,
                f'${order.total_amount:.2f}'
            )
            self.orders_tree.insert('', 'end', values=values, tags=(str(order.id),))

    @inject(MaterialService)
    def _on_order_select(self, event):
        """Handle sale selection in treeview"""
        selection = self.orders_tree.selection()
        if not selection:
            return

        try:
            order_id = int(self.orders_tree.item(selection[0])['tags'][0])
            self.current_order = self.order_manager.get_sale_by_id(order_id)
            if self.current_order:
                self._load_order_details(self.current_order.id)
        except Exception as e:
            messagebox.showerror('Selection Error', str(e))
            logger.error(f"Error selecting sale: {e}")

    @inject(MaterialService)
    def _load_order_details(self, order_id: int):
        """
        Load details for a specific sale

        Args:
            order_id: ID of the sale to load details for
        """
        try:
            for item in self.details_tree.get_children():
                self.details_tree.delete(item)

            details = self.order_manager.get_order_details(order_id)
            for detail in details:
                values = (
                    detail.article,
                    detail.unique_id,
                    f'${detail.price:.2f}',
                    detail.amount,
                    f'${detail.total:.2f}',
                    detail.notes or ''
                )
                self.details_tree.insert('', 'end', values=values, tags=(str(detail.id),))
        except Exception as e:
            messagebox.showerror('Details Load Error', str(e))
            logger.error(f"Failed to load sale details: {e}")

    @inject(MaterialService)
    def cleanup(self):
        """Cleanup resources and handle unsaved changes"""
        try:
            if self.modified:
                if messagebox.askyesno('Save Changes', 'Unsaved changes exist. Save now?'):
                    self.save_changes()
                else:
                    self.session.rollback()
        except Exception as e:
            messagebox.showerror('Cleanup Error', str(e))
            logger.error(f"Error during cleanup: {e}")
        finally:
            if self.session:
                self.session.close()

    def show_add_order_dialog(self):
        """Show dialog for adding a new sale"""
        # Implement this method
        pass

    def show_search_dialog(self):
        """Show dialog for searching orders"""
        # Implement this method
        pass

    def show_filter_dialog(self):
        """Show dialog for filtering orders"""
        # Implement this method
        pass

    def finish_order(self):
        """Mark selected sale as finished"""
        # Implement this method
        pass

    def show_export_dialog(self):
        """Show dialog for exporting orders"""
        # Implement this method
        pass

    def show_import_dialog(self):
        """Show dialog for importing orders"""
        # Implement this method
        pass

    def undo_action(self):
        """Undo last action"""
        # Implement this method
        pass

    def redo_action(self):
        """Redo last undone action"""
        # Implement this method
        pass

    def save_changes(self):
        """Save all changes to the database"""
        # Implement this method
        pass

    def reset_view(self):
        """Reset view to default state"""
        # Implement this method
        pass

    def show_add_item_dialog(self):
        """Show dialog for adding an item to the current sale"""
        # Implement this method
        pass