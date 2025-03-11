# gui/widgets/status_badge.py
"""
Status badge widget for displaying status values.
Provides visual indicators for status values.
"""

import tkinter as tk
from tkinter import ttk
from typing import Any, Dict, Optional

from gui import theme, config


class StatusBadge(tk.Frame):
    """
    Widget for displaying status values with appropriate styling.
    Shows a badge with background color based on status value.
    """

    def __init__(
            self,
            parent,
            text: str = "",
            status_value: Optional[str] = None,
            width: int = 12,
            **kwargs
    ):
        """
        Initialize the status badge.

        Args:
            parent: The parent widget
            text: The text to display
            status_value: The status value for styling (if different from text)
            width: The badge width
            **kwargs: Additional arguments for tk.Frame
        """
        # Get style for the status
        status_key = (status_value or text).lower()
        style = theme.get_status_style(status_key)

        # Initialize frame with appropriate background
        super().__init__(
            parent,
            background=style["bg"],
            highlightthickness=0,
            bd=0,
            **kwargs
        )

        # Create label for the status text
        self.label = tk.Label(
            self,
            text=text,
            foreground=style["fg"],
            background=style["bg"],
            font=theme.create_custom_font(theme.FONTS["small"]),
            width=width,
            padx=3,
            pady=1,
            anchor="center"
        )
        self.label.pack(fill=tk.BOTH, expand=True)

        # Round corners using canvas overlay (if available)
        self._try_round_corners()

    def _try_round_corners(self):
        """Try to create rounded corners using canvas clipping mask."""
        try:
            # This is an experimental feature and may not work on all platforms
            # It uses a canvas to create a clipping mask for rounded corners
            radius = 5  # Corner radius

            # Create canvas overlay
            self.canvas = tk.Canvas(
                self,
                highlightthickness=0,
                bg=self.label.cget("background"),
                width=self.label.winfo_reqwidth(),
                height=self.label.winfo_reqheight()
            )

            # Create rounded rectangle
            self.canvas.create_rectangle(
                radius, 0,
                self.label.winfo_reqwidth() - radius, self.label.winfo_reqheight(),
                fill=self.label.cget("background"),
                outline=""
            )

            # Create corner arcs
            self.canvas.create_arc(
                0, 0, radius * 2, radius * 2,
                start=90, extent=90,
                fill=self.label.cget("background"),
                outline=""
            )
            self.canvas.create_arc(
                self.label.winfo_reqwidth() - radius * 2, 0,
                self.label.winfo_reqwidth(), radius * 2,
                start=0, extent=90,
                fill=self.label.cget("background"),
                outline=""
            )
            self.canvas.create_arc(
                0, self.label.winfo_reqheight() - radius * 2,
                   radius * 2, self.label.winfo_reqheight(),
                start=180, extent=90,
                fill=self.label.cget("background"),
                outline=""
            )
            self.canvas.create_arc(
                self.label.winfo_reqwidth() - radius * 2,
                self.label.winfo_reqheight() - radius * 2,
                self.label.winfo_reqwidth(), self.label.winfo_reqheight(),
                start=270, extent=90,
                fill=self.label.cget("background"),
                outline=""
            )

            # Create text
            self.canvas.create_text(
                self.label.winfo_reqwidth() / 2,
                self.label.winfo_reqheight() / 2,
                text=self.label.cget("text"),
                fill=self.label.cget("foreground"),
                font=self.label.cget("font")
            )

            # Replace label with canvas
            self.label.pack_forget()
            self.canvas.pack(fill=tk.BOTH, expand=True)

        except Exception:
            # If anything goes wrong, just keep the regular label
            pass

    def set_text(self, text: str, status_value: Optional[str] = None):
        """
        Update the status badge text and styling.

        Args:
            text: The new text to display
            status_value: The status value for styling (if different from text)
        """
        # Get style for the status
        status_key = (status_value or text).lower()
        style = theme.get_status_style(status_key)

        # Update label
        self.label.config(text=text, background=style["bg"], foreground=style["fg"])
        self.configure(background=style["bg"])

        # Update canvas if it exists
        if hasattr(self, "canvas"):
            try:
                self.canvas.config(background=style["bg"])
                # Update all canvas items
                for item in self.canvas.find_all():
                    if self.canvas.type(item) == "text":
                        self.canvas.itemconfig(item, fill=style["fg"], text=text)
                    else:
                        self.canvas.itemconfig(item, fill=style["bg"])
            except Exception:
                # If canvas update fails, switch back to label
                self.canvas.destroy()
                self.label.pack(fill=tk.BOTH, expand=True)