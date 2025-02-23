# gui/main_window.py

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any, Dict, Optional, Callable
import logging
from abc import ABC

logger = logging.getLogger(__name__)


class MainWindow(ttk.Frame):
    """
    Main application window that contains the primary UI components including
    menu bar, notebook for views, and status bar.

    Args:
        root (tk.Tk): Root window of the application
        app (Any): Main application instance for accessing services and configuration
    """

    def __init__(self, root: tk.Tk, app: Any) -> None:
        super().__init__(root)
        self.root = root
        self.app = app
        self.views: Dict[str, ttk.Frame] = {}

        # Initialize UI components
        self._setup_window()
        self._create_menu()
        self._create_notebook()
        self._create_status_bar()

        logger.debug("MainWindow initialized")

    def _setup_window(self) -> None:
        """Configure the main window properties and layout."""
        self.root.title("Store Management System")
        self.root.geometry("1024x768")

        # Configure grid weights
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Place main frame
        self.grid(row=0, column=0, sticky="nsew")
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

    def _create_menu(self) -> None:
        """Create and configure the main menu bar."""
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)

        # File menu
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New", command=self._on_new)
        file_menu.add_command(label="Open", command=self._on_open)
        file_menu.add_command(label="Save", command=self._on_save)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._on_exit)

        # Edit menu
        edit_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Undo", command=self._on_undo)
        edit_menu.add_command(label="Redo", command=self._on_redo)
        edit_menu.add_separator()
        edit_menu.add_command(label="Refresh", command=self._on_refresh)

    def _create_notebook(self) -> None:
        """Create the notebook widget for managing multiple views."""
        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

    def _create_status_bar(self) -> None:
        """Create the status bar at the bottom of the window."""
        self.status_bar = ttk.Label(self, text="Ready", relief=tk.SUNKEN)
        self.status_bar.grid(row=2, column=0, sticky="ew")

    def set_status(self, message: str) -> None:
        """
        Update the status bar message.

        Args:
            message (str): Message to display in the status bar
        """
        self.status_bar.config(text=message)
        logger.debug(f"Status bar updated: {message}")

    def add_view(self, name: str, view: ttk.Frame) -> None:
        """
        Add a new view to the notebook.

        Args:
            name (str): Name of the view (displayed in tab)
            view (ttk.Frame): View instance to add
        """
        try:
            self.notebook.add(view, text=name)
            self.views[name] = view
            logger.info(f"Added view: {name}")
        except Exception as e:
            logger.error(f"Error adding view {name}: {str(e)}")
            messagebox.showerror("Error", f"Failed to add view: {name}")

    def _on_new(self) -> None:
        """Handle New menu command."""
        logger.debug("New command triggered")
        # Implement new document/record creation

    def _on_open(self) -> None:
        """Handle Open menu command."""
        logger.debug("Open command triggered")
        # Implement open functionality

    def _on_save(self) -> None:
        """Handle Save menu command."""
        logger.debug("Save command triggered")
        # Implement save functionality

    def _on_undo(self) -> None:
        """Handle Undo menu command."""
        logger.debug("Undo command triggered")
        # Implement undo functionality

    def _on_redo(self) -> None:
        """Handle Redo menu command."""
        logger.debug("Redo command triggered")
        # Implement redo functionality

    def _on_refresh(self) -> None:
        """Handle Refresh menu command."""
        logger.debug("Refresh command triggered")
        current_view = self.notebook.select()
        if current_view:
            view_name = self.notebook.tab(current_view, "text")
            if view_name in self.views:
                try:
                    self.views[view_name].refresh()
                    self.set_status(f"Refreshed {view_name}")
                except Exception as e:
                    logger.error(f"Error refreshing view {view_name}: {str(e)}")
                    messagebox.showerror("Error", f"Failed to refresh {view_name}")

    def _on_exit(self) -> None:
        """Handle Exit menu command."""
        logger.debug("Exit command triggered")
        if messagebox.askokcancel("Exit", "Are you sure you want to exit?"):
            # Clean up and close the application
            try:
                for view in self.views.values():
                    if hasattr(view, 'cleanup'):
                        view.cleanup()
                self.root.quit()
            except Exception as e:
                logger.error(f"Error during application exit: {str(e)}")
                messagebox.showerror("Error", "Failed to exit cleanly")