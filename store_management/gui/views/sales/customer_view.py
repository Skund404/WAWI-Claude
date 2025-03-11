# gui/views/sales/customer_view.py
"""
Customer management view for the leatherworking ERP system.

This view provides a comprehensive interface for searching, filtering,
and managing customer records, including metrics and quick actions.
"""

import datetime
import logging
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Any, Dict, List, Optional, Tuple

from database.models.enums import CustomerStatus, CustomerTier, CustomerSource
from gui.base.base_list_view import BaseListView
from gui.theme import COLORS, get_status_style
from gui.utils.event_bus import publish, subscribe, unsubscribe
from gui.utils.service_access import get_service
from gui.widgets.status_badge import StatusBadge


class CustomerView(BaseListView):
    """
    Customer list view with advanced search, filtering, and management capabilities.

    This view extends the BaseListView to provide a comprehensive interface
    for managing customer records, including detailed metrics and quick actions.
    """

    def __init__(self, parent):
        """Initialize the customer view.

        Args:
            parent: The parent widget
        """
        super().__init__(parent)
        self.title = "Customer Management"
        self.icon = "👤"
        self.logger = logging.getLogger(__name__)

        # Initialize services
        self.customer_service = get_service("customer_service")
        self.sales_service = get_service("sales_service")

        # Set column definitions for the treeview
        self.columns = (
            "id", "name", "email", "phone", "status",
            "tier", "created_at", "last_purchase", "total_spent"
        )
        self.column_widths = {
            "id": 60,
            "name": 200,
            "email": 200,
            "phone": 120,
            "status": 100,
            "tier": 100,
            "created_at": 120,
            "last_purchase": 120,
            "total_spent": 120
        }

        # Subscribe to events
        subscribe("customer_updated", self.on_customer_updated)
        subscribe("sale_completed", self.on_sale_completed)

        # Build the view
        self.build()

        # Load initial data
        self.load_data()

    def build(self):
        """Build the customer view layout."""
        super().build()

        # Create customer metrics panel at the top
        self.create_metrics_panel(self.content_frame)

        # Add advanced filters to search frame
        self.add_advanced_filters()

    def _add_default_action_buttons(self):
        """Add default action buttons to the header."""
        actions_frame = ttk.Frame(self.header)
        actions_frame.pack(side=tk.RIGHT, padx=10)

        ttk.Button(
            actions_frame,
            text="Add Customer",
            command=self.on_add
        ).pack(side=tk.RIGHT, padx=5)

        ttk.Button(
            actions_frame,
            text="Reports",
            command=self.on_generate_reports
        ).pack(side=tk.RIGHT, padx=5)

        ttk.Button(
            actions_frame,
            text="Export",
            command=self.on_export
        ).pack(side=tk.RIGHT, padx=5)

        ttk.Button(
            actions_frame,
            text="Refresh",
            command=self.refresh
        ).pack(side=tk.RIGHT, padx=5)

    def create_metrics_panel(self, parent):
        """Create customer metrics panel with key insights.

        Args:
            parent: The parent widget
        """
        metrics_frame = ttk.LabelFrame(parent, text="Customer Metrics")
        metrics_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        # Grid layout for metrics
        metrics_grid = ttk.Frame(metrics_frame)
        metrics_grid.pack(fill=tk.X, padx=10, pady=10)

        # First row - Total counts
        ttk.Label(metrics_grid, text="Total Customers:", font=('TkDefaultFont', 9, 'bold')).grid(row=0, column=0,
                                                                                                 padx=5, pady=2,
                                                                                                 sticky=tk.W)
        self.total_customers_label = ttk.Label(metrics_grid, text="0")
        self.total_customers_label.grid(row=0, column=1, padx=5, pady=2, sticky=tk.W)

        ttk.Label(metrics_grid, text="Active Customers:", font=('TkDefaultFont', 9, 'bold')).grid(row=0, column=2,
                                                                                                  padx=5, pady=2,
                                                                                                  sticky=tk.W)
        self.active_customers_label = ttk.Label(metrics_grid, text="0")
        self.active_customers_label.grid(row=0, column=3, padx=5, pady=2, sticky=tk.W)

        ttk.Label(metrics_grid, text="Inactive Customers:", font=('TkDefaultFont', 9, 'bold')).grid(row=0, column=4,
                                                                                                    padx=5, pady=2,
                                                                                                    sticky=tk.W)
        self.inactive_customers_label = ttk.Label(metrics_grid, text="0")
        self.inactive_customers_label.grid(row=0, column=5, padx=5, pady=2, sticky=tk.W)

        # Second row - Customer tiers
        ttk.Label(metrics_grid, text="Standard Tier:", font=('TkDefaultFont', 9, 'bold')).grid(row=1, column=0, padx=5,
                                                                                               pady=2, sticky=tk.W)
        self.standard_tier_label = ttk.Label(metrics_grid, text="0")
        self.standard_tier_label.grid(row=1, column=1, padx=5, pady=2, sticky=tk.W)

        ttk.Label(metrics_grid, text="Premium Tier:", font=('TkDefaultFont', 9, 'bold')).grid(row=1, column=2, padx=5,
                                                                                              pady=2, sticky=tk.W)
        self.premium_tier_label = ttk.Label(metrics_grid, text="0")
        self.premium_tier_label.grid(row=1, column=3, padx=5, pady=2, sticky=tk.W)

        ttk.Label(metrics_grid, text="VIP Tier:", font=('TkDefaultFont', 9, 'bold')).grid(row=1, column=4, padx=5,
                                                                                          pady=2, sticky=tk.W)
        self.vip_tier_label = ttk.Label(metrics_grid, text="0")
        self.vip_tier_label.grid(row=1, column=5, padx=5, pady=2, sticky=tk.W)

        # Third row - Recent activity
        ttk.Label(metrics_grid, text="New This Month:", font=('TkDefaultFont', 9, 'bold')).grid(row=2, column=0, padx=5,
                                                                                                pady=2, sticky=tk.W)
        self.new_this_month_label = ttk.Label(metrics_grid, text="0")
        self.new_this_month_label.grid(row=2, column=1, padx=5, pady=2, sticky=tk.W)

        ttk.Label(metrics_grid, text="Recent Purchases:", font=('TkDefaultFont', 9, 'bold')).grid(row=2, column=2,
                                                                                                  padx=5, pady=2,
                                                                                                  sticky=tk.W)
        self.recent_purchases_label = ttk.Label(metrics_grid, text="0")
        self.recent_purchases_label.grid(row=2, column=3, padx=5, pady=2, sticky=tk.W)

        ttk.Label(metrics_grid, text="Total Revenue:", font=('TkDefaultFont', 9, 'bold')).grid(row=2, column=4, padx=5,
                                                                                               pady=2, sticky=tk.W)
        self.total_revenue_label = ttk.Label(metrics_grid, text="$0.00")
        self.total_revenue_label.grid(row=2, column=5, padx=5, pady=2, sticky=tk.W)

    def create_treeview(self, parent):
        """Create the treeview for displaying customer data.

        Args:
            parent: The parent widget
        """
        # Create a frame for the treeview
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Create the treeview
        self.treeview = ttk.Treeview(
            tree_frame,
            columns=self.columns,
            show="headings",
            selectmode="browse"
        )

        # Configure column headings and widths
        self.treeview.heading("id", text="ID", command=lambda: self.on_sort("id", "asc"))
        self.treeview.heading("name", text="Name", command=lambda: self.on_sort("name", "asc"))
        self.treeview.heading("email", text="Email", command=lambda: self.on_sort("email", "asc"))
        self.treeview.heading("phone", text="Phone", command=lambda: self.on_sort("phone", "asc"))
        self.treeview.heading("status", text="Status", command=lambda: self.on_sort("status", "asc"))
        self.treeview.heading("tier", text="Tier", command=lambda: self.on_sort("tier", "asc"))
        self.treeview.heading("created_at", text="Created", command=lambda: self.on_sort("created_at", "desc"))
        self.treeview.heading("last_purchase", text="Last Purchase",
                              command=lambda: self.on_sort("last_purchase", "desc"))
        self.treeview.heading("total_spent", text="Total Spent", command=lambda: self.on_sort("total_spent", "desc"))

        for col, width in self.column_widths.items():
            self.treeview.column(col, width=width, minwidth=50)

        # Create vertical scrollbar
        yscrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.treeview.yview)
        yscrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.treeview.configure(yscrollcommand=yscrollbar.set)

        # Create horizontal scrollbar
        xscrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.treeview.xview)
        xscrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.treeview.configure(xscrollcommand=xscrollbar.set)

        self.treeview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Bind double-click to view customer
        self.treeview.bind("<Double-1>", lambda e: self.on_view())

        # Bind selection to update action buttons
        self.treeview.bind("<<TreeviewSelect>>", self.on_select)

    def add_advanced_filters(self):
        """Add advanced search filters to the search frame."""
        # Get the search frame from the base class
        search_frame = self.search_frame

        # Add additional filters
        filters_frame = ttk.LabelFrame(search_frame, text="Advanced Filters")
        filters_frame.pack(fill=tk.X, padx=10, pady=5, after=search_frame.winfo_children()[0])

        # First row - Status and Tier
        row1_frame = ttk.Frame(filters_frame)
        row1_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(row1_frame, text="Status:").pack(side=tk.LEFT, padx=(0, 5))
        self.status_var = tk.StringVar(value="All")
        status_combo = ttk.Combobox(row1_frame, textvariable=self.status_var, width=15, state="readonly")
        status_values = ["All"] + [s.value.title() for s in CustomerStatus]
        status_combo["values"] = status_values
        status_combo.pack(side=tk.LEFT, padx=5)

        ttk.Label(row1_frame, text="Tier:").pack(side=tk.LEFT, padx=(15, 5))
        self.tier_var = tk.StringVar(value="All")
        tier_combo = ttk.Combobox(row1_frame, textvariable=self.tier_var, width=15, state="readonly")
        tier_values = ["All"] + [t.value.title() for t in CustomerTier]
        tier_combo["values"] = tier_values
        tier_combo.pack(side=tk.LEFT, padx=5)

        ttk.Label(row1_frame, text="Source:").pack(side=tk.LEFT, padx=(15, 5))
        self.source_var = tk.StringVar(value="All")
        source_combo = ttk.Combobox(row1_frame, textvariable=self.source_var, width=15, state="readonly")
        source_values = ["All"] + [s.value.replace("_", " ").title() for s in CustomerSource]
        source_combo["values"] = source_values
        source_combo.pack(side=tk.LEFT, padx=5)

        # Second row - Date ranges
        row2_frame = ttk.Frame(filters_frame)
        row2_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(row2_frame, text="Created From:").pack(side=tk.LEFT, padx=(0, 5))
        self.created_from_var = tk.StringVar()
        created_from_entry = ttk.Entry(row2_frame, textvariable=self.created_from_var, width=12)
        created_from_entry.pack(side=tk.LEFT, padx=(0, 2))
        ttk.Button(
            row2_frame,
            text="...",
            width=2,
            command=lambda: self.show_date_picker(self.created_from_var)
        ).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Label(row2_frame, text="To:").pack(side=tk.LEFT, padx=(5, 5))
        self.created_to_var = tk.StringVar()
        created_to_entry = ttk.Entry(row2_frame, textvariable=self.created_to_var, width=12)
        created_to_entry.pack(side=tk.LEFT, padx=(0, 2))
        ttk.Button(
            row2_frame,
            text="...",
            width=2,
            command=lambda: self.show_date_picker(self.created_to_var)
        ).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Label(row2_frame, text="Last Purchase:").pack(side=tk.LEFT, padx=(15, 5))
        self.purchase_from_var = tk.StringVar()
        purchase_from_entry = ttk.Entry(row2_frame, textvariable=self.purchase_from_var, width=12)
        purchase_from_entry.pack(side=tk.LEFT, padx=(0, 2))
        ttk.Button(
            row2_frame,
            text="...",
            width=2,
            command=lambda: self.show_date_picker(self.purchase_from_var)
        ).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Label(row2_frame, text="To:").pack(side=tk.LEFT, padx=(5, 5))
        self.purchase_to_var = tk.StringVar()
        purchase_to_entry = ttk.Entry(row2_frame, textvariable=self.purchase_to_var, width=12)
        purchase_to_entry.pack(side=tk.LEFT, padx=(0, 2))
        ttk.Button(
            row2_frame,
            text="...",
            width=2,
            command=lambda: self.show_date_picker(self.purchase_to_var)
        ).pack(side=tk.LEFT, padx=(0, 5))

        # Add apply filters button
        ttk.Button(
            filters_frame,
            text="Apply Filters",
            command=self.on_apply_filters
        ).pack(side=tk.RIGHT, padx=10, pady=5)

        ttk.Button(
            filters_frame,
            text="Clear Filters",
            command=self.on_clear_filters
        ).pack(side=tk.RIGHT, padx=5, pady=5)

    def create_item_actions(self, parent):
        """Create action buttons for selected customers.

        Args:
            parent: The parent widget
        """
        actions_frame = ttk.LabelFrame(parent, text="Customer Actions")
        actions_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        ttk.Button(
            actions_frame,
            text="View Details",
            command=self.on_view,
            state=tk.DISABLED
        ).pack(side=tk.LEFT, padx=5, pady=5)

        self.view_btn = actions_frame.winfo_children()[-1]

        ttk.Button(
            actions_frame,
            text="Edit Customer",
            command=self.on_edit,
            state=tk.DISABLED
        ).pack(side=tk.LEFT, padx=5, pady=5)

        self.edit_btn = actions_frame.winfo_children()[-1]

        ttk.Button(
            actions_frame,
            text="View Sales",
            command=self.on_view_sales,
            state=tk.DISABLED
        ).pack(side=tk.LEFT, padx=5, pady=5)

        self.view_sales_btn = actions_frame.winfo_children()[-1]

        ttk.Button(
            actions_frame,
            text="New Sale",
            command=self.on_create_sale,
            state=tk.DISABLED
        ).pack(side=tk.LEFT, padx=5, pady=5)

        self.new_sale_btn = actions_frame.winfo_children()[-1]

        ttk.Button(
            actions_frame,
            text="View Projects",
            command=self.on_view_projects,
            state=tk.DISABLED
        ).pack(side=tk.LEFT, padx=5, pady=5)

        self.view_projects_btn = actions_frame.winfo_children()[-1]

        ttk.Button(
            actions_frame,
            text="Send Email",
            command=self.on_send_email,
            state=tk.DISABLED
        ).pack(side=tk.LEFT, padx=5, pady=5)

        self.send_email_btn = actions_frame.winfo_children()[-1]

        ttk.Button(
            actions_frame,
            text="Change Status",
            command=self.on_change_status,
            state=tk.DISABLED
        ).pack(side=tk.LEFT, padx=5, pady=5)

        self.change_status_btn = actions_frame.winfo_children()[-1]

        ttk.Button(
            actions_frame,
            text="Delete",
            command=self.on_delete,
            state=tk.DISABLED
        ).pack(side=tk.LEFT, padx=5, pady=5)

        self.delete_btn = actions_frame.winfo_children()[-1]

    def add_context_menu_items(self, menu):
        """Add customer-specific context menu items.

        Args:
            menu: The context menu to add items to
        """
        menu.add_command(label="View Details", command=self.on_view)
        menu.add_command(label="Edit Customer", command=self.on_edit)
        menu.add_separator()
        menu.add_command(label="View Sales History", command=self.on_view_sales)
        menu.add_command(label="Create New Sale", command=self.on_create_sale)
        menu.add_command(label="View Projects", command=self.on_view_projects)
        menu.add_separator()
        menu.add_command(label="Send Email", command=self.on_send_email)
        menu.add_command(label="Change Status", command=self.on_change_status)
        menu.add_separator()
        menu.add_command(label="Delete Customer", command=self.on_delete)

    def load_data(self):
        """Load customer data into the treeview based on current filters and pagination."""
        try:
            # Clear existing items
            for item in self.treeview.get_children():
                self.treeview.delete(item)

            # Get current page and search criteria
            offset = (self.current_page - 1) * self.page_size

            # Get search criteria
            search_text = self.search_var.get() if hasattr(self, 'search_var') else ""

            # Collect filter criteria
            filters = {}

            if hasattr(self, 'status_var') and self.status_var.get() != "All":
                filters['status'] = self.status_var.get().upper()

            if hasattr(self, 'tier_var') and self.tier_var.get() != "All":
                filters['tier'] = self.tier_var.get().upper()

            if hasattr(self, 'source_var') and self.source_var.get() != "All":
                filters['source'] = self.source_var.get().replace(" ", "_").upper()

            # Date ranges
            if hasattr(self, 'created_from_var') and self.created_from_var.get():
                try:
                    filters['created_from'] = datetime.datetime.strptime(self.created_from_var.get(), "%Y-%m-%d")
                except ValueError:
                    self.logger.warning(f"Invalid date format for created_from: {self.created_from_var.get()}")

            if hasattr(self, 'created_to_var') and self.created_to_var.get():
                try:
                    filters['created_to'] = datetime.datetime.strptime(self.created_to_var.get(), "%Y-%m-%d")
                except ValueError:
                    self.logger.warning(f"Invalid date format for created_to: {self.created_to_var.get()}")

            if hasattr(self, 'purchase_from_var') and self.purchase_from_var.get():
                try:
                    filters['purchase_from'] = datetime.datetime.strptime(self.purchase_from_var.get(), "%Y-%m-%d")
                except ValueError:
                    self.logger.warning(f"Invalid date format for purchase_from: {self.purchase_from_var.get()}")

            if hasattr(self, 'purchase_to_var') and self.purchase_to_var.get():
                try:
                    filters['purchase_to'] = datetime.datetime.strptime(self.purchase_to_var.get(), "%Y-%m-%d")
                except ValueError:
                    self.logger.warning(f"Invalid date format for purchase_to: {self.purchase_to_var.get()}")

            # Get the current sort field and direction
            sort_field = getattr(self, 'sort_field', 'name')
            sort_direction = getattr(self, 'sort_direction', 'asc')

            # Get total count
            total_count = self.customer_service.count_customers(
                search_text=search_text,
                filters=filters
            )

            # Calculate total pages
            total_pages = (total_count + self.page_size - 1) // self.page_size

            # Update pagination display
            self.update_pagination_display(total_pages)

            # Get customers for current page
            customers = self.customer_service.search_customers(
                search_text=search_text,
                filters=filters,
                sort_field=sort_field,
                sort_direction=sort_direction,
                offset=offset,
                limit=self.page_size
            )

            # Insert customers into treeview
            for customer in customers:
                values = self.extract_item_values(customer)
                item_id = str(customer.id) if hasattr(customer, 'id') else "0"

                self.treeview.insert('', 'end', iid=item_id, values=values)

                # Apply status styling
                if hasattr(customer, 'status') and customer.status:
                    status_style = get_status_style(customer.status.value)
                    tag_name = f"status_{customer.status.value}"

                    # Configure tag with status color if not already configured
                    if tag_name not in self.treeview.tag_configure():
                        self.treeview.tag_configure(tag_name, background=status_style.get('bg_light'))

                    # Apply tag to the row
                    self.treeview.item(item_id, tags=(tag_name,))

            # Update metrics
            self.update_metrics()

        except Exception as e:
            self.logger.error(f"Error loading customer data: {e}")
            messagebox.showerror("Error", f"Failed to load customer data: {str(e)}")

    def extract_item_values(self, item):
        """Extract values from a customer item for display in the treeview.

        Args:
            item: The customer item to extract values from

        Returns:
            List of values corresponding to treeview columns
        """
        # Extract customer values
        item_id = item.id if hasattr(item, 'id') else ""

        # Format name
        name = ""
        if hasattr(item, 'first_name') and item.first_name:
            name += item.first_name
        if hasattr(item, 'last_name') and item.last_name:
            if name:
                name += " "
            name += item.last_name

        email = item.email if hasattr(item, 'email') else ""
        phone = item.phone if hasattr(item, 'phone') else ""

        # Format status
        status = ""
        if hasattr(item, 'status') and item.status:
            status = item.status.value.replace("_", " ").title()

        # Format tier
        tier = ""
        if hasattr(item, 'tier') and item.tier:
            tier = item.tier.value.title()

        # Format dates
        created_at = ""
        if hasattr(item, 'created_at') and item.created_at:
            created_at = item.created_at.strftime("%Y-%m-%d")

        # Last purchase date and total spent
        last_purchase = ""
        total_spent = "0.00"

        if hasattr(item, 'sales_summary'):
            summary = item.sales_summary
            if 'last_purchase_date' in summary and summary['last_purchase_date']:
                last_purchase = summary['last_purchase_date'].strftime("%Y-%m-%d")

            if 'total_spent' in summary:
                total_spent = f"{summary['total_spent']:.2f}"

        return (
            item_id, name, email, phone, status, tier,
            created_at, last_purchase, total_spent
        )

    def update_metrics(self):
        """Update customer metrics displayed in the panel."""
        try:
            # Get customer metrics
            metrics = self.customer_service.get_customer_metrics()

            # Update labels with metric values
            if 'total_customers' in metrics:
                self.total_customers_label.configure(text=str(metrics['total_customers']))

            if 'active_customers' in metrics:
                self.active_customers_label.configure(text=str(metrics['active_customers']))

            if 'inactive_customers' in metrics:
                self.inactive_customers_label.configure(text=str(metrics['inactive_customers']))

            if 'standard_tier' in metrics:
                self.standard_tier_label.configure(text=str(metrics['standard_tier']))

            if 'premium_tier' in metrics:
                self.premium_tier_label.configure(text=str(metrics['premium_tier']))

            if 'vip_tier' in metrics:
                self.vip_tier_label.configure(text=str(metrics['vip_tier']))

            if 'new_this_month' in metrics:
                self.new_this_month_label.configure(text=str(metrics['new_this_month']))

            if 'recent_purchases' in metrics:
                self.recent_purchases_label.configure(text=str(metrics['recent_purchases']))

            if 'total_revenue' in metrics:
                formatted_revenue = f"${metrics['total_revenue']:.2f}"
                self.total_revenue_label.configure(text=formatted_revenue)

        except Exception as e:
            self.logger.error(f"Error updating customer metrics: {e}")

    def on_select(self, event=None):
        """Handle customer selection in the treeview."""
        selected_id = self.treeview.focus()

        # Enable/disable action buttons based on selection
        if selected_id:
            self.view_btn.configure(state=tk.NORMAL)
            self.edit_btn.configure(state=tk.NORMAL)
            self.view_sales_btn.configure(state=tk.NORMAL)
            self.new_sale_btn.configure(state=tk.NORMAL)
            self.view_projects_btn.configure(state=tk.NORMAL)
            self.send_email_btn.configure(state=tk.NORMAL)
            self.change_status_btn.configure(state=tk.NORMAL)
            self.delete_btn.configure(state=tk.NORMAL)
        else:
            self.view_btn.configure(state=tk.DISABLED)
            self.edit_btn.configure(state=tk.DISABLED)
            self.view_sales_btn.configure(state=tk.DISABLED)
            self.new_sale_btn.configure(state=tk.DISABLED)
            self.view_projects_btn.configure(state=tk.DISABLED)
            self.send_email_btn.configure(state=tk.DISABLED)
            self.change_status_btn.configure(state=tk.DISABLED)
            self.delete_btn.configure(state=tk.DISABLED)

    def on_apply_filters(self):
        """Handle apply filters button click."""
        # Reset to first page and reload data
        self.current_page = 1
        self.load_data()

    def on_clear_filters(self):
        """Handle clear filters button click."""
        # Reset filter values
        if hasattr(self, 'status_var'):
            self.status_var.set("All")

        if hasattr(self, 'tier_var'):
            self.tier_var.set("All")

        if hasattr(self, 'source_var'):
            self.source_var.set("All")

        if hasattr(self, 'created_from_var'):
            self.created_from_var.set("")

        if hasattr(self, 'created_to_var'):
            self.created_to_var.set("")

        if hasattr(self, 'purchase_from_var'):
            self.purchase_from_var.set("")

        if hasattr(self, 'purchase_to_var'):
            self.purchase_to_var.set("")

        # Reset search
        if hasattr(self, 'search_var'):
            self.search_var.set("")

        # Reset to first page and reload data
        self.current_page = 1
        self.load_data()

    def on_add(self):
        """Handle add new customer action."""
        # Navigate to customer details view for new customer
        self.parent.master.show_view(
            "customer_details",
            view_data={"create_new": True}
        )

    def on_view(self):
        """Handle view customer action."""
        selected_id = self.treeview.focus()
        if not selected_id:
            messagebox.showwarning("No Selection", "Please select a customer to view.")
            return

        # Navigate to customer details view
        self.parent.master.show_view(
            "customer_details",
            view_data={"customer_id": int(selected_id), "readonly": True}
        )

    def on_edit(self):
        """Handle edit customer action."""
        selected_id = self.treeview.focus()
        if not selected_id:
            messagebox.showwarning("No Selection", "Please select a customer to edit.")
            return

        # Navigate to customer details view for editing
        self.parent.master.show_view(
            "customer_details",
            view_data={"customer_id": int(selected_id)}
        )

    def on_delete(self):
        """Handle delete customer action."""
        selected_id = self.treeview.focus()
        if not selected_id:
            messagebox.showwarning("No Selection", "Please select a customer to delete.")
            return

        # Get customer name for confirmation message
        item = self.treeview.item(selected_id)
        customer_name = item["values"][1] if item and "values" in item and len(item["values"]) > 1 else "this customer"

        # Confirm deletion
        if not messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete {customer_name}?"):
            return

        try:
            # Delete customer
            result = self.customer_service.delete_customer(int(selected_id))

            if result:
                # Remove from treeview
                self.treeview.delete(selected_id)

                # Update metrics
                self.update_metrics()

                # Show success message
                messagebox.showinfo("Success", f"Customer '{customer_name}' has been deleted.")

                # Publish event
                publish("customer_deleted", {"customer_id": int(selected_id)})

        except Exception as e:
            self.logger.error(f"Error deleting customer: {e}")
            messagebox.showerror("Delete Error", f"Failed to delete customer: {str(e)}")

    def on_view_sales(self):
        """Handle view sales history action."""
        selected_id = self.treeview.focus()
        if not selected_id:
            messagebox.showwarning("No Selection", "Please select a customer to view sales.")
            return

        # Navigate to sales view with customer filter
        self.parent.master.show_view(
            "sales",
            view_data={"filter_customer_id": int(selected_id)}
        )

    def on_create_sale(self):
        """Handle create new sale action."""
        selected_id = self.treeview.focus()
        if not selected_id:
            messagebox.showwarning("No Selection", "Please select a customer to create sale.")
            return

        # Navigate to sales details view for new sale with customer pre-selected
        self.parent.master.show_view(
            "sales_details",
            view_data={"create_new": True, "customer_id": int(selected_id)}
        )

    def on_view_projects(self):
        """Handle view projects action."""
        selected_id = self.treeview.focus()
        if not selected_id:
            messagebox.showwarning("No Selection", "Please select a customer to view projects.")
            return

        # Navigate to project list view with customer filter
        self.parent.master.show_view(
            "project_list",
            view_data={"filter_customer_id": int(selected_id)}
        )

    def on_send_email(self):
        """Handle send email action."""
        selected_id = self.treeview.focus()
        if not selected_id:
            messagebox.showwarning("No Selection", "Please select a customer to send email.")
            return

        # Get customer email
        item = self.treeview.item(selected_id)
        customer_email = item["values"][2] if item and "values" in item and len(item["values"]) > 2 else ""

        if not customer_email:
            messagebox.showwarning("No Email", "Selected customer does not have an email address.")
            return

        # This would integrate with an email system
        # For this implementation, we'll just show a message
        messagebox.showinfo("Send Email", f"Email functionality would open for: {customer_email}")

    def on_change_status(self):
        """Handle change status action."""
        selected_id = self.treeview.focus()
        if not selected_id:
            messagebox.showwarning("No Selection", "Please select a customer to change status.")
            return

        # Get current status
        item = self.treeview.item(selected_id)
        current_status = item["values"][4] if item and "values" in item and len(item["values"]) > 4 else ""
        current_status = current_status.upper().replace(" ", "_") if current_status else ""

        # Create status change dialog
        dialog = tk.Toplevel(self)
        dialog.title("Change Customer Status")
        dialog.transient(self)
        dialog.grab_set()
        dialog.geometry("400x200")

        # Status selection
        ttk.Label(dialog, text="Current Status:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        current_status_label = ttk.Label(dialog, text=current_status.replace("_", " ").title())
        current_status_label.grid(row=0, column=1, padx=10, pady=10, sticky=tk.W)

        ttk.Label(dialog, text="New Status:").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        new_status_var = tk.StringVar()
        status_combo = ttk.Combobox(dialog, textvariable=new_status_var, width=20, state="readonly")
        status_values = [s.name for s in CustomerStatus]
        status_combo["values"] = status_values
        status_combo.grid(row=1, column=1, padx=10, pady=10, sticky=tk.W)

        # Notes
        ttk.Label(dialog, text="Notes:").grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
        notes_var = tk.StringVar()
        notes_entry = ttk.Entry(dialog, textvariable=notes_var, width=30)
        notes_entry.grid(row=2, column=1, padx=10, pady=10, sticky=tk.W)

        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=3, column=0, columnspan=2, pady=20)

        def on_status_change():
            # Validate input
            if not new_status_var.get():
                messagebox.showwarning("Input Error", "Please select a new status.", parent=dialog)
                return

            try:
                # Update customer status
                result = self.customer_service.update_customer_status(
                    int(selected_id),
                    new_status_var.get(),
                    notes=notes_var.get()
                )

                if result:
                    # Close dialog
                    dialog.destroy()

                    # Refresh data
                    self.load_data()

                    # Show success message
                    messagebox.showinfo("Success", "Customer status has been updated.")

                    # Publish event
                    publish("customer_status_changed", {
                        "customer_id": int(selected_id),
                        "new_status": new_status_var.get()
                    })

            except Exception as e:
                self.logger.error(f"Error updating customer status: {e}")
                messagebox.showerror("Update Error", f"Failed to update customer status: {str(e)}", parent=dialog)

        ttk.Button(
            button_frame,
            text="Update",
            command=on_status_change
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            button_frame,
            text="Cancel",
            command=dialog.destroy
        ).pack(side=tk.LEFT, padx=5)

    def on_generate_reports(self):
        """Handle generate reports button click."""
        # Create reports dialog
        dialog = tk.Toplevel(self)
        dialog.title("Customer Reports")
        dialog.transient(self)
        dialog.grab_set()
        dialog.geometry("400x300")

        # Report options frame
        options_frame = ttk.LabelFrame(dialog, text="Available Reports")
        options_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Report types
        report_var = tk.StringVar(value="customer_list")
        ttk.Radiobutton(
            options_frame,
            text="Customer List Report",
            variable=report_var,
            value="customer_list"
        ).pack(anchor=tk.W, padx=10, pady=5)

        ttk.Radiobutton(
            options_frame,
            text="Customer Activity Report",
            variable=report_var,
            value="customer_activity"
        ).pack(anchor=tk.W, padx=10, pady=5)

        ttk.Radiobutton(
            options_frame,
            text="Customer Tier Analysis",
            variable=report_var,
            value="tier_analysis"
        ).pack(anchor=tk.W, padx=10, pady=5)

        ttk.Radiobutton(
            options_frame,
            text="New Customers Report",
            variable=report_var,
            value="new_customers"
        ).pack(anchor=tk.W, padx=10, pady=5)

        ttk.Radiobutton(
            options_frame,
            text="Customer Retention Report",
            variable=report_var,
            value="retention"
        ).pack(anchor=tk.W, padx=10, pady=5)

        # Format options
        format_frame = ttk.LabelFrame(dialog, text="Output Format")
        format_frame.pack(fill=tk.X, padx=10, pady=5)

        format_var = tk.StringVar(value="pdf")
        ttk.Radiobutton(
            format_frame,
            text="PDF",
            variable=format_var,
            value="pdf"
        ).pack(side=tk.LEFT, padx=10, pady=5)

        ttk.Radiobutton(
            format_frame,
            text="Excel",
            variable=format_var,
            value="excel"
        ).pack(side=tk.LEFT, padx=10, pady=5)

        ttk.Radiobutton(
            format_frame,
            text="CSV",
            variable=format_var,
            value="csv"
        ).pack(side=tk.LEFT, padx=10, pady=5)

        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        def generate_report():
            report_type = report_var.get()
            output_format = format_var.get()

            # This would integrate with a reporting system
            # For this implementation, we'll just show a message
            messagebox.showinfo(
                "Generate Report",
                f"Report '{report_type}' would be generated in {output_format.upper()} format.",
                parent=dialog
            )
            dialog.destroy()

        ttk.Button(
            button_frame,
            text="Generate",
            command=generate_report
        ).pack(side=tk.RIGHT, padx=5)

        ttk.Button(
            button_frame,
            text="Cancel",
            command=dialog.destroy
        ).pack(side=tk.RIGHT, padx=5)

    def on_export(self):
        """Handle export button click."""
        # Create file save dialog
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx"), ("All files", "*.*")]
        )

        if not file_path:
            return

        try:
            # Export data
            result = self.customer_service.export_customers(file_path)

            if result:
                # Show success message
                messagebox.showinfo("Export Success", f"Customer data has been exported to {file_path}.")

        except Exception as e:
            self.logger.error(f"Error exporting customer data: {e}")
            messagebox.showerror("Export Error", f"Failed to export customer data: {str(e)}")

    def on_customer_updated(self, data):
        """Handle customer updated event.

        Args:
            data: Event data including customer_id
        """
        # Refresh data to show the updated customer
        self.load_data()

    def on_sale_completed(self, data):
        """Handle sale completed event.

        Args:
            data: Event data including customer_id
        """
        # Refresh data to update metrics and customer info
        self.update_metrics()
        self.load_data()

    def show_date_picker(self, date_var):
        """Show a date picker dialog.

        Args:
            date_var: The StringVar to update with selected date
        """
        # Create a simple date picker dialog
        date_dialog = tk.Toplevel(self)
        date_dialog.title("Select Date")
        date_dialog.transient(self)
        date_dialog.grab_set()

        # Create a calendar (simplified version - production would use a better calendar)
        cal_frame = ttk.Frame(date_dialog, padding=10)
        cal_frame.pack(fill=tk.BOTH, expand=True)

        # Current year and month selection
        current_date = datetime.datetime.now()
        if date_var.get():
            try:
                current_date = datetime.datetime.strptime(date_var.get(), "%Y-%m-%d")
            except ValueError:
                pass

        year_var = tk.StringVar(value=str(current_date.year))
        month_var = tk.StringVar(value=str(current_date.month))

        header_frame = ttk.Frame(cal_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(header_frame, text="Year:").pack(side=tk.LEFT)
        ttk.Spinbox(
            header_frame,
            from_=2000,
            to=2050,
            textvariable=year_var,
            width=5
        ).pack(side=tk.LEFT, padx=(5, 10))

        ttk.Label(header_frame, text="Month:").pack(side=tk.LEFT)
        month_spin = ttk.Spinbox(
            header_frame,
            from_=1,
            to=12,
            textvariable=month_var,
            width=3
        )
        month_spin.pack(side=tk.LEFT, padx=5)

        # Simple calendar grid (would use a proper calendar widget in production)
        def select_date(day):
            year = int(year_var.get())
            month = int(month_var.get())
            date_var.set(f"{year:04d}-{month:02d}-{day:02d}")
            date_dialog.destroy()

        days_frame = ttk.Frame(cal_frame)
        days_frame.pack(fill=tk.BOTH, expand=True)

        # Button for each day (simplified)
        for day in range(1, 32):
            day_btn = ttk.Button(
                days_frame,
                text=str(day),
                width=3,
                command=lambda d=day: select_date(d)
            )
            row = (day - 1) // 7
            col = (day - 1) % 7
            day_btn.grid(row=row, column=col, padx=2, pady=2)

        # Cancel button
        ttk.Button(
            cal_frame,
            text="Cancel",
            command=date_dialog.destroy
        ).pack(pady=10)

    def destroy(self):
        """Clean up resources and listeners before destroying the view."""
        # Unsubscribe from events
        unsubscribe("customer_updated", self.on_customer_updated)
        unsubscribe("sale_completed", self.on_sale_completed)

        # Call parent destroy
        super().destroy()