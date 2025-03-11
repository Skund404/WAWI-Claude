# views/purchases/supplier_view.py
import tkinter as tk
from tkinter import ttk, messagebox
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from database.models.enums import SupplierStatus

from gui.base.base_list_view import BaseListView
from gui.theme import COLORS, get_status_style
from gui.utils.service_access import get_service
from gui.utils.event_bus import publish, subscribe, unsubscribe
from gui.widgets.status_badge import StatusBadge
from gui.views.purchases.supplier_details_dialog import SupplierDetailsDialog

logger = logging.getLogger(__name__)


class SupplierView(BaseListView):
    """View for displaying and managing suppliers."""

    def __init__(self, parent):
        """Initialize the supplier view.

        Args:
            parent: The parent widget
        """
        super().__init__(parent)
        self.title = "Suppliers"
        self.subtitle = "Manage supplier information and purchase history"

        # Subscribe to events
        subscribe("supplier_updated", self.on_supplier_updated)
        subscribe("supplier_created", self.on_supplier_updated)

        # Initialize filter variables
        self.filter_status = tk.StringVar(value="All")

        # Build the view
        self.build()

    def build(self):
        """Build the supplier view layout."""
        super().build()

        # Add supplier metrics panel
        self.create_metrics_panel(self.content_frame)

    def _add_default_action_buttons(self):
        """Add default action buttons to the header."""
        # Add "Add" button
        self.add_button = ttk.Button(
            self.header,
            text="Add Supplier",
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

    def create_metrics_panel(self, parent):
        """Create supplier metrics panel with key insights.

        Args:
            parent: The parent widget
        """
        # Create metrics frame
        metrics_frame = ttk.LabelFrame(parent, text="Supplier Overview")
        metrics_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        # Create metrics grid
        metrics_grid = ttk.Frame(metrics_frame)
        metrics_grid.pack(fill=tk.X, padx=10, pady=10)

        # Configure grid columns with equal width
        for i in range(4):
            metrics_grid.columnconfigure(i, weight=1)

        # Create metrics
        self.metrics = {
            "total_suppliers": self._create_metric_widget(metrics_grid, "Total Suppliers", "Loading...", 0, 0),
            "active_suppliers": self._create_metric_widget(metrics_grid, "Active Suppliers", "Loading...", 0, 1),
            "purchases_last_30d": self._create_metric_widget(metrics_grid, "Purchases (30 days)", "Loading...", 0, 2),
            "avg_lead_time": self._create_metric_widget(metrics_grid, "Avg. Lead Time", "Loading...", 0, 3),
        }

        # Create status badges
        status_frame = ttk.Frame(metrics_frame)
        status_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        self.status_badges = {}
        statuses = [status.name for status in SupplierStatus]

        for i, status in enumerate(statuses):
            self.status_badges[status] = self._create_status_badge(status_frame, status, status, i)

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
        """Create the treeview for displaying supplier data.

        Args:
            parent: The parent widget
        """
        # Create the treeview with columns
        self.treeview = ttk.Treeview(
            parent,
            columns=("id", "name", "contact_email", "status", "phone", "website", "active_since"),
            show="headings",
            selectmode="browse"
        )

        # Set column headings
        self.treeview.heading("id", text="ID")
        self.treeview.heading("name", text="Name")
        self.treeview.heading("contact_email", text="Contact Email")
        self.treeview.heading("status", text="Status")
        self.treeview.heading("phone", text="Phone")
        self.treeview.heading("website", text="Website")
        self.treeview.heading("active_since", text="Active Since")

        # Configure column widths
        self.treeview.column("id", width=50, stretch=False)
        self.treeview.column("name", width=200, stretch=True)
        self.treeview.column("contact_email", width=200, stretch=True)
        self.treeview.column("status", width=100, stretch=False)
        self.treeview.column("phone", width=120, stretch=False)
        self.treeview.column("website", width=200, stretch=True)
        self.treeview.column("active_since", width=120, stretch=False)

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
        # Add status filter
        status_frame = ttk.Frame(self.search_frame)
        status_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        ttk.Label(status_frame, text="Status:").pack(side=tk.LEFT, padx=(0, 5))

        # Create status combobox
        statuses = ["All"] + [status.name for status in SupplierStatus]
        status_combobox = ttk.Combobox(
            status_frame,
            textvariable=self.filter_status,
            values=statuses,
            state="readonly",
            width=15
        )
        status_combobox.pack(side=tk.LEFT)
        status_combobox.bind("<<ComboboxSelected>>", lambda e: self.on_apply_filters())

        # Add filter buttons
        btn_frame = ttk.Frame(status_frame)
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

    def create_item_actions(self, parent):
        """Create action buttons for selected suppliers.

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
        self.purchases_btn = ttk.Button(
            actions_frame,
            text="View Purchases",
            command=self.on_view_purchases,
            state=tk.DISABLED
        )
        self.purchases_btn.pack(side=tk.LEFT, padx=5)

        self.new_purchase_btn = ttk.Button(
            actions_frame,
            text="Create Purchase",
            command=self.on_create_purchase,
            state=tk.DISABLED
        )
        self.new_purchase_btn.pack(side=tk.LEFT, padx=5)

    def add_context_menu_items(self, menu):
        """Add supplier-specific context menu items.

        Args:
            menu: The context menu to add items to
        """
        menu.add_command(label="View Details", command=self.on_view)
        menu.add_command(label="Edit Supplier", command=self.on_edit)
        menu.add_separator()
        menu.add_command(label="View Purchases", command=self.on_view_purchases)
        menu.add_command(label="Create Purchase", command=self.on_create_purchase)
        menu.add_separator()
        menu.add_command(label="Delete Supplier", command=self.on_delete)

    def extract_item_values(self, item):
        """Extract values from a supplier item for display in the treeview.

        Args:
            item: The supplier item to extract values from

        Returns:
            List of values corresponding to treeview columns
        """
        # Format active_since date
        active_since = item.get('active_since', '')
        if active_since:
            if isinstance(active_since, datetime):
                active_since = active_since.strftime('%Y-%m-%d')

        # Get status
        status = item.get('status', '')
        if isinstance(status, SupplierStatus):
            status = status.name

        return [
            item.get('id', ''),
            item.get('name', ''),
            item.get('contact_email', ''),
            status,
            item.get('phone', ''),
            item.get('website', ''),
            active_since
        ]

    def load_data(self):
        """Load supplier data into the treeview based on current filters and pagination."""
        try:
            # Clear treeview
            self.treeview.delete(*self.treeview.get_children())

            # Get supplier service
            supplier_service = get_service('ISupplierService')

            # Calculate offset
            offset = (self.current_page - 1) * self.page_size

            # Get total count
            total_count = self.get_total_count(supplier_service)

            # Calculate total pages
            self.total_pages = (total_count + self.page_size - 1) // self.page_size

            # Update pagination display
            self.update_pagination_display(self.total_pages)

            # Get suppliers
            suppliers = self.get_items(supplier_service, offset, self.page_size)

            # Insert suppliers into treeview
            for supplier in suppliers:
                values = self.extract_item_values(supplier)
                self.treeview.insert('', 'end', values=values)

            # Update metrics
            self.update_metrics()

        except Exception as e:
            logger.error(f"Error loading supplier data: {e}")
            messagebox.showerror("Error", f"Failed to load supplier data: {e}")

    def get_items(self, service, offset, limit):
        """Get suppliers for the current page.

        Args:
            service: The service to use
            offset: Pagination offset
            limit: Page size

        Returns:
            List of suppliers
        """
        # Get filter values
        status_filter = self.filter_status.get()
        if status_filter == "All":
            status_filter = None

        # Get search text
        search_text = self.search_frame.get_field_value("search_text") if hasattr(self, "search_frame") else ""

        # Get suppliers
        return service.get_suppliers(
            search_text=search_text,
            status=status_filter,
            offset=offset,
            limit=limit
        )

    def get_total_count(self, service):
        """Get the total count of suppliers.

        Args:
            service: The service to use

        Returns:
            The total count of suppliers
        """
        # Get filter values
        status_filter = self.filter_status.get()
        if status_filter == "All":
            status_filter = None

        # Get search text
        search_text = self.search_frame.get_field_value("search_text") if hasattr(self, "search_frame") else ""

        # Get total count
        return service.get_supplier_count(
            search_text=search_text,
            status=status_filter
        )

    def update_metrics(self):
        """Update supplier metrics displayed in the panel."""
        try:
            # Get supplier service
            supplier_service = get_service('ISupplierService')

            # Get metrics
            metrics = supplier_service.get_supplier_metrics()

            # Update metric values
            self.metrics["total_suppliers"]["value"].config(text=str(metrics.get("total_suppliers", 0)))
            self.metrics["active_suppliers"]["value"].config(text=str(metrics.get("active_suppliers", 0)))
            self.metrics["purchases_last_30d"]["value"].config(text=str(metrics.get("purchases_last_30d", 0)))

            # Format lead time
            lead_time = metrics.get("avg_lead_time", 0)
            if isinstance(lead_time, float):
                lead_time = f"{lead_time:.1f} days"
            self.metrics["avg_lead_time"]["value"].config(text=lead_time)

            # Update status badges
            for status, count in metrics.get("status_counts", {}).items():
                if status in self.status_badges:
                    self.status_badges[status].config(text=str(count))

        except Exception as e:
            logger.error(f"Error updating supplier metrics: {e}")

    def on_select(self, event=None):
        """Handle supplier selection in the treeview."""
        # Enable/disable buttons based on selection
        if self.treeview.selection():
            self.view_btn.config(state=tk.NORMAL)
            self.edit_btn.config(state=tk.NORMAL)
            self.delete_btn.config(state=tk.NORMAL)
            self.purchases_btn.config(state=tk.NORMAL)
            self.new_purchase_btn.config(state=tk.NORMAL)
        else:
            self.view_btn.config(state=tk.DISABLED)
            self.edit_btn.config(state=tk.DISABLED)
            self.delete_btn.config(state=tk.DISABLED)
            self.purchases_btn.config(state=tk.DISABLED)
            self.new_purchase_btn.config(state=tk.DISABLED)

    def on_apply_filters(self):
        """Handle apply filters button click."""
        # Reset to first page and reload data
        self.current_page = 1
        self.load_data()

    def on_clear_filters(self):
        """Handle clear filters button click."""
        # Reset filter values
        self.filter_status.set("All")

        # Reset search field if exists
        if hasattr(self, "search_frame"):
            self.search_frame.set_field_value("search_text", "")

        # Reload data
        self.on_apply_filters()

    def on_add(self):
        """Handle add new supplier action."""
        dialog = SupplierDetailsDialog(
            self.winfo_toplevel(),
            create_new=True
        )
        if dialog.show():
            # Refresh the view
            self.refresh()

    def on_view(self):
        """Handle view supplier action."""
        # Get selected supplier ID
        selected_id = self.get_selected_id()
        if not selected_id:
            return

        # Show supplier details dialog in readonly mode
        dialog = SupplierDetailsDialog(
            self.winfo_toplevel(),
            supplier_id=selected_id,
            readonly=True
        )
        dialog.show()

    def on_edit(self):
        """Handle edit supplier action."""
        # Get selected supplier ID
        selected_id = self.get_selected_id()
        if not selected_id:
            return

        # Show supplier details dialog in edit mode
        dialog = SupplierDetailsDialog(
            self.winfo_toplevel(),
            supplier_id=selected_id
        )
        if dialog.show():
            # Refresh the view
            self.refresh()

    def on_delete(self):
        """Handle delete supplier action."""
        # Get selected supplier ID
        selected_id = self.get_selected_id()
        if not selected_id:
            return

        # Confirm deletion
        if not messagebox.askyesno(
                "Confirm Delete",
                "Are you sure you want to delete this supplier?\n\nThis action cannot be undone."
        ):
            return

        try:
            # Get supplier service
            supplier_service = get_service('ISupplierService')

            # Delete supplier
            success = supplier_service.delete_supplier(selected_id)

            if success:
                messagebox.showinfo("Success", "Supplier deleted successfully.")

                # Refresh the view
                self.refresh()
            else:
                messagebox.showerror("Error", "Failed to delete supplier.")

        except Exception as e:
            logger.error(f"Error deleting supplier: {e}")
            messagebox.showerror("Error", f"Failed to delete supplier: {e}")

    def on_view_purchases(self):
        """Handle view purchases action."""
        # Get selected supplier ID
        selected_id = self.get_selected_id()
        if not selected_id:
            return

        # Get selected supplier name
        selected_values = self.treeview.item(self.treeview.selection()[0], "values")
        supplier_name = selected_values[1]

        # Create view data
        view_data = {
            "filter_supplier_id": selected_id,
            "filter_supplier_name": supplier_name
        }

        # Show purchase view
        self.master.show_view("purchase_view", view_data=view_data)

    def on_create_purchase(self):
        """Handle create purchase action."""
        # Get selected supplier ID
        selected_id = self.get_selected_id()
        if not selected_id:
            return

        # Get selected supplier name
        selected_values = self.treeview.item(self.treeview.selection()[0], "values")
        supplier_name = selected_values[1]

        # Create view data
        view_data = {
            "supplier_id": selected_id,
            "supplier_name": supplier_name,
            "create_new": True
        }

        # Show purchase details view
        self.master.show_view("purchase_details_view", view_data=view_data)

    def on_generate_reports(self):
        """Handle generate reports button click."""
        # Create simple reports dialog
        report_dialog = tk.Toplevel(self.winfo_toplevel())
        report_dialog.title("Generate Supplier Reports")
        report_dialog.geometry("400x300")
        report_dialog.transient(self.winfo_toplevel())
        report_dialog.grab_set()

        # Create report options
        options_frame = ttk.LabelFrame(report_dialog, text="Report Options")
        options_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Report type
        ttk.Label(options_frame, text="Report Type:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        report_type = tk.StringVar(value="supplier_list")
        report_types = [
            ("Supplier List", "supplier_list"),
            ("Supplier Performance", "supplier_performance"),
            ("Procurement Summary", "procurement_summary")
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
        """Generate supplier report.

        Args:
            report_type: Type of report to generate
            date_from: Start date for report data
            date_to: End date for report data
            output_format: Output format (pdf, excel)
            dialog: Dialog to close on success
        """
        try:
            # Get supplier service
            supplier_service = get_service('ISupplierService')

            # Generate report
            result = supplier_service.generate_report(
                report_type=report_type,
                date_from=date_from,
                date_to=date_to,
                output_format=output_format
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
            # Get supplier service
            supplier_service = get_service('ISupplierService')

            # Export suppliers to CSV
            result = supplier_service.export_suppliers()

            if result:
                messagebox.showinfo(
                    "Export Complete",
                    f"Suppliers have been exported successfully.\n\nFile: {result}"
                )
            else:
                messagebox.showerror("Error", "Failed to export suppliers.")

        except Exception as e:
            logger.error(f"Error exporting suppliers: {e}")
            messagebox.showerror("Error", f"Failed to export suppliers: {e}")

    def on_supplier_updated(self, data):
        """Handle supplier updated event.

        Args:
            data: Event data including supplier_id
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
        """Get the ID of the selected supplier.

        Returns:
            The ID of the selected supplier, or None if no selection
        """
        selection = self.treeview.selection()
        if not selection:
            messagebox.showinfo("No Selection", "Please select a supplier first.")
            return None

        # Get selected supplier ID
        values = self.treeview.item(selection[0], "values")
        return values[0]

    def refresh(self):
        """Refresh the view."""
        self.load_data()

    def destroy(self):
        """Clean up resources and listeners before destroying the view."""
        # Unsubscribe from events
        unsubscribe("supplier_updated", self.on_supplier_updated)
        unsubscribe("supplier_created", self.on_supplier_updated)

        # Call parent destroy
        super().destroy()