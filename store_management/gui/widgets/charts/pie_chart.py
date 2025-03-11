# gui/widgets/charts/pie_chart.py
"""
Pie chart widget for displaying category distributions.

This module provides a pie chart component for visualizing data as proportional segments.
"""

import math
import tkinter as tk
from tkinter import ttk
from typing import Any, Dict, List, Optional, Tuple

from gui.theme import COLORS


class PieChart(ttk.Frame):
    """A pie chart widget that displays data as proportional segments."""

    def __init__(
            self,
            parent,
            data: List[Dict[str, Any]],
            label_key: str = "label",
            value_key: str = "value",
            title: str = "Pie Chart",
            width: int = 400,
            height: int = 400,
            colors: Optional[List[str]] = None,
            show_labels: bool = True,
            show_percentages: bool = True,
            show_legend: bool = True,
            donut: bool = False,
            animate: bool = True,
            **kwargs
    ):
        """
        Initialize the pie chart widget.

        Args:
            parent: The parent widget
            data: List of dictionaries with chart data
            label_key: Key in data dictionaries for segment labels
            value_key: Key in data dictionaries for segment values
            title: Chart title
            width: Chart width
            height: Chart height
            colors: List of colors for segments (defaults to theme colors)
            show_labels: Whether to show labels on chart segments
            show_percentages: Whether to show percentages on chart segments
            show_legend: Whether to show a legend
            donut: Whether to create a donut chart
            animate: Whether to animate the chart on initial display
        """
        super().__init__(parent, **kwargs)
        self.data = data
        self.label_key = label_key
        self.value_key = value_key
        self.title = title
        self.chart_width = width
        self.chart_height = height
        self.colors = colors or [
            "#4e79a7", "#f28e2c", "#e15759", "#76b7b2", "#59a14f",
            "#edc949", "#af7aa1", "#ff9da7", "#9c755f", "#bab0ab"
        ]
        self.show_labels = show_labels
        self.show_percentages = show_percentages
        self.show_legend = show_legend
        self.donut = donut
        self.animate = animate

        # Internal variables
        self.canvas = None
        self.segments = []
        self.labels = []
        self.percentage_labels = []
        self.legend_items = []
        self.tooltip = None
        self.tooltip_visible = False

        # Layout
        self.padding = 40  # Padding around the chart
        self.legend_width = 150 if self.show_legend else 0

        # Animation
        self.animation_duration = 750  # ms
        self.animation_steps = 30
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

    def render(self):
        """Render the chart with the current data."""
        if not self.data:
            return

        # Clear previous elements
        self._clear_chart_elements()

        # Filter out zero or negative values
        filtered_data = [item for item in self.data if item.get(self.value_key, 0) > 0]

        if not filtered_data:
            # Display "No Data" message if no valid data
            self.canvas.create_text(
                self.chart_width // 2,
                self.chart_height // 2,
                text="No Data",
                fill=COLORS["text"],
                font=("Helvetica", 12),
                tags=("no_data",)
            )
            return

        # Calculate total value
        total_value = sum(item.get(self.value_key, 0) for item in filtered_data)

        if total_value <= 0:
            # Cannot create pie chart with non-positive total
            return

        # Calculate chart center and radius
        if self.show_legend:
            center_x = (self.chart_width - self.legend_width) // 2
        else:
            center_x = self.chart_width // 2

        center_y = self.chart_height // 2
        radius = min(center_x, center_y) - self.padding

        # Calculate donut hole radius if needed
        inner_radius = radius // 2 if self.donut else 0

        # Current angle for drawing segments
        start_angle = 0

        # Prepare segments for animation
        segment_data = []

        for i, item in enumerate(filtered_data):
            value = item.get(self.value_key, 0)
            label = item.get(self.label_key, f"Item {i}")

            # Calculate segment angles
            angle = (value / total_value) * 360
            end_angle = start_angle + angle

            # Determine color
            color_index = i % len(self.colors)
            color = self.colors[color_index]

            # Store segment data
            segment_data.append({
                "start_angle": start_angle,
                "end_angle": end_angle,
                "color": color,
                "value": value,
                "label": label,
                "percentage": (value / total_value) * 100
            })

            # Update start angle for next segment
            start_angle = end_angle

        # Draw segments with animation if needed
        for i, segment in enumerate(segment_data):
            # Calculate animation angles
            if self.animate:
                current_end_angle = segment["start_angle"] + (
                        (self.animation_step / self.animation_steps) *
                        (segment["end_angle"] - segment["start_angle"])
                )
            else:
                current_end_angle = segment["end_angle"]

            # Skip segments that are too small for current animation step
            if current_end_angle <= segment["start_angle"]:
                continue

            # Create segment
            pie_segment = self._create_arc(
                center_x, center_y,
                radius, inner_radius,
                segment["start_angle"],
                current_end_angle,
                segment["color"]
            )

            # Store the segment
            self.segments.append(pie_segment)

            # Store segment data for tooltips
            self.canvas.itemconfig(pie_segment, tags=(f"segment_{i}", "segment"))
            self.canvas.itemconfig(pie_segment, data=(segment["label"], segment["value"], segment["percentage"]))

            # Add label and percentage if needed and segment is big enough
            if (self.show_labels or self.show_percentages) and (segment["end_angle"] - segment["start_angle"] >= 10):
                # Calculate label position
                midpoint_angle = math.radians((segment["start_angle"] + current_end_angle) / 2)
                label_distance = (radius + inner_radius) / 2 if self.donut else radius * 0.7

                label_x = center_x + label_distance * math.cos(midpoint_angle)
                label_y = center_y + label_distance * math.sin(midpoint_angle)

                # Add label
                if self.show_labels:
                    # Truncate long labels
                    display_label = segment["label"]
                    if len(display_label) > 10:
                        display_label = display_label[:10] + "..."

                    label = self.canvas.create_text(
                        label_x, label_y,
                        text=display_label,
                        fill="white",  # Use white for visibility on colored segments
                        font=("Helvetica", 8, "bold"),
                        anchor="center",
                        tags=(f"label_{i}", "label")
                    )
                    self.labels.append(label)

                # Add percentage
                if self.show_percentages:
                    percentage_text = f"{segment['percentage']:.1f}%"

                    # Adjust position for percentage
                    perc_y = label_y + 12 if self.show_labels else label_y

                    percentage = self.canvas.create_text(
                        label_x, perc_y,
                        text=percentage_text,
                        fill="white",  # Use white for visibility on colored segments
                        font=("Helvetica", 8),
                        anchor="center",
                        tags=(f"percentage_{i}", "percentage")
                    )
                    self.percentage_labels.append(percentage)

        # Create legend if needed
        if self.show_legend:
            legend_x = self.chart_width - self.legend_width + 10
            legend_y = self.padding + 20
            legend_spacing = 25

            for i, segment in enumerate(segment_data):
                # Create legend color box
                color_box = self.canvas.create_rectangle(
                    legend_x, legend_y + i * legend_spacing,
                              legend_x + 15, legend_y + i * legend_spacing + 15,
                    fill=segment["color"],
                    outline=COLORS["border"],
                    tags=(f"legend_box_{i}", "legend")
                )

                # Create legend label
                legend_label = self.canvas.create_text(
                    legend_x + 20, legend_y + i * legend_spacing + 7,
                    text=segment["label"],
                    fill=COLORS["text"],
                    font=("Helvetica", 8),
                    anchor="w",
                    tags=(f"legend_label_{i}", "legend")
                )

                # Create legend percentage
                legend_percentage = self.canvas.create_text(
                    legend_x + 120, legend_y + i * legend_spacing + 7,
                    text=f"{segment['percentage']:.1f}%",
                    fill=COLORS["text"],
                    font=("Helvetica", 8),
                    anchor="e",
                    tags=(f"legend_percentage_{i}", "legend")
                )

                self.legend_items.extend([color_box, legend_label, legend_percentage])

        # Continue animation if needed
        if self.animate and self.animation_step < self.animation_steps:
            self.animation_step += 1
            self.after(self.animation_duration // self.animation_steps, self.render)

    def _create_arc(self, center_x, center_y, radius, inner_radius, start_angle, end_angle, fill_color):
        """
        Create a pie segment or donut segment.

        Args:
            center_x: X coordinate of center
            center_y: Y coordinate of center
            radius: Outer radius
            inner_radius: Inner radius (0 for pie chart)
            start_angle: Start angle in degrees
            end_angle: End angle in degrees
            fill_color: Segment color

        Returns:
            Canvas polygon ID
        """
        # Convert angles to radians
        start_angle_rad = math.radians(start_angle - 90)  # -90 to start at 12 o'clock
        end_angle_rad = math.radians(end_angle - 90)

        # Calculate outer arc points
        outer_points = []
        step = math.radians(2)  # 2 degree steps for smooth arc

        angle = start_angle_rad
        while angle <= end_angle_rad:
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            outer_points.append((x, y))
            angle += step

        # Ensure end point is included
        x = center_x + radius * math.cos(end_angle_rad)
        y = center_y + radius * math.sin(end_angle_rad)
        outer_points.append((x, y))

        if inner_radius > 0:
            # Donut chart - add inner arc points in reverse
            inner_points = []
            angle = end_angle_rad
            while angle >= start_angle_rad:
                x = center_x + inner_radius * math.cos(angle)
                y = center_y + inner_radius * math.sin(angle)
                inner_points.append((x, y))
                angle -= step

            # Ensure start point is included
            x = center_x + inner_radius * math.cos(start_angle_rad)
            y = center_y + inner_radius * math.sin(angle)
            inner_points.append((x, y))

            # Combine points
            points = outer_points + inner_points
        else:
            # Regular pie chart - add center point
            points = outer_points + [(center_x, center_y)]

        # Create polygon for segment
        coords = []
        for x, y in points:
            coords.extend([x, y])

        return self.canvas.create_polygon(
            *coords,
            fill=fill_color,
            outline=COLORS["background"],
            width=1,
            smooth=True
        )

    def _clear_chart_elements(self):
        """Clear the chart elements."""
        # Clear segments
        for segment in self.segments:
            self.canvas.delete(segment)
        self.segments = []

        # Clear labels
        for label in self.labels:
            self.canvas.delete(label)
        self.labels = []

        # Clear percentage labels
        for label in self.percentage_labels:
            self.canvas.delete(label)
        self.percentage_labels = []

        # Clear legend items
        for item in self.legend_items:
            self.canvas.delete(item)
        self.legend_items = []

        # Clear no data message
        self.canvas.delete("no_data")

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
        # Get segment under cursor
        item_id = self.canvas.find_withtag("current")
        for segment_id in item_id:
            tags = self.canvas.gettags(segment_id)
            if "segment" in tags:
                # Get data from segment
                data = self.canvas.itemcget(segment_id, "data")
                if data:
                    label, value, percentage = eval(data)
                    tooltip_text = f"{label}: {value} ({percentage:.1f}%)"
                    self._create_tooltip(event.x + 10, event.y - 10, tooltip_text)
                return

        # Hide tooltip if not over a segment
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