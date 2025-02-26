# store_management/fallback_mainwindow.py
"""
Fallback Main Window for the Leatherworking Store Management Application.

Provides a minimal functional window in case of primary window initialization failure.
"""

import logging
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any, Optional

def create_fallback_window(root: Optional[tk.Tk] = None, container: Optional[Any] = None) -> tk.Toplevel:
    """
    Create a fallback main window with minimal functionality.

    Args:
        root (Optional[tk.Tk]): Parent Tkinter root window
        container (Optional[Any]): Dependency injection container

    Returns:
        tk.Toplevel: A minimal but functional main window
    """
    if root is None:
        root = tk.Tk()

    try:
        window = tk.Toplevel(root)
        window.title("Leatherworking Store Management - Fallback")
        window.geometry("600x400")

        # Ensure the root is withdrawn if it was just created
        root.withdraw()

        # Setup a basic notebook (tabbed interface)
        notebook = ttk.Notebook(window)
        notebook.pack(expand=True, fill='both')

        # Add placeholder tabs
        tabs = [
            ("Dashboard", "Dashboard placeholder"),
            ("Inventory", "Inventory placeholder"),
            ("Orders", "Orders placeholder"),
            ("Projects", "Projects placeholder")
        ]

        for title, content in tabs:
            frame = ttk.Frame(notebook)
            label = ttk.Label(frame, text=content, padding=20)
            label.pack(expand=True, fill='both')
            notebook.add(frame, text=title)

        # Fallback Status Bar
        status_var = tk.StringVar(value="Fallback mode: Application started in reduced functionality")
        status_bar = ttk.Label(window, textvariable=status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # Basic menu
        menubar = tk.Menu(window)
        window.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Exit", command=window.quit)

        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(
            label="About",
            command=lambda: messagebox.showinfo(
                "About",
                "Leatherworking Store Management\nFallback Window"
            )
        )

        logging.info("Fallback window created successfully")
        return window

    except Exception as e:
        logging.error(f"Error creating fallback window: {e}")
        messagebox.showerror("Critical Error", f"Could not create fallback window: {e}")
        raise

def get_service(service_type):
    """
    Minimal service retrieval method for fallback window.

    Args:
        service_type (type): The type of service to retrieve

    Returns:
        None: Placeholder for service retrieval
    """
    logging.warning(f"Service retrieval not available in fallback mode: {service_type}")
    return None