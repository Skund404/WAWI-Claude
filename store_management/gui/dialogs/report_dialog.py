# gui/dialogs/report_dialog.py
"""
Report generation dialog for configuring and generating various reports.
"""

import logging
import tkinter as tk
from tkinter import ttk
from typing import Any, Dict, List, Optional, Callable, Tuple
import datetime

from gui.base.base_dialog import BaseDialog
from gui.components.form_builder import FormBuilder, DateField
from gui.components.calendar_widget import CalendarWidget
from gui.theme import get_color

logger = logging.getLogger(__name__)


class ReportFormat:
    """Class representing available report output formats."""
    PDF = "PDF"
    EXCEL = "Excel"
    CSV = "CSV"
    HTML = "HTML"
    PLAIN_TEXT = "Plain Text"

    @classmethod
    def all_formats(cls) -> List[str]:
        """Get all available formats.

        Returns:
            List[str]: List of format names
        """
        return [cls.PDF, cls.EXCEL, cls.CSV, cls.HTML, cls.PLAIN_TEXT]


class ReportType:
    """Class representing available report types."""
    # Inventory Reports
    INVENTORY_SUMMARY = "Inventory Summary"
    INVENTORY_VALUATION = "Inventory Valuation"
    LOW_STOCK_ITEMS = "Low Stock Items"
    INVENTORY_MOVEMENTS = "Inventory Movements"

    # Sales Reports
    SALES_SUMMARY = "Sales Summary"
    SALES_BY_PRODUCT = "Sales by Product"
    SALES_BY_CUSTOMER = "Sales by Customer"
    TOP_SELLING_PRODUCTS = "Top Selling Products"

    # Project Reports
    PROJECT_STATUS = "Project Status"
    PROJECT_PROFITABILITY = "Project Profitability"
    PROJECT_TIME_ANALYSIS = "Project Time Analysis"

    # Financial Reports
    PROFIT_LOSS = "Profit and Loss"
    COST_ANALYSIS = "Cost Analysis"
    MATERIAL_USAGE_COST = "Material Usage Cost"

    # Supplier Reports
    SUPPLIER_PERFORMANCE = "Supplier Performance"
    PURCHASE_HISTORY = "Purchase History"

    @classmethod
    def by_category(cls) -> Dict[str, List[str]]:
        """Get report types organized by category.

        Returns:
            Dict[str, List[str]]: Dictionary mapping categories to report types
        """
        return {
            "Inventory": [
                cls.INVENTORY_SUMMARY,
                cls.INVENTORY_VALUATION,
                cls.LOW_STOCK_ITEMS,
                cls.INVENTORY_MOVEMENTS
            ],
            "Sales": [
                cls.SALES_SUMMARY,
                cls.SALES_BY_PRODUCT,
                cls.SALES_BY_CUSTOMER,
                cls.TOP_SELLING_PRODUCTS
            ],
            "Projects": [
                cls.PROJECT_STATUS,
                cls.PROJECT_PROFITABILITY,
                cls.PROJECT_TIME_ANALYSIS
            ],
            "Financial": [
                cls.PROFIT_LOSS,
                cls.COST_ANALYSIS,
                cls.MATERIAL_USAGE_COST
            ],
            "Suppliers": [
                cls.SUPPLIER_PERFORMANCE,
                cls.PURCHASE_HISTORY
            ]
        }

    @classmethod
    def all_types(cls) -> List[str]:
        """Get all available report types.

        Returns:
            List[str]: List of report type names
        """
        all_types = []
        for category_types in cls.by_category().values():
            all_types.extend(category_types)
        return all_types


class ReportDialog(BaseDialog):
    """Dialog for configuring and generating reports."""

    def __init__(self, parent: tk.Widget, title: str,
                 callback: Callable[[Dict[str, Any]], None],
                 available_report_types: Optional[List[str]] = None,
                 entity_type: Optional[str] = None,
                 size: tuple = (700, 600)):
        """Initialize the report dialog.

        Args:
            parent: Parent widget
            title: Dialog title
            callback: Function to call with report configuration when generated
            available_report_types: List of available report types, or None for all
            entity_type: Optional entity type name for the dialog title
            size: Dialog size (width, height)
        """
        self.callback = callback
        self.report_config = {}
        self.report_type_var = None
        self.date_range_var = None
        self.format_var = None
        self.custom_date_frame = None
        self.start_date_var = None
        self.end_date_var = None
        self.options_frame = None
        self.options_widgets = {}
        self.entity_type = entity_type or "Data"
        self.available_report_types = available_report_types

        # Customize title if entity type is provided
        if entity_type and "Report" not in title:
            title = f"{entity_type} Reports"

        # Set dialog size
        self.width, self.height = size

        super().__init__(parent, title)

    def _create_body(self) -> ttk.Frame:
        """Create the dialog body with report configuration controls.

        Returns:
            ttk.Frame: The dialog body frame
        """
        body = ttk.Frame(self)
        body.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create the category and report type selection frame
        report_select_frame = ttk.LabelFrame(body, text="Report Selection")
        report_select_frame.pack(fill=tk.X, pady=(0, 10))

        # Create the category selection
        category_frame = ttk.Frame(report_select_frame)
        category_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(category_frame, text="Category:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))

        self.category_var = tk.StringVar()
        categories = list(ReportType.by_category().keys())
        category_combo = ttk.Combobox(category_frame, textvariable=self.category_var,
                                      values=categories, state="readonly")
        category_combo.grid(row=0, column=1, sticky=tk.W + tk.E, padx=(0, 5))

        # Create the report type selection
        report_type_frame = ttk.Frame(report_select_frame)
        report_type_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(report_type_frame, text="Report Type:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))

        self.report_type_var = tk.StringVar()
        self.report_type_combo = ttk.Combobox(report_type_frame, textvariable=self.report_type_var,
                                              values=[], state="readonly")
        self.report_type_combo.grid(row=0, column=1, sticky=tk.W + tk.E, padx=(0, 5))

        # Create the date range frame
        date_frame = ttk.LabelFrame(body, text="Date Range")
        date_frame.pack(fill=tk.X, pady=(0, 10))

        # Date range options
        date_range_options = [
            "Today",
            "Yesterday",
            "This Week",
            "Last Week",
            "This Month",
            "Last Month",
            "This Quarter",
            "Last Quarter",
            "This Year",
            "Last Year",
            "Custom"
        ]

        self.date_range_var = tk.StringVar(value=date_range_options[4])  # Default to "This Month"

        # Create radio buttons for date range options
        date_radio_frame = ttk.Frame(date_frame)
        date_radio_frame.pack(fill=tk.X, padx=10, pady=5)

        for i, option in enumerate(date_range_options):
            col = i % 3
            row = i // 3
            ttk.Radiobutton(date_radio_frame, text=option, variable=self.date_range_var,
                            value=option, command=self._on_date_range_change).grid(
                row=row, column=col, sticky=tk.W, padx=5, pady=2)

        # Create custom date range frame (initially hidden)
        self.custom_date_frame = ttk.Frame(date_frame)
        self.custom_date_frame.pack(fill=tk.X, padx=10, pady=5)
        self.custom_date_frame.pack_forget()  # Hide initially

        # Create From date field
        ttk.Label(self.custom_date_frame, text="From:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.start_date_var = tk.StringVar()
        start_date_entry = ttk.Entry(self.custom_date_frame, textvariable=self.start_date_var)
        start_date_entry.grid(row=0, column=1, sticky=tk.W, padx=(0, 5))

        # Create calendar button for start date
        start_date_btn = ttk.Button(self.custom_date_frame, text="📅", width=3,
                                    command=lambda: self._show_calendar(self.start_date_var))
        start_date_btn.grid(row=0, column=2, sticky=tk.W, padx=(0, 15))

        # Create To date field
        ttk.Label(self.custom_date_frame, text="To:").grid(row=0, column=3, sticky=tk.W, padx=(0, 5))
        self.end_date_var = tk.StringVar()
        end_date_entry = ttk.Entry(self.custom_date_frame, textvariable=self.end_date_var)
        end_date_entry.grid(row=0, column=4, sticky=tk.W, padx=(0, 5))

        # Create calendar button for end date
        end_date_btn = ttk.Button(self.custom_date_frame, text="📅", width=3,
                                  command=lambda: self._show_calendar(self.end_date_var))
        end_date_btn.grid(row=0, column=5, sticky=tk.W)

        # Set default dates for custom range (This month)
        today = datetime.date.today()
        first_day = datetime.date(today.year, today.month, 1)
        self.start_date_var.set(first_day.strftime("%Y-%m-%d"))
        self.end_date_var.set(today.strftime("%Y-%m-%d"))

        # Create format selection frame
        format_frame = ttk.LabelFrame(body, text="Output Format")
        format_frame.pack(fill=tk.X, pady=(0, 10))

        format_option_frame = ttk.Frame(format_frame)
        format_option_frame.pack(fill=tk.X, padx=10, pady=5)

        self.format_var = tk.StringVar(value=ReportFormat.PDF)

        for i, format_option in enumerate(ReportFormat.all_formats()):
            ttk.Radiobutton(format_option_frame, text=format_option, variable=self.format_var,
                            value=format_option).grid(row=0, column=i, padx=10, pady=5)

        # Create placeholder for report-specific options
        self.options_frame = ttk.LabelFrame(body, text="Report Options")
        self.options_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Set up event handlers
        self.category_var.trace_add("write", self._on_category_change)
        self.report_type_var.trace_add("write", self._on_report_type_change)

        # Initialize with first category
        if categories:
            self.category_var.set(categories[0])

        return body

    def _create_buttons(self) -> ttk.Frame:
        """Create dialog buttons.

        Returns:
            ttk.Frame: The button frame
        """
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        # Create Generate button
        generate_btn = ttk.Button(
            button_frame,
            text="Generate Report",
            command=self._on_ok,
            style="Accent.TButton"
        )
        generate_btn.pack(side=tk.RIGHT, padx=5)

        # Create Cancel button
        cancel_btn = ttk.Button(
            button_frame,
            text="Cancel",
            command=self._on_cancel
        )
        cancel_btn.pack(side=tk.RIGHT, padx=5)

        return button_frame

    def _on_category_change(self, *args) -> None:
        """Handle category selection change."""
        category = self.category_var.get()
        if category:
            report_types = ReportType.by_category().get(category, [])
            self.report_type_combo['values'] = report_types

            if report_types:
                self.report_type_var.set(report_types[0])
            else:
                self.report_type_var.set("")

    def _on_report_type_change(self, *args) -> None:
        """Handle report type selection change."""
        self._update_options_frame()

    def _update_options_frame(self) -> None:
        """Update the options frame with report-specific options."""
        # Clear existing options
        for widget in self.options_frame.winfo_children():
            widget.destroy()

        self.options_widgets = {}

        report_type = self.report_type_var.get()
        if not report_type:
            return

        # Add report-specific options based on the selected report type
        if report_type == ReportType.INVENTORY_SUMMARY:
            self._add_inventory_summary_options()
        elif report_type == ReportType.SALES_SUMMARY:
            self._add_sales_summary_options()
        elif report_type == ReportType.PROJECT_STATUS:
            self._add_project_status_options()
        elif report_type == ReportType.PROFIT_LOSS:
            self._add_profit_loss_options()
        # Add more report-specific options here

    def _add_inventory_summary_options(self) -> None:
        """Add options specific to inventory summary report."""
        options_frame = ttk.Frame(self.options_frame)
        options_frame.pack(fill=tk.X, padx=10, pady=5)

        # Include zero stock items
        self.options_widgets['include_zero_stock'] = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Include zero stock items",
                        variable=self.options_widgets['include_zero_stock']).grid(
            row=0, column=0, sticky=tk.W, padx=(0, 15))

        # Group by type
        self.options_widgets['group_by_type'] = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Group by material type",
                        variable=self.options_widgets['group_by_type']).grid(
            row=0, column=1, sticky=tk.W, padx=(0, 15))

        # Include cost data
        self.options_widgets['include_cost'] = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Include cost data",
                        variable=self.options_widgets['include_cost']).grid(
            row=0, column=2, sticky=tk.W)

    def _add_sales_summary_options(self) -> None:
        """Add options specific to sales summary report."""
        options_frame = ttk.Frame(self.options_frame)
        options_frame.pack(fill=tk.X, padx=10, pady=5)

        # Group by options
        ttk.Label(options_frame, text="Group by:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))

        self.options_widgets['group_by'] = tk.StringVar(value="month")
        ttk.Radiobutton(options_frame, text="Day", variable=self.options_widgets['group_by'],
                        value="day").grid(row=0, column=1, sticky=tk.W, padx=(0, 10))
        ttk.Radiobutton(options_frame, text="Week", variable=self.options_widgets['group_by'],
                        value="week").grid(row=0, column=2, sticky=tk.W, padx=(0, 10))
        ttk.Radiobutton(options_frame, text="Month", variable=self.options_widgets['group_by'],
                        value="month").grid(row=0, column=3, sticky=tk.W, padx=(0, 10))
        ttk.Radiobutton(options_frame, text="Quarter", variable=self.options_widgets['group_by'],
                        value="quarter").grid(row=0, column=4, sticky=tk.W, padx=(0, 10))

        # Include options
        options_frame2 = ttk.Frame(self.options_frame)
        options_frame2.pack(fill=tk.X, padx=10, pady=5)

        self.options_widgets['include_tax'] = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame2, text="Include tax data",
                        variable=self.options_widgets['include_tax']).grid(
            row=0, column=0, sticky=tk.W, padx=(0, 15))

        self.options_widgets['include_returns'] = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame2, text="Include returns",
                        variable=self.options_widgets['include_returns']).grid(
            row=0, column=1, sticky=tk.W, padx=(0, 15))

    def _add_project_status_options(self) -> None:
        """Add options specific to project status report."""
        options_frame = ttk.Frame(self.options_frame)
        options_frame.pack(fill=tk.X, padx=10, pady=5)

        # Status options
        ttk.Label(options_frame, text="Include projects with status:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))

        status_frame = ttk.Frame(self.options_frame)
        status_frame.pack(fill=tk.X, padx=20, pady=5)

        statuses = ['In Progress', 'Not Started', 'Completed', 'Cancelled', 'On Hold']

        for i, status in enumerate(statuses):
            var_name = f"status_{status.lower().replace(' ', '_')}"
            self.options_widgets[var_name] = tk.BooleanVar(value=True if status != 'Cancelled' else False)
            ttk.Checkbutton(status_frame, text=status, variable=self.options_widgets[var_name]).grid(
                row=0, column=i, sticky=tk.W, padx=(0, 15))

        # Include cost data
        options_frame2 = ttk.Frame(self.options_frame)
        options_frame2.pack(fill=tk.X, padx=10, pady=5)

        self.options_widgets['include_cost_data'] = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame2, text="Include cost data",
                        variable=self.options_widgets['include_cost_data']).grid(
            row=0, column=0, sticky=tk.W, padx=(0, 15))

        self.options_widgets['include_time_data'] = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame2, text="Include time tracking data",
                        variable=self.options_widgets['include_time_data']).grid(
            row=0, column=1, sticky=tk.W)

    def _add_profit_loss_options(self) -> None:
        """Add options specific to profit and loss report."""
        options_frame = ttk.Frame(self.options_frame)
        options_frame.pack(fill=tk.X, padx=10, pady=5)

        # Comparison period
        ttk.Label(options_frame, text="Compare with:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))

        self.options_widgets['comparison_period'] = tk.StringVar(value="none")
        ttk.Radiobutton(options_frame, text="Previous Period",
                        variable=self.options_widgets['comparison_period'],
                        value="previous").grid(row=0, column=1, sticky=tk.W, padx=(0, 10))
        ttk.Radiobutton(options_frame, text="Same Period Last Year",
                        variable=self.options_widgets['comparison_period'],
                        value="last_year").grid(row=0, column=2, sticky=tk.W, padx=(0, 10))
        ttk.Radiobutton(options_frame, text="None",
                        variable=self.options_widgets['comparison_period'],
                        value="none").grid(row=0, column=3, sticky=tk.W)

        # Detailed breakdown
        options_frame2 = ttk.Frame(self.options_frame)
        options_frame2.pack(fill=tk.X, padx=10, pady=5)

        self.options_widgets['detailed_breakdown'] = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame2, text="Include detailed category breakdown",
                        variable=self.options_widgets['detailed_breakdown']).grid(
            row=0, column=0, sticky=tk.W, padx=(0, 15))

        self.options_widgets['include_chart'] = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame2, text="Include charts",
                        variable=self.options_widgets['include_chart']).grid(
            row=0, column=1, sticky=tk.W)

    def _on_date_range_change(self) -> None:
        """Handle date range selection change."""
        date_range = self.date_range_var.get()
        if date_range == "Custom":
            self.custom_date_frame.pack(fill=tk.X, padx=10, pady=5)
        else:
            self.custom_date_frame.pack_forget()

    def _show_calendar(self, date_var: tk.StringVar) -> None:
        """Show calendar for date selection.

        Args:
            date_var: Variable to store the selected date
        """
        top = tk.Toplevel(self)
        top.title("Select Date")
        top.grab_set()

        def on_date_select(date_str):
            date_var.set(date_str)
            top.destroy()

        try:
            current_date = datetime.datetime.strptime(date_var.get(), "%Y-%m-%d").date()
        except (ValueError, TypeError):
            current_date = datetime.date.today()

        cal = CalendarWidget(top, on_date_select=on_date_select)
        cal.set_date(current_date)
        cal.pack(padx=10, pady=10)

    def _validate(self) -> bool:
        """Validate report configuration inputs.

        Returns:
            bool: True if all inputs are valid, False otherwise
        """
        if not self.report_type_var.get():
            self.show_error("Error", "Please select a report type.")
            return False

        if self.date_range_var.get() == "Custom":
            try:
                start_date = datetime.datetime.strptime(self.start_date_var.get(), "%Y-%m-%d").date()
                end_date = datetime.datetime.strptime(self.end_date_var.get(), "%Y-%m-%d").date()

                if start_date > end_date:
                    self.show_error("Error", "Start date cannot be after end date.")
                    return False
            except ValueError:
                self.show_error("Error", "Please enter valid dates in YYYY-MM-DD format.")
                return False

        return True

    def _apply(self) -> None:
        """Apply the report configuration by calling the callback function."""
        try:
            # Collect report configuration
            config = {
                "type": self.report_type_var.get(),
                "format": self.format_var.get(),
                "date_range": self.date_range_var.get(),
            }

            # Add date range details
            if config["date_range"] == "Custom":
                config["start_date"] = self.start_date_var.get()
                config["end_date"] = self.end_date_var.get()
            else:
                # Calculate actual dates based on selected range
                today = datetime.date.today()

                if config["date_range"] == "Today":
                    config["start_date"] = today.strftime("%Y-%m-%d")
                    config["end_date"] = today.strftime("%Y-%m-%d")
                elif config["date_range"] == "Yesterday":
                    yesterday = today - datetime.timedelta(days=1)
                    config["start_date"] = yesterday.strftime("%Y-%m-%d")
                    config["end_date"] = yesterday.strftime("%Y-%m-%d")
                elif config["date_range"] == "This Week":
                    start = today - datetime.timedelta(days=today.weekday())
                    config["start_date"] = start.strftime("%Y-%m-%d")
                    config["end_date"] = today.strftime("%Y-%m-%d")
                elif config["date_range"] == "Last Week":
                    end = today - datetime.timedelta(days=today.weekday() + 1)
                    start = end - datetime.timedelta(days=6)
                    config["start_date"] = start.strftime("%Y-%m-%d")
                    config["end_date"] = end.strftime("%Y-%m-%d")
                elif config["date_range"] == "This Month":
                    start = datetime.date(today.year, today.month, 1)
                    config["start_date"] = start.strftime("%Y-%m-%d")
                    config["end_date"] = today.strftime("%Y-%m-%d")
                elif config["date_range"] == "Last Month":
                    if today.month == 1:
                        last_month = 12
                        year = today.year - 1
                    else:
                        last_month = today.month - 1
                        year = today.year

                    start = datetime.date(year, last_month, 1)
                    if last_month == 12:
                        end_month = 1
                        end_year = year + 1
                    else:
                        end_month = last_month + 1
                        end_year = year

                    end = datetime.date(end_year, end_month, 1) - datetime.timedelta(days=1)
                    config["start_date"] = start.strftime("%Y-%m-%d")
                    config["end_date"] = end.strftime("%Y-%m-%d")
                # Similar logic for other date ranges...

            # Add report-specific options
            config["options"] = {}
            for key, widget in self.options_widgets.items():
                if isinstance(widget, (tk.BooleanVar, tk.StringVar, tk.IntVar, tk.DoubleVar)):
                    config["options"][key] = widget.get()

            # Call the callback with the report configuration
            self.callback(config)
            logger.debug(f"Report configuration: {config}")
        except Exception as e:
            logger.error(f"Error applying report configuration: {str(e)}")
            raise

    def show_error(self, title: str, message: str) -> None:
        """Show an error message.

        Args:
            title: Dialog title
            message: Error message
        """
        from tkinter import messagebox
        messagebox.showerror(title, message, parent=self)

    @staticmethod
    def show_dialog(parent: tk.Widget,
                    title: str = "Generate Report",
                    entity_type: Optional[str] = None,
                    available_report_types: Optional[List[str]] = None,
                    size: tuple = (700, 600)) -> Optional[Dict[str, Any]]:
        """Show a report dialog and return the result.

        Args:
            parent: Parent widget
            title: Dialog title
            entity_type: Optional entity type name
            available_report_types: List of available report types, or None for all
            size: Dialog size (width, height)

        Returns:
            The report configuration if generated, None if cancelled
        """
        # Create a variable to hold the result
        result_config = None

        # Define callback
        def on_generate(config):
            nonlocal result_config
            result_config = config

        # Create and show the dialog
        dialog = ReportDialog(
            parent,
            title=title,
            callback=on_generate,
            available_report_types=available_report_types,
            entity_type=entity_type,
            size=size
        )

        # Return the result (None if cancelled)
        return result_config