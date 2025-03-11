# gui/base/base_view.py
"""
Base View class for all GUI views.
Provides common functionality for views, including service access.
"""

import logging
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any, Dict, List, Optional, Type, TypeVar

from di import resolve
from gui import theme, config

# Type variable for service type hints
T = TypeVar('T')

class BaseView:
    """Base class for all views in the application."""
    
    def __init__(self, parent):
        """
        Initialize the base view.
        
        Args:
            parent: The parent widget
        """
        self.parent = parent
        self.logger = logging.getLogger(self.__class__.__name__)
        self.frame = None
        self.title = "Base View"
        self.services = {}  # Cache for resolved services
    
    def build(self):
        """
        Build the view layout.
        Must be implemented by subclasses.
        """
        self.frame = ttk.Frame(self.parent)
        self.frame.pack(fill=tk.BOTH, expand=True)
        
        # Create a header
        self.create_header()
        
        # Add content placeholder - subclasses should override this
        content = ttk.Frame(self.frame)
        ttk.Label(content, text="Content not implemented").pack(pady=20)
        content.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def create_header(self):
        """Create a standard header for the view."""
        header_frame = ttk.Frame(self.frame)
        
        # Title label
        title_label = ttk.Label(
            header_frame, 
            text=self.title,
            font=theme.create_custom_font(theme.FONTS["header"]))
        title_label.pack(side=tk.LEFT, padx=10, pady=10)
        
        # Action buttons frame on the right
        self.action_buttons = ttk.Frame(header_frame)
        self.action_buttons.pack(side=tk.RIGHT, padx=10, pady=10)
        
        # Add action buttons - subclasses can add more
        self._add_default_action_buttons()
        
        header_frame.pack(fill=tk.X)
        
        # Add a separator
        ttk.Separator(self.frame, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=5, pady=5)
    
    def _add_default_action_buttons(self):
        """Add default action buttons to the header."""
        # Implemented by subclasses
        pass
    
    def refresh(self):
        """Refresh the view content."""
        self.logger.info(f"Refreshing view: {self.title}")
        # Clear and rebuild the view
        if self.frame:
            self.frame.destroy()
        self.build()
    
    def get_service(self, service_type: str) -> T:
        """
        Get a service instance using DI.
        
        Args:
            service_type: The type/name of service to resolve
            
        Returns:
            The resolved service instance
        """
        if service_type not in self.services:
            try:
                self.services[service_type] = resolve(service_type)
            except Exception as e:
                self.logger.error(f"Error resolving service {service_type}: {str(e)}")
                messagebox.showerror(
                    "Service Error",
                    f"Failed to access {service_type} service: {str(e)}"
                )
                return None
        
        return self.services[service_type]
    
    def show_error(self, title: str, message: str):
        """
        Show an error message dialog.
        
        Args:
            title: The error dialog title
            message: The error message
        """
        self.logger.error(f"Error: {message}")
        messagebox.showerror(title, message)
    
    def show_warning(self, title: str, message: str):
        """
        Show a warning message dialog.
        
        Args:
            title: The warning dialog title
            message: The warning message
        """
        self.logger.warning(f"Warning: {message}")
        messagebox.showwarning(title, message)
    
    def show_info(self, title: str, message: str):
        """
        Show an info message dialog.
        
        Args:
            title: The info dialog title
            message: The info message
        """
        messagebox.showinfo(title, message)
    
    def show_confirm(self, title: str, message: str) -> bool:
        """
        Show a confirmation dialog.
        
        Args:
            title: The confirmation dialog title
            message: The confirmation message
            
        Returns:
            True if confirmed, False otherwise
        """
        return messagebox.askyesno(title, message)
    
    def destroy(self):
        """Destroy the view."""
        if self.frame:
            self.frame.destroy()