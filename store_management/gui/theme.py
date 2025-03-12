# gui/theme.py
"""
Defines the application's visual theme, including colors, fonts, and styles.
Provides functions to apply the theme to Tkinter widgets.
"""

import tkinter as tk
from tkinter import font
import tkinter.ttk as ttk

# Define colors
COLORS = {
    # Primary colors
    "primary": "#2980b9",
    "primary_light": "#3498db",
    "primary_dark": "#21618c",
    "secondary": "#7f8c8d",
    "success": "#2ecc71",
    "success_light": "#59d68c",
    "warning": "#f39c12",
    "warning_light": "#f8ba50",
    "danger": "#e74c3c",
    "danger_light": "#ec7063",
    "accent": "#9b59b6",
    "accent_light": "#af7ac1",
    "text": "#2c3e50",
    "text_secondary": "#777777",
    "text_inverted": "#ffffff",
    # Background colors
    "bg": "#ecf0f1",
    "bg_light": "#f5f5f5",
    "border": "#cccccc",
    "light_grey": "#DDDDDD",
    # Border colours
    "border_medium": "#bdc3c7",  # Added border_medium color
    "border_dark": "#95a5a6",
    "text_primary": "#2c3e50",
    "info": "#3498db",
    "error": "#c0392b", #Added this
}

# Define fonts
FONTS = {
    "header": {"family": "Helvetica", "size": 16, "weight": "bold"},
    "subheader": {"family": "Helvetica", "size": 14, "weight": "bold"},
    "title": {"family": "Arial", "size": 16, "weight": "normal"},
    "body": {"family": "Arial", "size": 12, "weight": "normal"},
    "small": {"family": "Arial", "size": 10, "weight": "normal"}
}

# Default padding sizes
PADDING = {
    "small": 5,
    "medium": 10,
    "large": 15
}

# Widget styling
BUTTON_STYLE = {
    "padding": (PADDING["medium"], PADDING["small"]),
    "relief": tk.RAISED,
    "borderwidth": 1
}

ENTRY_STYLE = {
    "padding": (PADDING["small"], PADDING["small"]),
    "borderwidth": 1,
    "relief": tk.SOLID,
    "highlightbackground": COLORS["border_medium"],
    "highlightthickness": 1,
}

COMBOBOX_STYLE = {
    "padding": (PADDING["small"], PADDING["small"]),
    "borderwidth": 1,
    "relief": tk.SOLID
}

TREEVIEW_STYLE = {
    "rowheight": 25,
    "font": FONTS["body"]
}

FRAME_STYLE = {
    "bg": COLORS["bg_light"],
    "highlightbackground": COLORS["border_medium"],
    "highlightthickness": 1
}

LABEL_STYLE = {
    "bg": COLORS["bg_light"],
    "fg": COLORS["text_primary"],
    "padx": PADDING["small"],
    "pady": PADDING["small"]
}

# Status badge styles
STATUS_BADGE_STYLES = {
    # Project status
    "initial_consultation": {"bg": COLORS["info"], "fg": COLORS["text_inverted"]},
    "design_phase": {"bg": COLORS["info"], "fg": COLORS["text_inverted"]},
    "pattern_development": {"bg": COLORS["info"], "fg": COLORS["text_inverted"]},
    "client_approval": {"bg": COLORS["warning"], "fg": COLORS["text_inverted"]},
    "material_selection": {"bg": COLORS["info"], "fg": COLORS["text_inverted"]},
    "material_purchased": {"bg": COLORS["info"], "fg": COLORS["text_inverted"]},
    "cutting": {"bg": COLORS["info"], "fg": COLORS["text_inverted"]},
    "skiving": {"bg": COLORS["info"], "fg": COLORS["text_inverted"]},
    "preparation": {"bg": COLORS["info"], "fg": COLORS["text_inverted"]},
    "assembly": {"bg": COLORS["info"], "fg": COLORS["text_inverted"]},
    "stitching": {"bg": COLORS["info"], "fg": COLORS["text_inverted"]},
    "edge_finishing": {"bg": COLORS["info"], "fg": COLORS["text_inverted"]},
    "hardware_installation": {"bg": COLORS["info"], "fg": COLORS["text_inverted"]},
    "conditioning": {"bg": COLORS["info"], "fg": COLORS["text_inverted"]},
    "quality_check": {"bg": COLORS["info"], "fg": COLORS["text_inverted"]},
    "final_touches": {"bg": COLORS["info"], "fg": COLORS["text_inverted"]},
    "photography": {"bg": COLORS["info"], "fg": COLORS["text_inverted"]},
    "packaging": {"bg": COLORS["info"], "fg": COLORS["text_inverted"]},
    "completed": {"bg": COLORS["success"], "fg": COLORS["text_inverted"]},
    "on_hold": {"bg": COLORS["warning"], "fg": COLORS["text_inverted"]},
    "cancelled": {"bg": COLORS["error"], "fg": COLORS["text_inverted"]},
    # Inventory status
    "in_stock": {"bg": COLORS["success"], "fg": COLORS["text_inverted"]},
    "low_stock": {"bg": COLORS["warning"], "fg": COLORS["text_inverted"]},
    "out_of_stock": {"bg": COLORS["error"], "fg": COLORS["text_inverted"]},
    "discontinued": {"bg": COLORS["secondary"], "fg": COLORS["text_inverted"]},
    # Default for undefined status
    "default": {"bg": COLORS["secondary"], "fg": COLORS["text_inverted"]}
}


def create_custom_font(font_config):
    """
    Create a custom font based on the provided configuration.

    Args:
        font_config: Dictionary with font configuration (family, size, weight)

    Returns:
        Font object
    """
    return font.Font(
        family=font_config["family"],
        size=font_config["size"],
        weight=font_config["weight"]
    )


def get_status_style(status_value):
    """
    Get the style for a specific status value.

    Args:
        status_value: The status value as a string

    Returns:
        Dict with bg and fg colors
    """
    status_key = str(status_value).lower()
    return STATUS_BADGE_STYLES.get(status_key, STATUS_BADGE_STYLES["default"])


def apply_theme():
    """
    Apply the theme to the application.
    Sets up ttk styles and other global styling.
    """
    import tkinter.ttk as ttk

    style = ttk.Style()

    # Configure ttk element styles
    style.configure("TButton",
                    background=BUTTON_STYLE["bg"],
                    foreground=BUTTON_STYLE["fg"],
                    padding=(PADDING["medium"], PADDING["small"]))

    style.configure("TEntry",
                   fieldbackground=ENTRY_STYLE["bg"],
                   foreground=ENTRY_STYLE["fg"],
                   highlightbackground=ENTRY_STYLE["highlightbackground"],
                   highlightthickness=ENTRY_STYLE["highlightthickness"])

    style.configure("TCombobox",
                   **COMBOBOX_STYLE)

    style.configure("Treeview",
                   **TREEVIEW_STYLE)

    style.configure("TFrame",
                   background=FRAME_STYLE["bg"],
                   highlightbackground=FRAME_STYLE["highlightbackground"],
                   highlightthickness=FRAME_STYLE["highlightthickness"])

    # Dashboard Frame Style
    style.configure("Dashboard.TFrame", background=COLORS["bg"])

    style.configure("TLabel",
                   background=LABEL_STYLE["bg"],
                   foreground=LABEL_STYLE["fg"],
                   padding=(PADDING["small"], PADDING["small"]))

    # Configure tag styles for treeview
    style.configure("Treeview.Tag.success", background=COLORS["success"], foreground=COLORS["text_inverted"])
    style.configure("Treeview.Tag.warning", background=COLORS["warning"], foreground=COLORS["text_inverted"])
    style.configure("Treeview.Tag.error", background=COLORS["error"], foreground=COLORS["text_inverted"])
    style.configure("Treeview.Tag.info", background=COLORS["info"], foreground=COLORS["text_inverted"])


def fix_button_styles():
    """
    Fix button styling to ensure consistent text colors across all buttons.
    Call this function after initializing the application theme.
    """
    style = ttk.Style()

    # Configure standard buttons with consistent foreground
    style.configure("TButton", foreground=COLORS["text"])

    # Configure other button states to maintain text color
    style.map("TButton",
              foreground=[
                  ("active", COLORS["text_primary"]),
                  ("disabled", COLORS["text_secondary"])
              ],
              background=[
                  ("active", COLORS["bg_light"]),  # slightly lighter when active
                  ("disabled", COLORS["light_grey"])  # even lighter when disabled
              ]
              )

    # Create a custom style for navigation buttons if needed
    style.configure("Navigation.TButton", foreground=COLORS["text"])
    style.map("Navigation.TButton",
              foreground=[
                  ("active", COLORS["text_primary"]),
                  ("disabled", COLORS["text_secondary"])
              ]
              )

    # Ensure consistency across all variations of buttons that might use different styles
    for button_style in ["Toolbutton", "Flat.TButton", "Accent.TButton"]:
        if button_style in style.theme_names():  # Check if the style exists
            style.configure(button_style, foreground=COLORS["text"])
            style.map(button_style,
                      foreground=[
                          ("active", COLORS["text_primary"]),
                          ("disabled", COLORS["text_secondary"])
                      ]
                      )