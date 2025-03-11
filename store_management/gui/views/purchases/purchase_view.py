# views/purchases/purchase_view.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from database.models.enums import PurchaseStatus

from gui.base.base_list_view import BaseListView
from gui.base.base_dialog import BaseDialog
from gui.theme import COLORS, get_status_style
from gui.utils.event_bus import publish, subscribe, unsubscribe
from gui.utils.service_access import get_service
from gui.widgets.status_badge import StatusBadge
from gui.widgets.enhanced_treeview import EnhancedTreeview
from gui.config import DATE_FORMAT, DATETIME_FORMAT

logger = logging.getLogger(__name__)


class PurchaseView(BaseListView):
    """View for displaying and managing purchases."""

    def __init__(self, parent, **kwargs):
        """Initialize the purchase view.

        Args:
            parent: The parent widget
            **kwargs: Additional arguments including:
                filter_supplier_id: ID of supplier to filter purchases by
                filter_supplier_name: Name of supplier (for display)
                filter_status: Status to filter purchases by
                filter_date_range: Date range to filter purchases by
        """
        super().__init__(parent)
        self.title = "Purchases"
        self.subtitle = "Manage purchase orders and supplier transactions"

        # Initialize filter variables
        self.filter_supplier_id = kwargs.get('filter_supplier_id')
        self.filter_supplier_name = kwargs.get('filter_supplier_name')
        self.filter_status = tk.StringVar(value="All")
        self.filter_date_from = tk.StringVar()
        self.filter_date_to = tk.StringVar()

        # Set default dates (last 30 days)
        today = datetime.now()
        self.filter_date_to.set(today.strftime("%Y-%m-%d"))
        self.filter_date_from.set((today - timedelta(days=30)).strftime("%Y-%m-%d"))

        # Calendar variables
        self.cal_year = today.year
        self.cal_month = today.month

        # Subscribe to events
        subscribe("purchase_updated", self.on_purchase_updated)
        subscribe("purchase_created", self.on_purchase_updated)
        subscribe("inventory_updated", self.on_inventory_updated)

        # Build the view
        self.build()

    def build(self):
        """Build the purchase view layout."""
        super().build()

        # Add purchase metrics panel
        self.create_metrics_panel(self.content_frame)

        # If filtering by supplier, show supplier info
        if self.filter_supplier_id:
            self.create_supplier_info(self.content_frame)

    def _add_default_action_buttons(self):
        """Add default action buttons to the header."""
        # Add "Add" button
        self.add_button = ttk.Button(
            self.header,
            text="Create Purchase",
            command=self.on_add,
            style="Accent.TButton"
        )
        self.add_button.pack(side=tk.RIGHT, padx=(0, 10))

        # Add "Generate Report" button
        self.report_button = ttk.Button(
            self.header,
            text="Generate Report",
            command=self.on_generate_reports
        )
        self.report_button.pack(side=tk.RIGHT, padx=(0, 10))

        # Add "Export" button
        self.export_button = ttk.Button(
            self.header,
            text="Export",
            command=self.on_export
        )
        self.export_button.pack(side=tk.RIGHT, padx=(0, 10))

        # If filtering by supplier, add "Back to Suppliers" button
        if self.filter_supplier_id:
            self.back_button = ttk.Button(
                self.header,
                text="Back to Suppliers",
                command=self.on_back_to_suppliers
            )
            self.back_button.pack(side=tk.LEFT, padx=(0, 10))

    def create_metrics_panel(self, parent):
        """Create purchase metrics panel with key insights.

        Args:
            parent: The parent widget
        """
        # Create metrics frame
        metrics_frame = ttk.LabelFrame(parent, text="Purchase Overview")
        metrics_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        # Create metrics grid
        metrics_grid = ttk.Frame(metrics_frame)
        metrics_grid.pack(fill=tk.X, padx=10, pady=10)

        # Configure grid columns with equal width
        for i in range(4):
            metrics_grid.columnconfigure(i, weight=1)

        # Create metrics
        self.metrics = {
            "total_purchases": self._create_metric_widget(metrics_grid, "Total Purchases", "Loading...", 0, 0),
            "pending_orders": self._create_metric_widget(metrics_grid, "Pending Orders", "Loading...", 0, 1),
            "total_month": self._create_metric_widget(metrics_grid, "This Month", "Loading...", 0, 2),
            "avg_order_value": self._create_metric_widget(metrics_grid, "Avg. Order Value", "Loading...", 0, 3),
        }

        # Create status badges
        status_frame = ttk.Frame(metrics_frame)
        status_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        self.status_badges = {}
        statuses = [status.name for status in PurchaseStatus]

        for i, status in enumerate(statuses):
            self.status_badges[status] = self._create_status_badge(status_frame, status, status, i)

        # Create separator
        ttk.Separator(parent, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10, pady=5)

    def create_supplier_info(self, parent):
        """Create supplier info panel when filtering by supplier.

        Args:
            parent: The parent widget
        """
        # Create supplier info frame
        supplier_frame = ttk.LabelFrame(parent, text="Supplier Information")
        supplier_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        # Create inner frame
        inner_frame = ttk.Frame(supplier_frame)
        inner_frame.pack(fill=tk.X, padx=10, pady=10)

        # Supplier name
        supplier_name = self.filter_supplier_name or f"Supplier #{self.filter_supplier_id}"
        ttk.Label(
            inner_frame,
            text=supplier_name,
            font=("", 12, "bold")
        ).pack(anchor=tk.W)

        # Create bottom frame with stats
        stats_frame = ttk.Frame(inner_frame)
        stats_frame.pack(fill=tk.X, pady=(10, 0))

        # Configure grid columns with equal width
        for i in range(3):
            stats_frame.columnconfigure(i, weight=1)

        # Create supplier stats
        self.supplier_stats = {
            "total_purchases": self._create_supplier_stat(stats_frame, "Total Purchases", "Loading...", 0, 0),
            "total_value": self._create_supplier_stat(stats_frame, "Total Value", "Loading...", 0, 1),
            "last_purchase": self._create_supplier_stat(stats_frame, "Last Purchase", "Loading...", 0, 2),
        }

        # Create separator
        ttk.Separator(parent, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10, pady=5)

    def _create_metric_widget(self, parent, title, value, row, column):
        """Create a metric widget with title and value.

        Args:
            parent: The parent widget
            title: The title for the metric
            value: The initial value for the metric
            row: Grid row
            column: Grid column

        Returns:
            Dictionary with references to the widget labels
        """
        frame = ttk.Frame(parent)
        frame.grid(row=row, column=column, padx=10, pady=5, sticky="nsew")

        title_label = ttk.Label(
            frame,
            text=title,
            style="Secondary.TLabel",
            font=("", 10, "")
        )
        title_label.pack(anchor="w")

        value_label = ttk.Label(
            frame,
            text=value,
            font=("", 16, "bold")
        )
        value_label.pack(anchor="w", pady=(5, 0))

        return {"title": title_label, "value": value_label}

    def _create_supplier_stat(self, parent, title, value, row, column):
        """Create a supplier stat widget with title and value.

        Args:
            parent: The parent widget
            title: The title for the stat
            value: The initial value for the stat
            row: Grid row
            column: Grid column

        Returns:
            Dictionary with references to the widget labels
        """
        frame = ttk.Frame(parent)
        frame.grid(row=row, column=column, padx=10, pady=5, sticky="nsew")

        title_label = ttk.Label(
            frame,
            text=title,
            style="Secondary.TLabel",
            font=("", 10, "")
        )
        title_label.pack(anchor="w")

        value_label = ttk.Label(
            frame,
            text=value,
            font=("", 12, "")
        )
        value_label.pack(anchor="w", pady=(5, 0))

        return {"title": title_label, "value": value_label}

    def _create_status_badge(self, parent, label_text, status_value, col):
        """Create a status badge with counter.

        Args:
            parent: The parent widget
            label_text: The text to display on the badge
            status_value: The status value for styling
            col: Grid column

        Returns:
            Label widget for the count
        """
        frame = ttk.Frame(parent)
        frame.pack(side=tk.LEFT, padx=10, pady=5)

        badge = StatusBadge(frame, text=label_text, status_value=status_value)
        badge.pack(side=tk.LEFT)

        count_label = ttk.Label(frame, text="0", font=("", 10, "bold"))
        count_label.pack(side=tk.LEFT, padx=(5, 0))

        return count_label

    def create_treeview(self, parent):
        """Create the treeview for displaying purchase data.

        Args:
            parent: The parent widget
        """
        # Create the treeview with columns
        self.treeview = ttk.Treeview(
            parent,
            columns=("id", "date", "supplier", "status", "items", "amount", "received"),
            show="headings",
            selectmode="browse"
        )

        # Set column headings
        self.treeview.heading("id", text="ID")
        self.treeview.heading("date", text="Date")
        self.treeview.heading("supplier", text="Supplier")
        self.treeview.heading("status", text="Status")
        self.treeview.heading("items", text="Items")
        self.treeview.heading("amount", text="Amount")
        self.treeview.heading("received", text="Received")

        # Configure column widths
        self.treeview.column("id", width=50, stretch=False)
        self.treeview.column("date", width=100, stretch=False)
        self.treeview.column("supplier", width=200, stretch=True)
        self.treeview.column("status", width=100, stretch=False)
        self.treeview.column("items", width=60, stretch=False)
        self.treeview.column("amount", width=100, stretch=False)
        self.treeview.column("received", width=100, stretch=False)

        # Create scrollbar
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.treeview.yview)
        self.treeview.configure(yscroll=scrollbar.set)

        # Place widgets
        self.treeview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind events
        self.treeview.bind("<<TreeviewSelect>>", self.on_select)
        self.treeview.bind("<Double-1>", lambda e: self.on_view())

    def add_advanced_filters(self):
        """Add advanced search filters to the search frame."""
        # Add filter frame
        filter_frame = ttk.Frame(self.search_frame)
        filter_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        # Date range filter
        date_frame = ttk.Frame(filter_frame)
        date_frame.pack(side=tk.LEFT, padx=(0, 20))

        ttk.Label(date_frame, text="Date Range:").pack(side=tk.LEFT, padx=(0, 5))

        # From date
        ttk.Label(date_frame, text="From:").pack(side=tk.LEFT, padx=(10, 5))
        date_from_entry = ttk.Entry(date_frame, textvariable=self.filter_date_from, width=12)
        date_from_entry.pack(side=tk.LEFT)

        ttk.Button(
            date_frame,
            text="...",
            width=3,
            command=lambda: self.show_date_picker(self.filter_date_from)
        ).pack(side=tk.LEFT, padx=(2, 10))

        # To date
        ttk.Label(date_frame, text="To:").pack(side=tk.LEFT, padx=(0, 5))
        date_to_entry = ttk.Entry(date_frame, textvariable=self.filter_date_to, width=12)
        date_to_entry.pack(side=tk.LEFT)

        ttk.Button(
            date_frame,
            text="...",
            width=3,
            command=lambda: self.show_date_picker(self.filter_date_to)
        ).pack(side=tk.LEFT, padx=(2, 0))

        # Status filter
        status_frame = ttk.Frame(filter_frame)
        status_frame.pack(side=tk.LEFT)

        ttk.Label(status_frame, text="Status:").pack(side=tk.LEFT, padx=(0, 5))

        # Create status combobox
        statuses = ["All"] + [status.name for status in PurchaseStatus]
        status_combobox = ttk.Combobox(
            status_frame,
            textvariable=self.filter_status,
            values=statuses,
            state="readonly",
            width=15
        )
        status_combobox.pack(side=tk.LEFT)

        # Add filter buttons
        btn_frame = ttk.Frame(filter_frame)
        btn_frame.pack(side=tk.RIGHT)

        ttk.Button(
            btn_frame,
            text="Apply Filters",
            command=self.on_apply_filters
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            btn_frame,
            text="Clear Filters",
            command=self.on_clear_filters
        ).pack(side=tk.LEFT)

    def add_context_menu_items(self, menu):
        """Add purchase-specific context menu items.

        Args:
            menu: The context menu to add items to
        """
        menu.add_command(label="View Details", command=self.on_view)
        menu.add_command(label="Edit Purchase", command=self.on_edit)
        menu.add_separator()
        menu.add_command(label="Receive Items", command=self.on_receive)
        menu.add_command(label="Update Status", command=self.on_update_status)
        menu.add_separator()
        menu.add_command(label="Delete Purchase", command=self.on_delete)

    def create_item_actions(self, parent):
        """Create action buttons for selected purchases.

        Args:
            parent: The parent widget
        """
        # Create action buttons frame
        actions_frame = ttk.Frame(parent)
        actions_frame.pack(fill=tk.X, padx=10, pady=10)

        # View button
        self.view_btn = ttk.Button(
            actions_frame,
            text="View Details",
            command=self.on_view,
            state=tk.DISABLED
        )
        self.view_btn.pack(side=tk.LEFT, padx=(0, 5))

        # Edit button
        self.edit_btn = ttk.Button(
            actions_frame,
            text="Edit",
            command=self.on_edit,
            state=tk.DISABLED
        )
        self.edit_btn.pack(side=tk.LEFT, padx=5)

        # Delete button
        self.delete_btn = ttk.Button(
            actions_frame,
            text="Delete",
            command=self.on_delete,
            state=tk.DISABLED
        )
        self.delete_btn.pack(side=tk.LEFT, padx=5)

        # Add additional buttons
        self.receive_btn = ttk.Button(
            actions_frame,
            text="Receive Items",
            command=self.on_receive,
            state=tk.DISABLED
        )
        self.receive_btn.pack(side=tk.LEFT, padx=5)

        self.status_btn = ttk.Button(
            actions_frame,
            text="Update Status",
            command=self.on_update_status,
            state=tk.DISABLED
        )
        self.status_btn.pack(side=tk.LEFT, padx=5)

        self.print_btn = ttk.Button(
            actions_frame,
            text="Print PO",
            command=self.on_print,
            state=tk.DISABLED
        )
        self.print_btn.pack(side=tk.LEFT, padx=5)

    def add_item_action_buttons(self, parent):
        """Add additional action buttons for purchases.

        Args:
            parent: The parent widget for the buttons
        """
        # Add bulk actions section
        bulk_frame = ttk.LabelFrame(parent, text="Bulk Actions")
        bulk_frame.pack(fill=tk.X, padx=10, pady=10)

        # Create inner frame
        inner_frame = ttk.Frame(bulk_frame)
        inner_frame.pack(fill=tk.X, padx=10, pady=10)

        # Create receive all button
        ttk.Button(
            inner_frame,
            text="Receive All Pending",
            command=self.on_receive_all_pending
        ).pack(side=tk.LEFT, padx=(0, 5))

        # Create check late orders button
        ttk.Button(
            inner_frame,
            text="Check Late Orders",
            command=self.on_check_late_orders
        ).pack(side=tk.LEFT, padx=5)

        # Create reorder low stock button
        ttk.Button(
            inner_frame,
            text="Reorder Low Stock",
            command=self.on_reorder_low_stock
        ).pack(side=tk.LEFT, padx=5)

    def extract_item_values(self, item):
        """Extract values from a purchase item for display in the treeview.

        Args:
            item: The purchase item to extract values from

        Returns:
            List of values corresponding to treeview columns
        """
        # Format date
        purchase_date = item.get('created_at', '')
        if isinstance(purchase_date, datetime):
            purchase_date = purchase_date.strftime('%Y-%m-%d')

        # Format supplier
        supplier = item.get('supplier', {})
        supplier_name = supplier.get('name', '') if supplier else ''

        # Format status
        status = item.get('status', '')
        if hasattr(status, 'name'):
            status = status.name

        # Format items count
        items_count = len(item.get('items', []))

        # Format amount
        amount = item.get('total_amount', 0)
        if isinstance(amount, (int, float)):
            amount = f"${amount:.2f}"

        # Format received date
        received_date = item.get('received_at', '')
        if isinstance(received_date, datetime):
            received_date = received_date.strftime('%Y-%m-%d')
        elif not received_date and status in ['RECEIVED', 'COMPLETED']:
            received_date = "Yes"
        elif not received_date:
            received_date = "No"

        return [
            item.get('id', ''),
            purchase_date,
            supplier_name,
            status,
            items_count,
            amount,
            received_date
        ]

    def get_items(self, service, offset, limit):
        """Get purchases for the current page.

        Args:
            service: The service to use
            offset: Pagination offset
            limit: Page size

        Returns:
            List of purchases
        """
        # Get filter values
        status_filter = self.filter_status.get()
        if status_filter == "All":
            status_filter = None

        # Get date filters
        date_from = self.filter_date_from.get()
        date_to = self.filter_date_to.get()

        # Get search text
        search_text = self.search_frame.get_field_value("search_text") if hasattr(self, "search_frame") else ""

        # Get purchases
        return service.get_purchases(
            search_text=search_text,
            supplier_id=self.filter_supplier_id,
            status=status_filter,
            date_from=date_from,
            date_to=date_to,
            offset=offset,
            limit=limit
        )

    def get_total_count(self, service):
        """Get the total count of purchases.

        Args:
            service: The service to use

        Returns:
            The total count of purchases
        """
        # Get filter values
        status_filter = self.filter_status.get()
        if status_filter == "All":
            status_filter = None

        # Get date filters
        date_from = self.filter_date_from.get()
        date_to = self.filter_date_to.get()

        # Get search text
        search_text = self.search_frame.get_field_value("search_text") if hasattr(self, "search_frame") else ""

        # Get total count
        return service.get_purchase_count(
            search_text=search_text,
            supplier_id=self.filter_supplier_id,
            status=status_filter,
            date_from=date_from,
            date_to=date_to
        )

    def load_data(self):
        """Load purchase data into the treeview based on current filters and pagination."""
        try:
            # Clear treeview
            self.treeview.delete(*self.treeview.get_children())

            # Get purchase service
            purchase_service = get_service('IPurchaseService')

            # Calculate offset
            offset = (self.current_page - 1) * self.page_size

            # Get total count
            total_count = self.get_total_count(purchase_service)

            # Calculate total pages
            self.total_pages = (total_count + self.page_size - 1) // self.page_size

            # Update pagination display
            self.update_pagination_display(self.total_pages)

            # Get purchases
            purchases = self.get_items(purchase_service, offset, self.page_size)

            # Insert purchases into treeview
            for purchase in purchases:
                values = self.extract_item_values(purchase)
                self.treeview.insert('', 'end', values=values)

            # Update metrics
            self.update_metrics()

            # Update supplier stats if filtering by supplier
            if self.filter_supplier_id:
                self.update_supplier_stats()

        except Exception as e:
            logger.error(f"Error loading purchase data: {e}")
            messagebox.showerror("Error", f"Failed to load purchase data: {e}")

    def update_metrics(self):
        """Update purchase metrics displayed in the panel."""
        try:
            # Get purchase service
            purchase_service = get_service('IPurchaseService')

            # Get metrics
            metrics = purchase_service.get_purchase_metrics()

            # Update metric values
            self.metrics["total_purchases"]["value"].config(text=str(metrics.get("total_purchases", 0)))
            self.metrics["pending_orders"]["value"].config(text=str(metrics.get("pending_orders", 0)))

            # Format month total
            month_total = metrics.get("month_total", 0)
            if isinstance(month_total, (int, float)):
                month_total = f"${month_total:.2f}"
            self.metrics["total_month"]["value"].config(text=month_total)

            # Format average order value
            avg_order = metrics.get("avg_order_value", 0)
            if isinstance(avg_order, (int, float)):
                avg_order = f"${avg_order:.2f}"
            self.metrics["avg_order_value"]["value"].config(text=avg_order)

            # Update status badges
            for status, count in metrics.get("status_counts", {}).items():
                if status in self.status_badges:
                    self.status_badges[status].config(text=str(count))

        except Exception as e:
            logger.error(f"Error updating purchase metrics: {e}")
            messagebox.showerror("Error", f"Failed to update purchase metrics: {e}")

    def update_supplier_stats(self):
        """Update supplier stats when filtering by supplier."""
        try:
            # Get purchase service
            purchase_service = get_service('IPurchaseService')

            # Get supplier stats
            stats = purchase_service.get_supplier_purchase_stats(self.filter_supplier_id)

            # Update stats
            self.supplier_stats["total_purchases"]["value"].config(text=str(stats.get("total_purchases", 0)))

            # Format total value
            total_value = stats.get("total_value", 0)
            if isinstance(total_value, (int, float)):
                total_value = f"${total_value:.2f}"
            self.supplier_stats["total_value"]["value"].config(text=total_value)

            # Format last purchase date
            last_purchase = stats.get("last_purchase", "")
            if isinstance(last_purchase, datetime):
                last_purchase = last_purchase.strftime('%Y-%m-%d')
            self.supplier_stats["last_purchase"]["value"].config(text=last_purchase)

        except Exception as e:
            logger.error(f"Error updating supplier stats: {e}")
            messagebox.showerror("Error", f"Failed to update supplier stats: {e}")

    def on_select(self, event=None):
        """Handle item selection."""
        # Enable/disable buttons based on selection
        if self.treeview.selection():
            # Get selected purchase status
            selected_values = self.treeview.item(self.treeview.selection()[0], "values")
            status = selected_values[3]

            # Enable common buttons
            self.view_btn.config(state=tk.NORMAL)
            self.edit_btn.config(state=tk.NORMAL)
            self.delete_btn.config(state=tk.NORMAL)
            self.status_btn.config(state=tk.NORMAL)
            self.print_btn.config(state=tk.NORMAL)

            # Enable/disable receive button based on status
            if status in ['ORDERED', 'PARTIALLY_RECEIVED']:
                self.receive_btn.config(state=tk.NORMAL)
            else:
                self.receive_btn.config(state=tk.DISABLED)
        else:
            self.view_btn.config(state=tk.DISABLED)
            self.edit_btn.config(state=tk.DISABLED)
            self.delete_btn.config(state=tk.DISABLED)
            self.receive_btn.config(state=tk.DISABLED)
            self.status_btn.config(state=tk.DISABLED)
            self.print_btn.config(state=tk.DISABLED)

    def on_apply_filters(self):
        """Handle apply filters button click."""
        # Reset to first page and reload data
        self.current_page = 1
        self.load_data()

    def on_clear_filters(self):
        """Handle clear filters button click."""
        # Reset filter values (except supplier filter if present)
        self.filter_status.set("All")

        # Set default dates (last 30 days)
        today = datetime.now()
        self.filter_date_to.set(today.strftime("%Y-%m-%d"))
        self.filter_date_from.set((today - timedelta(days=30)).strftime("%Y-%m-%d"))

        # Reset search field if exists
        if hasattr(self, "search_frame"):
            self.search_frame.set_field_value("search_text", "")

        # Reload data
        self.on_apply_filters()

    def on_back_to_suppliers(self):
        """Handle back to suppliers button click."""
        # Navigate to supplier view
        self.master.show_view("supplier_view")

    def on_add(self):
        """Handle add new purchase action."""
        # Create view data
        view_data = {
            "create_new": True
        }

        # If filtering by supplier, include supplier info
        if self.filter_supplier_id:
            view_data["supplier_id"] = self.filter_supplier_id
            view_data["supplier_name"] = self.filter_supplier_name

        # Navigate to purchase details view
        self.master.show_view("purchase_details_view", view_data=view_data)

    def on_view(self):
        """Handle view purchase action."""
        # Get selected purchase ID
        selected_id = self.get_selected_id()
        if not selected_id:
            return

        # Create view data
        view_data = {
            "purchase_id": selected_id,
            "readonly": True
        }

        # Navigate to purchase details view
        self.master.show_view("purchase_details_view", view_data=view_data)

    def on_edit(self):
        """Handle edit purchase action."""
        # Get selected purchase ID
        selected_id = self.get_selected_id()
        if not selected_id:
            return

        # Create view data
        view_data = {
            "purchase_id": selected_id,
            "readonly": False
        }

        # Navigate to purchase details view
        self.master.show_view("purchase_details_view", view_data=view_data)

    def on_delete(self):
        """Handle delete purchase action."""
        # Get selected purchase ID
        selected_id = self.get_selected_id()
        if not selected_id:
            return

        # Confirm deletion
        if not messagebox.askyesno(
                "Confirm Delete",
                "Are you sure you want to delete this purchase?\n\nThis action cannot be undone."
        ):
            return

        try:
            # Get purchase service
            purchase_service = get_service('IPurchaseService')

            # Delete purchase
            success = purchase_service.delete_purchase(selected_id)

            if success:
                messagebox.showinfo("Success", "Purchase deleted successfully.")

                # Refresh the view
                self.refresh()
            else:
                messagebox.showerror("Error", "Failed to delete purchase.")

        except Exception as e:
            logger.error(f"Error deleting purchase: {e}")
            messagebox.showerror("Error", f"Failed to delete purchase: {e}")

    def on_receive(self):
        """Handle receive items action."""
        # Get selected purchase ID
        selected_id = self.get_selected_id()
        if not selected_id:
            return

        try:
            # Get purchase service
            purchase_service = get_service('IPurchaseService')

            # Get purchase details
            purchase = purchase_service.get_purchase(selected_id)

            if not purchase:
                messagebox.showerror("Error", f"Could not find purchase with ID {selected_id}")
                return

            # Create receive dialog
            dialog = BaseDialog(self.winfo_toplevel(), "Receive Purchase Items")
            main_frame = ttk.Frame(dialog.interior, padding=10)
            main_frame.pack(fill=tk.BOTH, expand=True)

            # Purchase info
            info_frame = ttk.Frame(main_frame)
            info_frame.pack(fill=tk.X, pady=(0, 10))

            # Purchase ID and supplier
            ttk.Label(
                info_frame,
                text=f"Purchase Order #{purchase.get('id', '')}",
                font=("", 12, "bold")
            ).pack(side=tk.LEFT)

            supplier = purchase.get('supplier', {})
            if supplier:
                ttk.Label(
                    info_frame,
                    text=f" - {supplier.get('name', '')}",
                    style="Secondary.TLabel"
                ).pack(side=tk.LEFT)

            # Create separator
            ttk.Separator(main_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)

            # Create receive date frame
            date_frame = ttk.Frame(main_frame)
            date_frame.pack(fill=tk.X, pady=(0, 10))

            ttk.Label(date_frame, text="Receive Date:").pack(side=tk.LEFT, padx=(0, 5))

            receive_date = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
            date_entry = ttk.Entry(date_frame, textvariable=receive_date, width=15)
            date_entry.pack(side=tk.LEFT)

            ttk.Button(
                date_frame,
                text="...",
                width=3,
                command=lambda: self.show_date_picker(receive_date)
            ).pack(side=tk.LEFT, padx=(5, 0))

            # Create items frame
            items_frame = ttk.LabelFrame(main_frame, text="Items to Receive")
            items_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

            # Create treeview for items
            tree_frame = ttk.Frame(items_frame)
            tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

            items_tree = ttk.Treeview(
                tree_frame,
                columns=("id", "name", "ordered", "received", "to_receive", "status"),
                show="headings",
                selectmode="browse"
            )

            # Configure columns
            items_tree.heading("id", text="ID")
            items_tree.heading("name", text="Item")
            items_tree.heading("ordered", text="Ordered")
            items_tree.heading("received", text="Already Received")
            items_tree.heading("to_receive", text="To Receive")
            items_tree.heading("status", text="Status")

            items_tree.column("id", width=50, stretch=False)
            items_tree.column("name", width=200, stretch=True)
            items_tree.column("ordered", width=80, stretch=False)
            items_tree.column("received", width=120, stretch=False)
            items_tree.column("to_receive", width=80, stretch=False)
            items_tree.column("status", width=100, stretch=False)

            # Create scrollbar
            scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=items_tree.yview)
            items_tree.configure(yscroll=scrollbar.set)

            items_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            # Populate items tree
            items = purchase.get('items', [])
            item_vars = {}

            for item in items:
                item_id = item.get('id')
                quantity_ordered = item.get('quantity', 0)
                quantity_received = item.get('quantity_received', 0)
                to_receive = quantity_ordered - quantity_received

                # Skip fully received items
                if to_receive <= 0:
                    continue

                # Create variable for to_receive value
                item_vars[item_id] = tk.StringVar(value=str(to_receive))

                # Insert item
                items_tree.insert(
                    '',
                    'end',
                    values=(
                        item_id,
                        item.get('name', ''),
                        quantity_ordered,
                        quantity_received,
                        to_receive,
                        "Pending"
                    )
                )

            # Create quantity adjustment frame
            qty_frame = ttk.Frame(items_frame)
            qty_frame.pack(fill=tk.X, padx=5, pady=(0, 5))

            ttk.Label(qty_frame, text="Adjust Quantity:").pack(side=tk.LEFT, padx=(0, 5))

            # Create spinbox for quantity
            ttk.Label(qty_frame, text="To Receive:").pack(side=tk.LEFT, padx=(10, 5))

            qty_var = tk.StringVar(value="0")
            qty_spinbox = ttk.Spinbox(qty_frame, from_=0, to=1000, textvariable=qty_var, width=5)
            qty_spinbox.pack(side=tk.LEFT, padx=(0, 5))

            # Button to update quantity
            ttk.Button(
                qty_frame,
                text="Update",
                command=lambda: self.update_receive_quantity(items_tree, item_vars, qty_var.get())
            ).pack(side=tk.LEFT, padx=5)

            # Create received quality frame
            quality_frame = ttk.Frame(items_frame)
            quality_frame.pack(fill=tk.X, padx=5, pady=(0, 5))

            ttk.Label(quality_frame, text="Quality Notes:").pack(side=tk.LEFT, padx=(0, 5))

            quality_var = tk.StringVar()
            ttk.Entry(quality_frame, textvariable=quality_var, width=40).pack(side=tk.LEFT, expand=True, fill=tk.X)

            # Create notes frame
            notes_frame = ttk.LabelFrame(main_frame, text="Receipt Notes")
            notes_frame.pack(fill=tk.X, pady=(0, 10))

            notes_var = tk.StringVar()
            ttk.Entry(notes_frame, textvariable=notes_var).pack(padx=5, pady=5, fill=tk.X)

            # Button frame
            button_frame = ttk.Frame(main_frame)
            button_frame.pack(fill=tk.X, pady=(0, 5))

            ttk.Button(
                button_frame,
                text="Receive Items",
                command=lambda: self.process_receive(
                    selected_id,
                    items_tree,
                    item_vars,
                    receive_date.get(),
                    notes_var.get(),
                    dialog
                ),
                style="Accent.TButton"
            ).pack(side=tk.RIGHT, padx=5)

            ttk.Button(
                button_frame,
                text="Cancel",
                command=dialog.destroy
            ).pack(side=tk.RIGHT, padx=5)

            # Select first item if available
            if items_tree.get_children():
                items_tree.selection_set(items_tree.get_children()[0])

            # Bind select to update qty_var
            def on_item_select(event):
                if items_tree.selection():
                    item_id = items_tree.item(items_tree.selection()[0], "values")[0]
                    if item_id in item_vars:
                        qty_var.set(item_vars[item_id].get())

            items_tree.bind("<<TreeviewSelect>>", on_item_select)

            # Show dialog
            dialog.show()

        except Exception as e:
            logger.error(f"Error showing receive dialog: {e}")
            messagebox.showerror("Error", f"Failed to open receive dialog: {e}")

    def update_receive_quantity(self, tree, item_vars, qty):
        """Update receive quantity for selected item.

        Args:
            tree: The treeview with items
            item_vars: Dictionary of item_id -> StringVar for quantities
            qty: New quantity as string
        """
        selection = tree.selection()
        if not selection:
            return

        # Get selected item
        item_values = tree.item(selection[0], "values")
        item_id = item_values[0]
        ordered = int(item_values[2])
        received = int(item_values[3])
        max_receive = ordered - received

        # Validate quantity
        try:
            new_qty = int(qty)
            if new_qty < 0:
                new_qty = 0
            elif new_qty > max_receive:
                new_qty = max_receive
        except ValueError:
            new_qty = 0

        # Update variable
        if item_id in item_vars:
            item_vars[item_id].set(str(new_qty))

        # Update tree
        tree.item(
            selection[0],
            values=(
                item_id,
                item_values[1],
                ordered,
                received,
                new_qty,
                "Pending"
            )
        )

    def process_receive(self, purchase_id, tree, item_vars, receive_date, notes, dialog):
        """Process receive action.

        Args:
            purchase_id: ID of the purchase
            tree: The treeview with items
            item_vars: Dictionary of item_id -> StringVar for quantities
            receive_date: Date of receipt
            notes: Receipt notes
            dialog: Dialog to close on success
        """
        try:
            # Create receipt data
            receipt_data = {
                'purchase_id': purchase_id,
                'receive_date': receive_date,
                'notes': notes,
                'items': []
            }

            # Add items with quantities to receive
            for item_id, qty_var in item_vars.items():
                try:
                    qty = int(qty_var.get())
                    if qty > 0:
                        receipt_data['items'].append({
                            'item_id': item_id,
                            'quantity': qty
                        })
                except ValueError:
                    pass

            # Validate at least one item
            if not receipt_data['items']:
                messagebox.showerror("Error", "Please enter at least one item to receive.")
                return

            # Get purchase service
            purchase_service = get_service('IPurchaseService')

            # Process receipt
            result = purchase_service.receive_purchase_items(receipt_data)

            if result:
                messagebox.showinfo("Success", "Items received successfully.")
                dialog.destroy()

                # Publish event
                publish("purchase_updated", {"purchase_id": purchase_id})
                publish("inventory_updated", {})

                # Refresh the view
                self.refresh()
            else:
                messagebox.showerror("Error", "Failed to receive items.")

        except Exception as e:
            logger.error(f"Error receiving items: {e}")
            messagebox.showerror("Error", f"Failed to receive items: {e}")

    def on_update_status(self):
        """Handle update status action."""
        # Get selected purchase ID
        selected_id = self.get_selected_id()
        if not selected_id:
            return

        try:
            # Get purchase service
            purchase_service = get_service('IPurchaseService')

            # Get purchase details
            purchase = purchase_service.get_purchase(selected_id)

            if not purchase:
                messagebox.showerror("Error", f"Could not find purchase with ID {selected_id}")
                return

            # Get current status
            current_status = purchase.get('status', '')
            if hasattr(current_status, 'name'):
                current_status = current_status.name

            # Create status dialog
            dialog = tk.Toplevel(self.winfo_toplevel())
            dialog.title("Update Purchase Status")
            dialog.geometry("400x250")
            dialog.transient(self.winfo_toplevel())
            dialog.grab_set()

            # Create main frame
            main_frame = ttk.Frame(dialog, padding=10)
            main_frame.pack(fill=tk.BOTH, expand=True)

            # Current status
            ttk.Label(main_frame, text=f"Current Status: {current_status}").pack(anchor=tk.W, pady=(0, 10))

            # New status
            ttk.Label(main_frame, text="New Status:").pack(anchor=tk.W)

            # Status options
            statuses = [status.name for status in PurchaseStatus]
            status_var = tk.StringVar(value=current_status)

            status_combo = ttk.Combobox(
                main_frame,
                textvariable=status_var,
                values=statuses,
                state="readonly",
                width=20
            )
            status_combo.pack(anchor=tk.W, pady=(5, 10))

            # Notes
            ttk.Label(main_frame, text="Status Change Notes:").pack(anchor=tk.W)

            notes_var = tk.StringVar()
            ttk.Entry(main_frame, textvariable=notes_var, width=40).pack(fill=tk.X, pady=(5, 10))

            # Buttons
            button_frame = ttk.Frame(main_frame)
            button_frame.pack(fill=tk.X, pady=(10, 0))

            ttk.Button(
                button_frame,
                text="Update",
                command=lambda: self.update_purchase_status(
                    selected_id,
                    status_var.get(),
                    notes_var.get(),
                    dialog
                ),
                style="Accent.TButton"
            ).pack(side=tk.RIGHT, padx=(5, 0))

            ttk.Button(
                button_frame,
                text="Cancel",
                command=dialog.destroy
            ).pack(side=tk.RIGHT, padx=(0, 5))

        except Exception as e:
            logger.error(f"Error updating status: {e}")
            messagebox.showerror("Error", f"Failed to update status: {e}")

    def update_purchase_status(self, purchase_id, status, notes, dialog):
        """Update purchase status.

        Args:
            purchase_id: ID of the purchase
            status: New status value
            notes: Status change notes
            dialog: Dialog to close on success
        """
        try:
            # Get purchase service
            purchase_service = get_service('IPurchaseService')

            # Update status
            result = purchase_service.update_purchase_status(
                purchase_id,
                status,
                notes
            )

            if result:
                messagebox.showinfo("Success", "Status updated successfully.")
                dialog.destroy()

                # Publish event
                publish("purchase_updated", {"purchase_id": purchase_id})

                # Refresh the view
                self.refresh()
            else:
                messagebox.showerror("Error", "Failed to update status.")

        except Exception as e:
            logger.error(f"Error updating status: {e}")
            messagebox.showerror("Error", f"Failed to update status: {e}")

    def on_print(self):
        """Handle print purchase order action."""
        # Get selected purchase ID
        selected_id = self.get_selected_id()
        if not selected_id:
            return

        try:
            # Get purchase service
            purchase_service = get_service('IPurchaseService')

            # Print purchase order
            result = purchase_service.print_purchase_order(selected_id)

            if result:
                messagebox.showinfo(
                    "Print Complete",
                    f"Purchase order has been generated successfully.\n\nFile: {result}"
                )
            else:
                messagebox.showerror("Error", "Failed to generate purchase order.")

        except Exception as e:
            logger.error(f"Error printing purchase order: {e}")
            messagebox.showerror("Error", f"Failed to print purchase order: {e}")

    def on_receive_all_pending(self):
        """Handle receive all pending button click."""
        try:
            # Get purchase service
            purchase_service = get_service('IPurchaseService')

            # Get pending deliveries
            pending_deliveries = purchase_service.get_pending_deliveries()

            if not pending_deliveries:
                messagebox.showinfo("No Pending Deliveries", "There are no pending deliveries to receive.")
                return

            # Create dialog to display pending purchases
            dialog = BaseDialog(self.winfo_toplevel(), "Receive Pending Deliveries")
            main_frame = ttk.Frame(dialog.interior, padding=10)
            main_frame.pack(fill=tk.BOTH, expand=True)

            # Create treeview
            ttk.Label(main_frame, text="Select purchases to receive:", font=("", 12, "bold")).pack(anchor="w",
                                                                                                   pady=(0, 10))
            tree_frame = ttk.Frame(main_frame)
            tree_frame.pack(fill=tk.BOTH, expand=True, pady=5)

            tree = EnhancedTreeview(
                tree_frame,
                columns=("id", "date", "supplier", "total", "items", "status"),
                show="headings",
                height=10
            )
            tree.heading("id", text="Order #")
            tree.heading("date", text="Order Date")
            tree.heading("supplier", text="Supplier")
            tree.heading("total", text="Total")
            tree.heading("items", text="Items")
            tree.heading("status", text="Status")

            tree.column("id", width=80)
            tree.column("date", width=120)
            tree.column("supplier", width=150)
            tree.column("total", width=100)
            tree.column("items", width=80)
            tree.column("status", width=120)

            tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            # Add scrollbar
            scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            tree.configure(yscrollcommand=scrollbar.set)

            # Populate tree
            for purchase in pending_deliveries:
                tree.insert("", "end", values=(
                    purchase.get('id'),
                    purchase.get('created_at').strftime(DATE_FORMAT) if purchase.get('created_at') else "",
                    purchase.get('supplier', {}).get('name', 'N/A'),
                    f"${purchase.get('total_amount', 0):.2f}",
                    len(purchase.get('items', [])),
                    purchase.get('status')
                ))

            # Add buttons
            btn_frame = ttk.Frame(main_frame)
            btn_frame.pack(fill=tk.X, pady=10)

            ttk.Button(
                btn_frame,
                text="Receive Selected",
                command=lambda: self.view_order_from_tree(tree, dialog)
            ).pack(side=tk.LEFT, padx=5)

            ttk.Button(
                btn_frame,
                text="Mark All Received",
                command=lambda: self.receive_all_orders(pending_deliveries, dialog)
            ).pack(side=tk.LEFT, padx=5)

            ttk.Button(
                btn_frame,
                text="Cancel",
                command=dialog.destroy
            ).pack(side=tk.RIGHT, padx=5)

            dialog.show()

        except Exception as e:
            logger.error(f"Error loading pending deliveries: {e}")
            messagebox.showerror("Error", f"Failed to load pending deliveries: {e}")

    def view_order_from_tree(self, tree, dialog):
        """View order from treeview.

        Args:
            tree: The treeview with orders
            dialog: Dialog to close
        """
        selection = tree.selection()
        if not selection:
            messagebox.showinfo("No Selection", "Please select an order first.")
            return

        # Get selected order ID
        order_id = tree.item(selection[0], "values")[0]

        # Create view data
        view_data = {
            "purchase_id": order_id,
            "readonly": True
        }

        # Close dialog
        dialog.destroy()

        # Navigate to purchase details view
        self.master.show_view("purchase_details_view", view_data=view_data)

    def receive_all_orders(self, purchases, dialog):
        """Mark all displayed orders as received.

        Args:
            purchases: List of purchase objects
            dialog: Dialog to close
        """
        if not messagebox.askyesno(
                "Confirm Action",
                f"Are you sure you want to mark {len(purchases)} orders as received? "
                "This will update inventory for all items."
        ):
            return

        try:
            # Get purchase service
            purchase_service = get_service('IPurchaseService')

            success_count = 0
            for purchase in purchases:
                try:
                    # Use default of receiving all items
                    receive_data = {
                        'purchase_id': purchase.get('id'),
                        'items': [
                            {
                                'item_id': item.get('id'),
                                'quantity': item.get('quantity') - item.get('quantity_received', 0)
                            }
                            for item in purchase.get('items', [])
                            if item.get('quantity', 0) > item.get('quantity_received', 0)
                        ],
                        'receive_date': datetime.now().strftime('%Y-%m-%d'),
                        'notes': "Bulk receiving process"
                    }

                    if receive_data['items']:
                        result = purchase_service.receive_purchase_items(receive_data)
                        if result:
                            success_count += 1
                except Exception as e:
                    logger.error(f"Error receiving purchase {purchase.get('id')}: {e}")

            if success_count > 0:
                messagebox.showinfo(
                    "Success",
                    f"Successfully processed {success_count} of {len(purchases)} orders."
                )

                # Publish events
                publish('purchase_updated', {'bulk_update': True})
                publish('inventory_updated', {})

                # Refresh the view
                self.refresh()
            else:
                messagebox.showerror("Error", "Failed to process any orders.")

            dialog.destroy()

        except Exception as e:
            logger.error(f"Error processing orders: {e}")
            messagebox.showerror("Error", f"Failed to process orders: {e}")

    def on_check_late_orders(self):
        """Handle check late orders button click."""
        try:
            # Get purchase service
            purchase_service = get_service('IPurchaseService')

            # Get late orders
            late_orders = purchase_service.get_late_orders()

            if not late_orders:
                messagebox.showinfo("No Late Orders", "There are no late deliveries at this time.")
                return

            # Create dialog to display late orders
            dialog = BaseDialog(self.winfo_toplevel(), "Late Purchase Orders")
            main_frame = ttk.Frame(dialog.interior, padding=10)
            main_frame.pack(fill=tk.BOTH, expand=True)

            # Create treeview
            ttk.Label(
                main_frame,
                text=f"Late Orders ({len(late_orders)}):",
                font=("", 12, "bold")
            ).pack(anchor="w", pady=(0, 10))

            tree_frame = ttk.Frame(main_frame)
            tree_frame.pack(fill=tk.BOTH, expand=True, pady=5)

            tree = EnhancedTreeview(
                tree_frame,
                columns=("id", "date", "supplier", "days_late", "total", "items", "status"),
                show="headings",
                height=10
            )
            tree.heading("id", text="Order #")
            tree.heading("date", text="Order Date")
            tree.heading("supplier", text="Supplier")
            tree.heading("days_late", text="Days Late")
            tree.heading("total", text="Total")
            tree.heading("items", text="Items")
            tree.heading("status", text="Status")

            tree.column("id", width=80)
            tree.column("date", width=120)
            tree.column("supplier", width=150)
            tree.column("days_late", width=80)
            tree.column("total", width=100)
            tree.column("items", width=80)
            tree.column("status", width=120)

            tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            # Add scrollbar
            scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            tree.configure(yscrollcommand=scrollbar.set)

            # Populate tree
            for order in late_orders:
                days_late = order.get('days_late', 0)
                tree.insert("", "end", values=(
                    order.get('id'),
                    order.get('created_at').strftime(DATE_FORMAT) if order.get('created_at') else "",
                    order.get('supplier', {}).get('name', 'N/A'),
                    days_late,
                    f"${order.get('total_amount', 0):.2f}",
                    len(order.get('items', [])),
                    order.get('status')
                ))

            # Add buttons
            btn_frame = ttk.Frame(main_frame)
            btn_frame.pack(fill=tk.X, pady=10)

            ttk.Button(
                btn_frame,
                text="View Order",
                command=lambda: self.view_order_from_tree(tree, dialog)
            ).pack(side=tk.LEFT, padx=5)

            ttk.Button(
                btn_frame,
                text="Send Reminder",
                command=lambda: self.send_reminder(tree)
            ).pack(side=tk.LEFT, padx=5)

            ttk.Button(
                btn_frame,
                text="Export List",
                command=lambda: self.export_late_orders(late_orders)
            ).pack(side=tk.LEFT, padx=5)

            ttk.Button(
                btn_frame,
                text="Close",
                command=dialog.destroy
            ).pack(side=tk.RIGHT, padx=5)

            dialog.show()

        except Exception as e:
            logger.error(f"Error checking late orders: {e}")
            messagebox.showerror("Error", f"Failed to check late orders: {e}")

    def send_reminder(self, tree):
        """Send reminder for late order.

        Args:
            tree: The treeview with orders
        """
        selection = tree.selection()
        if not selection:
            messagebox.showinfo("No Selection", "Please select an order first.")
            return

        # Get selected order ID
        order_id = tree.item(selection[0], "values")[0]

        try:
            # Get purchase service
            purchase_service = get_service('IPurchaseService')

            # Send reminder
            result = purchase_service.send_supplier_reminder(order_id)

            if result:
                messagebox.showinfo("Success", "Reminder sent successfully.")
            else:
                messagebox.showerror("Error", "Failed to send reminder.")

        except Exception as e:
            logger.error(f"Error sending reminder: {e}")
            messagebox.showerror("Error", f"Failed to send reminder: {e}")

    def export_late_orders(self, late_orders):
        """Export late orders to file.

        Args:
            late_orders: List of late orders to export
        """
        try:
            # Get file path to save
            file_path = filedialog.asksaveasfilename(
                title="Export Late Orders",
                defaultextension=".csv",
                filetypes=[("CSV Files", "*.csv"), ("Excel Files", "*.xlsx"), ("All Files", "*.*")]
            )

            if not file_path:
                return

            # Get purchase service
            purchase_service = get_service('IPurchaseService')

            # Export late orders
            result = purchase_service.export_late_orders(file_path)

            if result:
                messagebox.showinfo(
                    "Export Complete",
                    f"Late orders have been exported successfully.\n\nFile: {file_path}"
                )
            else:
                messagebox.showerror("Error", "Failed to export late orders.")

        except Exception as e:
            logger.error(f"Error exporting late orders: {e}")
            messagebox.showerror("Error", f"Failed to export late orders: {e}")

    def on_reorder_low_stock(self):
        """Handle reorder low stock button click."""
        try:
            # Get inventory service
            inventory_service = get_service('IInventoryService')

            # Get low stock items
            low_stock_items = inventory_service.get_low_stock_items()

            if not low_stock_items:
                messagebox.showinfo("Information", "No low stock items found.")
                return

            # Create low stock dialog
            dialog = BaseDialog(self.winfo_toplevel(), "Reorder Low Stock Items")
            main_frame = ttk.Frame(dialog.interior, padding=10)
            main_frame.pack(fill=tk.BOTH, expand=True)

            # Info section
            ttk.Label(
                main_frame,
                text=f"The following {len(low_stock_items)} items are low in stock:",
                font=("", 12, "bold")
            ).pack(anchor="w", pady=(0, 10))

            # Create treeview with checkboxes
            tree_frame = ttk.Frame(main_frame)
            tree_frame.pack(fill=tk.BOTH, expand=True, pady=5)

            tree = EnhancedTreeview(
                tree_frame,
                columns=("checkbox", "id", "name", "type", "current", "min", "max", "supplier"),
                show="headings",
                height=10
            )
            tree.heading("checkbox", text="Select")
            tree.heading("id", text="ID")
            tree.heading("name", text="Item Name")
            tree.heading("type", text="Type")
            tree.heading("current", text="Current Stock")
            tree.heading("min", text="Min Level")
            tree.heading("max", text="Max Level")
            tree.heading("supplier", text="Supplier")

            tree.column("checkbox", width=50, anchor="center")
            tree.column("id", width=50)
            tree.column("name", width=200)
            tree.column("type", width=100)
            tree.column("current", width=100)
            tree.column("min", width=80)
            tree.column("max", width=80)
            tree.column("supplier", width=150)

            tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            # Add scrollbar
            scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            tree.configure(yscrollcommand=scrollbar.set)

            # Add item selection tracking
            selected_items = {}

            # Populate tree
            for item in low_stock_items:
                # Create variable to track selection
                item_id = item.get('id')
                selected_items[item_id] = tk.BooleanVar(value=True)

                # Insert item
                tree.insert("", "end", iid=str(item_id), values=(
                    "✓",
                    item_id,
                    item.get('name', ''),
                    item.get('type', ''),
                    f"{item.get('current_quantity', 0)} {item.get('unit', '')}",
                    item.get('min_quantity', 0),
                    item.get('max_quantity', 0),
                    item.get('supplier', {}).get('name', 'N/A')
                ))

            # Add handler for checkbox clicks
            tree.bind("<Button-1>", lambda event: self.toggle_item_selection(event, tree, selected_items))

            # Options frame
            options_frame = ttk.LabelFrame(main_frame, text="Reorder Options")
            options_frame.pack(fill=tk.X, pady=10)

            # Group by supplier option
            group_by_supplier = tk.BooleanVar(value=True)
            ttk.Checkbutton(
                options_frame,
                text="Group by Supplier",
                variable=group_by_supplier
            ).pack(anchor="w", padx=10, pady=5)

            # Reorder to max level option
            reorder_to_max = tk.BooleanVar(value=True)
            ttk.Checkbutton(
                options_frame,
                text="Reorder to Maximum Stock Level",
                variable=reorder_to_max
            ).pack(anchor="w", padx=10, pady=5)

            # Notes field
            ttk.Label(options_frame, text="Purchase Notes:").pack(anchor="w", padx=10, pady=(5, 0))
            notes_text = tk.Text(options_frame, height=3, width=50)
            notes_text.pack(fill=tk.X, padx=10, pady=5)
            notes_text.insert("1.0", "Automatic reorder of low stock items")

            # Button frame
            btn_frame = ttk.Frame(main_frame)
            btn_frame.pack(fill=tk.X, pady=10)

            ttk.Button(
                btn_frame,
                text="Generate Purchase Orders",
                command=lambda: self.generate_reorder_purchases(
                    selected_items,
                    group_by_supplier.get(),
                    reorder_to_max.get(),
                    notes_text.get("1.0", "end-1c"),
                    dialog
                ),
                style="Accent.TButton"
            ).pack(side=tk.LEFT, padx=5)

            ttk.Button(
                btn_frame,
                text="Select All",
                command=lambda: self.select_all_items(tree, selected_items, True)
            ).pack(side=tk.LEFT, padx=5)

            ttk.Button(
                btn_frame,
                text="Deselect All",
                command=lambda: self.select_all_items(tree, selected_items, False)
            ).pack(side=tk.LEFT, padx=5)

            ttk.Button(
                btn_frame,
                text="Cancel",
                command=dialog.destroy
            ).pack(side=tk.RIGHT, padx=5)

            dialog.show()

        except Exception as e:
            logger.error(f"Error loading low stock items: {e}")
            messagebox.showerror("Error", f"Failed to load low stock items: {e}")

    def toggle_item_selection(self, event, tree, selected_items):
        """Toggle selection of an item in the reorder tree.

        Args:
            event: The click event
            tree: The treeview with items
            selected_items: Dictionary of item_id -> BooleanVar for selection
        """
        region = tree.identify_region(event.x, event.y)
        if region == "heading":
            return

        column = tree.identify_column(event.x)
        if column == "#1":  # Checkbox column
            iid = tree.identify_row(event.y)
            if iid:
                item_id = int(iid)
                if item_id in selected_items:
                    # Toggle checkbox
                    selected_items[item_id].set(not selected_items[item_id].get())

                    # Update checkbox display
                    values = list(tree.item(iid, "values"))
                    values[0] = "✓" if selected_items[item_id].get() else ""
                    tree.item(iid, values=values)

    def select_all_items(self, tree, selected_items, select=True):
        """Select or deselect all items in the tree.

        Args:
            tree: The treeview
            selected_items: Dictionary of item_id -> BooleanVar
            select: Whether to select (True) or deselect (False)
        """
        for item_id in selected_items:
            selected_items[item_id].set(select)

            # Update checkbox display
            iid = str(item_id)
            values = list(tree.item(iid, "values"))
            values[0] = "✓" if select else ""
            tree.item(iid, values=values)

    def generate_reorder_purchases(self, selected_items, group_by_supplier, reorder_to_max, notes, dialog):
        """Generate purchase orders for reordering.

        Args:
            selected_items: Dictionary of item_id -> BooleanVar for selection
            group_by_supplier: Whether to group by supplier
            reorder_to_max: Whether to reorder to maximum stock level
            notes: Purchase notes
            dialog: Dialog to close
        """
        # Get selected item IDs
        selected_item_ids = [item_id for item_id, selected in selected_items.items() if selected.get()]

        if not selected_item_ids:
            messagebox.showinfo("No Items Selected", "Please select at least one item to reorder.")
            return

        try:
            # Get purchase service
            purchase_service = get_service('IPurchaseService')

            # Generate purchase orders
            result = purchase_service.generate_reorder_purchases(
                item_ids=selected_item_ids,
                group_by_supplier=group_by_supplier,
                reorder_to_max=reorder_to_max,
                notes=notes
            )

            if result and result.get('success'):
                purchase_orders = result.get('purchase_orders', [])
                po_count = len(purchase_orders)

                if po_count > 0:
                    messagebox.showinfo(
                        "Success",
                        f"Successfully generated {po_count} purchase orders."
                    )

                    # Publish event
                    publish('purchase_updated', {'bulk_update': True})

                    # Refresh the view
                    self.refresh()

                    # Ask if user wants to view the first PO
                    if po_count == 1 or messagebox.askyesno(
                            "View Purchase Order",
                            "Do you want to view the first generated purchase order?"
                    ):
                        dialog.destroy()

                        # Navigate to first purchase order
                        first_po_id = purchase_orders[0].get('id')
                        self.master.show_view(
                            "purchase_details_view",
                            view_data={"purchase_id": first_po_id}
                        )
                        return
                else:
                    messagebox.showinfo(
                        "No Orders Created",
                        "No purchase orders were created. This may be due to missing supplier information."
                    )

                dialog.destroy()
            else:
                messagebox.showerror("Error", "Failed to generate purchase orders.")

        except Exception as e:
            logger.error(f"Error generating purchase orders: {e}")
            messagebox.showerror("Error", f"Failed to generate purchase orders: {e}")

    def on_generate_reports(self):
        """Handle generate reports button click."""
        # Create simple reports dialog
        report_dialog = tk.Toplevel(self.winfo_toplevel())
        report_dialog.title("Generate Purchase Reports")
        report_dialog.geometry("400x300")
        report_dialog.transient(self.winfo_toplevel())
        report_dialog.grab_set()

        # Create report options
        options_frame = ttk.LabelFrame(report_dialog, text="Report Options")
        options_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Report type
        ttk.Label(options_frame, text="Report Type:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        report_type = tk.StringVar(value="purchase_list")
        report_types = [
            ("Purchase List", "purchase_list"),
            ("Supplier Performance", "supplier_performance"),
            ("Procurement Summary", "procurement_summary"),
            ("Late Orders", "late_orders")
        ]

        for i, (text, value) in enumerate(report_types):
            ttk.Radiobutton(
                options_frame,
                text=text,
                value=value,
                variable=report_type
            ).grid(row=i, column=1, padx=5, pady=5, sticky="w")

        # Date range
        date_frame = ttk.Frame(options_frame)
        date_frame.grid(row=len(report_types), column=0, columnspan=2, padx=5, pady=10, sticky="w")

        ttk.Label(date_frame, text="Date Range:").grid(row=0, column=0, padx=5, pady=5, sticky="w")

        date_from = tk.StringVar()
        date_to = tk.StringVar()

        # Set default dates (last 3 months)
        today = datetime.now()
        date_to.set(today.strftime("%Y-%m-%d"))
        date_from.set((today - timedelta(days=90)).strftime("%Y-%m-%d"))

        ttk.Label(date_frame, text="From:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        from_entry = ttk.Entry(date_frame, textvariable=date_from, width=15)
        from_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        ttk.Button(
            date_frame,
            text="...",
            width=3,
            command=lambda: self.show_date_picker(date_from)
        ).grid(row=1, column=2, padx=2, pady=5, sticky="w")

        ttk.Label(date_frame, text="To:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        to_entry = ttk.Entry(date_frame, textvariable=date_to, width=15)
        to_entry.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        ttk.Button(
            date_frame,
            text="...",
            width=3,
            command=lambda: self.show_date_picker(date_to)
        ).grid(row=2, column=2, padx=2, pady=5, sticky="w")

        # Output format
        format_frame = ttk.Frame(options_frame)
        format_frame.grid(row=len(report_types) + 1, column=0, columnspan=2, padx=5, pady=10, sticky="w")

        ttk.Label(format_frame, text="Output Format:").grid(row=0, column=0, padx=5, pady=5, sticky="w")

        output_format = tk.StringVar(value="pdf")
        ttk.Radiobutton(
            format_frame,
            text="PDF",
            value="pdf",
            variable=output_format
        ).grid(row=0, column=1, padx=5, pady=5, sticky="w")

        ttk.Radiobutton(
            format_frame,
            text="Excel",
            value="excel",
            variable=output_format
        ).grid(row=0, column=2, padx=5, pady=5, sticky="w")

        # Buttons
        button_frame = ttk.Frame(report_dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(
            button_frame,
            text="Generate",
            command=lambda: self.generate_report(
                report_type.get(),
                date_from.get(),
                date_to.get(),
                output_format.get(),
                report_dialog
            ),
            style="Accent.TButton"
        ).pack(side=tk.RIGHT, padx=5)

        ttk.Button(
            button_frame,
            text="Cancel",
            command=report_dialog.destroy
        ).pack(side=tk.RIGHT, padx=5)

    def generate_report(self, report_type, date_from, date_to, output_format, dialog):
        """Generate purchase report.

        Args:
            report_type: Type of report to generate
            date_from: Start date for report data
            date_to: End date for report data
            output_format: Output format (pdf, excel)
            dialog: Dialog to close on success
        """
        try:
            # Get purchase service
            purchase_service = get_service('IPurchaseService')

            # Generate report
            result = purchase_service.generate_report(
                report_type=report_type,
                date_from=date_from,
                date_to=date_to,
                output_format=output_format,
                supplier_id=self.filter_supplier_id
            )

            if result:
                messagebox.showinfo(
                    "Report Generated",
                    f"Report has been generated successfully.\n\nFile: {result}"
                )
                dialog.destroy()
            else:
                messagebox.showerror("Error", "Failed to generate report.")

        except Exception as e:
            logger.error(f"Error generating report: {e}")
            messagebox.showerror("Error", f"Failed to generate report: {e}")

    def on_export(self):
        """Handle export button click."""
        try:
            # Get file path to save
            file_path = filedialog.asksaveasfilename(
                title="Export Purchases",
                defaultextension=".csv",
                filetypes=[("CSV Files", "*.csv"), ("Excel Files", "*.xlsx"), ("All Files", "*.*")]
            )

            if not file_path:
                return

            # Get purchase service
            purchase_service = get_service('IPurchaseService')

            # Get filter values
            status_filter = self.filter_status.get()
            if status_filter == "All":
                status_filter = None

            # Get date filters
            date_from = self.filter_date_from.get()
            date_to = self.filter_date_to.get()

            # Get search text
            search_text = self.search_frame.get_field_value("search_text") if hasattr(self, "search_frame") else ""

            # Export to file
            result = purchase_service.export_purchases(
                file_path=file_path,
                search_text=search_text,
                supplier_id=self.filter_supplier_id,
                status=status_filter,
                date_from=date_from,
                date_to=date_to
            )

            if result:
                messagebox.showinfo(
                    "Export Complete",
                    f"Purchases have been exported successfully.\n\nFile: {file_path}"
                )
            else:
                messagebox.showerror("Error", "Failed to export purchases.")

        except Exception as e:
            logger.error(f"Error exporting purchases: {e}")
            messagebox.showerror("Error", f"Failed to export purchases: {e}")

    def on_purchase_updated(self, data):
        """Handle purchase updated event.

        Args:
            data: Event data including purchase_id
        """
        # Refresh the view
        self.refresh()

    def on_inventory_updated(self, data):
        """Handle inventory updated event.

        Args:
            data: Event data
        """
        # Refresh the view
        self.refresh()

    def show_date_picker(self, date_var):
        """Show a date picker dialog.

        Args:
            date_var: The StringVar to update with selected date
        """
        # Create date picker dialog
        dialog = tk.Toplevel(self.winfo_toplevel())
        dialog.title("Select Date")
        dialog.geometry("300x250")
        dialog.resizable(False, False)
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        # Create calendar frame
        cal_frame = ttk.Frame(dialog)
        cal_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Month and year label and navigation
        header_frame = ttk.Frame(cal_frame)
        header_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(
            header_frame,
            text="<",
            width=3,
            command=lambda: self.prev_month(month_year_label, cal_grid)
        ).pack(side=tk.LEFT, padx=5)

        # Initialize with current date
        now = datetime.now()
        self.cal_year = now.year
        self.cal_month = now.month

        month_year_label = ttk.Label(
            header_frame,
            text=f"{now.strftime('%B')} {now.year}",
            font=("", 12, "bold")
        )
        month_year_label.pack(side=tk.LEFT, padx=5, expand=True)

        ttk.Button(
            header_frame,
            text=">",
            width=3,
            command=lambda: self.next_month(month_year_label, cal_grid)
        ).pack(side=tk.LEFT, padx=5)

        # Create calendar grid
        cal_grid = ttk.Frame(cal_frame)
        cal_grid.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create weekday headers
        weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for i, day in enumerate(weekdays):
            ttk.Label(
                cal_grid,
                text=day,
                font=("", 10, "bold"),
                anchor="center"
            ).grid(row=0, column=i, padx=2, pady=2, sticky="nsew")

        # Update calendar with current month
        self.update_calendar(cal_grid, month_year_label, self.cal_year, self.cal_month, date_var, dialog)

        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(
            button_frame,
            text="Cancel",
            command=dialog.destroy
        ).pack(side=tk.RIGHT, padx=5)

    def update_calendar(self, frame, label, year, month, date_var, dialog):
        """Update the calendar display based on selected month and year.

        Args:
            frame: Calendar frame
            label: Month/year label
            year: Year to display
            month: Month to display
            date_var: Variable to update with selected date
            dialog: Dialog to close on selection
        """
        # Update month/year label
        month_name = datetime(year, month, 1).strftime('%B')
        label.config(text=f"{month_name} {year}")

        # Clear existing calendar buttons
        for widget in frame.winfo_children():
            if isinstance(widget, tk.Button):
                widget.destroy()

        # Calculate first day of month (0 = Monday, 6 = Sunday)
        first_day = datetime(year, month, 1).weekday()

        # Get number of days in month
        if month == 12:
            last_day = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            last_day = datetime(year, month + 1, 1) - timedelta(days=1)

        days_in_month = last_day.day

        # Create calendar buttons
        day = 1
        for row in range(1, 7):  # 6 weeks max
            if day > days_in_month:
                break

            for col in range(7):  # 7 days per week
                if row == 1 and col < first_day:
                    # Empty cell before first day
                    continue

                if day > days_in_month:
                    # Break if we've reached the end of the month
                    break

                # Create button for day
                btn = tk.Button(
                    frame,
                    text=str(day),
                    width=3,
                    height=1,
                    command=lambda d=day: self.select_day(d, year, month, date_var, dialog)
                )
                btn.grid(row=row, column=col, padx=2, pady=2)

                day += 1

    def select_day(self, day, year, month, date_var, dialog):
        """Select a day in the calendar.

        Args:
            day: The day number to select
            year: The year
            month: The month
            date_var: The variable to update
            dialog: The dialog to close
        """
        # Format selected date
        selected_date = datetime(year, month, day).strftime("%Y-%m-%d")

        # Update variable
        date_var.set(selected_date)

        # Close dialog
        dialog.destroy()

    def prev_month(self, label, frame):
        """Go to previous month.

        Args:
            label: Month/year label to update
            frame: Calendar frame to update
        """
        # Update month/year
        if self.cal_month == 1:
            self.cal_month = 12
            self.cal_year -= 1
        else:
            self.cal_month -= 1

        # Update calendar
        self.update_calendar(frame, label, self.cal_year, self.cal_month, None, None)

    def next_month(self, label, frame):
        """Go to next month.

        Args:
            label: Month/year label to update
            frame: Calendar frame to update
        """
        # Update month/year
        if self.cal_month == 12:
            self.cal_month = 1
            self.cal_year += 1
        else:
            self.cal_month += 1

        # Update calendar
        self.update_calendar(frame, label, self.cal_year, self.cal_month, None, None)

    def get_selected_id(self):
        """Get the ID of the selected purchase.

        Returns:
            The ID of the selected purchase, or None if no selection
        """
        selection = self.treeview.selection()
        if not selection:
            messagebox.showinfo("No Selection", "Please select a purchase first.")
            return None

        # Get selected purchase ID
        values = self.treeview.item(selection[0], "values")
        return values[0]

    def refresh(self):
        """Refresh the view."""
        self.load_data()

    def destroy(self):
        """Clean up resources and listeners before destroying the view."""
        # Unsubscribe from events
        unsubscribe("purchase_updated", self.on_purchase_updated)
        unsubscribe("purchase_created", self.on_purchase_updated)
        unsubscribe("inventory_updated", self.on_inventory_updated)

        # Call parent destroy
        super().destroy()