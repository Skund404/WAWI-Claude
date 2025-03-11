# gui/widgets/charts/heatmap.py
"""
Heatmap chart widget for data visualization.

This module defines a customizable heatmap chart for visualizing tabular data
where color intensity corresponds to value magnitude.
"""

import tkinter as tk
from tkinter import ttk
from typing import Any, Dict, List, Optional, Tuple

from gui.theme import COLORS


class HeatmapChart(ttk.Frame):
    """Heatmap chart widget for displaying tabular data with color intensity."""

    def __init__(
            self,
            parent,
            data: Optional[List[Dict[str, Any]]] = None,
            title: str = "Heatmap Chart",
            x_label: str = "X Axis",
            y_label: str = "Y Axis",
            x_key: str = "x",
            y_key: str = "y",
            value_key: str = "value",
            width: int = 500,
            height: int = 400,
            cell_width: int = 40,
            cell_height: int = 30,
            color_min: str = COLORS["light_blue"],
            color_max: str = COLORS["dark_blue"],
            **kwargs
    ):
        """
        Initialize the heatmap chart.

        Args:
            parent: The parent widget
            data: List of data points
            title: Chart title
            x_label: X-axis label
            y_label: Y-axis label
            x_key: Data key for x values
            y_key: Data key for y values
            value_key: Data key for cell values
            width: Chart width
            height: Chart height
            cell_width: Width of heatmap cells
            cell_height: Height of heatmap cells
            color_min: Color for minimum values
            color_max: Color for maximum values
            **kwargs: Additional arguments
        """
        super().__init__(parent, **kwargs)
        self.parent = parent
        self.data = data or []
        self.title = title
        self.x_label = x_label
        self.y_label = y_label
        self.x_key = x_key
        self.y_key = y_key
        self.value_key = value_key
        self.chart_width = width
        self.chart_height = height
        self.cell_width = cell_width
        self.cell_height = cell_height
        self.color_min = color_min
        self.color_max = color_max

        self.padding = 10
        self.title_height = 30
        self.axis_label_space = 30
        self.label_padding = 5

        self.tooltip = None
        self.cells = []
        self.x_labels = []
        self.y_labels = []
        self.min_value = 0
        self.max_value = 0

        self._build_chart()

        if self.data:
            self.update_data(self.data)

    def _build_chart(self):
        """Build the chart layout."""
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # Create the main frame
        self.main_frame = ttk.Frame(self)
        self.main_frame.grid(row=0, column=0, sticky="nsew")

        # Create the title
        self._create_title()

        # Create the chart area
        self._create_chart_area()

        # Bind mouse events for tooltips
        self.canvas.bind("<Motion>", self._on_mouse_move)
        self.canvas.bind("<Leave>", self._on_mouse_leave)

    def _create_title(self):
        """Create the chart title."""
        self.title_label = ttk.Label(
            self.main_frame,
            text=self.title,
            font=("TkDefaultFont", 12, "bold"),
            anchor="center"
        )
        self.title_label.pack(side=tk.TOP, fill=tk.X, pady=(0, self.padding))

    def _create_chart_area(self):
        """Create the chart drawing area."""
        # Create canvas for the heatmap
        self.canvas_frame = ttk.Frame(self.main_frame)
        self.canvas_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Y-axis label
        self.y_axis_label = ttk.Label(
            self.canvas_frame,
            text=self.y_label,
            angle=90,  # This won't work directly with ttk.Label, we'll handle it in render()
            anchor="center"
        )
        self.y_axis_label.pack(side=tk.LEFT, padx=(0, self.label_padding))

        # Canvas for the heatmap
        self.canvas = tk.Canvas(
            self.canvas_frame,
            width=self.chart_width,
            height=self.chart_height,
            bg="white"
        )
        self.canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # X-axis label
        self.x_axis_label = ttk.Label(
            self.main_frame,
            text=self.x_label,
            anchor="center"
        )
        self.x_axis_label.pack(side=tk.TOP, padx=self.padding)

    def render(self):
        """Render the chart with the current data."""
        self._clear_chart_elements()

        if not self.data or not self.x_labels or not self.y_labels:
            return

        # Handle Y-axis label rotation (since ttk.Label doesn't support rotation)
        # We'll use canvas text for rotation
        self.canvas.create_text(
            self.padding,
            self.chart_height // 2,
            text=self.y_label,
            angle=90,
            anchor="center",
            tags="y_label"
        )

        # Draw the heatmap grid
        x_offset = self.axis_label_space + self.padding
        y_offset = self.padding

        # Draw Y-axis labels
        for i, label in enumerate(self.y_labels):
            y = y_offset + i * self.cell_height + self.cell_height // 2
            self.canvas.create_text(
                x_offset - self.label_padding,
                y,
                text=str(label),
                anchor="e",
                tags="y_labels"
            )

        # Draw X-axis labels
        for i, label in enumerate(self.x_labels):
            x = x_offset + i * self.cell_width + self.cell_width // 2
            self.canvas.create_text(
                x,
                y_offset + len(self.y_labels) * self.cell_height + self.label_padding,
                text=str(label),
                anchor="n",
                tags="x_labels"
            )

        # Draw the cells
        self.cells = []
        for point in self.data:
            try:
                x_index = self.x_labels.index(point[self.x_key])
                y_index = self.y_labels.index(point[self.y_key])
                value = point[self.value_key]

                # Calculate color based on value
                color = self._get_color_for_value(value)

                # Draw the cell
                x1 = x_offset + x_index * self.cell_width
                y1 = y_offset + y_index * self.cell_height
                x2 = x1 + self.cell_width
                y2 = y1 + self.cell_height

                cell_id = self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    fill=color,
                    outline=COLORS["border"],
                    tags="cells"
                )

                # Store the cell info for tooltips
                self.cells.append({
                    "id": cell_id,
                    "x1": x1,
                    "y1": y1,
                    "x2": x2,
                    "y2": y2,
                    "value": value,
                    "x_label": self.x_labels[x_index],
                    "y_label": self.y_labels[y_index]
                })

                # Add text for values that are significant
                if self.max_value - self.min_value > 0 and (value - self.min_value) / (
                        self.max_value - self.min_value) > 0.7:
                    text_color = "white"
                else:
                    text_color = "black"

                self.canvas.create_text(
                    (x1 + x2) // 2,
                    (y1 + y2) // 2,
                    text=str(value) if isinstance(value, int) else f"{value:.1f}",
                    fill=text_color,
                    tags="cell_values"
                )
            except (ValueError, KeyError):
                # Skip data points that don't match the axes
                continue

    def _clear_chart_elements(self):
        """Clear the chart elements."""
        self.canvas.delete("cells")
        self.canvas.delete("x_labels")
        self.canvas.delete("y_labels")
        self.canvas.delete("cell_values")
        self.canvas.delete("y_label")
        self._hide_tooltip()

    def update_data(self, data: List[Dict[str, Any]]):
        """
        Update the chart with new data.

        Args:
            data: List of dictionaries with chart data
        """
        self.data = data

        # Extract unique x and y values
        self.x_labels = sorted(list(set(point[self.x_key] for point in data)))
        self.y_labels = sorted(list(set(point[self.y_key] for point in data)))

        # Find min/max values for color scaling
        values = [point[self.value_key] for point in data]
        self.min_value = min(values) if values else 0
        self.max_value = max(values) if values else 0

        # Render the chart
        self.render()

    def _get_color_for_value(self, value: float) -> str:
        """
        Get the color for a value based on the min/max range.

        Args:
            value: The value to get the color for

        Returns:
            Hex color string
        """
        # If min and max are the same, use the min color
        if self.max_value == self.min_value:
            return self.color_min

        # Calculate intensity (0.0 to 1.0)
        intensity = (value - self.min_value) / (self.max_value - self.min_value)

        # Interpolate between min and max colors
        r1, g1, b1 = self._hex_to_rgb(self.color_min)
        r2, g2, b2 = self._hex_to_rgb(self.color_max)

        r = int(r1 + (r2 - r1) * intensity)
        g = int(g1 + (g2 - g1) * intensity)
        b = int(b1 + (b2 - b1) * intensity)

        return f"#{r:02x}{g:02x}{b:02x}"

    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """
        Convert hex color to RGB.

        Args:
            hex_color: Hex color string (#RRGGBB)

        Returns:
            Tuple of (r, g, b) values
        """
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))

    def _create_tooltip(self, x: int, y: int, text: str):
        """
        Create tooltip at the specified position.

        Args:
            x: X coordinate
            y: Y coordinate
            text: Tooltip text
        """
        self._hide_tooltip()

        self.tooltip = tk.Toplevel(self)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")

        label = ttk.Label(
            self.tooltip,
            text=text,
            background=COLORS["tooltip_bg"],
            foreground=COLORS["tooltip_fg"],
            relief="solid",
            borderwidth=1,
            padding=4
        )
        label.pack()

    def _on_mouse_move(self, event):
        """
        Handle mouse movement to show tooltips.

        Args:
            event: The mouse event
        """
        x, y = event.x, event.y

        # Check if the mouse is over a cell
        for cell in self.cells:
            if cell["x1"] <= x <= cell["x2"] and cell["y1"] <= y <= cell["y2"]:
                # Show tooltip
                tooltip_text = f"{cell['y_label']}, {cell['x_label']}: {cell['value']}"
                self._create_tooltip(
                    self.winfo_rootx() + x + 15,
                    self.winfo_rooty() + y + 10,
                    tooltip_text
                )
                return

        # If not over a cell, hide the tooltip
        self._hide_tooltip()

    def _on_mouse_leave(self, event):
        """
        Handle mouse leave event to hide tooltips.

        Args:
            event: The mouse event
        """
        self._hide_tooltip()

    def _hide_tooltip(self):
        """Hide the tooltip."""
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None