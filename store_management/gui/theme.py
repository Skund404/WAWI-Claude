# gui/theme.py
"""
Theme definitions for the GUI application.
Provides consistent styling across all views and components.
"""

from tkinter import font

# Colors
COLORS = {
    # Primary colors
    "primary": "#2c3e50",
    "secondary": "#95a5a6",
    "accent": "#e74c3c",
    
    # Background colors
    "bg_light": "#f5f5f5",
    "bg_medium": "#ecf0f1",
    "bg_dark": "#bdc3c7",
    
    # Text colors
    "text_primary": "#2c3e50",
    "text_secondary": "#7f8c8d",
    "text_inverted": "#ffffff",
    
    # Status colors
    "success": "#27ae60",
    "warning": "#f39c12",
    "error": "#c0392b",
    "info": "#3498db",
    
    # Inventory status colors
    "in_stock": "#27ae60",
    "low_stock": "#f39c12", 
    "out_of_stock": "#c0392b",
    "discontinued": "#7f8c8d",
    
    # Border colors
    "border_light": "#ecf0f1",
    "border_medium": "#bdc3c7",
    "border_dark": "#95a5a6",
}

# Font styles
FONTS = {
    "header": {
        "family": "Helvetica",
        "size": 16,
        "weight": "bold"
    },
    "subheader": {
        "family": "Helvetica",
        "size": 14,
        "weight": "bold"
    },
    "body": {
        "family": "Helvetica",
        "size": 10,
        "weight": "normal"
    },
    "small": {
        "family": "Helvetica",
        "size": 8,
        "weight": "normal"
    },
    "input": {
        "family": "Helvetica",
        "size": 10,
        "weight": "normal"
    },
    "button": {
        "family": "Helvetica",
        "size": 10,
        "weight": "bold"
    }
}

# Padding and spacing
PADDING = {
    "small": 5,
    "medium": 10,
    "large": 20
}

# Widget styling
BUTTON_STYLE = {
    "bg": COLORS["primary"],
    "fg": COLORS["text_inverted"],
    "activebackground": "#34495e",
    "activeforeground": COLORS["text_inverted"],
    "padx": PADDING["medium"],
    "pady": PADDING["small"],
    "borderwidth": 0
}

ENTRY_STYLE = {
    "bg": "#ffffff",
    "fg": COLORS["text_primary"],
    "highlightbackground": COLORS["border_medium"],
    "highlightthickness": 1,
    "relief": "flat"
}

COMBOBOX_STYLE = {
    "background": "#ffffff",
    "foreground": COLORS["text_primary"],
    "fieldbackground": "#ffffff",
    "selectbackground": COLORS["primary"],
    "selectforeground": COLORS["text_inverted"]
}

TREEVIEW_STYLE = {
    "background": "#ffffff",
    "foreground": COLORS["text_primary"],
    "fieldbackground": "#ffffff",
    "rowheight": 25
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
                   foreground=ENTRY_STYLE["fg"])
    
    style.configure("TCombobox", 
                   **COMBOBOX_STYLE)
    
    style.configure("Treeview", 
                   **TREEVIEW_STYLE)
    
    style.configure("TFrame", 
                   background=FRAME_STYLE["bg"])
    
    style.configure("TLabel", 
                   background=LABEL_STYLE["bg"],
                   foreground=LABEL_STYLE["fg"],
                   padding=(PADDING["small"], PADDING["small"]))
    
    # Configure tag styles for treeview
    style.configure("Treeview.Tag.success", background=COLORS["success"], foreground=COLORS["text_inverted"])
    style.configure("Treeview.Tag.warning", background=COLORS["warning"], foreground=COLORS["text_inverted"])
    style.configure("Treeview.Tag.error", background=COLORS["error"], foreground=COLORS["text_inverted"])
    style.configure("Treeview.Tag.info", background=COLORS["info"], foreground=COLORS["text_inverted"])