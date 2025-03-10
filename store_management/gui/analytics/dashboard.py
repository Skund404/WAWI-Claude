# gui/analytics/dashboard.py
from __future__ import annotations

# Standard library imports
import tkinter as tk
from tkinter import ttk, messagebox
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

# Lazy import utility
from utils.lazy_imports import lazy_import_service

# Dependency Injection
from di.inject import inject

# Base view and error handling
from gui.base.base_view import BaseView
from services.base_service import ValidationError, NotFoundError

# Service interfaces (explicit import)
from services.interfaces.analytics_service import IAnalyticsService
from services.interfaces.project_service import IProjectService
from services.interfaces.inventory_service import IInventoryService
from services.interfaces.sales_service import ISalesService
from services.interfaces.customer_service import ICustomerService
from services.interfaces.purchase_service import IPurchaseService

class DashboardView(BaseView):
    """Dashboard view showing overview of business metrics."""

    @inject
    def __init__(self, parent: tk.Widget,
                 analytics_service: IAnalyticsService = None,
                 project_service: IProjectService = None,
                 inventory_service: IInventoryService = None,
                 sales_service: ISalesService = None,
                 customer_service: ICustomerService = None,
                 purchase_service: IPurchaseService = None):
        """Initialize the dashboard view.

        Args:
            parent: Parent widget
            analytics_service: Analytics service for business metrics
            project_service: Project service for project operations
            inventory_service: Inventory service for inventory operations
            sales_service: Sales service for sales operations
            customer_service: Customer service for customer operations
            purchase_service: Purchase service for purchase operations
        """
        # Lazy load services if not provided
        self.analytics_service = (
                analytics_service or
                lazy_import_service('AnalyticsService')()
        )
        self.project_service = (
                project_service or
                lazy_import_service('ProjectService')()
        )
        self.inventory_service = (
                inventory_service or
                lazy_import_service('InventoryService')()
        )
        self.sales_service = (
                sales_service or
                lazy_import_service('SalesService')()
        )
        self.customer_service = (
                customer_service or
                lazy_import_service('CustomerService')()
        )
        self.purchase_service = (
                purchase_service or
                lazy_import_service('PurchaseService')()
        )

        # Call parent initializer
        super().__init__(parent)


    def initialize_ui(self) -> None:
        """Initialize UI components with error handling."""
        try:
            # Create main layout
            self.frame.columnconfigure(0, weight=1)
            self.frame.columnconfigure(1, weight=1)
            self.frame.rowconfigure(1, weight=1)
            self.frame.rowconfigure(3, weight=1)

            # Create title
            title_frame = ttk.Frame(self.frame)
            title_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=(10, 5))

            title_label = ttk.Label(title_frame, text="Business Dashboard", font=("Helvetica", 16, "bold"))
            title_label.pack(side=tk.LEFT)

            # Add refresh button
            refresh_btn = ttk.Button(title_frame, text="Refresh", command=self.refresh_dashboard)
            refresh_btn.pack(side=tk.RIGHT)

            # Create dashboard sections
            self._create_key_metrics_section()
            self._create_active_projects_section()
            self._create_inventory_section()
            self._create_sales_section()

            # Load data
            self.refresh_dashboard()

        except Exception as e:
            self.logger.error(f"Error initializing dashboard UI: {e}")
            messagebox.showerror("Dashboard Initialization Error",
                                 f"Could not initialize dashboard: {e}")

    def refresh_dashboard(self) -> None:
        """Refresh all dashboard data with comprehensive error handling."""
        try:
            # Show loading message
            self.status_var.set("Loading dashboard data...")
            self.frame.update_idletasks()

            # Centralize dashboard data fetching
            dashboard_data = self._fetch_dashboard_metrics()

            if dashboard_data:
                metrics = dashboard_data.get('metrics', {})

                # Update dashboard sections
                self._update_key_metrics(metrics)
                self._update_active_projects(metrics.get('recent_projects', []))
                self._update_inventory_status()
                self._update_sales_data()

                # Update status
                self.status_var.set(f"Dashboard refreshed at {datetime.now().strftime('%H:%M:%S')}")
            else:
                self.status_var.set("No dashboard data available")

        except ValidationError as ve:
            self.logger.warning(f"Validation error in dashboard refresh: {ve}")
            messagebox.showwarning("Dashboard Warning", str(ve))
            self.status_var.set("Dashboard refresh failed: Validation error")
        except NotFoundError as nfe:
            self.logger.info(f"Not found error in dashboard refresh: {nfe}")
            messagebox.showinfo("Dashboard Information", str(nfe))
            self.status_var.set("Dashboard refresh incomplete: Some data not found")
        except Exception as e:
            self.logger.error(f"Unexpected error in dashboard refresh: {e}")
            messagebox.showerror("Dashboard Error",
                                 f"Unexpected error refreshing dashboard: {e}")
            self.status_var.set("Dashboard refresh failed")

    def _fetch_dashboard_metrics(self) -> Dict[str, Any]:
        """
        Fetch dashboard metrics from analytics service with fallback.

        Returns:
            Dict containing dashboard metrics
        """
        try:
            # Primary method: Use analytics service
            return self.analytics_service.get_dashboard_metrics()
        except Exception as primary_error:
            self.logger.warning(f"Primary metrics fetch failed: {primary_error}")

            try:
                # Fallback: Aggregate data from individual services
                return {
                    'metrics': {
                        'total_projects': self.project_service.get_total_count(),
                        'active_projects': self.project_service.get_active_count(),
                        'total_sales': self.sales_service.get_total_sales(),
                        'inventory_value': self.inventory_service.get_total_value(),
                        'customer_count': self.customer_service.get_total_count(),
                        'low_stock_items': self.inventory_service.get_low_stock_items()
                    }
                }
            except Exception as fallback_error:
                self.logger.error(f"Fallback metrics fetch failed: {fallback_error}")
                raise ValidationError("Could not retrieve dashboard metrics")

    def _create_key_metrics_section(self) -> None:
        """Create the key metrics section."""
        # Create key metrics frame
        metrics_frame = ttk.LabelFrame(self.frame, text="Key Metrics")
        metrics_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)

        # Configure grid
        metrics_frame.columnconfigure(0, weight=1)
        metrics_frame.columnconfigure(1, weight=1)

        # Create metrics cards
        self.metric_widgets = {}

        self._create_metric_card(metrics_frame, "customer_count", "Customers", 0, 0)
        self._create_metric_card(metrics_frame, "active_projects", "Active Projects", 0, 1)
        self._create_metric_card(metrics_frame, "sales_this_month", "Sales This Month", 1, 0, is_currency=True)
        self._create_metric_card(metrics_frame, "inventory_value", "Inventory Value", 1, 1, is_currency=True)
        self._create_metric_card(metrics_frame, "orders_this_month", "Orders This Month", 2, 0)
        self._create_metric_card(metrics_frame, "low_stock_count", "Low Stock Items", 2, 1)

        # Add status bar
        status_frame = ttk.Frame(metrics_frame)
        status_frame.grid(row=3, column=0, columnspan=2, sticky="ew", padx=5, pady=5)

        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(status_frame, textvariable=self.status_var, font=("Helvetica", 9, "italic"))
        status_label.pack(side=tk.LEFT)

    def _create_metric_card(self, parent: ttk.Frame, key: str, label: str, row: int, col: int,
                            is_currency: bool = False) -> None:
        """Create a metric card widget.

        Args:
            parent: Parent frame
            key: Metric key
            label: Metric label
            row: Grid row
            col: Grid column
            is_currency: Whether the metric is a currency value
        """
        # Create card frame
        card = ttk.Frame(parent, borderwidth=1, relief="solid", padding=10)
        card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")

        # Create label
        label_widget = ttk.Label(card, text=label, font=("Helvetica", 10))
        label_widget.pack(pady=(0, 5))

        # Create value
        value_var = tk.StringVar(value="0")
        value_widget = ttk.Label(card, textvariable=value_var, font=("Helvetica", 14, "bold"))
        value_widget.pack()

        # Store references
        self.metric_widgets[key] = {
            'var': value_var,
            'is_currency': is_currency
        }

    def _create_active_projects_section(self) -> None:
        """Create the active projects section."""
        # Create projects frame
        projects_frame = ttk.LabelFrame(self.frame, text="Active Projects")
        projects_frame.grid(row=1, column=1, sticky="nsew", padx=10, pady=5)

        # Configure grid
        projects_frame.columnconfigure(0, weight=1)
        projects_frame.rowconfigure(0, weight=1)

        # Create treeview
        columns = ("name", "type", "status", "start_date")
        self.projects_tree = ttk.Treeview(projects_frame, columns=columns, show="headings")

        # Configure columns
        self.projects_tree.heading("name", text="Name")
        self.projects_tree.heading("type", text="Type")
        self.projects_tree.heading("status", text="Status")
        self.projects_tree.heading("start_date", text="Start Date")

        self.projects_tree.column("name", width=150)
        self.projects_tree.column("type", width=120)
        self.projects_tree.column("status", width=120)
        self.projects_tree.column("start_date", width=100)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(projects_frame, orient=tk.VERTICAL, command=self.projects_tree.yview)
        self.projects_tree.configure(yscrollcommand=scrollbar.set)

        # Add to grid
        self.projects_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Add buttons
        buttons_frame = ttk.Frame(projects_frame)
        buttons_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=5)

        ttk.Button(buttons_frame, text="View Details", command=self._view_project_details).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Add Project", command=self._add_project).pack(side=tk.LEFT, padx=5)

    def _create_inventory_section(self) -> None:
        """Create the inventory section."""
        # Create inventory frame
        inventory_frame = ttk.LabelFrame(self.frame, text="Low Stock Inventory")
        inventory_frame.grid(row=3, column=0, sticky="nsew", padx=10, pady=5)

        # Configure grid
        inventory_frame.columnconfigure(0, weight=1)
        inventory_frame.rowconfigure(0, weight=1)

        # Create treeview
        columns = ("name", "type", "quantity", "status")
        self.inventory_tree = ttk.Treeview(inventory_frame, columns=columns, show="headings")

        # Configure columns
        self.inventory_tree.heading("name", text="Name")
        self.inventory_tree.heading("type", text="Type")
        self.inventory_tree.heading("quantity", text="Quantity")
        self.inventory_tree.heading("status", text="Status")

        self.inventory_tree.column("name", width=150)
        self.inventory_tree.column("type", width=120)
        self.inventory_tree.column("quantity", width=80)
        self.inventory_tree.column("status", width=100)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(inventory_frame, orient=tk.VERTICAL, command=self.inventory_tree.yview)
        self.inventory_tree.configure(yscrollcommand=scrollbar.set)

        # Add to grid
        self.inventory_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Add buttons
        buttons_frame = ttk.Frame(inventory_frame)
        buttons_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=5)

        ttk.Button(buttons_frame, text="View Inventory", command=self._view_inventory).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Generate Order", command=self._generate_order).pack(side=tk.LEFT, padx=5)

    def _create_sales_section(self) -> None:
        """Create the sales section."""
        # Create sales frame
        sales_frame = ttk.LabelFrame(self.frame, text="Recent Sales")
        sales_frame.grid(row=3, column=1, sticky="nsew", padx=10, pady=5)

        # Configure grid
        sales_frame.columnconfigure(0, weight=1)
        sales_frame.rowconfigure(0, weight=1)

        # Create treeview
        columns = ("date", "customer", "amount", "status")
        self.sales_tree = ttk.Treeview(sales_frame, columns=columns, show="headings")

        # Configure columns
        self.sales_tree.heading("date", text="Date")
        self.sales_tree.heading("customer", text="Customer")
        self.sales_tree.heading("amount", text="Amount")
        self.sales_tree.heading("status", text="Status")

        self.sales_tree.column("date", width=100)
        self.sales_tree.column("customer", width=150)
        self.sales_tree.column("amount", width=100)
        self.sales_tree.column("status", width=100)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(sales_frame, orient=tk.VERTICAL, command=self.sales_tree.yview)
        self.sales_tree.configure(yscrollcommand=scrollbar.set)

        # Add to grid
        self.sales_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Add buttons
        buttons_frame = ttk.Frame(sales_frame)
        buttons_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=5)

        ttk.Button(buttons_frame, text="View Sales", command=self._view_sales).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Add Sale", command=self._add_sale).pack(side=tk.LEFT, padx=5)

    def _update_key_metrics(self, metrics: Dict[str, Any]) -> None:
        """Update key metrics display.

        Args:
            metrics: Metrics data
        """
        for key, widget_data in self.metric_widgets.items():
            if key in metrics:
                value = metrics[key]
                if widget_data['is_currency']:
                    widget_data['var'].set(f"${value:.2f}")
                else:
                    widget_data['var'].set(str(value))

    def _update_active_projects(self, projects: List[Dict[str, Any]]) -> None:
        """Update active projects list.

        Args:
            projects: List of active projects
        """
        # Clear treeview
        for item in self.projects_tree.get_children():
            self.projects_tree.delete(item)

        # Add projects
        for project in projects:
            # Format date
            start_date = "N/A"
            if project.get('start_date'):
                start_date_str = project['start_date']
                if isinstance(start_date_str, str):
                    try:
                        start_date_dt = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
                        start_date = start_date_dt.strftime('%Y-%m-%d')
                    except ValueError:
                        start_date = start_date_str
                elif isinstance(start_date_str, datetime):
                    start_date = start_date_str.strftime('%Y-%m-%d')

            # Add to treeview
            self.projects_tree.insert('', 'end', values=(
                project.get('name', 'N/A'),
                project.get('type', 'N/A'),
                project.get('status', 'N/A'),
                start_date
            ), tags=(str(project.get('id')),))

    def _update_inventory_status(self) -> None:
        """Update inventory status list."""
        try:
            # Get low stock report
            report = self.execute_service_call(
                lambda: self.analytics_service.get_low_stock_report(),
                error_title="Inventory Error"
            )

            if not report:
                return

            # Clear treeview
            for item in self.inventory_tree.get_children():
                self.inventory_tree.delete(item)

            # Combine low stock and out of stock items
            items = report.get('low_stock_items', []) + report.get('out_of_stock_items', [])

            # Add items to treeview (limit to 10)
            for item in items[:10]:
                self.inventory_tree.insert('', 'end', values=(
                    item.get('name', 'N/A'),
                    item.get('material_type', item.get('type', 'N/A')),
                    item.get('quantity', 0),
                    item.get('status', 'N/A')
                ), tags=(str(item.get('id', '')),))
        except Exception as e:
            self.logger.error(f"Error updating inventory status: {str(e)}")

    def _update_sales_data(self) -> None:
        """Update sales data list."""
        try:
            # Get sales for the last 30 days
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)

            # Get sales from the service
            sales = self.execute_service_call(
                lambda: self.sales_service.get_by_date_range(start_date, end_date),
                error_title="Sales Error"
            )

            # If no sales data returned, try to get it from analytics service
            if not sales:
                report = self.execute_service_call(
                    lambda: self.analytics_service.get_sales_report(start_date, end_date),
                    error_title="Sales Error"
                )
                if not report:
                    return

            # Clear treeview
            for item in self.sales_tree.get_children():
                self.sales_tree.delete(item)

            # Get the most recent 10 sales
            recent_sales = sales[:10] if isinstance(sales, list) else []

            # Add sales to treeview
            for sale in recent_sales:
                # Format date
                sale_date = "N/A"
                if 'created_at' in sale:
                    sale_date_val = sale['created_at']
                    if isinstance(sale_date_val, str):
                        try:
                            sale_date_dt = datetime.fromisoformat(sale_date_val.replace('Z', '+00:00'))
                            sale_date = sale_date_dt.strftime('%Y-%m-%d')
                        except ValueError:
                            sale_date = sale_date_val
                    elif isinstance(sale_date_val, datetime):
                        sale_date = sale_date_val.strftime('%Y-%m-%d')

                # Get customer name
                customer_name = "N/A"
                if 'customer_id' in sale and sale['customer_id']:
                    try:
                        customer = self.customer_service.get_by_id(sale['customer_id'])
                        if customer:
                            customer_name = customer.get('name', 'N/A')
                    except Exception:
                        pass

                # Format amount
                amount = f"${sale.get('total_amount', 0):.2f}" if 'total_amount' in sale else "N/A"

                # Add to treeview
                self.sales_tree.insert('', 'end', values=(
                    sale_date,
                    customer_name,
                    amount,
                    sale.get('status', 'N/A')
                ), tags=(str(sale.get('id', '')),))
        except Exception as e:
            self.logger.error(f"Error updating sales data: {str(e)}")

    def _view_project_details(self) -> None:
        """View details of the selected project."""
        # Get selected project
        selected = self.projects_tree.selection()
        if not selected:
            messagebox.showinfo("Selection", "Please select a project to view")
            return

        # Get project ID from tags
        project_id = int(self.projects_tree.item(selected[0], 'tags')[0])

        try:
            # Get project details
            project = self.execute_service_call(
                lambda: self.project_service.get_by_id(project_id),
                error_title="Project Error"
            )

            if not project:
                return

            # Show project details dialog
            self._show_project_details_dialog(project)
        except Exception as e:
            self.logger.error(f"Error viewing project details: {str(e)}")
            messagebox.showerror("Project Error", f"Error viewing project details: {str(e)}")

    def _show_project_details_dialog(self, project: Dict[str, Any]) -> None:
        """Show dialog with project details.

        Args:
            project: Project data
        """
        # Create dialog
        dialog = tk.Toplevel(self.frame)
        dialog.title(f"Project Details: {project.get('name', 'Unknown')}")
        dialog.geometry("600x400")
        dialog.transient(self.frame)
        dialog.grab_set()

        # Configure grid
        dialog.columnconfigure(0, weight=1)
        dialog.rowconfigure(1, weight=1)

        # Create title
        title_frame = ttk.Frame(dialog)
        title_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        ttk.Label(title_frame, text=f"Project: {project.get('name', 'Unknown')}",
                  font=("Helvetica", 14, "bold")).pack(side=tk.LEFT)

        # Create notebook
        notebook = ttk.Notebook(dialog)
        notebook.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)

        # Create tabs
        details_frame = ttk.Frame(notebook)
        components_frame = ttk.Frame(notebook)

        notebook.add(details_frame, text="Details")
        notebook.add(components_frame, text="Components")

        # Details tab
        details_frame.columnconfigure(1, weight=1)

        # Add project details
        fields = [
            ("ID:", "id"),
            ("Name:", "name"),
            ("Type:", "type"),
            ("Status:", "status"),
            ("Description:", "description"),
            ("Start Date:", "start_date"),
            ("End Date:", "end_date")
        ]

        for i, (label_text, key) in enumerate(fields):
            ttk.Label(details_frame, text=label_text, font=("Helvetica", 10, "bold")).grid(
                row=i, column=0, sticky="w", padx=10, pady=5)

            value = project.get(key, "N/A")
            if key in ['start_date', 'end_date'] and value:
                if isinstance(value, str):
                    try:
                        value_dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                        value = value_dt.strftime('%Y-%m-%d')
                    except ValueError:
                        pass
                elif isinstance(value, datetime):
                    value = value.strftime('%Y-%m-%d')

            ttk.Label(details_frame, text=str(value)).grid(
                row=i, column=1, sticky="w", padx=10, pady=5)

        # Components tab
        components_frame.columnconfigure(0, weight=1)
        components_frame.rowconfigure(0, weight=1)

        # Create components treeview
        columns = ("id", "name", "type", "quantity")
        components_tree = ttk.Treeview(components_frame, columns=columns, show="headings")

        # Configure columns
        components_tree.heading("id", text="ID")
        components_tree.heading("name", text="Name")
        components_tree.heading("type", text="Type")
        components_tree.heading("quantity", text="Quantity")

        components_tree.column("id", width=50)
        components_tree.column("name", width=200)
        components_tree.column("type", width=150)
        components_tree.column("quantity", width=100)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(components_frame, orient=tk.VERTICAL, command=components_tree.yview)
        components_tree.configure(yscrollcommand=scrollbar.set)

        # Add to grid
        components_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Add components
        components = project.get('components', [])
        for component in components:
            components_tree.insert('', 'end', values=(
                component.get('id', 'N/A'),
                component.get('name', 'N/A'),
                component.get('component_type', 'N/A'),
                component.get('quantity', 0)
            ))

        # Add close button
        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)

        ttk.Button(button_frame, text="Close", command=dialog.destroy).pack(side=tk.RIGHT)

        # Add additional action buttons
        ttk.Button(button_frame, text="Update Status",
                   command=lambda: self._update_project_status(dialog, project)).pack(side=tk.LEFT, padx=5)

        ttk.Button(button_frame, text="Generate Picking List",
                   command=lambda: self._generate_project_picking_list(dialog, project)).pack(side=tk.LEFT, padx=5)

    def _update_project_status(self, parent: tk.Toplevel, project: Dict[str, Any]) -> None:
        """Show dialog to update project status.

        Args:
            parent: Parent dialog
            project: Project data
        """
        # Get available statuses from the project_service or use a predefined list
        statuses = [
            "INITIAL_CONSULTATION",
            "DESIGN_PHASE",
            "PATTERN_DEVELOPMENT",
            "MATERIAL_SELECTION",
            "CUTTING",
            "ASSEMBLY",
            "IN_PROGRESS",
            "QUALITY_CHECK",
            "COMPLETED"
        ]

        # Create dialog
        dialog = tk.Toplevel(parent)
        dialog.title("Update Project Status")
        dialog.transient(parent)
        dialog.grab_set()

        # Add instructions
        ttk.Label(dialog, text=f"Current status: {project.get('status', 'Unknown')}",
                  font=("Helvetica", 10, "bold")).pack(padx=20, pady=(20, 10))

        ttk.Label(dialog, text="Select new status:").pack(padx=20, pady=(0, 10))

        # Add status selection
        status_var = tk.StringVar(value=project.get('status', ''))
        for status in statuses:
            ttk.Radiobutton(dialog, text=status, variable=status_var, value=status).pack(
                padx=20, pady=2, anchor="w")

        # Add buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(padx=20, pady=20, fill="x")

        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side="right", padx=5)
        ttk.Button(button_frame, text="Update",
                   command=lambda: self._perform_status_update(dialog, project, status_var.get())
                   ).pack(side="right", padx=5)

        # Center dialog
        dialog.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - dialog.winfo_width()) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")

    def _perform_status_update(self, dialog: tk.Toplevel, project: Dict[str, Any], new_status: str) -> None:
        """Perform the project status update.

        Args:
            dialog: Dialog window
            project: Project data
            new_status: New project status
        """
        if not new_status or new_status == project.get('status', ''):
            dialog.destroy()
            return

        try:
            # Update project status
            result = self.execute_service_call(
                lambda: self.project_service.update_status(project['id'], new_status),
                error_title="Status Update Error"
            )

            if result:
                messagebox.showinfo("Status Updated",
                                    f"Project status updated to {new_status}",
                                    parent=dialog)
                dialog.destroy()

                # Refresh dashboard
                self.refresh_dashboard()
        except Exception as e:
            self.logger.error(f"Error updating project status: {str(e)}")
            messagebox.showerror("Status Update Error",
                                 f"Error updating project status: {str(e)}",
                                 parent=dialog)

    def _generate_project_picking_list(self, parent: tk.Toplevel, project: Dict[str, Any]) -> None:
        """Generate picking list for a project.

        Args:
            parent: Parent dialog
            project: Project data
        """
        try:
            # Generate picking list
            picking_list = self.execute_service_call(
                lambda: self.project_service.generate_picking_list(project['id']),
                error_title="Picking List Error"
            )

            if picking_list:
                messagebox.showinfo("Picking List",
                                    f"Picking list #{picking_list.get('id', 'N/A')} generated successfully",
                                    parent=parent)
        except Exception as e:
            self.logger.error(f"Error generating picking list: {str(e)}")
            messagebox.showerror("Picking List Error",
                                 f"Error generating picking list: {str(e)}",
                                 parent=parent)

    def _add_project(self) -> None:
        """Add a new project."""
        # This would typically navigate to the project view or show a dialog
        # Here we'll show a dialog with a simplified form

        try:
            # Get customers for dropdown
            customers = self.execute_service_call(
                lambda: self.customer_service.get_all(),
                error_title="Customer Error"
            )

            if not customers:
                messagebox.showinfo("Add Project", "No customers available. Please add a customer first.")
                return

            # Create dialog
            dialog = tk.Toplevel(self.frame)
            dialog.title("Add Project")
            dialog.geometry("500x400")
            dialog.transient(self.frame)
            dialog.grab_set()

            # Configure grid
            dialog.columnconfigure(1, weight=1)

            # Project types - this would ideally come from the project service
            project_types = [
                "WALLET", "BRIEFCASE", "MESSENGER_BAG", "TOTE_BAG", "BACKPACK",
                "BELT", "WATCH_STRAP", "NOTEBOOK_COVER", "PHONE_CASE", "CUSTOM"
            ]

            # Add form fields
            ttk.Label(dialog, text="Project Name:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
            name_var = tk.StringVar()
            ttk.Entry(dialog, textvariable=name_var, width=30).grid(row=0, column=1, sticky="ew", padx=10, pady=5)

            ttk.Label(dialog, text="Project Type:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
            type_var = tk.StringVar()
            type_combo = ttk.Combobox(dialog, textvariable=type_var, values=project_types, width=28)
            type_combo.grid(row=1, column=1, sticky="ew", padx=10, pady=5)

            ttk.Label(dialog, text="Customer:").grid(row=2, column=0, sticky="w", padx=10, pady=5)
            customer_var = tk.StringVar()
            customer_combo = ttk.Combobox(dialog, textvariable=customer_var, width=28)
            customer_combo['values'] = [f"{c.get('id')} - {c.get('name', 'N/A')}" for c in customers]
            customer_combo.grid(row=2, column=1, sticky="ew", padx=10, pady=5)

            ttk.Label(dialog, text="Description:").grid(row=3, column=0, sticky="nw", padx=10, pady=5)
            description_text = tk.Text(dialog, height=5, width=30)
            description_text.grid(row=3, column=1, sticky="ew", padx=10, pady=5)

            # Add buttons
            button_frame = ttk.Frame(dialog)
            button_frame.grid(row=4, column=0, columnspan=2, sticky="ew", padx=10, pady=20)

            ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
            ttk.Button(button_frame, text="Create Project",
                       command=lambda: self._create_project(dialog, {
                           'name': name_var.get(),
                           'type': type_var.get(),
                           'customer_id': int(customer_var.get().split(' - ')[0]) if customer_var.get() else None,
                           'description': description_text.get("1.0", tk.END).strip()
                       })).pack(side=tk.RIGHT, padx=5)
        except Exception as e:
            self.logger.error(f"Error showing add project dialog: {str(e)}")
            messagebox.showerror("Dialog Error", f"Error showing add project dialog: {str(e)}")

    def _create_project(self, dialog: tk.Toplevel, project_data: Dict[str, Any]) -> None:
        """Create a new project.

        Args:
            dialog: Dialog window
            project_data: Project data
        """
        # Validate input
        if not project_data.get('name'):
            messagebox.showerror("Validation Error", "Project name is required", parent=dialog)
            return

        if not project_data.get('type'):
            messagebox.showerror("Validation Error", "Project type is required", parent=dialog)
            return

        if not project_data.get('customer_id'):
            messagebox.showerror("Validation Error", "Customer is required", parent=dialog)
            return

        try:
            # Create project
            result = self.execute_service_call(
                lambda: self.project_service.create(project_data),
                error_title="Project Creation Error"
            )

            if result:
                messagebox.showinfo("Project Created",
                                    f"Project '{result.get('name')}' created successfully",
                                    parent=dialog)
                dialog.destroy()

                # Refresh dashboard
                self.refresh_dashboard()
        except Exception as e:
            self.logger.error(f"Error creating project: {str(e)}")
            messagebox.showerror("Project Creation Error",
                                 f"Error creating project: {str(e)}",
                                 parent=dialog)

    def _view_inventory(self) -> None:
        """View inventory."""
        # This would typically navigate to the inventory view
        # Notify the parent (main window) to switch to inventory view
        self.frame.event_generate("<<ShowInventoryView>>")

    def _generate_order(self) -> None:
        """Generate a purchase order for low stock items."""
        try:
            # Get reorder list
            reorder_list = self.execute_service_call(
                lambda: self.purchase_service.generate_reorder_list(),
                error_title="Reorder Error"
            )

            if not reorder_list:
                messagebox.showinfo("Reorder List", "No items found for reordering")
                return

            # Create dialog to show reorder list
            dialog = tk.Toplevel(self.frame)
            dialog.title("Reorder List")
            dialog.geometry("700x500")
            dialog.transient(self.frame)
            dialog.grab_set()

            # Configure grid
            dialog.columnconfigure(0, weight=1)
            dialog.rowconfigure(1, weight=1)

            # Create title
            ttk.Label(dialog, text="Recommended Items for Reordering",
                      font=("Helvetica", 14, "bold")).grid(row=0, column=0, sticky="w", padx=10, pady=10)

            # Create treeview
            columns = ("material_id", "name", "quantity", "reorder_quantity", "supplier")
            tree = ttk.Treeview(dialog, columns=columns, show="headings")

            # Configure columns
            tree.heading("material_id", text="ID")
            tree.heading("name", text="Material")
            tree.heading("quantity", text="Current Qty")
            tree.heading("reorder_quantity", text="Reorder Qty")
            tree.heading("supplier", text="Supplier")

            tree.column("material_id", width=50)
            tree.column("name", width=200)
            tree.column("quantity", width=100)
            tree.column("reorder_quantity", width=100)
            tree.column("supplier", width=200)

            # Add scrollbar
            scrollbar = ttk.Scrollbar(dialog, orient=tk.VERTICAL, command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)

            # Add to grid
            tree.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
            scrollbar.grid(row=1, column=1, sticky="ns", pady=5)

            # Add items to treeview
            for item in reorder_list:
                supplier_name = item.get('supplier_name', 'N/A')

                tree.insert('', 'end', values=(
                    item.get('material_id', 'N/A'),
                    item.get('material_name', 'N/A'),
                    item.get('current_quantity', 0),
                    item.get('reorder_quantity', 0),
                    supplier_name
                ))

            # Add buttons
            button_frame = ttk.Frame(dialog)
            button_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=10)

            ttk.Button(button_frame, text="Close", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
            ttk.Button(button_frame, text="Create Purchase Order",
                       command=lambda: self._create_purchase_order(dialog, reorder_list)).pack(side=tk.RIGHT, padx=5)

        except Exception as e:
            self.logger.error(f"Error generating reorder list: {str(e)}")
            messagebox.showerror("Reorder Error", f"Error generating reorder list: {str(e)}")

    def _create_purchase_order(self, dialog: tk.Toplevel, reorder_list: List[Dict[str, Any]]) -> None:
        """Create purchase orders from the reorder list.

        Args:
            dialog: Dialog window
            reorder_list: List of items to reorder
        """
        try:
            # Group items by supplier
            items_by_supplier = {}
            for item in reorder_list:
                supplier_id = item.get('supplier_id')
                if supplier_id:
                    if supplier_id not in items_by_supplier:
                        items_by_supplier[supplier_id] = {
                            'supplier_name': item.get('supplier_name', 'Unknown'),
                            'items': []
                        }

                    items_by_supplier[supplier_id]['items'].append({
                        'item_type': 'material',
                        'item_id': item.get('material_id'),
                        'quantity': item.get('reorder_quantity', 1),
                        'price': 0.0  # Would need to get actual price
                    })

            # Create purchase orders
            orders_created = 0
            for supplier_id, supplier_data in items_by_supplier.items():
                # Create purchase data
                purchase_data = {
                    'supplier_id': supplier_id,
                    'status': 'DRAFT',
                    'created_at': datetime.now(),
                    'items': supplier_data['items']
                }

                # Create purchase
                result = self.execute_service_call(
                    lambda: self.purchase_service.create(purchase_data),
                    error_title="Purchase Creation Error"
                )

                if result:
                    orders_created += 1

            # Show success message
            messagebox.showinfo("Purchase Orders Created",
                                f"Created {orders_created} purchase orders",
                                parent=dialog)
            dialog.destroy()

        except Exception as e:
            self.logger.error(f"Error creating purchase orders: {str(e)}")
            messagebox.showerror("Purchase Creation Error",
                                 f"Error creating purchase orders: {str(e)}",
                                 parent=dialog)

    def _view_sales(self) -> None:
        """View sales."""
        # This would typically navigate to the sales view
        # Notify the parent (main window) to switch to sales view
        self.frame.event_generate("<<ShowSalesView>>")

    def _add_sale(self) -> None:
        """Add a new sale."""
        # This would typically navigate to the sales view or show a dialog
        # Notify the parent (main window) to show add sale dialog
        self.frame.event_generate("<<ShowAddSaleDialog>>")


# gui/analytics/sales_report_view.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
import csv
import os

from di.inject import inject
from services.interfaces.analytics_service import IAnalyticsService
from gui.base.base_view import BaseView
from services.base_service import ValidationError, NotFoundError


class SalesReportView(BaseView):
    """View for generating and displaying sales reports."""

    @inject
    def __init__(self, parent: tk.Widget,
                 analytics_service: IAnalyticsService):
        """Initialize the sales report view.

        Args:
            parent: Parent widget
            analytics_service: Analytics service for business metrics
        """
        self.analytics_service = analytics_service
        super().__init__(parent)

    def initialize_ui(self) -> None:
        """Initialize UI components."""
        # Create main layout
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(2, weight=1)

        # Create title
        title_frame = ttk.Frame(self.frame)
        title_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))

        title_label = ttk.Label(title_frame, text="Sales Report", font=("Helvetica", 16, "bold"))
        title_label.pack(side=tk.LEFT)

        # Create date selection frame
        date_frame = ttk.Frame(self.frame)
        date_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)

        # Start date
        ttk.Label(date_frame, text="Start Date:").pack(side=tk.LEFT, padx=(0, 5))

        self.start_year_var = tk.StringVar(value=str(datetime.now().year))
        start_year = ttk.Combobox(date_frame, textvariable=self.start_year_var, width=6)
        start_year['values'] = [str(year) for year in range(datetime.now().year - 5, datetime.now().year + 1)]
        start_year.pack(side=tk.LEFT, padx=2)

        ttk.Label(date_frame, text="-").pack(side=tk.LEFT)

        self.start_month_var = tk.StringVar(value=str(datetime.now().month))
        start_month = ttk.Combobox(date_frame, textvariable=self.start_month_var, width=3)
        start_month['values'] = [str(month).zfill(2) for month in range(1, 13)]
        start_month.pack(side=tk.LEFT, padx=2)

        ttk.Label(date_frame, text="-").pack(side=tk.LEFT)

        self.start_day_var = tk.StringVar(value="01")
        start_day = ttk.Combobox(date_frame, textvariable=self.start_day_var, width=3)
        start_day['values'] = [str(day).zfill(2) for day in range(1, 32)]
        start_day.pack(side=tk.LEFT, padx=2)

        # End date
        ttk.Label(date_frame, text="End Date:").pack(side=tk.LEFT, padx=(20, 5))

        self.end_year_var = tk.StringVar(value=str(datetime.now().year))
        end_year = ttk.Combobox(date_frame, textvariable=self.end_year_var, width=6)
        end_year['values'] = [str(year) for year in range(datetime.now().year - 5, datetime.now().year + 1)]
        end_year.pack(side=tk.LEFT, padx=2)

        ttk.Label(date_frame, text="-").pack(side=tk.LEFT)

        self.end_month_var = tk.StringVar(value=str(datetime.now().month))
        end_month = ttk.Combobox(date_frame, textvariable=self.end_month_var, width=3)
        end_month['values'] = [str(month).zfill(2) for month in range(1, 13)]
        end_month.pack(side=tk.LEFT, padx=2)

        ttk.Label(date_frame, text="-").pack(side=tk.LEFT)

        self.end_day_var = tk.StringVar(value=str(datetime.now().day))
        end_day = ttk.Combobox(date_frame, textvariable=self.end_day_var, width=3)
        end_day['values'] = [str(day).zfill(2) for day in range(1, 32)]
        end_day.pack(side=tk.LEFT, padx=2)

        # Generate button
        ttk.Button(date_frame, text="Generate Report", command=self.generate_report).pack(side=tk.LEFT, padx=20)

        # Create notebook for report sections
        self.notebook = ttk.Notebook(self.frame)
        self.notebook.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)

        # Create report sections
        self.summary_frame = ttk.Frame(self.notebook)
        self.by_product_frame = ttk.Frame(self.notebook)
        self.by_month_frame = ttk.Frame(self.notebook)

        self.notebook.add(self.summary_frame, text="Summary")
        self.notebook.add(self.by_product_frame, text="By Product")
        self.notebook.add(self.by_month_frame, text="By Month")

        # Initialize report sections
        self._init_summary_section()
        self._init_by_product_section()
        self._init_by_month_section()

        # Create button frame
        button_frame = ttk.Frame(self.frame)
        button_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=10)

        ttk.Button(button_frame, text="Export to CSV", command=self.export_to_csv).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Print Report", command=self.print_report).pack(side=tk.LEFT, padx=5)

        # Initialize with current month data
        self._set_current_month()
        self.generate_report()

    def _init_summary_section(self) -> None:
        """Initialize summary section."""
        # Configure grid
        self.summary_frame.columnconfigure(0, weight=1)
        self.summary_frame.columnconfigure(1, weight=1)

        # Create summary fields
        fields = [
            ("Date Range:", "date_range"),
            ("Total Sales:", "total_sales"),
            ("Total Orders:", "total_count"),
            ("Completed Orders:", "completed_sales"),
            ("Cancelled Orders:", "cancelled_sales"),
            ("Completion Rate:", "completion_rate")
        ]

        # Create field variables
        self.summary_vars = {}

        # Add fields
        for i, (label_text, key) in enumerate(fields):
            ttk.Label(self.summary_frame, text=label_text, font=("Helvetica", 10, "bold")).grid(
                row=i, column=0, sticky="w", padx=10, pady=5)

            var = tk.StringVar(value="")
            ttk.Label(self.summary_frame, textvariable=var).grid(
                row=i, column=1, sticky="w", padx=10, pady=5)

            self.summary_vars[key] = var

    def _init_by_product_section(self) -> None:
        """Initialize by product section."""
        # Configure grid
        self.by_product_frame.columnconfigure(0, weight=1)
        self.by_product_frame.rowconfigure(0, weight=1)

        # Create treeview
        columns = ("id", "name", "count", "amount")
        self.product_tree = ttk.Treeview(self.by_product_frame, columns=columns, show="headings")

        # Configure columns
        self.product_tree.heading("id", text="ID")
        self.product_tree.heading("name", text="Product")
        self.product_tree.heading("count", text="Count")
        self.product_tree.heading("amount", text="Amount")

        self.product_tree.column("id", width=50)
        self.product_tree.column("name", width=200)
        self.product_tree.column("count", width=100)
        self.product_tree.column("amount", width=100)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.by_product_frame, orient=tk.VERTICAL, command=self.product_tree.yview)
        self.product_tree.configure(yscrollcommand=scrollbar.set)

        # Add to grid
        self.product_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

    def _init_by_month_section(self) -> None:
        """Initialize by month section."""
        # Configure grid
        self.by_month_frame.columnconfigure(0, weight=1)
        self.by_month_frame.rowconfigure(0, weight=1)

        # Create treeview
        columns = ("month", "count", "amount")
        self.month_tree = ttk.Treeview(self.by_month_frame, columns=columns, show="headings")

        # Configure columns
        self.month_tree.heading("month", text="Month")
        self.month_tree.heading("count", text="Count")
        self.month_tree.heading("amount", text="Amount")

        self.month_tree.column("month", width=200)
        self.month_tree.column("count", width=100)
        self.month_tree.column("amount", width=100)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.by_month_frame, orient=tk.VERTICAL, command=self.month_tree.yview)
        self.month_tree.configure(yscrollcommand=scrollbar.set)

        # Add to grid
        self.month_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

    def _set_current_month(self) -> None:
        """Set date fields to current month."""
        now = datetime.now()

        # Set start date to first day of current month
        self.start_year_var.set(str(now.year))
        self.start_month_var.set(str(now.month).zfill(2))
        self.start_day_var.set("01")

        # Set end date to current day
        self.end_year_var.set(str(now.year))
        self.end_month_var.set(str(now.month).zfill(2))
        self.end_day_var.set(str(now.day).zfill(2))

    def generate_report(self) -> None:
        """Generate sales report based on selected date range."""
        try:
            # Parse dates
            try:
                start_date = datetime(
                    int(self.start_year_var.get()),
                    int(self.start_month_var.get()),
                    int(self.start_day_var.get())
                )

                end_date = datetime(
                    int(self.end_year_var.get()),
                    int(self.end_month_var.get()),
                    int(self.end_day_var.get()),
                    23, 59, 59  # End of day
                )

                if start_date > end_date:
                    raise ValueError("Start date must be before end date")
            except ValueError as e:
                messagebox.showerror("Date Error", str(e))
                return

            # Generate report
            report = self.execute_service_call(
                lambda: self.analytics_service.get_sales_report(start_date, end_date),
                error_title="Report Error"
            )

            if not report:
                return

            # Store report data
            self.report_data = report

            # Update summary section
            self._update_summary(report)

            # Update by product section
            self._update_by_product(report)

            # Update by month section
            self._update_by_month(report)
        except Exception as e:
            self.logger.error(f"Error generating report: {str(e)}")
            messagebox.showerror("Report Error", f"Error generating report: {str(e)}")

    def _update_summary(self, report: Dict[str, Any]) -> None:
        """Update summary section with report data.

        Args:
            report: Report data
        """
        # Format date range
        start_date = report.get('start_date')
        end_date = report.get('end_date')

        if start_date and end_date:
            if isinstance(start_date, str):
                start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            if isinstance(end_date, str):
                end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))

            date_range = f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
        else:
            date_range = "N/A"

        # Update summary fields
        self.summary_vars['date_range'].set(date_range)
        self.summary_vars['total_sales'].set(f"${report.get('total_sales', 0):.2f}")
        self.summary_vars['total_count'].set(str(report.get('total_count', 0)))
        self.summary_vars['completed_sales'].set(str(report.get('completed_sales', 0)))
        self.summary_vars['cancelled_sales'].set(str(report.get('cancelled_sales', 0)))
        self.summary_vars['completion_rate'].set(f"{report.get('completion_rate', 0):.1f}%")

    def _update_by_product(self, report: Dict[str, Any]) -> None:
        """Update by product section with report data.

        Args:
            report: Report data
        """
        # Clear treeview
        for item in self.product_tree.get_children():
            self.product_tree.delete(item)

        # Add products
        for product in report.get('sales_by_product', []):
            self.product_tree.insert('', 'end', values=(
                product.get('id', 'N/A'),
                product.get('name', 'N/A'),
                product.get('count', 0),
                f"${product.get('amount', 0):.2f}"
            ))

    def _update_by_month(self, report: Dict[str, Any]) -> None:
        """Update by month section with report data.

        Args:
            report: Report data
        """
        # Clear treeview
        for item in self.month_tree.get_children():
            self.month_tree.delete(item)

        # Add months
        for month_data in report.get('time_series', []):
            month = month_data.get('date', 'N/A')
            # Format month (YYYY-MM to Month YYYY)
            if len(month) == 7:  # YYYY-MM format
                try:
                    year = month[:4]
                    month_num = int(month[5:7])
                    month_name = datetime(2000, month_num, 1).strftime('%B')
                    formatted_month = f"{month_name} {year}"
                except ValueError:
                    formatted_month = month
            else:
                formatted_month = month

            self.month_tree.insert('', 'end', values=(
                formatted_month,
                month_data.get('count', 0),
                f"${month_data.get('amount', 0):.2f}"
            ))

    def export_to_csv(self) -> None:
        """Export report data to CSV file."""
        try:
            if not hasattr(self, 'report_data'):
                messagebox.showinfo("Export", "No report data to export")
                return

            # Ask for file location
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                title="Export Sales Report"
            )

            if not file_path:
                return

            # Write report to CSV
            with open(file_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)

                # Write header
                writer.writerow(['Sales Report'])
                writer.writerow([f"Date Range: {self.summary_vars['date_range'].get()}"])
                writer.writerow([f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"])
                writer.writerow([])

                # Write summary
                writer.writerow(['Summary'])
                writer.writerow(['Total Sales', self.summary_vars['total_sales'].get()])
                writer.writerow(['Total Orders', self.summary_vars['total_count'].get()])
                writer.writerow(['Completed Orders', self.summary_vars['completed_sales'].get()])
                writer.writerow(['Cancelled Orders', self.summary_vars['cancelled_sales'].get()])
                writer.writerow(['Completion Rate', self.summary_vars['completion_rate'].get()])
                writer.writerow([])

                # Write sales by product
                writer.writerow(['Sales by Product'])
                writer.writerow(['ID', 'Product', 'Count', 'Amount'])

                for product in self.report_data.get('sales_by_product', []):
                    writer.writerow([
                        product.get('id', 'N/A'),
                        product.get('name', 'N/A'),
                        product.get('count', 0),
                        f"${product.get('amount', 0):.2f}"
                    ])

                writer.writerow([])

                # Write sales by month
                writer.writerow(['Sales by Month'])
                writer.writerow(['Month', 'Count', 'Amount'])

                for month_data in self.report_data.get('time_series', []):
                    month = month_data.get('date', 'N/A')
                    writer.writerow([
                        month,
                        month_data.get('count', 0),
                        f"${month_data.get('amount', 0):.2f}"
                    ])

            messagebox.showinfo("Export Successful", f"Report exported to {os.path.basename(file_path)}")
        except Exception as e:
            self.logger.error(f"Error exporting report: {str(e)}")
            messagebox.showerror("Export Error", f"Error exporting report: {str(e)}")

    def print_report(self) -> None:
        """Print the report."""
        # This is a placeholder - actual printing would require additional libraries
        messagebox.showinfo("Print", "Print functionality would be implemented here")
