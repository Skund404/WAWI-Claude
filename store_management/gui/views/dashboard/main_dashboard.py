# gui/views/dashboard/main_dashboard.py
"""
Main dashboard view for the leatherworking application.

Provides an overview of key metrics, recent activities, and quick actions
for the most common operations in the application.
"""

import logging
import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
import math
from typing import Any, Dict, List, Optional

from di import resolve
from gui.config import DATE_FORMAT
from gui.theme import COLORS, get_status_style

logger = logging.getLogger(__name__)


class DashboardView:
    """
    Main dashboard view showing key metrics and providing quick access to common actions.
    """

    def __init__(self, parent):
        """
        Initialize the dashboard view.

        Args:
            parent: The parent widget
        """
        self.parent = parent
        self.title = "Dashboard"
        self.description = "Overview of your leatherworking business"
        self.logger = logging.getLogger(__name__)

        # Initialize data containers
        self.inventory_stats = {}
        self.project_stats = {}
        self.sales_stats = {}
        self.purchase_stats = {}

        # Track reference to charts/widgets that need updates
        self.kpi_widgets = {}
        self.chart_frames = {}

        # Subscribe to events
        # Note: This would require an event bus implementation
        # For now, we'll just load data on init and offer a refresh method

    def build(self):
        """Build the dashboard view layout."""
        # Create main dashboard layout
        main_frame = ttk.Frame(self.parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create header
        self.create_header(main_frame)

        # Create main content with 2-column layout
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Left column - KPIs and Actions
        left_column = ttk.Frame(content_frame)
        left_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        self.create_kpi_section(left_column)
        self.create_quick_actions(left_column)
        self.create_recent_activities(left_column)

        # Right column - Charts and Status
        right_column = ttk.Frame(content_frame)
        right_column.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        self.create_inventory_status_section(right_column)
        self.create_project_status_section(right_column)

        # Bottom section - spans both columns
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X, expand=False, pady=(10, 0))

        self.create_upcoming_section(bottom_frame)

        # Load the data
        self.load_data()

    def create_header(self, parent):
        """
        Create a header for the dashboard.

        Args:
            parent: The parent widget
        """
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill=tk.X, expand=False, pady=(0, 10))

        # Dashboard title
        title_label = ttk.Label(
            header_frame,
            text="Dashboard",
            font=("", 18, "bold")
        )
        title_label.pack(side=tk.LEFT)

        # Add refresh button
        refresh_button = ttk.Button(
            header_frame,
            text="Refresh",
            command=self.refresh
        )
        refresh_button.pack(side=tk.RIGHT)

    def create_kpi_section(self, parent):
        """
        Create the KPI widgets section.

        Args:
            parent: The parent widget
        """
        kpi_frame = ttk.LabelFrame(parent, text="Key Metrics")
        kpi_frame.pack(fill=tk.X, expand=False, pady=(0, 10))

        # Create grid layout for KPIs
        for i in range(2):
            kpi_frame.columnconfigure(i, weight=1)

        # Sales KPI
        sales_frame = self._create_kpi_widget(
            kpi_frame,
            "Monthly Sales",
            "$0.00",
            "0% vs last month",
            row=0, column=0
        )
        self.kpi_widgets["sales"] = sales_frame

        # Projects KPI
        projects_frame = self._create_kpi_widget(
            kpi_frame,
            "Active Projects",
            "0",
            "0 completed this month",
            row=0, column=1
        )
        self.kpi_widgets["projects"] = projects_frame

        # Inventory KPI
        inventory_frame = self._create_kpi_widget(
            kpi_frame,
            "Inventory Value",
            "$0.00",
            "0 items low stock",
            row=1, column=0
        )
        self.kpi_widgets["inventory"] = inventory_frame

        # Purchases KPI
        purchases_frame = self._create_kpi_widget(
            kpi_frame,
            "Pending Orders",
            "0",
            "$0.00 pending receipt",
            row=1, column=1
        )
        self.kpi_widgets["purchases"] = purchases_frame

    def _create_kpi_widget(self, parent, title, value, subtitle, row, column):
        """
        Create a single KPI widget.

        Args:
            parent: The parent widget
            title: KPI title
            value: KPI value
            subtitle: KPI subtitle/context
            row: Grid row
            column: Grid column

        Returns:
            Frame containing the KPI widget references
        """
        frame = ttk.Frame(parent, padding=10)
        frame.grid(row=row, column=column, sticky="nsew", padx=5, pady=5)

        # Title
        title_label = ttk.Label(
            frame,
            text=title,
            font=("", 10),
            foreground=COLORS["text_secondary"]
        )
        title_label.pack(anchor="w")

        # Value
        value_label = ttk.Label(
            frame,
            text=value,
            font=("", 24, "bold")
        )
        value_label.pack(anchor="w")

        # Subtitle
        subtitle_label = ttk.Label(
            frame,
            text=subtitle,
            font=("", 9),
            foreground=COLORS["text_secondary"]
        )
        subtitle_label.pack(anchor="w")

        return {
            "frame": frame,
            "title": title_label,
            "value": value_label,
            "subtitle": subtitle_label
        }

    def create_quick_actions(self, parent):
        """
        Create quick action buttons.

        Args:
            parent: The parent widget
        """
        actions_frame = ttk.LabelFrame(parent, text="Quick Actions")
        actions_frame.pack(fill=tk.X, expand=False, pady=(0, 10))

        # Create grid layout for action buttons
        for i in range(2):
            actions_frame.columnconfigure(i, weight=1)

        # New Project
        new_project_btn = ttk.Button(
            actions_frame,
            text="New Project",
            command=self.on_new_project
        )
        new_project_btn.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

        # New Sale
        new_sale_btn = ttk.Button(
            actions_frame,
            text="New Sale",
            command=self.on_new_sale
        )
        new_sale_btn.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        # Add Inventory
        add_inventory_btn = ttk.Button(
            actions_frame,
            text="Add Inventory",
            command=self.on_add_inventory
        )
        add_inventory_btn.grid(row=1, column=0, sticky="ew", padx=5, pady=5)

        # New Purchase
        new_purchase_btn = ttk.Button(
            actions_frame,
            text="New Purchase",
            command=self.on_new_purchase
        )
        new_purchase_btn.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

    def create_recent_activities(self, parent):
        """
        Create recent activities section.

        Args:
            parent: The parent widget
        """
        activities_frame = ttk.LabelFrame(parent, text="Recent Activities")
        activities_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Create treeview for recent activities
        columns = ("timestamp", "type", "description")
        self.activities_tree = ttk.Treeview(
            activities_frame,
            columns=columns,
            show="headings",
            selectmode="browse",
            height=6
        )

        # Define headings
        self.activities_tree.heading("timestamp", text="Time")
        self.activities_tree.heading("type", text="Type")
        self.activities_tree.heading("description", text="Description")

        # Define columns
        self.activities_tree.column("timestamp", width=100)
        self.activities_tree.column("type", width=100)
        self.activities_tree.column("description", width=300)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(
            activities_frame,
            orient=tk.VERTICAL,
            command=self.activities_tree.yview
        )
        self.activities_tree.configure(yscrollcommand=scrollbar.set)

        # Pack widgets
        self.activities_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind double-click to view activity details
        self.activities_tree.bind("<Double-1>", self.on_activity_selected)

    def create_inventory_status_section(self, parent):
        """
        Create inventory status section with charts.

        Args:
            parent: The parent widget
        """
        inventory_frame = ttk.LabelFrame(parent, text="Inventory Status")
        inventory_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Status overview frame
        status_frame = ttk.Frame(inventory_frame, padding=5)
        status_frame.pack(fill=tk.X, expand=False)

        # Status indicators
        self.inventory_status = {
            "in_stock": self._create_status_indicator(status_frame, "In Stock", "0", 0),
            "low_stock": self._create_status_indicator(status_frame, "Low Stock", "0", 1),
            "out_of_stock": self._create_status_indicator(status_frame, "Out of Stock", "0", 2)
        }

        # Placeholder for chart
        chart_frame = ttk.Frame(inventory_frame, padding=5)
        chart_frame.pack(fill=tk.BOTH, expand=True)

        # Add a label for now (in a real app, this would be a chart)
        chart_placeholder = ttk.Label(
            chart_frame,
            text="Inventory Distribution by Category",
            font=("", 12, "bold"),
            anchor="center"
        )
        chart_placeholder.pack(pady=20)

        # Placeholder for the chart
        canvas = tk.Canvas(chart_frame, bg=COLORS["background"], height=150)
        canvas.pack(fill=tk.BOTH, expand=True)

        # Save reference for updating
        self.chart_frames["inventory"] = {
            "frame": chart_frame,
            "canvas": canvas
        }

    def create_project_status_section(self, parent):
        """
        Create project status section with charts.

        Args:
            parent: The parent widget
        """
        project_frame = ttk.LabelFrame(parent, text="Project Status")
        project_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Status overview frame
        status_frame = ttk.Frame(project_frame, padding=5)
        status_frame.pack(fill=tk.X, expand=False)

        # Status indicators
        self.project_status = {
            "planning": self._create_status_indicator(status_frame, "Planning", "0", 0),
            "in_progress": self._create_status_indicator(status_frame, "In Progress", "0", 1),
            "completed": self._create_status_indicator(status_frame, "Completed", "0", 2)
        }

        # Placeholder for chart
        chart_frame = ttk.Frame(project_frame, padding=5)
        chart_frame.pack(fill=tk.BOTH, expand=True)

        # Add a label for now (in a real app, this would be a chart)
        chart_placeholder = ttk.Label(
            chart_frame,
            text="Project Timeline Overview",
            font=("", 12, "bold"),
            anchor="center"
        )
        chart_placeholder.pack(pady=20)

        # Placeholder for the chart
        canvas = tk.Canvas(chart_frame, bg=COLORS["background"], height=150)
        canvas.pack(fill=tk.BOTH, expand=True)

        # Save reference for updating
        self.chart_frames["projects"] = {
            "frame": chart_frame,
            "canvas": canvas
        }

    def _create_status_indicator(self, parent, label, value, column):
        """
        Create a status indicator with label and value.

        Args:
            parent: The parent widget
            label: Status label
            value: Status value
            column: Grid column

        Returns:
            Dictionary with references to the indicator widgets
        """
        frame = ttk.Frame(parent, padding=5)
        frame.grid(row=0, column=column, sticky="ew", padx=5)

        value_label = ttk.Label(
            frame,
            text=value,
            font=("", 18, "bold")
        )
        value_label.pack(anchor="center")

        text_label = ttk.Label(
            frame,
            text=label,
            font=("", 9),
            foreground=COLORS["text_secondary"]
        )
        text_label.pack(anchor="center")

        return {
            "frame": frame,
            "value": value_label,
            "label": text_label
        }

    def create_upcoming_section(self, parent):
        """
        Create upcoming deadlines/events section.

        Args:
            parent: The parent widget
        """
        upcoming_frame = ttk.LabelFrame(parent, text="Upcoming Deadlines")
        upcoming_frame.pack(fill=tk.X, expand=False)

        # Create 4-column layout
        for i in range(4):
            upcoming_frame.columnconfigure(i, weight=1)

        # Placeholders for upcoming deadlines
        placeholders = [
            {"title": "Client Meeting", "date": "Tomorrow, 10:00 AM", "type": "Meeting"},
            {"title": "Belt Order Due", "date": "Mar 14, 2025", "type": "Order"},
            {"title": "Leather Shipment", "date": "Mar 15, 2025", "type": "Delivery"},
            {"title": "Inventory Audit", "date": "Mar 20, 2025", "type": "Task"}
        ]

        # Create deadline cards
        for i, item in enumerate(placeholders):
            self._create_deadline_card(upcoming_frame, item, i)

    def _create_deadline_card(self, parent, data, column):
        """
        Create a card for an upcoming deadline or event.

        Args:
            parent: The parent widget
            data: Dictionary with deadline data
            column: Grid column
        """
        frame = ttk.Frame(parent, padding=10)
        frame.grid(row=0, column=column, sticky="nsew", padx=5, pady=5)

        # Type badge
        type_frame = ttk.Frame(frame)
        type_frame.pack(fill=tk.X, anchor="w")

        type_label = ttk.Label(
            type_frame,
            text=data["type"],
            padding=(5, 2),
            background=COLORS["primary_light"],
            foreground=COLORS["primary"]
        )
        type_label.pack(side=tk.LEFT)

        # Title
        title_label = ttk.Label(
            frame,
            text=data["title"],
            font=("", 11, "bold"),
            wraplength=150
        )
        title_label.pack(anchor="w", pady=(5, 0))

        # Date
        date_label = ttk.Label(
            frame,
            text=data["date"],
            font=("", 9),
            foreground=COLORS["text_secondary"]
        )
        date_label.pack(anchor="w")

    def load_data(self):
        """Load dashboard data from services."""
        try:
            # Load inventory statistics
            self.load_inventory_stats()

            # Load project statistics
            self.load_project_stats()

            # Load sales statistics
            self.load_sales_stats()

            # Load purchase statistics
            self.load_purchase_stats()

            # Load recent activities
            self.load_recent_activities()

            # Update the dashboard with loaded data
            self.update_dashboard()

            self.logger.info("Dashboard data loaded successfully")
        except Exception as e:
            self.logger.error(f"Error loading dashboard data: {str(e)}")
            # We don't have access to a show_error method, so we'll just log it

    def load_inventory_stats(self):
        """Load inventory statistics from inventory service."""
        try:
            # Use safe service access
            try:
                inventory_service = resolve("IInventoryService")
            except Exception:
                # If service is not available, use placeholder data
                self.inventory_stats = {
                    "total_value": 12500.00,
                    "total_items": 356,
                    "low_stock_count": 12,
                    "out_of_stock_count": 3,
                    "in_stock_count": 341,
                    "categories": {
                        "Leather": 25,
                        "Hardware": 120,
                        "Supplies": 211
                    }
                }
                return

            # If service is available, get actual data
            self.inventory_stats = {
                "total_value": inventory_service.get_total_inventory_value(),
                "total_items": inventory_service.get_total_inventory_count(),
                "low_stock_count": inventory_service.get_low_stock_count(),
                "out_of_stock_count": inventory_service.get_out_of_stock_count(),
                "in_stock_count": inventory_service.get_in_stock_count(),
                "categories": inventory_service.get_inventory_by_category()
            }
        except Exception as e:
            self.logger.error(f"Error loading inventory statistics: {str(e)}")
            # Use placeholder data on error
            self.inventory_stats = {
                "total_value": 12500.00,
                "total_items": 356,
                "low_stock_count": 12,
                "out_of_stock_count": 3,
                "in_stock_count": 341,
                "categories": {
                    "Leather": 25,
                    "Hardware": 120,
                    "Supplies": 211
                }
            }

    def load_project_stats(self):
        """Load project statistics from project service."""
        try:
            # Use safe service access
            try:
                project_service = resolve("IProjectService")
            except Exception:
                # If service is not available, use placeholder data
                self.project_stats = {
                    "active_count": 8,
                    "completed_this_month": 3,
                    "by_status": {
                        "planning": 2,
                        "initial_consultation": 1,
                        "in_progress": 3,
                        "assembly": 2,
                        "completed": 3,
                        "on_hold": 1
                    },
                    "upcoming_deadlines": []
                }
                return

            # If service is available, get actual data
            self.project_stats = {
                "active_count": project_service.get_active_project_count(),
                "completed_this_month": project_service.get_completed_project_count_for_period(
                    datetime.now().replace(day=1),
                    datetime.now()
                ),
                "by_status": project_service.get_projects_by_status(),
                "upcoming_deadlines": project_service.get_upcoming_deadlines(limit=5)
            }
        except Exception as e:
            self.logger.error(f"Error loading project statistics: {str(e)}")
            # Use placeholder data on error
            self.project_stats = {
                "active_count": 8,
                "completed_this_month": 3,
                "by_status": {
                    "planning": 2,
                    "initial_consultation": 1,
                    "in_progress": 3,
                    "assembly": 2,
                    "completed": 3,
                    "on_hold": 1
                },
                "upcoming_deadlines": []
            }

    def load_sales_stats(self):
        """Load sales statistics from sales service."""
        try:
            # Use safe service access
            try:
                sales_service = resolve("ISalesService")
            except Exception:
                # If service is not available, use placeholder data
                self.sales_stats = {
                    "current_month": 4250.00,
                    "prev_month": 3980.00,
                    "percentage_change": 6.8,
                    "recent_sales": []
                }
                return

            # Calculate date ranges
            today = datetime.now()
            start_of_month = today.replace(day=1)
            start_of_prev_month = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
            end_of_prev_month = today.replace(day=1) - timedelta(days=1)

            # Get sales statistics
            current_month_sales = sales_service.get_total_sales_for_period(
                start_of_month,
                today
            )

            prev_month_sales = sales_service.get_total_sales_for_period(
                start_of_prev_month,
                end_of_prev_month
            )

            # Calculate change percentage
            if prev_month_sales and prev_month_sales > 0:
                percentage_change = ((current_month_sales - prev_month_sales) / prev_month_sales) * 100
            else:
                percentage_change = 0

            self.sales_stats = {
                "current_month": current_month_sales,
                "prev_month": prev_month_sales,
                "percentage_change": percentage_change,
                "recent_sales": sales_service.get_recent_sales(limit=5)
            }
        except Exception as e:
            self.logger.error(f"Error loading sales statistics: {str(e)}")
            # Use placeholder data on error
            self.sales_stats = {
                "current_month": 4250.00,
                "prev_month": 3980.00,
                "percentage_change": 6.8,
                "recent_sales": []
            }

    def load_purchase_stats(self):
        """Load purchase statistics from purchase service."""
        try:
            # Use safe service access
            try:
                purchase_service = resolve("IPurchaseService")
            except Exception:
                # If service is not available, use placeholder data
                self.purchase_stats = {
                    "pending_count": 3,
                    "pending_amount": 1250.00,
                    "recent_purchases": []
                }
                return

            # Get purchase statistics
            self.purchase_stats = {
                "pending_count": purchase_service.get_pending_purchase_count(),
                "pending_amount": purchase_service.get_pending_purchase_amount(),
                "recent_purchases": purchase_service.get_recent_purchases(limit=5)
            }
        except Exception as e:
            self.logger.error(f"Error loading purchase statistics: {str(e)}")
            # Use placeholder data on error
            self.purchase_stats = {
                "pending_count": 3,
                "pending_amount": 1250.00,
                "recent_purchases": []
            }

    def load_recent_activities(self):
        """Load recent activities from various services."""
        try:
            # Clear existing activities
            for item in self.activities_tree.get_children():
                self.activities_tree.delete(item)

            # Since we might not have access to all services, use placeholder data
            activities = [
                {
                    "timestamp": datetime.now() - timedelta(hours=1),
                    "type": "Inventory",
                    "description": "Added 5 sq ft of Veg Tan Leather",
                    "id": "1",
                    "source": "inventory"
                },
                {
                    "timestamp": datetime.now() - timedelta(hours=2),
                    "type": "Project",
                    "description": "Wallet Project moved to Assembly",
                    "id": "2",
                    "source": "project"
                },
                {
                    "timestamp": datetime.now() - timedelta(hours=5),
                    "type": "Sale",
                    "description": "New sale: $120.00 - Custom Belt",
                    "id": "3",
                    "source": "sale"
                },
                {
                    "timestamp": datetime.now() - timedelta(hours=8),
                    "type": "Purchase",
                    "description": "Ordered hardware from Buckleguy",
                    "id": "4",
                    "source": "purchase"
                },
                {
                    "timestamp": datetime.now() - timedelta(days=1),
                    "type": "Project",
                    "description": "Messenger Bag Project completed",
                    "id": "5",
                    "source": "project"
                },
                {
                    "timestamp": datetime.now() - timedelta(days=1, hours=4),
                    "type": "Inventory",
                    "description": "Low stock alert: 1/4\" Copper Rivets",
                    "id": "6",
                    "source": "inventory"
                }
            ]

            # Add to treeview
            for i, activity in enumerate(activities):
                timestamp_str = activity["timestamp"].strftime("%m/%d %H:%M")
                self.activities_tree.insert(
                    "",
                    "end",
                    iid=str(i),
                    values=(timestamp_str, activity["type"], activity["description"]),
                    tags=(activity["source"],)
                )

                # Store the activity data for retrieval
                self.activities_tree.item(str(i), tags=(activity["source"], str(activity["id"])))

        except Exception as e:
            self.logger.error(f"Error loading recent activities: {str(e)}")

    def update_dashboard(self):
        """Update dashboard widgets with loaded data."""
        # Update KPI widgets
        self._update_kpi_widgets()

        # Update inventory status indicators
        self._update_inventory_status()

        # Update project status indicators
        self._update_project_status()

        # Update charts
        self._update_charts()

    def _update_kpi_widgets(self):
        """Update KPI widgets with current statistics."""
        # Update Sales KPI
        sales_kpi = self.kpi_widgets["sales"]
        sales_kpi["value"].config(text=f"${self.sales_stats['current_month']:.2f}")

        change_text = f"{self.sales_stats['percentage_change']:.1f}% vs last month"
        sales_kpi["subtitle"].config(text=change_text)

        # Update Projects KPI
        projects_kpi = self.kpi_widgets["projects"]
        projects_kpi["value"].config(text=str(self.project_stats["active_count"]))

        completed_text = f"{self.project_stats['completed_this_month']} completed this month"
        projects_kpi["subtitle"].config(text=completed_text)

        # Update Inventory KPI
        inventory_kpi = self.kpi_widgets["inventory"]
        inventory_kpi["value"].config(text=f"${self.inventory_stats['total_value']:.2f}")

        low_stock_text = f"{self.inventory_stats['low_stock_count']} items low stock"
        inventory_kpi["subtitle"].config(text=low_stock_text)

        # Update Purchases KPI
        purchases_kpi = self.kpi_widgets["purchases"]
        purchases_kpi["value"].config(text=str(self.purchase_stats["pending_count"]))

        pending_text = f"${self.purchase_stats['pending_amount']:.2f} pending receipt"
        purchases_kpi["subtitle"].config(text=pending_text)

    def _update_inventory_status(self):
        """Update inventory status indicators."""
        # Update in stock count
        self.inventory_status["in_stock"]["value"].config(
            text=str(self.inventory_stats["in_stock_count"])
        )

        # Update low stock count
        self.inventory_status["low_stock"]["value"].config(
            text=str(self.inventory_stats["low_stock_count"])
        )

        # Update out of stock count
        self.inventory_status["out_of_stock"]["value"].config(
            text=str(self.inventory_stats["out_of_stock_count"])
        )

    def _update_project_status(self):
        """Update project status indicators."""
        # Get project status counts
        status_counts = self.project_stats["by_status"]

        # Update planning count
        planning_count = status_counts.get("planning", 0) + status_counts.get("initial_consultation", 0)
        self.project_status["planning"]["value"].config(text=str(planning_count))

        # Update in progress count
        in_progress_count = status_counts.get("in_progress", 0) + status_counts.get("assembly", 0)
        self.project_status["in_progress"]["value"].config(text=str(in_progress_count))

        # Update completed count
        completed_count = status_counts.get("completed", 0)
        self.project_status["completed"]["value"].config(text=str(completed_count))

    def _update_charts(self):
        """Update chart visualizations."""
        # In a real application, we would update the charts with actual data
        # For now, we'll just use placeholders

        # Update inventory chart (placeholder)
        self._draw_inventory_chart()

        # Update project chart (placeholder)
        self._draw_project_chart()

    def _draw_inventory_chart(self):
        """Draw inventory distribution chart (placeholder)."""
        canvas = self.chart_frames["inventory"]["canvas"]

        # Clear canvas
        canvas.delete("all")

        # Get categories data
        categories = self.inventory_stats.get("categories", {})
        if not categories:
            # Draw placeholder text
            canvas.create_text(
                canvas.winfo_width() // 2,
                canvas.winfo_height() // 2,
                text="No inventory data available",
                fill=COLORS["text_secondary"]
            )
            return

        # In a real application, this would draw a proper chart
        # For now, we'll draw a simple bar chart

        # Set up chart dimensions
        width = max(canvas.winfo_width(), 300)
        height = max(canvas.winfo_height(), 100)
        margin = 20
        bar_width = 30
        spacing = 10
        max_height = height - 2 * margin

        # Get max value for scaling
        max_value = max(categories.values()) if categories else 1

        # Draw bars
        x = margin
        for category, count in categories.items():
            # Calculate bar height
            bar_height = (count / max_value) * max_height
            y1 = height - margin - bar_height
            y2 = height - margin

            # Draw bar
            canvas.create_rectangle(
                x, y1, x + bar_width, y2,
                fill=COLORS["primary"],
                outline=""
            )

            # Draw category label
            canvas.create_text(
                x + bar_width // 2,
                y2 + 15,
                text=category[:10],
                fill=COLORS["text_secondary"],
                angle=90,
                anchor="w"
            )

            # Draw count
            canvas.create_text(
                x + bar_width // 2,
                y1 - 10,
                text=str(count),
                fill=COLORS["text"]
            )

            # Move to next bar
            x += bar_width + spacing

    def _draw_project_chart(self):
        """Draw project timeline overview chart (placeholder)."""
        canvas = self.chart_frames["projects"]["canvas"]

        # Clear canvas
        canvas.delete("all")

        # Get status data
        status_counts = self.project_stats.get("by_status", {})
        if not status_counts:
            # Draw placeholder text
            canvas.create_text(
                canvas.winfo_width() // 2,
                canvas.winfo_height() // 2,
                text="No project data available",
                fill=COLORS["text_secondary"]
            )
            return

        # In a real application, this would draw a proper chart
        # For now, we'll draw a simple pie chart

        # Set up chart dimensions
        width = max(canvas.winfo_width(), 300)
        height = max(canvas.winfo_height(), 100)
        center_x = width // 2
        center_y = height // 2
        radius = min(center_x, center_y) - 20

        # Calculate total for percentages
        total = sum(status_counts.values())

        # Colors for different statuses
        status_colors = {
            "initial_consultation": "#4CAF50",
            "design_phase": "#8BC34A",
            "pattern_development": "#CDDC39",
            "material_selection": "#FFEB3B",
            "cutting": "#FFC107",
            "assembly": "#FF9800",
            "stitching": "#FF5722",
            "quality_check": "#795548",
            "completed": "#607D8B",
            "on_hold": "#9E9E9E",
            "cancelled": "#F44336",
            "planning": "#2196F3",
            "in_progress": "#FF9800"
        }

        # Draw segments
        start_angle = 0
        for status, count in status_counts.items():
            # Calculate angle
            angle = (count / total) * 360
            end_angle = start_angle + angle

            # Get color
            color = status_colors.get(status, "#2196F3")

            # Draw segment
            canvas.create_arc(
                center_x - radius, center_y - radius,
                center_x + radius, center_y + radius,
                start=start_angle, extent=angle,
                fill=color, outline="white", width=1
            )

            # Calculate text position
            # Position text in the middle of the segment
            text_angle = math.radians((start_angle + end_angle) / 2)
            text_radius = radius * 0.7
            text_x = center_x + text_radius * math.cos(text_angle)
            text_y = center_y + text_radius * math.sin(text_angle)

            # Draw count if segment is large enough
            if angle > 30:
                canvas.create_text(
                    text_x, text_y,
                    text=str(count),
                    fill="white"
                )

            # Move to next segment
            start_angle = end_angle

    def on_activity_selected(self, event):
        """
        Handle activity selection (double-click).

        Args:
            event: The event object
        """
        # Get selected item
        selected_item = self.activities_tree.focus()
        if not selected_item:
            return

        # Get item tags (source and id)
        tags = self.activities_tree.item(selected_item, "tags")
        if not tags or len(tags) < 2:
            return

        source, item_id = tags

        # Navigate to the appropriate view based on the source
        # Get the main window
        main_window = self.parent.winfo_toplevel()

        if source == "inventory":
            main_window.show_view("inventory")
        elif source == "project":
            main_window.show_view("projects")
        elif source == "sale":
            main_window.show_view("sales")
        elif source == "purchase":
            main_window.show_view("purchases")

    def on_new_project(self):
        """Handle new project action."""
        # Navigate to projects view and trigger new project action
        main_window = self.parent.winfo_toplevel()
        main_window.create_new_project()

    def on_new_sale(self):
        """Handle new sale action."""
        # Navigate to sales view and trigger new sale action
        main_window = self.parent.winfo_toplevel()
        main_window.create_new_sale()

    def on_add_inventory(self):
        """Handle add inventory action."""
        # Navigate to inventory view
        main_window = self.parent.winfo_toplevel()
        main_window.show_view("inventory")

    def on_new_purchase(self):
        """Handle new purchase action."""
        # Navigate to purchases view and trigger new purchase action
        main_window = self.parent.winfo_toplevel()
        main_window.create_new_purchase()

    def refresh(self):
        """Refresh the dashboard data."""
        self.load_data()