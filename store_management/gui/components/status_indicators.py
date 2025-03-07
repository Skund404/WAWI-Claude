"""
Status indicators for visualizing state information.
Provides visual indicators for status and progress information.
"""
import logging
import tkinter as tk
from tkinter import ttk
from typing import Any, Callable, Dict, Optional, Union

logger = logging.getLogger(__name__)


class StatusIndicator(ttk.Frame):
    """
    Visual indicator for status information.

    Features:
    - Color-coded status display
    - Support for text and visual indicators
    - Optional badge counters
    - Customizable appearance
    """

    # Status colors
    STATUS_COLORS = {
        "success": "#0f9d58",  # Green
        "warning": "#f29900",  # Amber
        "danger": "#d93025",  # Red
        "info": "#1a73e8",  # Blue
        "default": "#5f6368",  # Gray
        "inactive": "#9e9e9e",  # Light Gray
    }

    def __init__(self, parent: tk.Widget, text: str = "",
                 status: str = "default",
                 badge: Optional[Union[int, str]] = None,
                 show_icon: bool = True,
                 clickable: bool = False,
                 command: Optional[Callable] = None,
                 width: int = 12, height: int = None,
                 **kwargs):
        """
        Initialize the status indicator.

        Args:
            parent: Parent widget
            text: Status text
            status: Status type (success, warning, danger, info, default, inactive)
            badge: Optional badge count or text
            show_icon: Whether to show the status icon
            clickable: Whether the indicator should be clickable
            command: Command to execute when clicked
            width: Text width in characters
            height: Height in pixels
            **kwargs: Additional arguments for ttk.Frame
        """
        super().__init__(parent, **kwargs)

        # Store parameters
        self.text = text
        self.status = status
        self.badge_text = badge
        self.show_icon = show_icon
        self.clickable = clickable
        self.command = command

        # Create the indicator
        self._create_indicator(width, height)

        # Make clickable if requested
        if clickable:
            self.bind("<Button-1>", self._on_click)
            self.label.bind("<Button-1>", self._on_click)
            if self.icon_canvas:
                self.icon_canvas.bind("<Button-1>", self._on_click)
            if self.badge_label:
                self.badge_label.bind("<Button-1>", self._on_click)

            # Change cursor on hover
            self.bind("<Enter>", lambda e: self.configure(cursor="hand2"))
            self.bind("<Leave>", lambda e: self.configure(cursor=""))

        logger.debug(f"Status indicator created: {text}, status={status}")

    def _create_indicator(self, width: int, height: Optional[int]):
        """
        Create the indicator components.

        Args:
            width: Text width
            height: Optional height
        """
        # Configure frame
        if height:
            self.configure(height=height)

        # Get the status color
        color = self.STATUS_COLORS.get(self.status, self.STATUS_COLORS["default"])

        # Create horizontal layout
        if self.show_icon:
            # Create icon canvas
            self.icon_canvas = tk.Canvas(
                self,
                width=16,
                height=16,
                bg=self.cget('background'),
                highlightthickness=0
            )
            self.icon_canvas.pack(side=tk.LEFT, padx=(0, 5))

            # Draw icon based on status
            self._draw_status_icon(color)
        else:
            self.icon_canvas = None

        # Create label
        self.label = ttk.Label(
            self,
            text=self.text,
            width=width,
            foreground=color
        )
        self.label.pack(side=tk.LEFT)

        # Create badge if provided
        if self.badge_text is not None:
            self.badge_label = ttk.Label(
                self,
                text=str(self.badge_text),
                width=4,
                padding=(3, 0),
                foreground="white",
                background=color,
                anchor=tk.CENTER
            )
            self.badge_label.pack(side=tk.LEFT, padx=(5, 0))
        else:
            self.badge_label = None

    def _draw_status_icon(self, color: str):
        """
        Draw the status icon on the canvas.

        Args:
            color: Icon color
        """
        if not self.icon_canvas:
            return

        # Clear canvas
        self.icon_canvas.delete("all")

        if self.status == "success":
            # Draw checkmark
            self.icon_canvas.create_line(4, 8, 7, 12, width=2, fill=color)
            self.icon_canvas.create_line(7, 12, 12, 5, width=2, fill=color)
        elif self.status == "warning":
            # Draw exclamation mark
            self.icon_canvas.create_oval(4, 4, 12, 12, outline=color, width=2)
            self.icon_canvas.create_line(8, 5, 8, 9, width=2, fill=color)
            self.icon_canvas.create_oval(7, 10, 9, 12, fill=color, outline=color)
        elif self.status == "danger":
            # Draw X
            self.icon_canvas.create_line(4, 4, 12, 12, width=2, fill=color)
            self.icon_canvas.create_line(4, 12, 12, 4, width=2, fill=color)
        elif self.status == "info":
            # Draw info symbol
            self.icon_canvas.create_oval(4, 4, 12, 12, outline=color, width=2)
            self.icon_canvas.create_oval(7, 5, 9, 7, fill=color, outline=color)
            self.icon_canvas.create_line(8, 8, 8, 11, width=2, fill=color)
        elif self.status == "inactive":
            # Draw inactive symbol (dash)
            self.icon_canvas.create_line(4, 8, 12, 8, width=2, fill=color)
        else:
            # Draw default circle
            self.icon_canvas.create_oval(4, 4, 12, 12, outline=color, width=2)

    def _on_click(self, event):
        """Handle click events."""
        if self.clickable and self.command:
            self.command()

    def set_status(self, status: str, text: Optional[str] = None,
                   badge: Optional[Union[int, str]] = None):
        """
        Update the status indicator.

        Args:
            status: New status
            text: Optional new text
            badge: Optional new badge
        """
        # Update stored values
        self.status = status
        if text is not None:
            self.text = text
        if badge is not None:
            self.badge_text = badge

        # Get the status color
        color = self.STATUS_COLORS.get(self.status, self.STATUS_COLORS["default"])

        # Update icon
        if self.show_icon and self.icon_canvas:
            self._draw_status_icon(color)

        # Update label
        if text is not None:
            self.label.configure(text=self.text)
        self.label.configure(foreground=color)

        # Update badge
        if self.badge_label:
            if badge is not None:
                self.badge_label.configure(
                    text=str(self.badge_text),
                    background=color
                )
            else:
                self.badge_label.configure(background=color)
        elif badge is not None:
            # Create new badge
            self.badge_text = badge
            self.badge_label = ttk.Label(
                self,
                text=str(self.badge_text),
                width=4,
                padding=(3, 0),
                foreground="white",
                background=color,
                anchor=tk.CENTER
            )
            self.badge_label.pack(side=tk.LEFT, padx=(5, 0))

            # Bind click if clickable
            if self.clickable:
                self.badge_label.bind("<Button-1>", self._on_click)

        logger.debug(f"Status updated: {self.text}, status={self.status}")


class ProgressIndicator(ttk.Frame):
    """
    Visual indicator for progress information.

    Features:
    - Determinate or indeterminate progress
    - Percentage display
    - Optional text label
    - Color-coding based on progress
    """

    def __init__(self, parent: tk.Widget, mode: str = "determinate",
                 value: int = 0, maximum: int = 100,
                 show_text: bool = True, label_text: str = "",
                 auto_color: bool = True, height: int = 20,
                 **kwargs):
        """
        Initialize the progress indicator.

        Args:
            parent: Parent widget
            mode: Progress mode ("determinate" or "indeterminate")
            value: Initial value (0-100)
            maximum: Maximum value
            show_text: Whether to show percentage text
            label_text: Optional label text
            auto_color: Whether to automatically color based on progress
            height: Height in pixels
            **kwargs: Additional arguments for ttk.Frame
        """
        super().__init__(parent, **kwargs)

        # Store parameters
        self.mode = mode
        self.maximum = maximum
        self.value = min(value, maximum)
        self.show_text = show_text
        self.label_text = label_text
        self.auto_color = auto_color

        # Create the indicator
        self._create_indicator(height)

        logger.debug(f"Progress indicator created: mode={mode}, value={value}/{maximum}")

    def _create_indicator(self, height: int):
        """
        Create the progress indicator components.

        Args:
            height: Height in pixels
        """
        # Create main layout
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Add label if provided
        if self.label_text:
            label = ttk.Label(main_frame, text=self.label_text)
            label.pack(anchor=tk.W, pady=(0, 2))

        # Create progress bar container
        bar_frame = ttk.Frame(main_frame)
        bar_frame.pack(fill=tk.X)

        # Get style based on value
        style = "TProgressbar"
        if self.auto_color:
            if self.value >= 80:
                style = "Success.TProgressbar"
            elif self.value >= 50:
                style = "Info.TProgressbar"
            elif self.value >= 30:
                style = "Warning.TProgressbar"
            else:
                style = "Danger.TProgressbar"

        # Create progress bar
        self.progress_var = tk.IntVar(value=self.value)
        self.progressbar = ttk.Progressbar(
            bar_frame,
            mode=self.mode,
            variable=self.progress_var,
            maximum=self.maximum,
            style=style,
            length=200,  # Will be resized with pack
            orient=tk.HORIZONTAL
        )
        self.progressbar.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Create percentage text
        if self.show_text:
            self.percent_var = tk.StringVar()
            self._update_percent_text()

            percent_label = ttk.Label(
                bar_frame,
                textvariable=self.percent_var,
                width=5,
                anchor=tk.E
            )
            percent_label.pack(side=tk.RIGHT, padx=(5, 0))

    def _update_percent_text(self):
        """Update the percentage text."""
        if hasattr(self, 'percent_var'):
            percent = int((self.value / self.maximum) * 100)
            self.percent_var.set(f"{percent}%")

    def _update_style(self):
        """Update the progressbar style based on the value."""
        if not self.auto_color or not hasattr(self, 'progressbar'):
            return

        percent = (self.value / self.maximum) * 100

        if percent >= 80:
            self.progressbar.configure(style="Success.TProgressbar")
        elif percent >= 50:
            self.progressbar.configure(style="Info.TProgressbar")
        elif percent >= 30:
            self.progressbar.configure(style="Warning.TProgressbar")
        else:
            self.progressbar.configure(style="Danger.TProgressbar")

    def set_value(self, value: int):
        """
        Set the progress value.

        Args:
            value: New value (0-maximum)
        """
        self.value = min(max(0, value), self.maximum)

        if hasattr(self, 'progress_var'):
            self.progress_var.set(self.value)

        self._update_percent_text()
        self._update_style()

        logger.debug(f"Progress value set to {self.value}/{self.maximum}")

    def increment(self, amount: int = 1):
        """
        Increment the progress value.

        Args:
            amount: Amount to increment by
        """
        self.set_value(self.value + amount)

    def set_indeterminate(self, indeterminate: bool = True):
        """
        Set the progress mode.

        Args:
            indeterminate: Whether to use indeterminate mode
        """
        if hasattr(self, 'progressbar'):
            self.mode = "indeterminate" if indeterminate else "determinate"
            self.progressbar.configure(mode=self.mode)

            # Start or stop animation
            if indeterminate:
                self.progressbar.start()
            else:
                self.progressbar.stop()

            logger.debug(f"Progress mode set to {self.mode}")

    def start(self):
        """Start the progress animation (indeterminate mode)."""
        if hasattr(self, 'progressbar') and self.mode == "indeterminate":
            self.progressbar.start()

    def stop(self):
        """Stop the progress animation."""
        if hasattr(self, 'progressbar'):
            self.progressbar.stop()


# Add styles for the progress indicators
def setup_progress_styles():
    """Configure ttk styles for progress indicators."""
    style = ttk.Style()

    # Progressbar styles
    style.configure("TProgressbar",
                    thickness=16,
                    borderwidth=0)

    style.configure("Success.TProgressbar",
                    background="#0f9d58",  # Green
                    troughcolor="#e0e0e0")

    style.configure("Info.TProgressbar",
                    background="#1a73e8",  # Blue
                    troughcolor="#e0e0e0")

    style.configure("Warning.TProgressbar",
                    background="#f29900",  # Amber
                    troughcolor="#e0e0e0")

    style.configure("Danger.TProgressbar",
                    background="#d93025",  # Red
                    troughcolor="#e0e0e0")


# Example usage
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Status Indicators Demo")
    root.geometry("600x500")

    # Set up styles
    setup_progress_styles()

    # Create demo frame
    frame = ttk.Frame(root, padding=20)
    frame.pack(fill=tk.BOTH, expand=True)

    # Status indicators section
    status_frame = ttk.LabelFrame(frame, text="Status Indicators", padding=10)
    status_frame.pack(fill=tk.X, pady=(0, 20))

    # Create various status indicators
    indicators = [
        {"text": "Active", "status": "success", "badge": 5},
        {"text": "Pending", "status": "warning", "badge": 12},
        {"text": "Failed", "status": "danger", "badge": 3},
        {"text": "Information", "status": "info"},
        {"text": "Default Status", "status": "default"},
        {"text": "Inactive", "status": "inactive"}
    ]

    for i, config in enumerate(indicators):
        indicator = StatusIndicator(status_frame, **config)
        indicator.grid(row=i // 3, column=i % 3, padx=10, pady=5, sticky=tk.W)


    # Clickable indicator example
    def indicator_clicked():
        print("Indicator clicked!")


    clickable = StatusIndicator(
        status_frame,
        text="Click Me",
        status="info",
        badge="New",
        clickable=True,
        command=indicator_clicked
    )
    clickable.grid(row=2, column=0, padx=10, pady=5, sticky=tk.W)

    # Progress indicators section
    progress_frame = ttk.LabelFrame(frame, text="Progress Indicators", padding=10)
    progress_frame.pack(fill=tk.X, pady=(0, 20))

    # Create various progress indicators
    progress1 = ProgressIndicator(
        progress_frame,
        value=75,
        label_text="Determinate Progress"
    )
    progress1.pack(fill=tk.X, pady=(0, 10))

    progress2 = ProgressIndicator(
        progress_frame,
        mode="indeterminate",
        label_text="Indeterminate Progress"
    )
    progress2.pack(fill=tk.X, pady=(0, 10))

    progress3 = ProgressIndicator(
        progress_frame,
        value=25,
        auto_color=True,
        label_text="Color-coded Progress"
    )
    progress3.pack(fill=tk.X, pady=(0, 10))

    # Control section
    control_frame = ttk.LabelFrame(frame, text="Controls", padding=10)
    control_frame.pack(fill=tk.X)

    # Value slider
    ttk.Label(control_frame, text="Progress Value:").grid(row=0, column=0, sticky=tk.W)


    def on_slide(val):
        value = int(float(val))
        progress1.set_value(value)
        progress3.set_value(value)


    slider = ttk.Scale(
        control_frame,
        from_=0,
        to=100,
        orient=tk.HORIZONTAL,
        command=on_slide
    )
    slider.set(75)
    slider.grid(row=0, column=1, sticky=tk.EW, padx=5)

    # Animation controls
    ttk.Label(control_frame, text="Indeterminate:").grid(row=1, column=0, sticky=tk.W)


    def toggle_animation():
        if animation_var.get():
            progress2.start()
        else:
            progress2.stop()


    animation_var = tk.BooleanVar(value=False)
    animation_check = ttk.Checkbutton(
        control_frame,
        text="Animate",
        variable=animation_var,
        command=toggle_animation
    )
    animation_check.grid(row=1, column=1, sticky=tk.W, padx=5)

    # Configure grid
    control_frame.columnconfigure(1, weight=1)

    root.mainloop()