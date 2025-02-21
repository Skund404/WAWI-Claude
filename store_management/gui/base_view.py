# store_management/gui/base_view.py

import tkinter as tk
from tkinter import ttk, messagebox
from ..application import Application


class BaseView(ttk.Frame):
    """Base class for all view components"""

    def __init__(self, parent, app: Application):
        super().__init__(parent)
        self.parent = parent
        self.app = app

    def load_data(self):
        """Load data into the view"""
        # To be implemented by subclasses
        pass

    def save(self):
        """Save current data"""
        # To be implemented by subclasses
        pass

    def undo(self):
        """Undo the last action"""
        # To be implemented by subclasses
        pass

    def redo(self):
        """Redo the last undone action"""
        # To be implemented by subclasses
        pass

    def show_error(self, title, message):
        """Show error message"""
        messagebox.showerror(title, message)

    def show_info(self, title, message):
        """Show information message"""
        messagebox.showinfo(title, message)

    def show_warning(self, title, message):
        """Show warning message"""
        messagebox.showwarning(title, message)

    def confirm(self, title, message):
        """Show confirmation dialog"""
        return messagebox.askyesno(title, message)

    def set_status(self, message):
        """Set status message in main window"""
        if hasattr(self.app, "main_window"):
            self.app.main_window.set_status(message)