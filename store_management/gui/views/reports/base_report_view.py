# gui/views/reports/base_report_view.py
"""
Base class for report views in the leatherworking ERP system.

This module provides a foundation for all types of reports, including
common functionality like date range selection, filtering, and export options.
"""

import logging
import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable, Tuple

from gui.base.base_view import BaseView
from gui.config import DEFAULT_PADDING
from gui.theme import COLORS
from utils.view_history_manager import ViewHistoryManager
from gui.widgets.enum_combobox import EnumCombobox

logger = logging.getLogger(__name__)


class DateRangeSelector(ttk.Frame):
    """A reusable component for selecting date ranges in reports."""

    PRESETS = {
        "Today": (0, 0),
        "Yesterday": (1, 1),
        "Last 7 Days": (6, 0),
        "Last 30 Days": (29, 0),
        "This Month": ("month_start", 0),
        "Last Month": ("last_month_start", "last_month_end"),
        "This Year": ("year_start", 0),
        "Last Year": ("last_year_start", "last_year_end"),
        "All Time": ("all", "all")
    }

    def __init__(self, parent, on_date_change: Optional[Callable] = None):
        """
        Initialize the date range selector.

        Args:
            parent: The parent widget
            on_date_change: Callback function when date range changes
        """
        super().__init__(parent)
        self.parent = parent
        self.on_date_change = on_date_change

        self.start_date = tk.StringVar()
        self.end_date = tk.StringVar()
        self.preset = tk.StringVar()

        self._build_ui()
        self._set_preset("Last 30 Days")  # Default selection

    def _build_ui(self):
        """Build the date range selector UI."""
        # Preset dropdown
        preset_frame = ttk.Frame(self)
        preset_frame.pack(fill=tk.X, padx=DEFAULT_PADDING, pady=(DEFAULT_PADDING, 0))

        ttk.Label(preset_frame, text="Preset Range:").pack(side=tk.LEFT, padx=(0, 5))
        preset_combo = ttk.Combobox(preset_frame, textvariable=self.preset,
                                    values=list(self.PRESETS.keys()),
                                    state="readonly", width=15)
        preset_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        preset_combo.bind("<<ComboboxSelected>>", self._on_preset_change)

        # Date range inputs
        date_frame = ttk.Frame(self)
        date_frame.pack(fill=tk.X, padx=DEFAULT_PADDING, pady=(5, DEFAULT_PADDING))

        ttk.Label(date_frame, text="From:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(date_frame, textvariable=self.start_date, width=10).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(date_frame, text="To:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(date_frame, textvariable=self.end_date, width=10).pack(side=tk.LEFT)

        # Calendar picker button
        ttk.Button(date_frame, text="📅", width=3,
                   command=self._show_date_picker).pack(side=tk.LEFT, padx=(5, 0))

        # Apply button
        ttk.Button(date_frame, text="Apply",
                   command=self._apply_date_range).pack(side=tk.RIGHT)

    def _on_preset_change(self, event):
        """Handle preset selection change."""
        self._set_preset(self.preset.get())
        self._apply_date_range()

    def _set_preset(self, preset_name: str):
        """Set date range based on selected preset."""
        if preset_name not in self.PRESETS:
            return

        start_offset, end_offset = self.PRESETS[preset_name]
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        # Handle special string-based offsets
        if start_offset == "month_start":
            start_date = today.replace(day=1)
        elif start_offset == "last_month_start":
            last_month = today.replace(day=1) - timedelta(days=1)
            start_date = last_month.replace(day=1)
        elif start_offset == "last_month_end":
            start_date = today.replace(day=1) - timedelta(days=1)
        elif start_offset == "year_start":
            start_date = today.replace(month=1, day=1)
        elif start_offset == "last_year_start":
            start_date = today.replace(year=today.year - 1, month=1, day=1)
        elif start_offset == "last_year_end":
            start_date = today.replace(year=today.year - 1, month=12, day=31)
        elif start_offset == "all":
            # For "All Time", use a very old date
            start_date = datetime(2000, 1, 1)
        else:
            # Numeric offset in days
            start_date = today - timedelta(days=start_offset)

        # Set end date
        if end_offset == "last_month_end":
            end_date = today.replace(day=1) - timedelta(days=1)
        elif end_offset == "all":
            # For "All Time", use today as end date
            end_date = today
        elif end_offset == 0:
            end_date = today
        else:
            # Numeric offset in days
            end_date = today - timedelta(days=end_offset)

        # Update the string variables
        self.start_date.set(start_date.strftime("%Y-%m-%d"))
        self.end_date.set(end_date.strftime("%Y-%m-%d"))

    def _show_date_picker(self):
        """Show a date picker dialog."""
        # This is a placeholder - in a real implementation,
        # we would show a calendar widget for date selection
        logger.info("Date picker not yet implemented")
        # In the actual implementation, this would display a calendar
        # for selecting start and end dates

    def _apply_date_range(self):
        """Apply the selected date range and trigger callback."""
        if self.on_date_change:
            try:
                start = datetime.strptime(self.start_date.get(), "%Y-%m-%d")
                end = datetime.strptime(self.end_date.get(), "%Y-%m-%d")
                self.on_date_change(start, end)
            except ValueError as e:
                logger.error(f"Invalid date format: {e}")

    def get_date_range(self) -> Tuple[datetime, datetime]:
        """
        Get the currently selected date range.

        Returns:
            Tuple of (start_date, end_date)
        """
        try:
            start = datetime.strptime(self.start_date.get(), "%Y-%m-%d")
            end = datetime.strptime(self.end_date.get(), "%Y-%m-%d")
            return start, end
        except ValueError:
            # Return a default range if parsing fails
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            return today - timedelta(days=30), today


class BaseReportView(BaseView):
    """
    Base class for all report views in the system.

    Provides common functionality for reports, including date range selection,
    filtering options, and export capabilities.
    """

    # Report title to display in the header
    REPORT_TITLE = "Report"

    # Optional description to display under the title
    REPORT_DESCRIPTION = ""

    def __init__(self, parent):
        """
        Initialize the base report view.

        Args:
            parent: The parent widget
        """
        super().__init__(parent)
        self.parent = parent

        # State variables
        self.filters = {}  # Dictionary to store filter values
        self.report_data = []  # List to store report data
        self.is_loading = False  # Flag to track loading state

        # UI elements
        self.content_frame = None
        self.filter_frame = None
        self.report_frame = None
        self.status_label = None
        self.date_selector = None

        # Build the UI
        self.build()

    def build(self):
        """Build the report view layout."""
        self.create_header()

        # Main content frame
        self.content_frame = ttk.Frame(self)
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=DEFAULT_PADDING, pady=DEFAULT_PADDING)

        # Filter section
        self.filter_frame = ttk.LabelFrame(self.content_frame, text="Filters")
        self.filter_frame.pack(fill=tk.X, padx=0, pady=(0, DEFAULT_PADDING))

        # Add date range selector
        self.date_selector = DateRangeSelector(self.filter_frame, self._on_date_range_change)
        self.date_selector.pack(fill=tk.X, padx=0, pady=(0, 5))

        # Add custom filters
        self.create_filters(self.filter_frame)

        # Add filter action buttons
        filter_actions = ttk.Frame(self.filter_frame)
        filter_actions.pack(fill=tk.X, padx=DEFAULT_PADDING, pady=DEFAULT_PADDING)

        ttk.Button(filter_actions, text="Apply Filters",
                   command=self.apply_filters).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(filter_actions, text="Reset Filters",
                   command=self.reset_filters).pack(side=tk.RIGHT)

        # Report content section
        self.report_frame = ttk.Frame(self.content_frame)
        self.report_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        # Create the report content (will be implemented by subclasses)
        self.create_report_content(self.report_frame)

        # Status bar
        status_frame = ttk.Frame(self)
        status_frame.pack(fill=tk.X, padx=DEFAULT_PADDING, pady=(0, DEFAULT_PADDING))

        # Left side: status message
        self.status_label = ttk.Label(status_frame, text="Ready")
        self.status_label.pack(side=tk.LEFT)

        # Right side: export options
        export_frame = ttk.Frame(status_frame)
        export_frame.pack(side=tk.RIGHT)

        ttk.Button(export_frame, text="Export PDF",
                   command=self.export_pdf).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(export_frame, text="Print",
                   command=self.print_report).pack(side=tk.LEFT)

        # Initial data load
        self.load_report_data()

    def _add_default_action_buttons(self):
        """Add default action buttons to the header."""
        # Add refresh button
        refresh_btn = ttk.Button(self.header_actions, text="Refresh",
                                 command=self.refresh)
        refresh_btn.pack(side=tk.RIGHT, padx=(0, 5))

    def create_header(self):
        """Create a standard header for the report view."""
        self.header_frame = ttk.Frame(self)
        self.header_frame.pack(fill=tk.X, padx=DEFAULT_PADDING, pady=DEFAULT_PADDING)

        # Title section
        title_frame = ttk.Frame(self.header_frame)
        title_frame.pack(side=tk.LEFT, fill=tk.Y)

        title_label = ttk.Label(title_frame, text=self.REPORT_TITLE,
                                font=("TkDefaultFont", 14, "bold"))
        title_label.pack(anchor=tk.W)

        if self.REPORT_DESCRIPTION:
            desc_label = ttk.Label(title_frame, text=self.REPORT_DESCRIPTION)
            desc_label.pack(anchor=tk.W)

        # Action buttons section
        self.header_actions = ttk.Frame(self.header_frame)
        self.header_actions.pack(side=tk.RIGHT, fill=tk.Y)

        self._add_default_action_buttons()

    def create_filters(self, parent):
        """
        Create filter inputs for the report.
        To be overridden by subclasses to add specific filters.

        Args:
            parent: The parent widget
        """
        pass

    def create_report_content(self, parent):
        """
        Create the main report content.
        Must be implemented by subclasses.

        Args:
            parent: The parent widget
        """
        ttk.Label(parent, text="Report content will be displayed here").pack(
            fill=tk.BOTH, expand=True, padx=50, pady=50)

    def _on_date_range_change(self, start_date, end_date):
        """
        Handle date range change.

        Args:
            start_date: The new start date
            end_date: The new end date
        """
        self.filters['start_date'] = start_date
        self.filters['end_date'] = end_date

    def apply_filters(self):
        """Apply current filters and reload report data."""
        self.load_report_data()

    def reset_filters(self):
        """Reset filters to default values."""
        # Clear filters dictionary
        self.filters = {}

        # Reset date selector to default
        if self.date_selector:
            self.date_selector._set_preset("Last 30 Days")
            self._on_date_range_change(*self.date_selector.get_date_range())

        # Reset custom filters (to be implemented by subclasses)
        self.reset_custom_filters()

        # Reload data
        self.load_report_data()

    def reset_custom_filters(self):
        """
        Reset custom filters to their default values.
        To be overridden by subclasses.
        """
        pass

    def load_report_data(self):
        """
        Load report data based on current filters.
        To be implemented by subclasses.
        """
        self.update_status("Loading report data...")
        self.is_loading = True

        # In a real implementation, this would be done in a separate thread
        # to prevent UI freezing during data loading

        # Example implementation
        self.report_data = []
        self.update_report_display()

        self.is_loading = False
        self.update_status("Report data loaded")

    def update_report_display(self):
        """
        Update the report display with current data.
        To be implemented by subclasses.
        """
        pass

    def update_status(self, message):
        """
        Update the status message.

        Args:
            message: The status message to display
        """
        if self.status_label:
            self.status_label.config(text=message)

    def export_pdf(self):
        """Export the report to PDF."""
        self.update_status("Exporting to PDF...")
        # This would typically call a method from export_utils.py
        # For now, we'll just log it
        logger.info("Export to PDF not yet implemented")
        self.update_status("PDF export not yet implemented")

    def print_report(self):
        """Print the report."""
        self.update_status("Preparing to print...")
        # This would typically call a method from export_utils.py
        # For now, we'll just log it
        logger.info("Print functionality not yet implemented")
        self.update_status("Print functionality not yet implemented")

    def refresh(self):
        """Refresh the report data."""
        self.load_report_data()