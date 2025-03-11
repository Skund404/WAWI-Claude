# gui/widgets/charts/bar_chart.py
"""
Bar chart widget for displaying data in vertical bars.

This module provides a simple bar chart component for data visualization.
"""

import tkinter as tk
from tkinter import ttk
from typing import Any, Dict, List, Optional, Tuple

from gui.theme import COLORS


class BarChart(ttk.Frame):
    """A bar chart widget that displays data in vertical bars."""

    def __init__(
            self,
            parent,
            data: List[Dict[str, Any]],
            x_key: str = "label",
            y_key: str = "value",
            title: str = "Bar Chart",
            width: int = 600,
            height: int = 400,
            x_label: str = "",
            y_label: str = "",
            color: str = COLORS["primary"],
            bar_width: int = 40,
            spacing: int = 20,
            show_values: bool = True,
            show_grid: bool = True,
            animate: bool = True,
            **kwargs
    ):
        """
        Initialize the bar chart widget.

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
            color: Bar color
            bar_width: Width of bars
            spacing: Space between bars
            show_values: Whether to show values above bars
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
        self.color = color
        self.bar_width = bar_width
        self.spacing = spacing
        self.show_values = show_values
        self.show_grid = show_grid
        self.animate = animate

        # Internal variables
        self.canvas = None
        self.chart_area = None
        self.x_axis = None
        self.y_axis = None
        self.bars = []
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

        if min_value > 0:
            min_value = 0  # Start from zero if all values are positive

        value_range = max_value - min_value

        # Ensure we have a non-zero range
        if value_range == 0:
            value_range = 1

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

        # Calculate bar positions
        total_bars = len(self.data)
        total_width = (self.bar_width + self.spacing) * total_bars

        # Adjust bar width if too many bars
        if total_width > chart_width:
            self.bar_width = int((chart_width - (total_bars + 1) * self.spacing) / total_bars)
            if self.bar_width < 5:
                self.bar_width = 5
                self.spacing = max(2, int((chart_width - self.bar_width * total_bars) / (total_bars + 1)))

        start_x = left + (chart_width - total_width) // 2 + self.spacing

        # Draw bars and x-axis labels
        for i, item in enumerate(self.data):
            # Get values and ensure they're numbers
            x_value = item.get(self.x_key, f"Item {i}")
            y_value = item.get(self.y_key, 0)
            try:
                y_value = float(y_value)
            except (ValueError, TypeError):
                y_value = 0

            # Calculate bar position
            bar_x = start_x + i * (self.bar_width + self.spacing)
            bar_height = (y_value - min_value) / value_range * chart_height

            # Calculate animation height if needed
            if self.animate:
                # Start with a small height and animate to full height
                current_height = (self.animation_step / self.animation_steps) * bar_height
            else:
                current_height = bar_height

            # Create bar
            if current_height > 0:
                bar = self.canvas.create_rectangle(
                    bar_x, bottom - current_height,
                           bar_x + self.bar_width, bottom,
                    fill=self.color,
                    outline=COLORS["border"],
                    tags=("bar", f"bar_{i}")
                )
                self.bars.append(bar)

                # Store data with the bar for tooltips
                self.canvas.itemconfig(bar, data=(x_value, y_value))

            # Create x-axis label
            label = self.canvas.create_text(
                bar_x + self.bar_width // 2,
                bottom + 15,
                text=str(x_value),
                fill=COLORS["text"],
                font=("Helvetica", 8),
                angle=45 if len(str(x_value)) > 5 else 0,  # Rotate if text is long
                anchor="ne" if len(str(x_value)) > 5 else "n",
                tags=("x_label",)
            )

            # Create value label if needed
            if self.show_values and current_height > 0:
                value_text = str(int(y_value)) if y_value == int(y_value) else f"{y_value:.1f}"
                value_label = self.canvas.create_text(
                    bar_x + self.bar_width // 2,
                    bottom - current_height - 5,
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
        # Clear bars
        for bar in self.bars:
            self.canvas.delete(bar)
        self.bars = []

        # Clear value labels
        for label in self.value_labels:
            self.canvas.delete(label)
        self.value_labels = []

        # Clear grid lines
        for line in self.grid_lines:
            self.canvas.delete(line)
        self.grid_lines = []

        # Clear existing x-axis labels
        self.canvas.delete("x_label")

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
        # Check if mouse is over a bar
        for bar in self.bars:
            bbox = self.canvas.bbox(bar)
            if bbox and bbox[0] <= event.x <= bbox[2] and bbox[1] <= event.y <= bbox[3]:
                # Get data from bar
                data = self.canvas.itemcget(bar, "data")
                if data:
                    x_value, y_value = eval(data)
                    tooltip_text = f"{x_value}: {y_value}"
                    self._create_tooltip(event.x + 10, event.y - 10, tooltip_text)
                return

        # Hide tooltip if not over a bar
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