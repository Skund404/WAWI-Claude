# gui/widgets/charts/line_chart.py
"""
Line chart widget for displaying trend data.

This module provides a line chart component for visualizing trend data over time.
"""

import tkinter as tk
from tkinter import ttk
from typing import Any, Dict, List, Optional, Tuple

from gui.theme import COLORS


class LineChart(ttk.Frame):
    """A line chart widget that displays trend data as a line."""

    def __init__(
            self,
            parent,
            data: List[Dict[str, Any]],
            x_key: str = "period",
            y_key: str = "value",
            title: str = "Line Chart",
            width: int = 600,
            height: int = 400,
            x_label: str = "",
            y_label: str = "",
            line_color: str = COLORS["primary"],
            line_width: int = 2,
            marker_size: int = 5,
            show_markers: bool = True,
            show_area: bool = False,
            area_color: Optional[str] = None,
            show_values: bool = False,
            show_grid: bool = True,
            animate: bool = True,
            **kwargs
    ):
        """
        Initialize the line chart widget.

        Args:
            parent: The parent widget
            data: List of dictionaries with chart data
            x_key: Key in data dictionaries for x-axis labels
            y_key: Key in data dictionaries for y-axis values
            title: Chart title
            width: Chart width
            height: Chart height
            x_label: X-axis label
            y_label: Y-axis label
            line_color: Line color
            line_width: Line width
            marker_size: Size of data point markers
            show_markers: Whether to show data point markers
            show_area: Whether to fill the area under the line
            area_color: Color for the area under the line (or None to use transparent line_color)
            show_values: Whether to show values at data points
            show_grid: Whether to show grid lines
            animate: Whether to animate the chart on initial display
        """
        super().__init__(parent, **kwargs)
        self.data = data
        self.x_key = x_key
        self.y_key = y_key
        self.title = title
        self.chart_width = width
        self.chart_height = height
        self.x_label = x_label
        self.y_label = y_label
        self.line_color = line_color
        self.line_width = line_width
        self.marker_size = marker_size
        self.show_markers = show_markers
        self.show_area = show_area
        self.area_color = area_color or self.line_color  # Default to line color
        self.show_values = show_values
        self.show_grid = show_grid
        self.animate = animate

        # Internal variables
        self.canvas = None
        self.chart_area = None
        self.x_axis = None
        self.y_axis = None
        self.line_segments = []
        self.markers = []
        self.area = None
        self.value_labels = []
        self.grid_lines = []
        self.tooltip = None
        self.tooltip_visible = False

        # Layout
        self.padding = 50  # Padding around the chart
        self.axis_padding = 10  # Padding between axis and chart area

        # Animation
        self.animation_duration = 500  # ms
        self.animation_steps = 20
        self.animation_step = 0

        # Build the chart
        self._build_chart()

        # If data is provided, render it
        if self.data:
            self.render()

    def _build_chart(self):
        """Build the chart layout."""
        # Create canvas
        self.canvas = tk.Canvas(
            self,
            width=self.chart_width,
            height=self.chart_height,
            bg=COLORS["background"]
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Create chart elements
        self._create_title()
        self._create_chart_area()

        # Set up mouse events for tooltips
        self.canvas.bind("<Motion>", self._on_mouse_move)
        self.canvas.bind("<Leave>", self._on_mouse_leave)

    def _create_title(self):
        """Create the chart title."""
        self.canvas.create_text(
            self.chart_width // 2,
            self.padding // 2,
            text=self.title,
            fill=COLORS["text"],
            font=("Helvetica", 14, "bold"),
            tags=("title",)
        )

    def _create_chart_area(self):
        """Create the chart drawing area."""
        # Calculate chart area dimensions
        left = self.padding + 30  # Extra space for y-axis labels
        top = self.padding
        right = self.chart_width - self.padding
        bottom = self.chart_height - self.padding - 30  # Extra space for x-axis labels

        # Create chart background
        self.chart_area = (left, top, right, bottom)
        self.canvas.create_rectangle(
            *self.chart_area,
            fill=COLORS["background"],
            outline=COLORS["border"],
            width=1,
            tags=("chart_bg",)
        )

        # Create x-axis
        self.x_axis = (left, bottom, right, bottom)
        self.canvas.create_line(
            *self.x_axis,
            fill=COLORS["text"],
            width=2,
            tags=("x_axis",)
        )

        # Create y-axis
        self.y_axis = (left, top, left, bottom)
        self.canvas.create_line(
            *self.y_axis,
            fill=COLORS["text"],
            width=2,
            tags=("y_axis",)
        )

        # Add axis labels
        if self.x_label:
            self.canvas.create_text(
                (left + right) // 2,
                bottom + 30,
                text=self.x_label,
                fill=COLORS["text"],
                font=("Helvetica", 10),
                tags=("x_label",)
            )

        if self.y_label:
            self.canvas.create_text(
                left - 40,
                (top + bottom) // 2,
                text=self.y_label,
                fill=COLORS["text"],
                font=("Helvetica", 10),
                angle=90,  # Rotated text
                tags=("y_label",)
            )

    def render(self):
        """Render the chart with the current data."""
        if not self.data:
            return

        # Clear previous elements
        self._clear_chart_elements()

        # Calculate value range for y-axis
        max_value = max(item.get(self.y_key, 0) for item in self.data)
        min_value = min(item.get(self.y_key, 0) for item in self.data)

        # Add padding to value range
        value_range = max_value - min_value
        if value_range == 0:
            # If all values are the same, create a range around the value
            value_range = max(1, abs(max_value) * 0.2)  # At least 1 or 20% of the value
            min_value = max_value - value_range
        else:
            # Add 10% padding to range
            padding = value_range * 0.1
            max_value += padding
            min_value -= padding

        # Start from zero if all values are positive and close to zero
        if min_value > 0 and min_value < value_range * 0.2:
            min_value = 0

        # Calculate chart dimensions
        left, top, right, bottom = self.chart_area
        chart_height = bottom - top
        chart_width = right - left

        # Calculate y-axis ticks and labels
        num_ticks = 5
        tick_values = []
        for i in range(num_ticks + 1):
            tick_values.append(min_value + (value_range * i / num_ticks))

        # Draw grid lines and y-axis labels
        for i, value in enumerate(tick_values):
            y_pos = bottom - (value - min_value) / value_range * chart_height

            # Draw grid line
            if self.show_grid and i > 0:
                grid_line = self.canvas.create_line(
                    left, y_pos, right, y_pos,
                    fill=COLORS["border"],
                    dash=(2, 4),
                    tags=("grid_line",)
                )
                self.grid_lines.append(grid_line)

            # Draw y-axis tick
            tick = self.canvas.create_line(
                left - 5, y_pos, left, y_pos,
                fill=COLORS["text"],
                tags=("y_tick",)
            )

            # Draw y-axis label
            format_str = "{:.0f}" if value == int(value) else "{:.1f}"
            label = self.canvas.create_text(
                left - 10,
                y_pos,
                text=format_str.format(value),
                fill=COLORS["text"],
                font=("Helvetica", 8),
                anchor="e",
                tags=("y_label",)
            )

        # Calculate x-axis positions
        x_positions = []
        for i, item in enumerate(self.data):
            x_value = item.get(self.x_key, f"Item {i}")
            x_pos = left + (i / (len(self.data) - 1 or 1)) * chart_width if len(self.data) > 1 else (left + right) // 2
            x_positions.append((x_pos, x_value))

        # Draw x-axis labels
        for i, (x_pos, x_value) in enumerate(x_positions):
            # Draw x-axis tick
            self.canvas.create_line(
                x_pos, bottom, x_pos, bottom + 5,
                fill=COLORS["text"],
                tags=("x_tick",)
            )

            # Draw x-axis label
            self.canvas.create_text(
                x_pos,
                bottom + 15,
                text=str(x_value),
                fill=COLORS["text"],
                font=("Helvetica", 8),
                angle=45 if len(str(x_value)) > 5 else 0,  # Rotate if text is long
                anchor="ne" if len(str(x_value)) > 5 else "n",
                tags=("x_label",)
            )

        # Calculate y positions and create points
        points = []
        for i, item in enumerate(self.data):
            x_pos = x_positions[i][0]
            y_value = item.get(self.y_key, 0)
            try:
                y_value = float(y_value)
            except (ValueError, TypeError):
                y_value = 0

            # Calculate y position
            full_y_pos = bottom - ((y_value - min_value) / value_range) * chart_height

            # Apply animation if needed
            if self.animate:
                # Animate from bottom to final position
                y_pos = bottom - ((self.animation_step / self.animation_steps) * (bottom - full_y_pos))
            else:
                y_pos = full_y_pos

            points.append((x_pos, y_pos, y_value))

        # Draw area under the line if requested
        if self.show_area and len(points) >= 2:
            # Create polygon points (add bottom corners)
            polygon_points = []
            for x_pos, y_pos, _ in points:
                polygon_points.extend([x_pos, y_pos])

            # Add bottom right and bottom left corners
            polygon_points.extend([points[-1][0], bottom, points[0][0], bottom])

            # Create area with transparent fill
            if self.animate:
                # Use transparency based on animation step
                alpha = int(180 * (self.animation_step / self.animation_steps))
                area_color = f"{self.area_color}80"  # 50% transparent
            else:
                area_color = f"{self.area_color}80"  # 50% transparent

            self.area = self.canvas.create_polygon(
                *polygon_points,
                fill=area_color,
                outline="",
                tags=("area",)
            )

        # Draw line segments
        for i in range(len(points) - 1):
            x1, y1, _ = points[i]
            x2, y2, _ = points[i + 1]

            line = self.canvas.create_line(
                x1, y1, x2, y2,
                fill=self.line_color,
                width=self.line_width,
                smooth=True,
                tags=("line_segment",)
            )
            self.line_segments.append(line)

        # Draw markers and value labels
        for i, (x_pos, y_pos, y_value) in enumerate(points):
            if self.show_markers:
                marker = self.canvas.create_oval(
                    x_pos - self.marker_size, y_pos - self.marker_size,
                    x_pos + self.marker_size, y_pos + self.marker_size,
                    fill=COLORS["background"],
                    outline=self.line_color,
                    width=2,
                    tags=("marker", f"marker_{i}")
                )
                self.markers.append(marker)

                # Store data with the marker for tooltips
                self.canvas.itemconfig(marker, data=(x_positions[i][1], y_value))

            if self.show_values:
                # Format value text
                value_text = str(int(y_value)) if y_value == int(y_value) else f"{y_value:.1f}"

                # Create value label
                value_label = self.canvas.create_text(
                    x_pos,
                    y_pos - self.marker_size - 8,
                    text=value_text,
                    fill=COLORS["text"],
                    font=("Helvetica", 8),
                    anchor="s",
                    tags=("value_label",)
                )
                self.value_labels.append(value_label)

        # Start animation if needed
        if self.animate and self.animation_step < self.animation_steps:
            self.animation_step += 1
            self.after(self.animation_duration // self.animation_steps, self.render)

    def _clear_chart_elements(self):
        """Clear the chart elements."""
        # Clear line segments
        for line in self.line_segments:
            self.canvas.delete(line)
        self.line_segments = []

        # Clear markers
        for marker in self.markers:
            self.canvas.delete(marker)
        self.markers = []

        # Clear area
        if self.area:
            self.canvas.delete(self.area)
            self.area = None

        # Clear value labels
        for label in self.value_labels:
            self.canvas.delete(label)
        self.value_labels = []

        # Clear grid lines
        for line in self.grid_lines:
            self.canvas.delete(line)
        self.grid_lines = []

        # Clear existing x-axis labels and ticks
        self.canvas.delete("x_label")
        self.canvas.delete("x_tick")

        # Clear existing y-axis labels and ticks
        self.canvas.delete("y_label")
        self.canvas.delete("y_tick")

    def update_data(self, data: List[Dict[str, Any]]):
        """
        Update the chart with new data.

        Args:
            data: List of dictionaries with chart data
        """
        self.data = data
        self.animation_step = 0  # Reset animation
        self.render()

    def _create_tooltip(self, x: int, y: int, text: str):
        """
        Create tooltip at the specified position.

        Args:
            x: X coordinate
            y: Y coordinate
            text: Tooltip text
        """
        # Delete existing tooltip
        if self.tooltip:
            self.canvas.delete(self.tooltip)

        # Create tooltip background
        bg = self.canvas.create_rectangle(
            x, y - 20,
               x + len(text) * 6 + 10, y,
            fill=COLORS["tooltip_bg"],
            outline=COLORS["border"],
            tags=("tooltip_bg",)
        )

        # Create tooltip text
        text = self.canvas.create_text(
            x + 5, y - 10,
            text=text,
            fill=COLORS["tooltip_text"],
            font=("Helvetica", 8),
            anchor="w",
            tags=("tooltip_text",)
        )

        # Store tooltip elements
        self.tooltip = (bg, text)
        self.tooltip_visible = True

    def _on_mouse_move(self, event):
        """
        Handle mouse movement to show tooltips.

        Args:
            event: The mouse event
        """
        # Check if mouse is over a marker
        for marker in self.markers:
            bbox = self.canvas.bbox(marker)
            if bbox and bbox[0] <= event.x <= bbox[2] and bbox[1] <= event.y <= bbox[3]:
                # Get data from marker
                data = self.canvas.itemcget(marker, "data")
                if data:
                    x_value, y_value = eval(data)
                    tooltip_text = f"{x_value}: {y_value}"
                    self._create_tooltip(event.x + 10, event.y - 10, tooltip_text)
                return

        # Hide tooltip if not over a marker
        if self.tooltip_visible:
            self._hide_tooltip()

    def _on_mouse_leave(self, event):
        """
        Handle mouse leave event to hide tooltips.

        Args:
            event: The mouse event
        """
        if self.tooltip_visible:
            self._hide_tooltip()

    def _hide_tooltip(self):
        """Hide the tooltip."""
        if self.tooltip:
            for item in self.tooltip:
                self.canvas.delete(item)
            self.tooltip = None
            self.tooltip_visible = False