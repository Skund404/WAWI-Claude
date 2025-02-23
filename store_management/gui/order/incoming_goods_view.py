# File: store_management/gui/order/incoming_goods_view.py

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import List, Optional, Dict

from sqlalchemy.orm import Session

from database.sqlalchemy.models_file import (
    Order,
    OrderStatus,
    PaymentStatus
)
from database.sqlalchemy.managers.order_manager import OrderManager
from utils.exporters.order_exporter import OrderExporter
from utils.validators.order_validator import OrderValidator
from gui.base_view import BaseView


class IncomingGoodsView(BaseView):
    """
    View for managing incoming goods and orders
    """

    def __init__(self, parent, session: Session):
        """
        Initialize Incoming Goods View

        Args:
            parent: Parent widget
            session: SQLAlchemy database session
        """
        super().__init__(parent)

        # Core dependencies
        self.session = session
        self.order_manager = OrderManager(session)

        # State management
        self.current_order: Optional[Order] = None
        self.modified = False
        self.undo_stack: List[tuple] = []
        self.redo_stack: List[tuple] = []

        # Setup UI components
        self._setup_ui()

        # Initial data load
        self._load_initial_data()

    def _setup_ui(self):
        """Setup the entire user interface"""
        self._create_toolbar()
        self._create_content_area()
        self._create_status_bar()

    def _create_toolbar(self):
        """Create the main toolbar with action buttons"""
        toolbar_actions = [
            ("Add Order", self.show_add_order_dialog),
            ("Search", self.show_search_dialog),
            ("Filter", self.show_filter_dialog),
            ("Finish Order", self.finish_order),
            ("Export", self.show_export_dialog),
            ("Import", self.show_import_dialog),
            ("Undo", self.undo_action),
            ("Redo", self.redo_action),
            ("Save", self.save_changes),
            ("Reset View", self.reset_view)
        ]

        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, padx=5, pady=5)

        for text, command in toolbar_actions:
            ttk.Button(toolbar, text=text, command=command).pack(side=tk.LEFT, padx=2)

    def _create_content_area(self):
        """Create main content area with orders and details tables"""
        paned_window = ttk.PanedWindow(self, orient=tk.VERTICAL)
        paned_window.pack(expand=True, fill='both', padx=5, pady=5)

        # Orders Table
        orders_frame = ttk.LabelFrame(paned_window, text="Orders")
        self.orders_tree = self._create_treeview(
            orders_frame,
            ['Order Number', 'Supplier', 'Date', 'Status', 'Payment', 'Total'],
            self._on_order_select
        )
        paned_window.add(orders_frame, weight=1)

        # Order Details Table
        details_frame = ttk.LabelFrame(paned_window, text="Order Details")
        details_frame.pack(expand=True, fill='both')

        ttk.Button(
            details_frame,
            text="Add Item",
            command=self.show_add_item_dialog
        ).pack(side=tk.TOP, pady=5)

        self.details_tree = self._create_treeview(
            details_frame,
            ['Article', 'Unique ID', 'Price', 'Amount', 'Total', 'Notes']
        )

        paned_window.add(details_frame, weight=1)

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

        # Configure columns
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, anchor='center')

        # Add scrollbar
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.pack(expand=True, fill='both')

        # Bind selection callback if provided
        if select_callback:
            tree.bind('<<TreeviewSelect>>', select_callback)

        return tree

    def _load_initial_data(self):
        """Load initial orders data"""
        try:
            orders = self.order_manager.get_all_orders()
            self._populate_orders_tree(orders)
        except Exception as e:
            messagebox.showerror("Load Error", str(e))

    def _populate_orders_tree(self, orders):
        """
        Populate orders treeview

        Args:
            orders: List of Order objects
        """
        # Clear existing items
        for item in self.orders_tree.get_children():
            self.orders_tree.delete(item)

        # Insert new items
        for order in orders:
            values = (
                order.order_number,
                order.supplier,
                order.date_of_order.strftime('%Y-%m-%d'),
                order.status.value,
                order.payed.value,
                f"${order.total_amount:.2f}"
            )
            self.orders_tree.insert('', 'end', values=values, tags=(str(order.id),))

    def _on_order_select(self, event):
        """Handle order selection in treeview"""
        selection = self.orders_tree.selection()
        if not selection:
            return

        try:
            order_id = int(self.orders_tree.item(selection[0])['tags'][0])
            self.current_order = self.order_manager.get_order_by_id(order_id)

            if self.current_order:
                self._load_order_details(self.current_order.id)
        except Exception as e:
            messagebox.showerror("Selection Error", str(e))

    def _load_order_details(self, order_id: int):
        """
        Load details for a specific order

        Args:
            order_id: ID of the order to load details for
        """
        try:
            # Clear existing details
            for item in self.details_tree.get_children():
                self.details_tree.delete(item)

            # Get and populate details
            details = self.order_manager.get_order_details(order_id)
            for detail in details:
                values = (
                    detail.article,
                    detail.unique_id,
                    f"${detail.price:.2f}",
                    detail.amount,
                    f"${detail.total:.2f}",
                    detail.notes or ''
                )
                self.details_tree.insert('', 'end', values=values, tags=(str(detail.id),))
        except Exception as e:
            messagebox.showerror("Details Load Error", str(e))

    # Add other methods like show_add_order_dialog, show_add_item_dialog, etc.

    def cleanup(self):
        """Cleanup resources and handle unsaved changes"""
        try:
            if self.modified:
                if messagebox.askyesno("Save Changes", "Unsaved changes exist. Save now?"):
                    self.save_changes()
                else:
                    self.session.rollback()
        except Exception as e:
            messagebox.showerror("Cleanup Error", str(e))
        finally:
            if self.session:
                self.session.close()