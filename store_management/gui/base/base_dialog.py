# gui/base/base_dialog.py
"""
Base Dialog class for modal dialogs.
Provides common functionality for dialog windows.
"""

import logging
import tkinter as tk
from tkinter import ttk
from typing import Any, Callable, Dict, List, Optional

from gui import theme, config

class BaseDialog:
    """Base class for all dialog windows in the application."""
    
    def __init__(self, parent, title="Dialog", width=500, height=400, modal=True):
        """
        Initialize the base dialog.
        
        Args:
            parent: The parent window
            title: The dialog title
            width: The dialog width
            height: The dialog height
            modal: Whether the dialog is modal
        """
        self.parent = parent
        self.title = title
        self.width = width
        self.height = height
        self.modal = modal
        self.dialog = None
        self.result = None
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def create_dialog(self):
        """Create the dialog window."""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title(self.title)
        self.dialog.geometry(f"{self.width}x{self.height}")
        self.dialog.minsize(self.width // 2, self.height // 2)
        
        # Make dialog modal if required
        if self.modal:
            self.dialog.transient(self.parent)
            self.dialog.grab_set()
            
        # Center the dialog on the parent window
        self.center_dialog()
        
        # Handle dialog close
        self.dialog.protocol("WM_DELETE_WINDOW", self.on_cancel)
        
        # Create the dialog layout
        self.create_layout()
    
    def center_dialog(self):
        """Center the dialog on the parent window."""
        if not self.dialog or not self.parent:
            return
        
        # Get parent geometry
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        # Calculate position
        x = parent_x + (parent_width - self.width) // 2
        y = parent_y + (parent_height - self.height) // 2
        
        # Set dialog position
        self.dialog.geometry(f"+{x}+{y}")
    
    def create_layout(self):
        """
        Create the dialog layout.
        Override in subclasses to define specific layout.
        """
        # Create main content frame
        content_frame = ttk.Frame(self.dialog, padding=10)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create placeholder content
        placeholder = ttk.Label(content_frame, text="Dialog content not implemented")
        placeholder.pack(pady=20)
        
        # Create button frame
        button_frame = ttk.Frame(self.dialog, padding="10 0 10 10")
        button_frame.pack(fill=tk.X)
        
        # Create Ok/Cancel buttons
        ttk.Button(button_frame, text="OK", command=self.on_ok).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.on_cancel).pack(side=tk.RIGHT, padx=5)
    
    def on_ok(self):
        """Handle OK button click."""
        self.result = True
        self.close()
    
    def on_cancel(self):
        """Handle Cancel button click."""
        self.result = False
        self.close()
    
    def close(self):
        """Close the dialog."""
        if self.dialog:
            self.dialog.grab_release()
            self.dialog.destroy()
    
    def show(self):
        """
        Show the dialog and wait for it to be closed.
        
        Returns:
            The dialog result
        """
        try:
            self.create_dialog()
            
            if self.modal:
                # Wait for the dialog to be closed
                self.parent.wait_window(self.dialog)
                return self.result
            
            return None
        except Exception as e:
            self.logger.error(f"Error showing dialog: {str(e)}")
            if self.dialog:
                self.dialog.destroy()
            return False