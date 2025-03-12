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
from typing import Any, Dict, List, Optional, Tuple

from di import resolve
from gui.config import DATE_FORMAT
from gui.theme import COLORS, get_status_style
from gui.widgets.charts import create_bar_chart, create_pie_chart, create_line_chart
from gui.widgets.charts.heatmap import HeatmapChart  # Import the heatmap chart
from gui.utils.event_bus import subscribe, unsubscribe, publish
from gui.utils.service_access import with_service
from gui.utils.view_history_manager import ViewHistoryManager
from gui.widgets.breadcrumb_navigation import BreadcrumbNavigation
from gui.widgets.status_badge import StatusBadge

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
        self.analytics_summary = None

        # Track reference to charts/widgets that need updates
        self.kpi_widgets = {}
        self.chart_widgets = {}

        # Container frames for sections
        self.content_frame = None
        self.left_column = None
        self.right_column = None
        self.bottom_frame = None

        # Add breadcrumb navigation
        self.breadcrumb_nav = None

        # Track view history for navigation
        self.view_history = None

        # Build the view
        self.build()

        # Subscribe to events
        self._subscribe_to_events()

        # Load the data
        self.load_data()

    def build(self):
        """Build the dashboard view layout."""
        # Create main dashboard container with padding
        main_frame = ttk.Frame(self.parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # Create header
        self.create_header(main_frame)

        # Create a canvas for scrolling
        canvas = tk.Canvas(main_frame, bg=main_frame.cget("background"))
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Create main content frame inside canvas for scrolling
        self.content_frame = ttk.Frame(canvas)
        canvas_frame = canvas.create_window((0, 0), window=self.content_frame, anchor=tk.NW)

        # Configure canvas scrolling
        self.content_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_frame, width=e.width))

        # Create 2-column layout for content
        columns_frame = ttk.Frame(self.content_frame)
        columns_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Left column - KPIs and Actions
        self.left_column = ttk.Frame(columns_frame)
        self.left_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))

        # Right column - Charts and Status
        self.right_column = ttk.Frame(columns_frame)
        self.right_column.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(8, 0))

        # Bottom section - spans both columns
        self.bottom_frame = ttk.Frame(self.content_frame)
        self.bottom_frame.pack(fill=tk.X, expand=False, pady=(10, 0))

        # Create dashboard sections
        self.create_kpi_section(self.left_column)
        self.create_quick_actions(self.left_column)
        self.create_recent_activities(self.left_column)

        self.create_inventory_status_section(self.right_column)
        self.create_project_status_section(self.right_column)
        self.create_analytics_section(self.right_column)

        self.create_upcoming_section(self.bottom_frame)

        # Initialize breadcrumb navigation
        self.init_breadcrumb_navigation()

    def create_header(self, parent):
        """
        Create a header for the dashboard.

        Args:
            parent: The parent widget
        """
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill=tk.X, expand=False, pady=(0, 15))

        # Add breadcrumb navigation at the top
        breadcrumb_frame = ttk.Frame(header_frame)
        breadcrumb_frame.pack(fill=tk.X, pady=(0, 10))

        self.breadcrumb_nav = BreadcrumbNavigation(breadcrumb_frame, callback=self._navigate_to_breadcrumb)
        self.breadcrumb_nav.pack(fill=tk.X)
        self.breadcrumb_nav.set_home_breadcrumb("Dashboard", "dashboard")

        # Left section - title and description
        title_frame = ttk.Frame(header_frame)
        title_frame.pack(side=tk.LEFT, fill=tk.Y)

        # Dashboard title
        title_label = ttk.Label(
            title_frame,
            text=self.title,
            font=("", 22, "bold")
        )
        title_label.pack(side=tk.TOP, anchor=tk.W)

        # Dashboard description
        desc_label = ttk.Label(
            title_frame,
            text=self.description,
            font=("", 11),
            foreground=COLORS["text_secondary"]
        )
        desc_label.pack(side=tk.TOP, anchor=tk.W)

        # Right section - action buttons
        action_frame = ttk.Frame(header_frame)
        action_frame.pack(side=tk.RIGHT, fill=tk.Y)

        # Analytics button
        analytics_button = ttk.Button(
            action_frame,
            text="View Analytics",
            command=self._open_analytics_dashboard
        )
        analytics_button.pack(side=tk.LEFT, padx=(0, 10))

        # Refresh button
        refresh_button = ttk.Button(
            action_frame,
            text="Refresh",
            command=self.refresh
        )
        refresh_button.pack(side=tk.LEFT)

        # Export dashboard button (new)
        export_button = ttk.Button(
            action_frame,
            text="Export Dashboard",
            command=self._export_dashboard
        )
        export_button.pack(side=tk.LEFT, padx=(10, 0))

    def create_kpi_section(self, parent):
        """
        Create the KPI widgets section.

        Args:
            parent: The parent widget
        """
        kpi_frame = ttk.LabelFrame(parent, text="Key Metrics")
        kpi_frame.pack(fill=tk.X, expand=False, pady=(0, 15))

        # Create grid layout for KPIs
        for i in range(2):
            kpi_frame.columnconfigure(i, weight=1)

        # Sales KPI
        sales_frame = self._create_kpi_widget(
            kpi_frame,
            "Monthly Sales",
            "$0.00",
            "0% vs last month",
            row=0, column=0,
            icon="sales",
            trend=0  # No trend initially
        )
        self.kpi_widgets["sales"] = sales_frame

        # Projects KPI
        projects_frame = self._create_kpi_widget(
            kpi_frame,
            "Active Projects",
            "0",
            "0 completed this month",
            row=0, column=1,
            icon="projects",
            trend=0  # No trend initially
        )
        self.kpi_widgets["projects"] = projects_frame

        # Inventory KPI
        inventory_frame = self._create_kpi_widget(
            kpi_frame,
            "Inventory Value",
            "$0.00",
            "0 items low stock",
            row=1, column=0,
            icon="inventory",
            trend=0  # No trend initially
        )
        self.kpi_widgets["inventory"] = inventory_frame

        # Purchases KPI
        purchases_frame = self._create_kpi_widget(
            kpi_frame,
            "Pending Orders",
            "0",
            "$0.00 pending receipt",
            row=1, column=1,
            icon="purchases",
            trend=0  # No trend initially
        )
        self.kpi_widgets["purchases"] = purchases_frame

    def _create_kpi_widget(self, parent, title, value, subtitle, row, column, icon=None, trend=0):
        """
        Create a single KPI widget.

        Args:
            parent: The parent widget
            title: KPI title
            value: KPI value
            subtitle: KPI subtitle/context
            row: Grid row
            column: Grid column
            icon: Optional icon identifier
            trend: Trend indicator value (positive, negative, or zero)

        Returns:
            Frame containing the KPI widget references
        """
        # Create main frame with border styling
        frame = ttk.Frame(parent, padding=15, style="Card.TFrame")
        frame.grid(row=row, column=column, sticky="nsew", padx=5, pady=5)

        # Header frame with title and icon
        header_frame = ttk.Frame(frame)
        header_frame.pack(fill=tk.X, expand=False, pady=(0, 8))

        # Add icon (would be implemented with proper icon widget in real app)
        if icon:
            # Placeholder for icon
            icon_frame = ttk.Label(
                header_frame,
                text="•",  # Placeholder icon
                font=("", 14),
                foreground=COLORS["primary"]
            )
            icon_frame.pack(side=tk.LEFT, padx=(0, 5))

        # Title
        title_label = ttk.Label(
            header_frame,
            text=title,
            font=("", 11),
            foreground=COLORS["text_secondary"]
        )
        title_label.pack(side=tk.LEFT)

        # Value with trend indicator
        value_frame = ttk.Frame(frame)
        value_frame.pack(fill=tk.X, expand=False)

        value_label = ttk.Label(
            value_frame,
            text=value,
            font=("", 24, "bold")
        )
        value_label.pack(side=tk.LEFT)

        # Trend indicator
        if trend != 0:
            trend_symbol = "↑" if trend > 0 else "↓"
            trend_color = COLORS["success"] if trend > 0 else COLORS["danger"]

            trend_label = ttk.Label(
                value_frame,
                text=f" {trend_symbol}",
                font=("", 16),
                foreground=trend_color
            )
            trend_label.pack(side=tk.LEFT, padx=(5, 0), pady=(0, 5))
        else:
            trend_label = None

        # Subtitle
        subtitle_label = ttk.Label(
            frame,
            text=subtitle,
            font=("", 9),
            foreground=COLORS["text_secondary"]
        )
        subtitle_label.pack(anchor="w", pady=(5, 0))

        return {
            "frame": frame,
            "title": title_label,
            "value": value_label,
            "subtitle": subtitle_label,
            "trend": trend_label
        }

    def create_quick_actions(self, parent):
        """
        Create quick action buttons.

        Args:
            parent: The parent widget
        """
        actions_frame = ttk.LabelFrame(parent, text="Quick Actions")
        actions_frame.pack(fill=tk.X, expand=False, pady=(0, 15))

        # Create grid layout for action buttons
        for i in range(2):
            actions_frame.columnconfigure(i, weight=1)

        # New Project
        new_project_btn = ttk.Button(
            actions_frame,
            text="New Project",
            style="Accent.TButton",
            command=self.on_new_project
        )
        new_project_btn.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

        # New Sale
        new_sale_btn = ttk.Button(
            actions_frame,
            text="New Sale",
            style="Accent.TButton",
            command=self.on_new_sale
        )
        new_sale_btn.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        # Add Inventory
        add_inventory_btn = ttk.Button(
            actions_frame,
            text="Add Inventory",
            style="Accent.TButton",
            command=self.on_add_inventory
        )
        add_inventory_btn.grid(row=1, column=0, sticky="ew", padx=5, pady=5)

        # New Purchase
        new_purchase_btn = ttk.Button(
            actions_frame,
            text="New Purchase",
            style="Accent.TButton",
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
        activities_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        # Create header with view all button
        header_frame = ttk.Frame(activities_frame, padding=(0, 0, 0, 5))
        header_frame.pack(fill=tk.X, expand=False)

        view_all_btn = ttk.Button(
            header_frame,
            text="View All",
            style="Link.TButton",
            command=self._view_all_activities
        )
        view_all_btn.pack(side=tk.RIGHT)

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

        # Configure tags for different activity types
        self.activities_tree.tag_configure("inventory", foreground=COLORS["primary"])
        self.activities_tree.tag_configure("project", foreground=COLORS["success"])
        self.activities_tree.tag_configure("sale", foreground=COLORS["accent"])
        self.activities_tree.tag_configure("purchase", foreground=COLORS["secondary"])
        self.activities_tree.tag_configure("alert", foreground=COLORS["danger"])

    def create_inventory_status_section(self, parent):
        """
        Create inventory status section with charts.

        Args:
            parent: The parent widget
        """
        inventory_frame = ttk.LabelFrame(parent, text="Inventory Status")
        inventory_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        # Header frame with view details button
        header_frame = ttk.Frame(inventory_frame, padding=(0, 0, 0, 5))
        header_frame.pack(fill=tk.X, expand=False)

        view_details_btn = ttk.Button(
            header_frame,
            text="View Details",
            style="Link.TButton",
            command=lambda: self._navigate_to_view("inventory")
        )
        view_details_btn.pack(side=tk.RIGHT)

        # Status overview frame
        status_frame = ttk.Frame(inventory_frame, padding=5)
        status_frame.pack(fill=tk.X, expand=False)

        # Status indicators
        self.inventory_status = {
            "in_stock": self._create_status_indicator(status_frame, "In Stock", "0", 0, COLORS["success"]),
            "low_stock": self._create_status_indicator(status_frame, "Low Stock", "0", 1, COLORS["warning"]),
            "out_of_stock": self._create_status_indicator(status_frame, "Out of Stock", "0", 2, COLORS["danger"])
        }

        # Create chart container
        chart_frame = ttk.Frame(inventory_frame, padding=5, height=200)
        chart_frame.pack(fill=tk.BOTH, expand=True)
        chart_frame.pack_propagate(False)  # Prevent shrinking

        # Save reference for updating
        self.chart_widgets["inventory"] = chart_frame

    def create_project_status_section(self, parent):
        """
        Create project status section with charts.

        Args:
            parent: The parent widget
        """
        project_frame = ttk.LabelFrame(parent, text="Project Status")
        project_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        # Header frame with view details button
        header_frame = ttk.Frame(project_frame, padding=(0, 0, 0, 5))
        header_frame.pack(fill=tk.X, expand=False)

        view_details_btn = ttk.Button(
            header_frame,
            text="View Details",
            style="Link.TButton",
            command=lambda: self._navigate_to_view("projects")
        )
        view_details_btn.pack(side=tk.RIGHT)

        # Status overview frame
        status_frame = ttk.Frame(project_frame, padding=5)
        status_frame.pack(fill=tk.X, expand=False)

        # Status indicators
        self.project_status = {
            "planning": self._create_status_indicator(status_frame, "Planning", "0", 0, COLORS["primary"]),
            "in_progress": self._create_status_indicator(status_frame, "In Progress", "0", 1, COLORS["warning"]),
            "completed": self._create_status_indicator(status_frame, "Completed", "0", 2, COLORS["success"])
        }

        # Create chart container
        chart_frame = ttk.Frame(project_frame, padding=5, height=200)
        chart_frame.pack(fill=tk.BOTH, expand=True)
        chart_frame.pack_propagate(False)  # Prevent shrinking

        # Save reference for updating
        self.chart_widgets["projects"] = chart_frame

    def create_analytics_section(self, parent):
        """
        Create analytics section with summary metrics and links.

        Args:
            parent: The parent widget
        """
        analytics_frame = ttk.LabelFrame(parent, text="Analytics Insights")
        analytics_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        # Header frame with view all button
        header_frame = ttk.Frame(analytics_frame, padding=(0, 0, 0, 5))
        header_frame.pack(fill=tk.X, expand=False)

        view_analytics_btn = ttk.Button(
            header_frame,
            text="View Analytics Dashboard",
            style="Link.TButton",
            command=self._open_analytics_dashboard
        )
        view_analytics_btn.pack(side=tk.RIGHT)

        # Create content frame
        content_frame = ttk.Frame(analytics_frame, padding=5)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Placeholder for analytics metrics
        self.analytics_metrics_frame = ttk.Frame(content_frame)
        self.analytics_metrics_frame.pack(fill=tk.BOTH, expand=True)

        # Links to specific analytics views
        links_frame = ttk.Frame(analytics_frame, padding=(5, 10, 5, 5))
        links_frame.pack(fill=tk.X, expand=False)

        # Create links for different analytics views
        analytics_links = [
            {"text": "Customer Analytics", "command": lambda: self._navigate_to_analytics("customer")},
            {"text": "Profitability", "command": lambda: self._navigate_to_analytics("profitability")},
            {"text": "Material Usage", "command": lambda: self._navigate_to_analytics("material_usage")},
            {"text": "Project Metrics", "command": lambda: self._navigate_to_analytics("project_metrics")}
        ]

        for i, link in enumerate(analytics_links):
            btn = ttk.Button(
                links_frame,
                text=link["text"],
                style="Link.TButton",
                command=link["command"]
            )
            btn.grid(row=0, column=i, padx=5)

        # Configure grid columns to be equal width
        for i in range(len(analytics_links)):
            links_frame.columnconfigure(i, weight=1)

    def _create_status_indicator(self, parent, label, value, column, color=None):
        """
        Create a status indicator with label and value.

        Args:
            parent: The parent widget
            label: Status label
            value: Status value
            column: Grid column
            color: Optional color for the value

        Returns:
            Dictionary with references to the indicator widgets
        """
        frame = ttk.Frame(parent, padding=5)
        frame.grid(row=0, column=column, sticky="ew", padx=5)

        value_label = ttk.Label(
            frame,
            text=value,
            font=("", 18, "bold"),
            foreground=color if color else COLORS["text"]
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

        # Header frame with view all button
        header_frame = ttk.Frame(upcoming_frame, padding=(0, 0, 0, 5))
        header_frame.pack(fill=tk.X, expand=False)

        view_calendar_btn = ttk.Button(
            header_frame,
            text="View Calendar",
            style="Link.TButton",
            command=self._view_calendar
        )
        view_calendar_btn.pack(side=tk.RIGHT)

        # Create 4-column layout for cards
        card_frame = ttk.Frame(upcoming_frame, padding=5)
        card_frame.pack(fill=tk.X, expand=True)

        for i in range(4):
            card_frame.columnconfigure(i, weight=1)

        # Container for deadline cards
        self.deadline_cards_frame = card_frame

        # Placeholders for upcoming deadlines - will be replaced with real data
        placeholders = [
            {"title": "Client Meeting", "date": "Tomorrow, 10:00 AM", "type": "Meeting"},
            {"title": "Belt Order Due", "date": "Mar 14, 2025", "type": "Order"},
            {"title": "Leather Shipment", "date": "Mar 15, 2025", "type": "Delivery"},
            {"title": "Inventory Audit", "date": "Mar 20, 2025", "type": "Task"}
        ]

        # Create deadline cards
        for i, item in enumerate(placeholders):
            self._create_deadline_card(self.deadline_cards_frame, item, i)

    def _create_deadline_card(self, parent, data, column):
        """
        Create a card for an upcoming deadline or event.

        Args:
            parent: The parent widget
            data: Dictionary with deadline data
            column: Grid column
        """
        # Create card with border and background
        frame = ttk.Frame(parent, padding=10, style="Card.TFrame")
        frame.grid(row=0, column=column, sticky="nsew", padx=5, pady=5)

        # Type badge with appropriate color
        type_colors = {
            "Meeting": (COLORS["primary_light"], COLORS["primary"]),
            "Order": (COLORS["accent_light"], COLORS["accent"]),
            "Delivery": (COLORS["success_light"], COLORS["success"]),
            "Task": (COLORS["secondary_light"], COLORS["secondary"]),
            "Deadline": (COLORS["warning_light"], COLORS["warning"])
        }

        bg_color, fg_color = type_colors.get(
            data["type"],
            (COLORS["light_grey"], COLORS["text_secondary"])
        )

        type_frame = ttk.Frame(frame)
        type_frame.pack(fill=tk.X, anchor="w")

        # Create badge with a status badge widget instead
        status_badge = StatusBadge(
            type_frame,
            text=data["type"],
            status_value=data["type"].lower()
        )
        status_badge.pack(side=tk.LEFT)

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

    def init_breadcrumb_navigation(self):
        """Initialize the breadcrumb navigation with the view history manager."""
        # Connect to the global view history manager if available
        try:
            main_window = self.parent.winfo_toplevel()
            if hasattr(main_window, "view_history_manager"):
                self.view_history = main_window.view_history_manager
        except Exception as e:
            self.logger.warning(f"Could not access view history manager: {str(e)}")

    def _navigate_to_breadcrumb(self, view_name, view_data=None):
        """
        Navigate to a view from breadcrumb click.

        Args:
            view_name: The name of the view to navigate to
            view_data: Optional data for the view
        """
        main_window = self.parent.winfo_toplevel()
        main_window.show_view(view_name, view_data)

    @with_service("IInventoryService")
    def load_inventory_stats(self, service=None):
        """Load inventory statistics from inventory service."""
        try:
            # If service is not available, use placeholder data
            if not service:
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
                    },
                    "value_trend": 3.2  # Percentage change from previous period
                }
                return

            # If service is available, get actual data
            self.inventory_stats = {
                "total_value": service.get_total_inventory_value(),
                "total_items": service.get_total_inventory_count(),
                "low_stock_count": service.get_low_stock_count(),
                "out_of_stock_count": service.get_out_of_stock_count(),
                "in_stock_count": service.get_in_stock_count(),
                "categories": service.get_inventory_by_category(),
                "value_trend": service.get_inventory_value_trend()
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
                },
                "value_trend": 3.2  # Percentage change from previous period
            }

    @with_service("IProjectService")
    def load_project_stats(self, service=None):
        """Load project statistics from project service."""
        try:
            # If service is not available, use placeholder data
            if not service:
                self.project_stats = {
                    "active_count": 8,
                    "completed_this_month": 3,
                    "completion_trend": 20.0,  # Percentage change from previous period
                    "by_status": {
                        "planning": 2,
                        "initial_consultation": 1,
                        "in_progress": 3,
                        "assembly": 2,
                        "completed": 3,
                        "on_hold": 1
                    },
                    "upcoming_deadlines": [
                        {"title": "Messenger Bag (John)", "date": "Tomorrow", "type": "Deadline"},
                        {"title": "Belt (Sarah)", "date": "Mar 15, 2025", "type": "Order"},
                        {"title": "Wallet Prototype", "date": "Mar 17, 2025", "type": "Task"},
                        {"title": "Client Meeting", "date": "Mar 18, 2025", "type": "Meeting"}
                    ]
                }
                return

            # If service is available, get actual data
            today = datetime.now()
            start_of_month = today.replace(day=1)

            completed_this_month = service.get_completed_project_count_for_period(
                start_of_month, today
            )

            # Calculate completion trend
            last_month_end = start_of_month - timedelta(days=1)
            last_month_start = last_month_end.replace(day=1)

            completed_last_month = service.get_completed_project_count_for_period(
                last_month_start, last_month_end
            )

            if completed_last_month > 0:
                completion_trend = ((completed_this_month - completed_last_month) / completed_last_month) * 100
            else:
                completion_trend = 0 if completed_this_month == 0 else 100

            self.project_stats = {
                "active_count": service.get_active_project_count(),
                "completed_this_month": completed_this_month,
                "completion_trend": completion_trend,
                "by_status": service.get_projects_by_status(),
                "upcoming_deadlines": service.get_upcoming_deadlines(limit=5)
            }
        except Exception as e:
            self.logger.error(f"Error loading project statistics: {str(e)}")
            # Use placeholder data on error
            self.project_stats = {
                "active_count": 8,
                "completed_this_month": 3,
                "completion_trend": 20.0,  # Percentage change from previous period
                "by_status": {
                    "planning": 2,
                    "initial_consultation": 1,
                    "in_progress": 3,
                    "assembly": 2,
                    "completed": 3,
                    "on_hold": 1
                },
                "upcoming_deadlines": [
                    {"title": "Messenger Bag (John)", "date": "Tomorrow", "type": "Deadline"},
                    {"title": "Belt (Sarah)", "date": "Mar 15, 2025", "type": "Order"},
                    {"title": "Wallet Prototype", "date": "Mar 17, 2025", "type": "Task"},
                    {"title": "Client Meeting", "date": "Mar 18, 2025", "type": "Meeting"}
                ]
            }

    @with_service("ISalesService")
    def load_sales_stats(self, service=None):
        """Load sales statistics from sales service."""
        try:
            # If service is not available, use placeholder data
            if not service:
                self.sales_stats = {
                    "current_month": 4250.00,
                    "prev_month": 3980.00,
                    "percentage_change": 6.8,
                    "recent_sales": [
                        {"id": "1", "customer": "John Smith", "amount": 120.00,
                         "date": datetime.now() - timedelta(hours=3)},
                        {"id": "2", "customer": "Sarah Johnson", "amount": 350.00,
                         "date": datetime.now() - timedelta(days=1)},
                        {"id": "3", "customer": "Mike Williams", "amount": 85.00,
                         "date": datetime.now() - timedelta(days=2)}
                    ],
                    "monthly_trend": [
                        {"month": "Jan", "value": 3600},
                        {"month": "Feb", "value": 3980},
                        {"month": "Mar", "value": 4250}
                    ]
                }
                return

            # Calculate date ranges
            today = datetime.now()
            start_of_month = today.replace(day=1)
            start_of_prev_month = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
            end_of_prev_month = today.replace(day=1) - timedelta(days=1)

            # Get sales statistics
            current_month_sales = service.get_total_sales_for_period(
                start_of_month,
                today
            )

            prev_month_sales = service.get_total_sales_for_period(
                start_of_prev_month,
                end_of_prev_month
            )

            # Calculate change percentage
            if prev_month_sales and prev_month_sales > 0:
                percentage_change = ((current_month_sales - prev_month_sales) / prev_month_sales) * 100
            else:
                percentage_change = 0 if current_month_sales == 0 else 100

            # Get monthly trend for the last 6 months
            monthly_trend = []
            for i in range(5, -1, -1):
                month_date = today.replace(day=15) - timedelta(days=30 * i)
                month_start = month_date.replace(day=1)
                if month_date.month == today.month:
                    month_end = today
                else:
                    next_month = month_date.replace(day=28) + timedelta(days=4)
                    month_end = next_month.replace(day=1) - timedelta(days=1)

                month_sales = service.get_total_sales_for_period(month_start, month_end)
                monthly_trend.append({
                    "month": month_date.strftime("%b"),
                    "value": month_sales
                })

            self.sales_stats = {
                "current_month": current_month_sales,
                "prev_month": prev_month_sales,
                "percentage_change": percentage_change,
                "recent_sales": service.get_recent_sales(limit=5),
                "monthly_trend": monthly_trend
            }
        except Exception as e:
            self.logger.error(f"Error loading sales statistics: {str(e)}")
            # Use placeholder data on error
            self.sales_stats = {
                "current_month": 4250.00,
                "prev_month": 3980.00,
                "percentage_change": 6.8,
                "recent_sales": [
                    {"id": "1", "customer": "John Smith", "amount": 120.00,
                     "date": datetime.now() - timedelta(hours=3)},
                    {"id": "2", "customer": "Sarah Johnson", "amount": 350.00,
                     "date": datetime.now() - timedelta(days=1)},
                    {"id": "3", "customer": "Mike Williams", "amount": 85.00,
                     "date": datetime.now() - timedelta(days=2)}
                ],
                "monthly_trend": [
                    {"month": "Jan", "value": 3600},
                    {"month": "Feb", "value": 3980},
                    {"month": "Mar", "value": 4250}
                ]
            }

    @with_service("IPurchaseService")
    def load_purchase_stats(self, service=None):
        """Load purchase statistics from purchase service."""
        try:
            # If service is not available, use placeholder data
            if not service:
                self.purchase_stats = {
                    "pending_count": 3,
                    "pending_amount": 1250.00,
                    "pending_trend": -15.0,  # Percentage change from previous period
                    "recent_purchases": [
                        {"id": "1", "supplier": "Buckleguy", "amount": 350.00,
                         "date": datetime.now() - timedelta(days=2)},
                        {"id": "2", "supplier": "Tandy Leather", "amount": 650.00,
                         "date": datetime.now() - timedelta(days=5)},
                        {"id": "3", "supplier": "Rocky Mountain Leather", "amount": 250.00,
                         "date": datetime.now() - timedelta(days=7)}
                    ]
                }
                return

            # Get current pending purchase amount
            pending_amount = service.get_pending_purchase_amount()

            # Get previous period pending amount (30 days ago)
            today = datetime.now()
            one_month_ago = today - timedelta(days=30)
            prev_pending_amount = service.get_pending_purchase_amount_at_date(one_month_ago)

            # Calculate trend
            if prev_pending_amount > 0:
                pending_trend = ((pending_amount - prev_pending_amount) / prev_pending_amount) * 100
            else:
                pending_trend = 0 if pending_amount == 0 else 100

            # Get purchase statistics
            self.purchase_stats = {
                "pending_count": service.get_pending_purchase_count(),
                "pending_amount": pending_amount,
                "pending_trend": pending_trend,
                "recent_purchases": service.get_recent_purchases(limit=5)
            }
        except Exception as e:
            self.logger.error(f"Error loading purchase statistics: {str(e)}")
            # Use placeholder data on error
            self.purchase_stats = {
                "pending_count": 3,
                "pending_amount": 1250.00,
                "pending_trend": -15.0,  # Percentage change from previous period
                "recent_purchases": [
                    {"id": "1", "supplier": "Buckleguy", "amount": 350.00, "date": datetime.now() - timedelta(days=2)},
                    {"id": "2", "supplier": "Tandy Leather", "amount": 650.00,
                     "date": datetime.now() - timedelta(days=5)},
                    {"id": "3", "supplier": "Rocky Mountain Leather", "amount": 250.00,
                     "date": datetime.now() - timedelta(days=7)}
                ]
            }

    @with_service("IAnalyticsDashboardService")
    def load_analytics_summary(self, service=None):
        """Load analytics summary from analytics service."""
        try:
            # If service is not available, use placeholder data
            if not service:
                self.analytics_summary = {
                    "total_revenue": 12500.00,
                    "profit_margin": 32.5,
                    "customer_retention": 78.4,
                    "most_profitable_category": "Wallets",
                    "resource_efficiency": 84.2,
                    "most_used_material": "Vegetable Tanned Leather",
                    "average_project_time": 8.5,  # days
                    "bottleneck_area": "Edge Finishing"
                }
                return

            # Get analytics summary
            today = datetime.now()
            start_date = today - timedelta(days=90)  # Last 90 days
            self.analytics_summary = service.get_analytics_summary(
                start_date=start_date,
                end_date=today
            )
        except Exception as e:
            self.logger.error(f"Error loading analytics summary: {str(e)}")
            # Use placeholder data on error
            self.analytics_summary = {
                "total_revenue": 12500.00,
                "profit_margin": 32.5,
                "customer_retention": 78.4,
                "most_profitable_category": "Wallets",
                "resource_efficiency": 84.2,
                "most_used_material": "Vegetable Tanned Leather",
                "average_project_time": 8.5,  # days
                "bottleneck_area": "Edge Finishing"
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

            # Load analytics summary
            self.load_analytics_summary()

            # Load recent activities
            self.load_recent_activities()

            # Update the dashboard with loaded data
            self.update_dashboard()

            self.logger.info("Dashboard data loaded successfully")
        except Exception as e:
            self.logger.error(f"Error loading dashboard data: {str(e)}")
            # We don't have access to a show_error method, so we'll just log it

    def update_dashboard(self):
        """Update dashboard widgets with loaded data."""
        # Update KPI widgets
        self._update_kpi_widgets()

        # Update inventory status indicators
        self._update_inventory_status()

        # Update project status indicators
        self._update_project_status()

        # Update analytics section
        self._update_analytics_section()

        # Update charts
        self._update_charts()

        # Update upcoming deadlines
        self._update_upcoming_deadlines()

    def _update_kpi_widgets(self):
        """Update KPI widgets with current statistics."""
        # Update Sales KPI
        sales_kpi = self.kpi_widgets["sales"]
        sales_kpi["value"].config(text=f"${self.sales_stats['current_month']:.2f}")

        # Update sales trend indicator
        percent_change = self.sales_stats['percentage_change']
        change_text = f"{abs(percent_change):.1f}% vs last month"
        sales_kpi["subtitle"].config(text=change_text)

        # Update trend indicator
        if "trend" in sales_kpi and sales_kpi["trend"]:
            trend_symbol = "↑" if percent_change > 0 else "↓"
            trend_color = COLORS["success"] if percent_change > 0 else COLORS["danger"]
            sales_kpi["trend"].config(text=f" {trend_symbol}", foreground=trend_color)

        # Update Projects KPI
        projects_kpi = self.kpi_widgets["projects"]
        projects_kpi["value"].config(text=str(self.project_stats["active_count"]))

        completed_text = f"{self.project_stats['completed_this_month']} completed this month"
        projects_kpi["subtitle"].config(text=completed_text)

        # Update trend indicator
        if "completion_trend" in self.project_stats and "trend" in projects_kpi and projects_kpi["trend"]:
            trend_value = self.project_stats["completion_trend"]
            trend_symbol = "↑" if trend_value > 0 else "↓"
            trend_color = COLORS["success"] if trend_value > 0 else COLORS["danger"]
            projects_kpi["trend"].config(text=f" {trend_symbol}", foreground=trend_color)

        # Update Inventory KPI
        inventory_kpi = self.kpi_widgets["inventory"]
        inventory_kpi["value"].config(text=f"${self.inventory_stats['total_value']:.2f}")

        low_stock_text = f"{self.inventory_stats['low_stock_count']} items low stock"
        inventory_kpi["subtitle"].config(text=low_stock_text)

        # Update trend indicator
        if "value_trend" in self.inventory_stats and "trend" in inventory_kpi and inventory_kpi["trend"]:
            trend_value = self.inventory_stats["value_trend"]
            trend_symbol = "↑" if trend_value > 0 else "↓"
            trend_color = COLORS["success"] if trend_value > 0 else COLORS["danger"]
            inventory_kpi["trend"].config(text=f" {trend_symbol}", foreground=trend_color)

        # Update Purchases KPI
        purchases_kpi = self.kpi_widgets["purchases"]
        purchases_kpi["value"].config(text=str(self.purchase_stats["pending_count"]))

        pending_text = f"${self.purchase_stats['pending_amount']:.2f} pending receipt"
        purchases_kpi["subtitle"].config(text=pending_text)

        # Update trend indicator
        if "pending_trend" in self.purchase_stats and "trend" in purchases_kpi and purchases_kpi["trend"]:
            trend_value = self.purchase_stats["pending_trend"]
            trend_symbol = "↑" if trend_value > 0 else "↓"
            # For purchases, decreasing is actually good
            trend_color = COLORS["success"] if trend_value < 0 else COLORS["danger"]
            purchases_kpi["trend"].config(text=f" {trend_symbol}", foreground=trend_color)

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

    def _update_analytics_section(self):
        """Update analytics section with summary data."""
        if not self.analytics_summary:
            return

        # Clear existing widgets
        for widget in self.analytics_metrics_frame.winfo_children():
            widget.destroy()

        # Create grid layout for metrics
        for i in range(2):  # 2 columns
            self.analytics_metrics_frame.columnconfigure(i, weight=1)

        # Key metrics to display
        metrics = [
            {"label": "Profit Margin", "value": f"{self.analytics_summary['profit_margin']}%", "row": 0, "col": 0},
            {"label": "Customer Retention", "value": f"{self.analytics_summary['customer_retention']}%", "row": 0,
             "col": 1},
            {"label": "Resource Efficiency", "value": f"{self.analytics_summary['resource_efficiency']}%", "row": 1,
             "col": 0},
            {"label": "Avg. Project Time", "value": f"{self.analytics_summary['average_project_time']} days", "row": 1,
             "col": 1}
        ]

        # Create metric labels
        for metric in metrics:
            frame = ttk.Frame(self.analytics_metrics_frame, padding=10)
            frame.grid(row=metric["row"], column=metric["col"], sticky="nsew", padx=5, pady=5)

            # Value
            value_label = ttk.Label(
                frame,
                text=metric["value"],
                font=("", 16, "bold")
            )
            value_label.pack(anchor="w")

            # Label
            label = ttk.Label(
                frame,
                text=metric["label"],
                font=("", 10),
                foreground=COLORS["text_secondary"]
            )
            label.pack(anchor="w")

    def _update_charts(self):
        """Update chart visualizations."""
        self._draw_inventory_chart()
        self._draw_project_chart()

    def _draw_inventory_chart(self):
        """Draw inventory distribution chart."""
        chart_frame = self.chart_widgets["inventory"]

        # Clear existing chart
        for widget in chart_frame.winfo_children():
            widget.destroy()

        # Get categories data
        categories = self.inventory_stats.get("categories", {})
        if not categories:
            # Draw placeholder text
            ttk.Label(
                chart_frame,
                text="No inventory data available",
                anchor="center"
            ).pack(expand=True, fill=tk.BOTH)
            return

        # Prepare data for pie chart
        chart_data = [
            {
                "label": category,
                "value": count,
                "color": COLORS.get(f"category_{i}", COLORS["primary"])
            }
            for i, (category, count) in enumerate(categories.items())
        ]

        # Create pie chart
        pie_chart = create_pie_chart(
            chart_frame,
            chart_data,
            title="Inventory Distribution by Category",
            width=chart_frame.winfo_width(),
            height=chart_frame.winfo_height(),
            show_legend=True,
            show_percentage=True
        )
        pie_chart.pack(fill=tk.BOTH, expand=True)

    def _draw_project_chart(self):
        """Draw project timeline overview chart."""
        chart_frame = self.chart_widgets["projects"]

        # Clear existing chart
        for widget in chart_frame.winfo_children():
            widget.destroy()

        # Get status data
        status_counts = self.project_stats.get("by_status", {})
        if not status_counts:
            # Draw placeholder text
            ttk.Label(
                chart_frame,
                text="No project data available",
                anchor="center"
            ).pack(expand=True, fill=tk.BOTH)
            return

        # If we have sales trend data, show that
        if "monthly_trend" in self.sales_stats and self.sales_stats["monthly_trend"]:
            # Create line chart for sales trend
            monthly_data = self.sales_stats["monthly_trend"]

            chart_data = [
                {
                    "label": item["month"],
                    "value": item["value"],
                    "color": COLORS["primary"]
                }
                for item in monthly_data
            ]

            # Create line chart
            line_chart = create_line_chart(
                chart_frame,
                chart_data,
                title="Monthly Sales Trend",
                x_label="Month",
                y_label="Sales ($)",
                width=chart_frame.winfo_width(),
                height=chart_frame.winfo_height(),
                show_points=True,
                area_fill=True
            )
            line_chart.pack(fill=tk.BOTH, expand=True)
        else:
            # Fall back to status distribution
            chart_data = [
                {
                    "label": status,
                    "value": count,
                    "color": self._get_status_color(status)
                }
                for status, count in status_counts.items()
            ]

            # Create pie chart
            pie_chart = create_pie_chart(
                chart_frame,
                chart_data,
                title="Project Status Distribution",
                width=chart_frame.winfo_width(),
                height=chart_frame.winfo_height(),
                show_legend=True,
                show_percentage=True
            )
            pie_chart.pack(fill=tk.BOTH, expand=True)

    def _get_status_color(self, status):
        """
        Get color for status visualization.

        Args:
            status: The status name

        Returns:
            Color hex code
        """
        status_colors = {
            "initial_consultation": COLORS.get("success", "#4CAF50"),
            "design_phase": COLORS.get("success_light", "#8BC34A"),
            "pattern_development": COLORS.get("primary", "#CDDC39"),
            "material_selection": COLORS.get("primary_light", "#FFEB3B"),
            "cutting": COLORS.get("warning", "#FFC107"),
            "assembly": COLORS.get("warning", "#FF9800"),
            "stitching": COLORS.get("warning", "#FF5722"),
            "quality_check": COLORS.get("accent", "#795548"),
            "completed": COLORS.get("success", "#607D8B"),
            "on_hold": COLORS.get("secondary", "#9E9E9E"),
            "cancelled": COLORS.get("danger", "#F44336"),
            "planning": COLORS.get("primary", "#2196F3"),
            "in_progress": COLORS.get("warning", "#FF9800")
        }

        return status_colors.get(status, COLORS.get("primary", "#2196F3"))

    def _update_upcoming_deadlines(self):
        """Update upcoming deadlines with real data."""
        # Clear existing cards
        for widget in self.deadline_cards_frame.winfo_children():
            widget.destroy()

        # Get upcoming deadlines from project statistics
        deadlines = self.project_stats.get("upcoming_deadlines", [])

        # Create deadline cards
        for i, item in enumerate(deadlines[:4]):  # Show up to 4 deadlines
            self._create_deadline_card(self.deadline_cards_frame, item, i)

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
        if not tags or len(tags) < 1:
            return

        source = tags[0]

        # Navigate to the appropriate view based on the source
        self._navigate_to_view(source)

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
        self._navigate_to_view("inventory")

    def on_new_purchase(self):
        """Handle new purchase action."""
        # Navigate to purchases view and trigger new purchase action
        main_window = self.parent.winfo_toplevel()
        main_window.create_new_purchase()

    def _navigate_to_view(self, view_name):
        """
        Navigate to a specific view.

        Args:
            view_name: Name of the view to navigate to
        """
        main_window = self.parent.winfo_toplevel()
        main_window.show_view(view_name)

    def _navigate_to_analytics(self, view_name):
        """
        Navigate to a specific analytics view.

        Args:
            view_name: Name of the analytics view to navigate to
        """
        main_window = self.parent.winfo_toplevel()

        # Check if the main window has a show_analytics_view method
        if hasattr(main_window, "show_analytics_view"):
            main_window.show_analytics_view(view_name)
        else:
            # Fallback to generic view navigation
            self._navigate_to_view("analytics")

    def _open_analytics_dashboard(self):
        """Open the analytics dashboard."""
        self._navigate_to_analytics("dashboard")

    def _view_all_activities(self):
        """View all activities."""
        # This would navigate to an activities log view if one existed
        # For now, just log that this was clicked
        self.logger.info("View all activities clicked")

    def _view_calendar(self):
        """View calendar with all deadlines and events."""
        # This would navigate to a calendar view if one existed
        # For now, just log that this was clicked
        self.logger.info("View calendar clicked")

    def _export_dashboard(self):
        """Export the dashboard as PDF or image."""
        self.logger.info("Export dashboard clicked")
        # Publish an event to trigger export handling elsewhere
        publish("dashboard.export_requested", {"view": "dashboard"})

    def refresh(self):
        """Refresh the dashboard data."""
        self.load_data()

    # EVENT BUS INTEGRATION
    def _subscribe_to_events(self):
        """Subscribe to relevant events for dashboard updates."""
        # Inventory events
        subscribe("inventory.item.added", self._handle_inventory_event)
        subscribe("inventory.item.updated", self._handle_inventory_event)
        subscribe("inventory.item.removed", self._handle_inventory_event)
        subscribe("inventory.low_stock", self._handle_inventory_alert)

        # Project events
        subscribe("project.created", self._handle_project_event)
        subscribe("project.updated", self._handle_project_event)
        subscribe("project.status_changed", self._handle_project_status_event)
        subscribe("project.completed", self._handle_project_completion)

        # Sales events
        subscribe("sale.created", self._handle_sale_event)
        subscribe("sale.updated", self._handle_sale_event)

        # Purchase events
        subscribe("purchase.created", self._handle_purchase_event)
        subscribe("purchase.updated", self._handle_purchase_event)
        subscribe("purchase.received", self._handle_purchase_received)

        # Other events
        subscribe("analytics.updated", self._handle_analytics_update)

        self.logger.info("Subscribed to dashboard events")

    def destroy(self):
        """
        Clean up resources and unsubscribe from events.
        Call this method when the dashboard is closed.
        """
        self._unsubscribe_from_events()
        # Clean up any other resources

        self.logger.info("Dashboard destroyed and unsubscribed from events")

    def _unsubscribe_from_events(self):
        """Unsubscribe from all events."""
        # Inventory events
        unsubscribe("inventory.item.added", self._handle_inventory_event)
        unsubscribe("inventory.item.updated", self._handle_inventory_event)
        unsubscribe("inventory.item.removed", self._handle_inventory_event)
        unsubscribe("inventory.low_stock", self._handle_inventory_alert)

        # Project events
        unsubscribe("project.created", self._handle_project_event)
        unsubscribe("project.updated", self._handle_project_event)
        unsubscribe("project.status_changed", self._handle_project_status_event)
        unsubscribe("project.completed", self._handle_project_completion)

        # Sales events
        unsubscribe("sale.created", self._handle_sale_event)
        unsubscribe("sale.updated", self._handle_sale_event)

        # Purchase events
        unsubscribe("purchase.created", self._handle_purchase_event)
        unsubscribe("purchase.updated", self._handle_purchase_event)
        unsubscribe("purchase.received", self._handle_purchase_received)

        # Other events
        unsubscribe("analytics.updated", self._handle_analytics_update)

        self.logger.info("Unsubscribed from all dashboard events")

    # Event handler methods
    def _handle_inventory_event(self, data):
        """
        Handle inventory-related events.

        Args:
            data: Event data containing inventory information
        """
        self.logger.info(f"Handling inventory event: {data}")

        # Only reload inventory stats, not the entire dashboard
        self.load_inventory_stats()
        self._update_inventory_status()
        self._draw_inventory_chart()

        # Update KPI widget
        self._update_kpi_widgets()

        # Add to recent activities
        self._add_activity_entry("Inventory", data.get("description", "Inventory updated"))

    def _handle_inventory_alert(self, data):
        """
        Handle inventory alert events (low stock, etc).

        Args:
            data: Event data containing alert information
        """
        self.logger.info(f"Handling inventory alert: {data}")

        # Update inventory status
        self.load_inventory_stats()
        self._update_inventory_status()

        # Add to recent activities with alert tag
        self._add_activity_entry("Inventory",
                                 data.get("description", "Inventory alert"),
                                 alert=True)

    def _handle_project_event(self, data):
        """
        Handle project-related events.

        Args:
            data: Event data containing project information
        """
        self.logger.info(f"Handling project event: {data}")

        # Only reload project stats, not the entire dashboard
        self.load_project_stats()
        self._update_project_status()
        self._draw_project_chart()
        self._update_upcoming_deadlines()

        # Update KPI widget
        self._update_kpi_widgets()

        # Add to recent activities
        self._add_activity_entry("Project", data.get("description", "Project updated"))

    def _handle_project_status_event(self, data):
        """
        Handle project status change events.

        Args:
            data: Event data containing project status information
        """
        self.logger.info(f"Handling project status change: {data}")

        # Only reload project stats, not the entire dashboard
        self.load_project_stats()
        self._update_project_status()
        self._update_kpi_widgets()

        # Add to recent activities
        status_desc = f"Project '{data.get('project_name', '')}' moved to {data.get('new_status', '')}"
        self._add_activity_entry("Project", data.get("description", status_desc))

    def _handle_project_completion(self, data):
        """
        Handle project completion events.

        Args:
            data: Event data containing completed project information
        """
        self.logger.info(f"Handling project completion: {data}")

        # Reload project stats
        self.load_project_stats()
        self._update_project_status()
        self._update_kpi_widgets()

        # Add to recent activities
        completion_desc = f"Project '{data.get('project_name', '')}' completed"
        self._add_activity_entry("Project", data.get("description", completion_desc))

    def _handle_sale_event(self, data):
        """
        Handle sale-related events.

        Args:
            data: Event data containing sale information
        """
        self.logger.info(f"Handling sale event: {data}")

        # Only reload sales stats, not the entire dashboard
        self.load_sales_stats()
        self._update_kpi_widgets()
        self._draw_project_chart()  # This also shows sales trend if available

        # Add to recent activities
        sale_desc = f"New sale: ${data.get('amount', '0.00')} - {data.get('description', 'Sale')}"
        self._add_activity_entry("Sale", data.get("description", sale_desc))

    def _handle_purchase_event(self, data):
        """
        Handle purchase-related events.

        Args:
            data: Event data containing purchase information
        """
        self.logger.info(f"Handling purchase event: {data}")

        # Only reload purchase stats, not the entire dashboard
        self.load_purchase_stats()
        self._update_kpi_widgets()

        # Add to recent activities
        purchase_desc = f"New purchase: ${data.get('amount', '0.00')} - {data.get('supplier', 'Purchase')}"
        self._add_activity_entry("Purchase", data.get("description", purchase_desc))

    def _handle_purchase_received(self, data):
        """
        Handle purchase received events.

        Args:
            data: Event data containing received purchase information
        """
        self.logger.info(f"Handling purchase received: {data}")

        # Update both purchase and inventory stats
        self.load_purchase_stats()
        self.load_inventory_stats()
        self._update_kpi_widgets()
        self._update_inventory_status()

        # Add to recent activities
        received_desc = f"Received order: {data.get('description', 'Purchase received')}"
        self._add_activity_entry("Purchase", data.get("description", received_desc))

    def _handle_analytics_update(self, data):
        """
        Handle analytics update events.

        Args:
            data: Event data containing analytics information
        """
        self.logger.info(f"Handling analytics update: {data}")

        # Reload analytics summary
        self.load_analytics_summary()
        self._update_analytics_section()

    def _add_activity_entry(self, activity_type, description, alert=False):
        """
        Add a new entry to the recent activities list.

        Args:
            activity_type: Type of activity (Inventory, Project, Sale, Purchase)
            description: Description of the activity
            alert: Whether this is an alert entry (highlighted)
        """
        # Get current time
        timestamp = datetime.now()
        timestamp_str = timestamp.strftime("%m/%d %H:%M")

        # Add to treeview at the top (0 index for newest first)
        item_id = self.activities_tree.insert(
            "",
            0,  # Insert at the beginning
            values=(timestamp_str, activity_type, description),
            tags=(activity_type.lower(), "alert" if alert else "")
        )

        # Limit the number of entries (keep the most recent 20)
        all_items = self.activities_tree.get_children()
        if len(all_items) > 20:
            # Remove the oldest entries
            for item in all_items[20:]:
                self.activities_tree.delete(item)

        return item_id