# gui/widgets/charts/__init__.py
"""
Chart components for data visualization.

This module provides easy access to various chart components
for visualizing data in the application.
"""

from gui.widgets.charts.bar_chart import BarChart
from gui.widgets.charts.line_chart import LineChart
from gui.widgets.charts.pie_chart import PieChart


def create_chart(chart_type, parent, data, **kwargs):
    """
    Create a chart of the specified type.

    Args:
        chart_type: Type of chart ('bar', 'line', 'pie')
        parent: Parent widget for the chart
        data: Data for the chart
        **kwargs: Additional arguments for the specific chart type

    Returns:
        Chart widget of the specified type

    Raises:
        ValueError: If chart_type is not supported
    """
    if chart_type == 'bar':
        return BarChart(parent, data, **kwargs)
    elif chart_type == 'line':
        return LineChart(parent, data, **kwargs)
    elif chart_type == 'pie':
        return PieChart(parent, data, **kwargs)
    else:
        raise ValueError(f"Unsupported chart type: {chart_type}")


# Function to convert data into the format needed for charts
def prepare_chart_data(data, label_key=None, value_key=None):
    """
    Prepare data for charts by converting into the expected format.

    Args:
        data: Data to prepare (dictionary, list of tuples, etc.)
        label_key: Key to use for labels (or None to use keys or indices)
        value_key: Key to use for values (or None to use values directly)

    Returns:
        List of dictionaries suitable for charts
    """
    result = []

    if isinstance(data, dict):
        # Convert dict to list of dicts
        for key, value in data.items():
            if isinstance(value, dict):
                # Handle nested dict
                if label_key is not None and value_key is not None:
                    if label_key in value and value_key in value:
                        result.append({
                            'label': value[label_key],
                            'value': value[value_key]
                        })
                else:
                    # Use key as label and value dict as is
                    item = {'label': key}
                    item.update(value)
                    result.append(item)
            else:
                # Simple key-value pairs
                result.append({
                    'label': key,
                    'value': value
                })

    elif isinstance(data, list):
        for i, item in enumerate(data):
            if isinstance(item, dict):
                # Dictionary items
                if label_key is not None and value_key is not None:
                    # Extract specified keys
                    if label_key in item and value_key in item:
                        result.append({
                            'label': item[label_key],
                            'value': item[value_key]
                        })
                else:
                    # Use entire dict
                    result.append(item)

            elif isinstance(item, tuple) and len(item) >= 2:
                # Tuple items (label, value)
                result.append({
                    'label': item[0],
                    'value': item[1]
                })

            else:
                # Simple values
                result.append({
                    'label': f"Item {i}",
                    'value': item
                })

    return result


# Example chart creation helpers
def create_bar_chart(parent, data, **kwargs):
    """Create a bar chart with sensible defaults."""
    return BarChart(parent, data, **kwargs)


def create_line_chart(parent, data, **kwargs):
    """Create a line chart with sensible defaults."""
    return LineChart(parent, data, **kwargs)


def create_pie_chart(parent, data, **kwargs):
    """Create a pie chart with sensible defaults."""
    return PieChart(parent, data, **kwargs)


def create_dashboard_kpi_chart(parent, title, current_value, previous_value, **kwargs):
    """
    Create a small KPI chart for dashboards.

    Args:
        parent: Parent widget
        title: KPI title
        current_value: Current KPI value
        previous_value: Previous period KPI value
        **kwargs: Additional arguments

    Returns:
        Line chart widget configured for KPI display
    """
    # Calculate percent change
    if previous_value and previous_value != 0:
        percent_change = ((current_value - previous_value) / abs(previous_value)) * 100
        change_str = f"{percent_change:+.1f}%"
    else:
        change_str = "N/A"

    # Create display title with change indicator
    display_title = f"{title}: {current_value:,.1f} ({change_str})"

    # Generate some trend data (placeholder)
    trend_data = [
        {"period": "Previous", "value": previous_value},
        {"period": "Current", "value": current_value}
    ]

    # Create compact line chart
    chart = LineChart(
        parent,
        data=trend_data,
        title=display_title,
        width=kwargs.get('width', 300),
        height=kwargs.get('height', 150),
        show_markers=kwargs.get('show_markers', True),
        show_area=kwargs.get('show_area', True),
        show_grid=kwargs.get('show_grid', False),
        line_color=COLORS["success"] if current_value >= previous_value else COLORS["danger"],
        **kwargs
    )

    return chart