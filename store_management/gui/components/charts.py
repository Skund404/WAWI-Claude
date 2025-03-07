"""
Chart components for data visualization.
Provides a factory for creating various types of charts.
"""
import logging
import tkinter as tk
from tkinter import ttk
from typing import Any, Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)

# Try to import matplotlib
try:
    import matplotlib
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure

    MATPLOTLIB_AVAILABLE = True
except ImportError:
    logger.warning("Matplotlib not available. Chart functionality will be limited.")
    MATPLOTLIB_AVAILABLE = False


class ChartFactory:
    """
    Factory for creating various types of charts.

    Provides methods for creating different visualizations such as:
    - Bar charts
    - Line charts
    - Pie charts
    - Scatter plots
    - Histograms
    """

    @staticmethod
    def create_bar_chart(parent: tk.Widget, data: Dict[str, Union[int, float]],
                         title: str = "", xlabel: str = "", ylabel: str = "",
                         width: int = 6, height: int = 4, color: str = "#1a73e8",
                         horizontal: bool = False, stacked: bool = False,
                         **kwargs) -> ttk.Frame:
        """
        Create a bar chart.

        Args:
            parent: Parent widget
            data: Dictionary of labels to values
            title: Chart title
            xlabel: X-axis label
            ylabel: Y-axis label
            width: Figure width in inches
            height: Figure height in inches
            color: Bar color
            horizontal: Whether to create a horizontal bar chart
            stacked: Whether to create a stacked bar chart (for grouped data)
            **kwargs: Additional arguments for matplotlib

        Returns:
            Frame containing the chart
        """
        if not MATPLOTLIB_AVAILABLE:
            return ChartFactory._create_chart_placeholder(parent, "Bar Chart")

        # Create frame for the chart
        frame = ttk.Frame(parent)

        # Create figure and axes
        fig = Figure(figsize=(width, height), dpi=100)
        ax = fig.add_subplot(111)

        # Plot the data
        if horizontal:
            if stacked and isinstance(next(iter(data.values() if data else {})), (list, tuple)):
                # Stacked horizontal bar chart for grouped data
                labels = list(data.keys())
                values_list = list(data.values())
                bottom = [0] * len(labels)

                for i, values in enumerate(zip(*values_list)):
                    ax.barh(labels, values, left=bottom, label=f"Series {i + 1}", **kwargs)
                    bottom = [b + v for b, v in zip(bottom, values)]

                ax.legend()
            else:
                # Simple horizontal bar chart
                ax.barh(list(data.keys()), list(data.values()), color=color, **kwargs)
        else:
            if stacked and isinstance(next(iter(data.values() if data else {})), (list, tuple)):
                # Stacked vertical bar chart for grouped data
                labels = list(data.keys())
                values_list = list(data.values())
                bottom = [0] * len(labels)

                for i, values in enumerate(zip(*values_list)):
                    ax.bar(labels, values, bottom=bottom, label=f"Series {i + 1}", **kwargs)
                    bottom = [b + v for b, v in zip(bottom, values)]

                ax.legend()
            else:
                # Simple vertical bar chart
                ax.bar(list(data.keys()), list(data.values()), color=color, **kwargs)

        # Set labels and title
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)

        # Rotate x-axis labels for better readability if not horizontal
        if not horizontal:
            plt.setp(ax.get_xticklabels(), rotation=45, ha="right")

        # Adjust layout
        fig.tight_layout()

        # Create canvas
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        return frame

    @staticmethod
    def create_line_chart(parent: tk.Widget, data: Dict[str, List[Union[int, float]]],
                          x_values: Optional[List] = None,
                          title: str = "", xlabel: str = "", ylabel: str = "",
                          width: int = 6, height: int = 4, grid: bool = True,
                          markers: bool = True, **kwargs) -> ttk.Frame:
        """
        Create a line chart.

        Args:
            parent: Parent widget
            data: Dictionary of series names to lists of values
            x_values: Optional list of x-axis values (default is indices)
            title: Chart title
            xlabel: X-axis label
            ylabel: Y-axis label
            width: Figure width in inches
            height: Figure height in inches
            grid: Whether to show grid lines
            markers: Whether to show markers on data points
            **kwargs: Additional arguments for matplotlib

        Returns:
            Frame containing the chart
        """
        if not MATPLOTLIB_AVAILABLE:
            return ChartFactory._create_chart_placeholder(parent, "Line Chart")

        # Create frame for the chart
        frame = ttk.Frame(parent)

        # Create figure and axes
        fig = Figure(figsize=(width, height), dpi=100)
        ax = fig.add_subplot(111)

        # Plot each series
        for label, values in data.items():
            if x_values:
                # Use provided x values
                x = x_values[:len(values)]  # Truncate if necessary
                ax.plot(x, values, label=label, marker='o' if markers else None, **kwargs)
            else:
                # Use indices as x values
                ax.plot(values, label=label, marker='o' if markers else None, **kwargs)

        # Show legend if there are multiple series
        if len(data) > 1:
            ax.legend()

        # Set labels and title
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)

        # Show grid
        if grid:
            ax.grid(True, linestyle='--', alpha=0.7)

        # Adjust layout
        fig.tight_layout()

        # Create canvas
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        return frame

    @staticmethod
    def create_pie_chart(parent: tk.Widget, data: Dict[str, Union[int, float]],
                         title: str = "", width: int = 6, height: int = 4,
                         colors: Optional[List[str]] = None,
                         explode: Optional[List[float]] = None,
                         shadow: bool = False,
                         startangle: int = 90,
                         autopct: str = '%1.1f%%', **kwargs) -> ttk.Frame:
        """
        Create a pie chart.

        Args:
            parent: Parent widget
            data: Dictionary of labels to values
            title: Chart title
            width: Figure width in inches
            height: Figure height in inches
            colors: Optional list of wedge colors
            explode: Optional list of wedge offsets
            shadow: Whether to draw shadow beneath pie
            startangle: Starting angle for wedges in degrees
            autopct: Format string for wedge labels
            **kwargs: Additional arguments for matplotlib

        Returns:
            Frame containing the chart
        """
        if not MATPLOTLIB_AVAILABLE:
            return ChartFactory._create_chart_placeholder(parent, "Pie Chart")

        # Create frame for the chart
        frame = ttk.Frame(parent)

        # Create figure and axes
        fig = Figure(figsize=(width, height), dpi=100)
        ax = fig.add_subplot(111)

        # Plot the data
        wedges, texts, autotexts = ax.pie(
            list(data.values()),
            labels=list(data.keys()),
            explode=explode,
            colors=colors,
            shadow=shadow,
            startangle=startangle,
            autopct=autopct,
            **kwargs
        )

        # Make the labels more readable
        for text in texts + autotexts:
            text.set_fontsize(9)

        # Equal aspect ratio ensures that pie is drawn as a circle
        ax.axis('equal')

        # Set title
        ax.set_title(title)

        # Adjust layout
        fig.tight_layout()

        # Create canvas
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        return frame

    @staticmethod
    def create_scatter_plot(parent: tk.Widget, x_values: List[Union[int, float]],
                            y_values: List[Union[int, float]],
                            title: str = "", xlabel: str = "", ylabel: str = "",
                            width: int = 6, height: int = 4, color: str = "#1a73e8",
                            marker: str = 'o', size: int = 50, grid: bool = True,
                            **kwargs) -> ttk.Frame:
        """
        Create a scatter plot.

        Args:
            parent: Parent widget
            x_values: X-axis values
            y_values: Y-axis values
            title: Chart title
            xlabel: X-axis label
            ylabel: Y-axis label
            width: Figure width in inches
            height: Figure height in inches
            color: Point color
            marker: Point marker style
            size: Point size
            grid: Whether to show grid lines
            **kwargs: Additional arguments for matplotlib

        Returns:
            Frame containing the chart
        """
        if not MATPLOTLIB_AVAILABLE:
            return ChartFactory._create_chart_placeholder(parent, "Scatter Plot")

        # Create frame for the chart
        frame = ttk.Frame(parent)

        # Create figure and axes
        fig = Figure(figsize=(width, height), dpi=100)
        ax = fig.add_subplot(111)

        # Plot the data
        ax.scatter(x_values, y_values, color=color, marker=marker, s=size, **kwargs)

        # Set labels and title
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)

        # Show grid
        if grid:
            ax.grid(True, linestyle='--', alpha=0.7)

        # Adjust layout
        fig.tight_layout()

        # Create canvas
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        return frame

    @staticmethod
    def create_histogram(parent: tk.Widget, data: List[Union[int, float]],
                         title: str = "", xlabel: str = "", ylabel: str = "Frequency",
                         width: int = 6, height: int = 4, color: str = "#1a73e8",
                         bins: Union[int, List] = 10, grid: bool = True,
                         **kwargs) -> ttk.Frame:
        """
        Create a histogram.

        Args:
            parent: Parent widget
            data: List of values to plot
            title: Chart title
            xlabel: X-axis label
            ylabel: Y-axis label
            width: Figure width in inches
            height: Figure height in inches
            color: Bar color
            bins: Number of bins or bin edges
            grid: Whether to show grid lines
            **kwargs: Additional arguments for matplotlib

        Returns:
            Frame containing the chart
        """
        if not MATPLOTLIB_AVAILABLE:
            return ChartFactory._create_chart_placeholder(parent, "Histogram")

        # Create frame for the chart
        frame = ttk.Frame(parent)

        # Create figure and axes
        fig = Figure(figsize=(width, height), dpi=100)
        ax = fig.add_subplot(111)

        # Plot the data
        ax.hist(data, bins=bins, color=color, **kwargs)

        # Set labels and title
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)

        # Show grid
        if grid:
            ax.grid(True, linestyle='--', alpha=0.7)

        # Adjust layout
        fig.tight_layout()

        # Create canvas
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        return frame

    @staticmethod
    def create_multi_chart(parent: tk.Widget, rows: int = 1, cols: int = 2,
                           width: int = 10, height: int = 6, shared_x: bool = False,
                           shared_y: bool = False) -> Tuple[ttk.Frame, Figure, List]:
        """
        Create a figure with multiple subplots.

        Args:
            parent: Parent widget
            rows: Number of rows
            cols: Number of columns
            width: Figure width in inches
            height: Figure height in inches
            shared_x: Whether subplots share x-axis
            shared_y: Whether subplots share y-axis

        Returns:
            Tuple of (frame, figure, axes_list)
        """
        if not MATPLOTLIB_AVAILABLE:
            return ChartFactory._create_chart_placeholder(parent, "Multi Chart"), None, []

        # Create frame for the chart
        frame = ttk.Frame(parent)

        # Create figure and axes
        fig, axes = plt.subplots(
            rows, cols,
            figsize=(width, height),
            dpi=100,
            sharex=shared_x,
            sharey=shared_y
        )

        # Adjust layout
        fig.tight_layout()

        # Create canvas
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Convert axes to list for easier access
        if rows == 1 and cols == 1:
            axes_list = [axes]
        elif rows == 1 or cols == 1:
            axes_list = list(axes)
        else:
            axes_list = [ax for axrow in axes for ax in axrow]

        return frame, fig, axes_list

    @staticmethod
    def _create_chart_placeholder(parent: tk.Widget, chart_type: str) -> ttk.Frame:
        """
        Create a placeholder for charts when matplotlib is not available.

        Args:
            parent: Parent widget
            chart_type: Type of chart to create a placeholder for

        Returns:
            Frame with placeholder message
        """
        frame = ttk.Frame(parent, style="Card.TFrame", padding=10)

        error_message = (
            f"{chart_type} not available.\n\n"
            "Matplotlib is required for chart functionality.\n"
            "Please install it with: pip install matplotlib"
        )

        label = ttk.Label(
            frame,
            text=error_message,
            justify=tk.CENTER,
            foreground="red"
        )
        label.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        return frame


# Example usage
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Chart Factory Demo")
    root.geometry("800x600")

    if not MATPLOTLIB_AVAILABLE:
        label = ttk.Label(
            root,
            text="Matplotlib is required for this demo.\nPlease install it with: pip install matplotlib",
            justify=tk.CENTER,
            foreground="red"
        )
        label.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    else:
        # Create notebook for different chart examples
        notebook = ttk.Notebook(root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Sample data
        sales_data = {
            "Jan": 12000,
            "Feb": 15000,
            "Mar": 18000,
            "Apr": 14000,
            "May": 19000,
            "Jun": 22000
        }

        product_data = {
            "Product A": 25,
            "Product B": 35,
            "Product C": 20,
            "Product D": 15,
            "Product E": 5
        }

        time_series = {
            "Series 1": [10, 12, 15, 18, 20, 22, 24],
            "Series 2": [8, 10, 14, 16, 19, 20, 21]
        }

        # Create bar chart
        bar_frame = ttk.Frame(notebook)
        bar_chart = ChartFactory.create_bar_chart(
            bar_frame,
            sales_data,
            title="Monthly Sales",
            xlabel="Month",
            ylabel="Sales ($)",
            width=8,
            height=4
        )
        bar_chart.pack(fill=tk.BOTH, expand=True)
        notebook.add(bar_frame, text="Bar Chart")

        # Create pie chart
        pie_frame = ttk.Frame(notebook)
        pie_chart = ChartFactory.create_pie_chart(
            pie_frame,
            product_data,
            title="Product Sales Distribution",
            width=7,
            height=5
        )
        pie_chart.pack(fill=tk.BOTH, expand=True)
        notebook.add(pie_frame, text="Pie Chart")

        # Create line chart
        line_frame = ttk.Frame(notebook)
        line_chart = ChartFactory.create_line_chart(
            line_frame,
            time_series,
            title="Time Series Data",
            xlabel="Time",
            ylabel="Value",
            width=8,
            height=4
        )
        line_chart.pack(fill=tk.BOTH, expand=True)
        notebook.add(line_frame, text="Line Chart")

        # Create multi chart
        multi_frame = ttk.Frame(notebook)
        frame, fig, axes = ChartFactory.create_multi_chart(
            multi_frame,
            rows=2,
            cols=2,
            width=8,
            height=6
        )

        # Plot on each subplot
        axes[0].bar(list(sales_data.keys()), list(sales_data.values()))
        axes[0].set_title("Monthly Sales")

        axes[1].pie(
            list(product_data.values()),
            labels=list(product_data.keys()),
            autopct='%1.1f%%'
        )
        axes[1].set_title("Product Distribution")

        for label, values in time_series.items():
            axes[2].plot(values, label=label)
        axes[2].legend()
        axes[2].set_title("Time Series")

        # Histogram of random data
        import numpy as np

        x = np.random.normal(0, 1, 1000)
        axes[3].hist(x, bins=30)
        axes[3].set_title("Histogram")

        # Adjust spacing between subplots
        fig.tight_layout()

        frame.pack(fill=tk.BOTH, expand=True)
        notebook.add(multi_frame, text="Multi Chart")

    root.mainloop()