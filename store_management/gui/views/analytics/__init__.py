# gui/views/analytics/__init__.py
"""
Analytics views module for the leatherworking ERP system.

This module initializes and provides access to the various analytics views.
"""

from gui.views.analytics.analytics_dashboard import AnalyticsDashboardView
from gui.views.analytics.customer_analytics_view import CustomerAnalyticsView
from gui.views.analytics.material_usage_view import MaterialUsageView
from gui.views.analytics.profitability_analytics_view import ProfitabilityAnalyticsView
from gui.views.analytics.project_metrics_view import ProjectMetricsView

# Dictionary of available analytics views
ANALYTICS_VIEWS = {
    "dashboard": AnalyticsDashboardView,
    "customer": CustomerAnalyticsView,
    "profitability": ProfitabilityAnalyticsView,
    "material_usage": MaterialUsageView,
    "project_metrics": ProjectMetricsView
}

# Dictionary of view titles
ANALYTICS_TITLES = {
    "dashboard": "Analytics Dashboard",
    "customer": "Customer Analytics",
    "profitability": "Profitability Analytics",
    "material_usage": "Material Usage Analytics",
    "project_metrics": "Project Metrics Analytics"
}


def get_analytics_view(view_name, parent):
    """
    Get an analytics view instance by name.

    Args:
        view_name: Name of the view to get
        parent: Parent widget for the view

    Returns:
        View instance or None if view_name is invalid
    """
    view_class = ANALYTICS_VIEWS.get(view_name)

    if view_class:
        return view_class(parent)

    return None


def get_analytics_title(view_name):
    """
    Get the title for an analytics view.

    Args:
        view_name: Name of the view

    Returns:
        View title or empty string if view_name is invalid
    """
    return ANALYTICS_TITLES.get(view_name, "")


def get_all_analytics_views():
    """
    Get a list of all available analytics views.

    Returns:
        List of dictionaries with view information
    """
    return [
        {
            "id": view_id,
            "title": ANALYTICS_TITLES.get(view_id, ""),
            "class": view_class
        }
        for view_id, view_class in ANALYTICS_VIEWS.items()
    ]