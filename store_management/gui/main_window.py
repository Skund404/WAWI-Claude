# Path: store_management/gui/main_window.py
import tkinter as tk
import tkinter.ttk as ttk
import sys
import os

from store_management.application import Application
from store_management.gui.order.order_view import OrderView
from store_management.gui.storage.storage_view import StorageView
from store_management.gui.recipe.recipe_view import RecipeView
from store_management.gui.shopping_list.shopping_list_view import ShoppingListView
from store_management.services.interfaces.storage_service import IStorageService
from store_management.services.interfaces.order_service import IOrderService
from store_management.services.interfaces.inventory_service import IInventoryService
from store_management.services.interfaces.recipe_service import IRecipeService
from store_management.services.interfaces.shopping_list_service import IShoppingListService


class MainWindow:
    """
    Main application window managing the core GUI structure.

    Responsibilities:
    - Create main application window
    - Manage application tabs
    - Handle global application-level interactions
    - Provide status bar and menu functionality
    """

    def __init__(self, root: tk.Tk, app: Application):
        """
        Initialize the main application window.

        Args:
            root: Tkinter root window
            app: Application instance for dependency management
        """
        self.root = root
        self.app = app
        self.root.title("Store Management System")

        # Get window size from application configuration
        try:
            from store_management.config import WINDOW_SIZE
            self.root.geometry(f"{WINDOW_SIZE[0]}x{WINDOW_SIZE[1]}")
        except ImportError:
            # Fallback to default size if not specified
            self.root.geometry("1200x800")

        # Create main UI components
        self._create_menu()
        self._create_main_notebook()
        self._create_status_bar()
        self._bind_global_shortcuts()

    def _create_menu(self):
        """Create the main menu bar with application-wide options."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New", command=self._on_new)
        file_menu.add_command(label="Open", command=self._on_open)
        file_menu.add_command(label="Save", command=self._on_save)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._on_exit)

        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Undo", command=self._on_undo)
        edit_menu.add_command(label="Redo", command=self._on_redo)

    def _create_main_notebook(self):
        """Create a notebook (tabbed) interface for different views."""
        # Create notebook widget
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill='both')

        # Create views with notebook as parent
        storage_view = StorageView(self.notebook, self.app)
        order_view = OrderView(self.notebook, self.app)
        recipe_view = RecipeView(self.notebook, self.app)
        shopping_list_view = ShoppingListView(self.notebook, self.app)

        # Add views to notebook
        self.notebook.add(storage_view, text="Storage")
        self.notebook.add(order_view, text="Orders")
        self.notebook.add(recipe_view, text="Recipes")
        self.notebook.add(shopping_list_view, text="Shopping Lists")

        # Load data for each view
        storage_view.load_data()
        order_view.load_data()
        recipe_view.load_data()
        shopping_list_view.load_data()

    def _create_status_bar(self):
        """Create a status bar at the bottom of the application window."""
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")

        status_bar = ttk.Label(
            self.root,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _bind_global_shortcuts(self):
        """Bind global keyboard shortcuts for common actions."""
        self.root.bind('<Control-n>', self._on_new)
        self.root.bind('<Control-o>', self._on_open)
        self.root.bind('<Control-s>', self._on_save)
        self.root.bind('<Control-z>', self._on_undo)
        self.root.bind('<Control-y>', self._on_redo)

    def set_status(self, message: str):
        """
        Update the status bar message.

        Args:
            message: Status message to display
        """
        self.status_var.set(message)

    def _on_new(self, event=None):
        """Handle 'New' menu action."""
        current_view = self._get_current_view()
        if current_view and hasattr(current_view, 'show_add_dialog'):
            current_view.show_add_dialog()

    def _on_open(self, event=None):
        """Handle 'Open' menu action."""
        # Placeholder for open functionality
        self.set_status("Open action not implemented")

    def _on_save(self, event=None):
        """
        Handle 'Save' menu action.

        Args:
            event: Optional tkinter event (for keyboard shortcut)
        """
        current_view = self._get_current_view()
        if current_view and hasattr(current_view, 'save'):
            current_view.save()
            self.set_status("Data saved successfully")

    def _on_undo(self, event=None):
        """
        Handle 'Undo' menu action.

        Args:
            event: Optional tkinter event (for keyboard shortcut)
        """
        current_view = self._get_current_view()
        if current_view and hasattr(current_view, 'undo'):
            current_view.undo()
            self.set_status("Last action undone")

    def _on_redo(self, event=None):
        """
        Handle 'Redo' menu action.

        Args:
            event: Optional tkinter event (for keyboard shortcut)
        """
        current_view = self._get_current_view()
        if current_view and hasattr(current_view, 'redo'):
            current_view.redo()
            self.set_status("Last action redone")

    def _get_current_view(self):
        """
        Get the currently selected view in the notebook.

        Returns:
            Currently selected view or None
        """
        current_tab_index = self.notebook.index(self.notebook.select())
        return self.notebook.winfo_children()[current_tab_index]

    def _on_exit(self):
        """
        Handle application exit.
        Performs cleanup and closes the application.
        """
        # Optional: Add cleanup logic for unsaved changes
        self.root.quit()

    def run(self):
        """Start the main application event loop."""
        # Center the window on the screen
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

        # Start the main event loop
        self.root.mainloop()