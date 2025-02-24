from di.core import inject
from services.interfaces import (
    MaterialService,
    ProjectService,
    InventoryService,
    OrderService,
)

"""
Fix for the main window to ensure views are properly created and loaded.
"""
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("main_window_fix")


def fix_main_window():
    """Fix the main window implementation to ensure views are properly loaded."""
    main_window_path = os.path.join("gui", "main_window.py")
    if not os.path.exists(main_window_path):
        logger.error(f"Main window file not found at {main_window_path}")
        return False
    backup_path = main_window_path + ".bak"
    try:
        with open(main_window_path, "r") as src:
            with open(backup_path, "w") as dst:
                dst.write(src.read())
        logger.info(f"Created backup of main window at {backup_path}")
    except Exception as e:
        logger.error(f"Failed to create backup: {str(e)}")
        return False
    new_content = """
# Path: gui/main_window.py
""\"
Main window implementation for the application.
""\"
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import logging

from gui.storage.storage_view import StorageView
# Uncomment other views when they're ready
# from gui.product.recipe_view import PatternView
# from gui.order.order_view import OrderView
# from gui.shopping_list.shopping_list_view import ShoppingListView

logger = logging.getLogger(__name__)

class MainWindow:
    ""\"
    Main window of the application.
    Contains the menu, notebook for views, and status bar.
    ""\"

    @inject(MaterialService)
        def __init__(self, root, app):
        ""\"
        Initialize the main window.

        Args:
            root: Root Tkinter window
            app: Application instance
        ""\"
        self.root = root
        self.app = app

        # Set up the main window
        self._setup_window()
        self._create_menu()
        self._create_notebook()
        self._create_status_bar()

        logger.info("Main window initialized")

    @inject(MaterialService)
        def _setup_window(self):
        ""\"Set up the main window properties.""\"
        self.root.title("Store Management System")
        self.root.geometry("1024x768")

        # Make the window resizable
        self.root.resizable(True, True)

        # Configure grid weights
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

    @inject(MaterialService)
        def _create_menu(self):
        ""\"Create the main menu.""\"
        self.menu_bar = tk.Menu(self.root)

        # File menu
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        file_menu.add_command(label="New", command=self._on_new, accelerator="Ctrl+N")
        file_menu.add_command(label="Open", command=self._on_open, accelerator="Ctrl+O")
        file_menu.add_command(label="Save", command=self._on_save, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._on_exit, accelerator="Alt+F4")
        self.menu_bar.add_cascade(label="File", menu=file_menu)

        # Edit menu
        edit_menu = tk.Menu(self.menu_bar, tearoff=0)
        edit_menu.add_command(label="Undo", command=self._on_undo, accelerator="Ctrl+Z")
        edit_menu.add_command(label="Redo", command=self._on_redo, accelerator="Ctrl+Y")
        self.menu_bar.add_cascade(label="Edit", menu=edit_menu)

        # Set the menu
        self.root.config(menu=self.menu_bar)

        # Bind keyboard shortcuts
        self.root.bind("<Control-n>", lambda event: self._on_new())
        self.root.bind("<Control-o>", lambda event: self._on_open())
        self.root.bind("<Control-s>", lambda event: self._on_save())
        self.root.bind("<Control-z>", lambda event: self._on_undo())
        self.root.bind("<Control-y>", lambda event: self._on_redo())

    @inject(MaterialService)
        def _create_notebook(self):
        ""\"Create the notebook with tabs for different views.""\"
        self.notebook = ttk.Notebook(self.root)
        self.notebook.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # Create and add tabs
        self._add_storage_tab()
        # Uncomment as other views are implemented
        # self._add_recipes_tab()
        # self._add_orders_tab()
        # self._add_shopping_list_tab()

    @inject(MaterialService)
        def _add_storage_tab(self):
        ""\"Add the storage tab to the notebook.""\"
        try:
            logger.info("Creating storage view")
            storage_frame = ttk.Frame(self.notebook)
            storage_view = StorageView(storage_frame, self.app)
            self.notebook.add(storage_frame, text="Storage")
            logger.info("Storage view created and added to notebook")
        except Exception as e:
            logger.error(f"Error creating storage view: {str(e)}", exc_info=True)
            messagebox.showerror("Error", f"Failed to create Storage view: {str(e)}")

    @inject(MaterialService)
        def _add_recipes_tab(self):
        ""\"Add the patterns tab to the notebook.""\"
        try:
            recipes_frame = ttk.Frame(self.notebook)
            recipe_view = RecipeView(recipes_frame, self.app)
            self.notebook.add(recipes_frame, text="Patterns")
        except Exception as e:
            logger.error(f"Error creating pattern view: {str(e)}", exc_info=True)
            messagebox.showerror("Error", f"Failed to create Patterns view: {str(e)}")

    @inject(MaterialService)
        def _add_orders_tab(self):
        ""\"Add the orders tab to the notebook.""\"
        try:
            orders_frame = ttk.Frame(self.notebook)
            order_view = OrderView(orders_frame, self.app)
            self.notebook.add(orders_frame, text="Orders")
        except Exception as e:
            logger.error(f"Error creating order view: {str(e)}", exc_info=True)
            messagebox.showerror("Error", f"Failed to create Orders view: {str(e)}")

    @inject(MaterialService)
        def _add_shopping_list_tab(self):
        ""\"Add the shopping list tab to the notebook.""\"
        try:
            shopping_list_frame = ttk.Frame(self.notebook)
            shopping_list_view = ShoppingListView(shopping_list_frame, self.app)
            self.notebook.add(shopping_list_frame, text="Shopping Lists")
        except Exception as e:
            logger.error(f"Error creating shopping list view: {str(e)}", exc_info=True)
            messagebox.showerror("Error", f"Failed to create Shopping Lists view: {str(e)}")

    @inject(MaterialService)
        def _create_status_bar(self):
        ""\"Create the status bar at the bottom of the window.""\"
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")

        self.status_bar = ttk.Label(
            self.root, 
            textvariable=self.status_var, 
            relief=tk.SUNKEN, 
            anchor=tk.W
        )
        self.status_bar.grid(row=1, column=0, sticky="ew")

    @inject(MaterialService)
        def set_status(self, message):
        ""\"
        Set the status message in the status bar.

        Args:
            message: Status message
        ""\"
        self.status_var.set(message)
        logger.debug(f"Status set to: {message}")

    @inject(MaterialService)
        def _on_new(self):
        ""\"Handle New menu action.""\"
        logger.info("New action triggered")
        # Implementation depends on the specific functionality needed

    @inject(MaterialService)
        def _on_open(self):
        ""\"Handle Open menu action.""\"
        logger.info("Open action triggered")
        # Implementation depends on the specific functionality needed

    @inject(MaterialService)
        def _on_save(self):
        ""\"Handle Save menu action.""\"
        logger.info("Save action triggered")

        # Get the current tab
        current_tab = self.notebook.select()
        if not current_tab:
            return

        # Get the view in the current tab
        tab_index = self.notebook.index(current_tab)
        tab_name = self.notebook.tab(tab_index, "text")

        # Find the view and call its save method
        try:
            for child in self.notebook.winfo_children()[tab_index].winfo_children():
                if hasattr(child, 'save'):
                    child.save()
                    self.set_status(f"{tab_name} data saved")
                    break
        except Exception as e:
            logger.error(f"Error saving {tab_name}: {str(e)}")
            messagebox.showerror("Save Error", f"Error saving {tab_name}: {str(e)}")

    @inject(MaterialService)
        def _on_undo(self):
        ""\"Handle Undo menu action.""\"
        logger.info("Undo action triggered")

        # Get the current tab
        current_tab = self.notebook.select()
        if not current_tab:
            return

        # Get the view in the current tab
        tab_index = self.notebook.index(current_tab)

        # Find the view and call its undo method
        try:
            for child in self.notebook.winfo_children()[tab_index].winfo_children():
                if hasattr(child, 'undo'):
                    child.undo()
                    break
        except Exception as e:
            logger.error(f"Error in undo: {str(e)}")
            messagebox.showerror("Undo Error", f"Error in undo operation: {str(e)}")

    @inject(MaterialService)
        def _on_redo(self):
        ""\"Handle Redo menu action.""\"
        logger.info("Redo action triggered")

        # Get the current tab
        current_tab = self.notebook.select()
        if not current_tab:
            return

        # Get the view in the current tab
        tab_index = self.notebook.index(current_tab)

        # Find the view and call its redo method
        try:
            for child in self.notebook.winfo_children()[tab_index].winfo_children():
                if hasattr(child, 'redo'):
                    child.redo()
                    break
        except Exception as e:
            logger.error(f"Error in redo: {str(e)}")
            messagebox.showerror("Redo Error", f"Error in redo operation: {str(e)}")

    @inject(MaterialService)
        def _on_exit(self):
        ""\"Handle Exit menu action.""\"
        logger.info("Exit action triggered")

        # Ask for confirmation
        if messagebox.askyesno("Exit", "Are you sure you want to exit?"):
            # Clean up and close the application
            self.app.quit()
"""
    try:
        with open(main_window_path, "w") as f:
            f.write(new_content.strip())
        logger.info(f"Updated main window at {main_window_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to update main window: {str(e)}")
        return False


if __name__ == "__main__":
    if fix_main_window():
        logger.info(
            "Main window fixed successfully. Run the application to see the changes."
        )
    else:
        logger.error("Failed to fix main window.")
