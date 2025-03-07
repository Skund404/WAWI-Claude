"""
Theme management for the Leatherworking Application.
Centralizes styling and visual appearance for consistent UI.
"""
import logging
import tkinter as tk
from tkinter import ttk
import os
import json

logger = logging.getLogger(__name__)


class AppTheme:
    """
    Application theme management for the Leatherworking Application.
    Provides consistent styling across all application components.
    """
    
    # Color scheme
    COLORS = {
        'primary': '#1a73e8',      # Main brand color - blue
        'primary_dark': '#0d47a1', # Darker variation of primary
        'primary_light': '#e3f2fd', # Lighter variation of primary
        'secondary': '#5f6368',    # Secondary color - gray
        'success': '#0f9d58',      # Success color - green
        'warning': '#f29900',      # Warning color - amber
        'danger': '#d93025',       # Danger/error color - red
        'info': '#6200ee',         # Info color - purple
        'light': '#f8f9fa',        # Light color for backgrounds
        'dark': '#202124',         # Dark color for text
        'surface': '#ffffff',      # Surface color - white
        'background': '#f1f3f4',   # Background color - light gray
        'border': '#dadce0',       # Border color
        'disabled': '#9e9e9e',     # Disabled elements color
        
        # Tool-specific category colors
        'leather': '#8d6e63',      # Brown for leather items
        'hardware': '#78909c',     # Blue-gray for hardware
        'tools': '#ff8f00',        # Amber for tools
        'thread': '#7cb342',       # Light green for thread
        'dye': '#6a1b9a',          # Purple for dyes
    }
    
    # Font definitions
    FONTS = {
        'heading': ('Helvetica', 14, 'bold'),
        'subheading': ('Helvetica', 12, 'bold'),
        'body': ('Helvetica', 10),
        'small': ('Helvetica', 9),
        'button': ('Helvetica', 10),
        'monospace': ('Courier', 10),
    }
    
    # Padding and spacing
    PADDING = {
        'small': 4,
        'medium': 8,
        'large': 12,
        'xlarge': 20,
    }
    
    def __init__(self, theme_file=None):
        """
        Initialize the theme manager.
        
        Args:
            theme_file: Optional path to a JSON theme file.
                        If provided, will override default theme settings.
        """
        self._style = None
        
        # Try to load a custom theme if provided
        if theme_file and os.path.exists(theme_file):
            try:
                with open(theme_file, 'r') as f:
                    custom_theme = json.load(f)
                
                # Override defaults with custom settings
                if 'colors' in custom_theme:
                    for key, value in custom_theme['colors'].items():
                        self.COLORS[key] = value
                
                if 'fonts' in custom_theme:
                    for key, value in custom_theme['fonts'].items():
                        self.FONTS[key] = tuple(value)
                
                if 'padding' in custom_theme:
                    for key, value in custom_theme['padding'].items():
                        self.PADDING[key] = value
                
                logger.info(f"Loaded custom theme from {theme_file}")
            except Exception as e:
                logger.error(f"Failed to load custom theme: {e}")
    
    def apply(self, root):
        """
        Apply the theme to the application.
        
        Args:
            root: The root Tk window of the application
        """
        logger.info("Applying application theme")
        
        # Create and configure ttk style
        self._style = ttk.Style()
        
        # Configure standard elements
        self._configure_common_elements()
        self._configure_buttons()
        self._configure_frames()
        self._configure_labels()
        self._configure_entries()
        self._configure_treeviews()
        self._configure_notebooks()
        self._configure_progressbars()
        self._configure_comboboxes()
        self._configure_scrollbars()
        
        # Configure root window
        root.configure(background=self.COLORS['background'])
        
        logger.info("Theme applied successfully")
    
    def _configure_common_elements(self):
        """Configure common elements to establish base theme."""
        # Configure the default font for all widgets
        self._style.configure('.', 
                              font=self.FONTS['body'],
                              background=self.COLORS['background'],
                              foreground=self.COLORS['dark'],
                              borderwidth=1,
                              bordercolor=self.COLORS['border'],
                              lightcolor=self.COLORS['light'],
                              darkcolor=self.COLORS['secondary'],
                              troughcolor=self.COLORS['light'],
                              selectbackground=self.COLORS['primary'],
                              selectforeground=self.COLORS['light'],
                              selectborderwidth=0,
                              insertwidth=2,
                              insertcolor=self.COLORS['dark'])
    
    def _configure_buttons(self):
        """Configure button styles."""
        # Standard button
        self._style.configure('TButton', 
                              font=self.FONTS['button'],
                              padding=(self.PADDING['medium'], self.PADDING['small']),
                              background=self.COLORS['primary'],
                              foreground=self.COLORS['light'])
        
        # Primary button (calls to action)
        self._style.configure('Primary.TButton', 
                              font=self.FONTS['button'],
                              padding=(self.PADDING['medium'], self.PADDING['small']),
                              background=self.COLORS['primary'],
                              foreground=self.COLORS['light'])
        
        # Secondary button (less prominent actions)
        self._style.configure('Secondary.TButton', 
                              font=self.FONTS['button'],
                              padding=(self.PADDING['medium'], self.PADDING['small']),
                              background=self.COLORS['secondary'],
                              foreground=self.COLORS['light'])
        
        # Success button (confirming actions)
        self._style.configure('Success.TButton', 
                              font=self.FONTS['button'],
                              padding=(self.PADDING['medium'], self.PADDING['small']),
                              background=self.COLORS['success'],
                              foreground=self.COLORS['light'])
        
        # Danger button (destructive actions)
        self._style.configure('Danger.TButton', 
                              font=self.FONTS['button'],
                              padding=(self.PADDING['medium'], self.PADDING['small']),
                              background=self.COLORS['danger'],
                              foreground=self.COLORS['light'])
        
        # Icon button (small buttons with icons)
        self._style.configure('Icon.TButton', 
                              font=self.FONTS['button'],
                              padding=self.PADDING['small'],
                              background=self.COLORS['background'],
                              foreground=self.COLORS['dark'])
    
    def _configure_frames(self):
        """Configure frame styles."""
        # Standard frame
        self._style.configure('TFrame', 
                              background=self.COLORS['background'])
        
        # Card frame (for content cards)
        self._style.configure('Card.TFrame', 
                              background=self.COLORS['surface'],
                              borderwidth=1,
                              relief='solid',
                              bordercolor=self.COLORS['border'])
        
        # Toolbar frame
        self._style.configure('Toolbar.TFrame', 
                              background=self.COLORS['primary_dark'])
        
        # Statusbar frame
        self._style.configure('Statusbar.TFrame', 
                              background=self.COLORS['secondary'],
                              relief='sunken')
    
    def _configure_labels(self):
        """Configure label styles."""
        # Standard label
        self._style.configure('TLabel', 
                              font=self.FONTS['body'],
                              background=self.COLORS['background'],
                              foreground=self.COLORS['dark'],
                              padding=(self.PADDING['small'], 0))
        
        # Heading label
        self._style.configure('Heading.TLabel', 
                              font=self.FONTS['heading'],
                              background=self.COLORS['background'],
                              foreground=self.COLORS['dark'],
                              padding=(self.PADDING['small'], self.PADDING['medium']))
        
        # Subheading label
        self._style.configure('Subheading.TLabel', 
                              font=self.FONTS['subheading'],
                              background=self.COLORS['background'],
                              foreground=self.COLORS['dark'],
                              padding=(self.PADDING['small'], self.PADDING['small']))
        
        # Status labels
        self._style.configure('Success.TLabel', 
                              foreground=self.COLORS['success'])
        self._style.configure('Warning.TLabel', 
                              foreground=self.COLORS['warning'])
        self._style.configure('Danger.TLabel', 
                              foreground=self.COLORS['danger'])
        self._style.configure('Info.TLabel', 
                              foreground=self.COLORS['info'])
    
    def _configure_entries(self):
        """Configure entry styles."""
        # Standard entry
        self._style.configure('TEntry', 
                              font=self.FONTS['body'],
                              padding=(self.PADDING['small'], self.PADDING['small']),
                              fieldbackground=self.COLORS['surface'])
        
        # Search entry
        self._style.configure('Search.TEntry', 
                              font=self.FONTS['body'],
                              padding=(self.PADDING['medium'], self.PADDING['small']),
                              fieldbackground=self.COLORS['surface'])
    
    def _configure_treeviews(self):
        """Configure treeview styles."""
        # Standard treeview
        self._style.configure('Treeview', 
                              background=self.COLORS['surface'],
                              foreground=self.COLORS['dark'],
                              rowheight=25,
                              borderwidth=0,
                              font=self.FONTS['body'])
        
        self._style.configure('Treeview.Heading', 
                              font=self.FONTS['subheading'],
                              background=self.COLORS['primary_light'],
                              foreground=self.COLORS['dark'],
                              padding=(self.PADDING['small'],))
        
        # Configure the colors of alternating rows
        self._style.map('Treeview',
                        background=[('selected', self.COLORS['primary'])],
                        foreground=[('selected', self.COLORS['light'])])
    
    def _configure_notebooks(self):
        """Configure notebook styles."""
        # Standard notebook
        self._style.configure('TNotebook', 
                              background=self.COLORS['background'],
                              tabmargins=(2, 5, 2, 0))
        
        self._style.configure('TNotebook.Tab', 
                              font=self.FONTS['body'],
                              padding=(self.PADDING['medium'], self.PADDING['small']),
                              background=self.COLORS['background'],
                              foreground=self.COLORS['dark'])
        
        self._style.map('TNotebook.Tab',
                        background=[('selected', self.COLORS['surface'])],
                        expand=[('selected', (1, 1, 1, 0))])
    
    def _configure_progressbars(self):
        """Configure progressbar styles."""
        # Standard progressbar
        self._style.configure('TProgressbar', 
                              thickness=20,
                              borderwidth=0,
                              troughcolor=self.COLORS['light'],
                              background=self.COLORS['primary'])
        
        # Success progressbar
        self._style.configure('Success.TProgressbar', 
                              background=self.COLORS['success'])
        
        # Warning progressbar
        self._style.configure('Warning.TProgressbar', 
                              background=self.COLORS['warning'])
    
    def _configure_comboboxes(self):
        """Configure combobox styles."""
        # Standard combobox
        self._style.configure('TCombobox', 
                              padding=(self.PADDING['small'], 0),
                              font=self.FONTS['body'])
        
        self._style.map('TCombobox',
                        fieldbackground=[('readonly', self.COLORS['surface'])],
                        selectbackground=[('readonly', self.COLORS['primary'])],
                        selectforeground=[('readonly', self.COLORS['light'])])
    
    def _configure_scrollbars(self):
        """Configure scrollbar styles."""
        # Standard scrollbar
        self._style.configure('TScrollbar', 
                              gripcount=0,
                              background=self.COLORS['background'],
                              darkcolor=self.COLORS['background'],
                              lightcolor=self.COLORS['background'],
                              troughcolor=self.COLORS['background'],
                              bordercolor=self.COLORS['background'],
                              arrowcolor=self.COLORS['secondary'])
    
    def get_color(self, color_name):
        """
        Get a color from the theme.
        
        Args:
            color_name: The name of the color to retrieve
            
        Returns:
            The color value or None if not found
        """
        return self.COLORS.get(color_name)
    
    def get_font(self, font_name):
        """
        Get a font from the theme.
        
        Args:
            font_name: The name of the font to retrieve
            
        Returns:
            The font tuple or None if not found
        """
        return self.FONTS.get(font_name)
    
    def get_padding(self, padding_name):
        """
        Get a padding value from the theme.
        
        Args:
            padding_name: The name of the padding to retrieve
            
        Returns:
            The padding value or None if not found
        """
        return self.PADDING.get(padding_name)


# Helper function to get colors easily
def get_color(color_name):
    """
    Get a color from the application theme.
    
    Args:
        color_name: The name of the color to retrieve
        
    Returns:
        The color value or None if not found
    """
    # This is a convenience function that can be imported
    # without having to create a theme instance
    return AppTheme.COLORS.get(color_name)
