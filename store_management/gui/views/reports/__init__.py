# gui/views/reports/__init__.py
"""
Reports module for the leatherworking ERP system.

This module provides various reports for inventory, sales, and projects,
along with data export capabilities.
"""

from gui.views.reports.base_report_view import BaseReportView, DateRangeSelector
from gui.views.reports.inventory_reports import StockLevelReport
from gui.views.reports.export_utils import ReportExporter, get_default_report_filename

# Define available reports
AVAILABLE_REPORTS = {
    # Inventory Reports
    "inventory_stock_level": {
        "name": "Inventory Stock Level Report",
        "description": "Overview of current inventory levels by material type",
        "category": "Inventory",
        "view_class": StockLevelReport
    },

    # Placeholder for future reports
    # Sales reports will be added in Phase 2
    # Project reports will be added in Phase 3
}


def get_report_view_class(report_id: str):
    """
    Get the view class for a report by ID.

    Args:
        report_id: The report identifier

    Returns:
        The report view class or None if not found
    """
    report_info = AVAILABLE_REPORTS.get(report_id)
    return report_info["view_class"] if report_info else None


def get_report_categories():
    """
    Get a list of report categories with their reports.

    Returns:
        Dictionary of categories and their reports
    """
    categories = {}

    for report_id, report_info in AVAILABLE_REPORTS.items():
        category = report_info.get("category", "Uncategorized")

        if category not in categories:
            categories[category] = []

        categories[category].append({
            "id": report_id,
            "name": report_info["name"],
            "description": report_info.get("description", "")
        })

    return categories