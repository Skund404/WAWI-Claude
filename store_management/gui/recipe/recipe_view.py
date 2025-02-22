# Path: gui/recipe/recipe_view.py
"""
Recipe view implementation that displays recipes.
"""
import tkinter as tk
from tkinter import ttk
import logging
import sqlite3
import os

from gui.base_view import BaseView
from services.interfaces.recipe_service import IRecipeService

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RecipeView(BaseView):
    """
    View for displaying and managing recipes.
    """

    def __init__(self, parent, app):
        """
        Initialize the recipe view.

        Args:
            parent: Parent widget
            app: Application instance
        """
        super().__init__(parent, app)
        self.db_path = self._find_database_file()
        logger.debug(f"RecipeView initialized with database: {self.db_path}")
        self.setup_ui()
        self.load_data()

    def _find_database_file(self):
        """Find the SQLite database file."""
        # List of possible locations
        possible_locations = [
            "store_management.db",
            "data/store_management.db",
            "database/store_management.db",
            "config/database/store_management.db"
        ]

        for location in possible_locations:
            if os.path.exists(location):
                return location

        # If not found in the predefined locations, search for it
        logger.info("Searching for database file...")
        for root, _, files in os.walk("."):
            for file in files:
                if file.endswith('.db'):
                    path = os.path.join(root, file)
                    logger.info(f"Found database file: {path}")
                    return path

        return None

    def setup_ui(self):
        """Set up the user interface components."""
        self.create_toolbar()
        self.create_treeview()

    def create_toolbar(self):
        """Create the toolbar with buttons."""
        toolbar = ttk.Frame(self)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        # Add buttons
        ttk.Button(toolbar, text="Add Recipe", command=self.show_add_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Delete Selected", command=lambda e=None: self.delete_selected(e)).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Search", command=self.show_search_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Refresh", command=self.load_data).pack(side=tk.LEFT, padx=2)

        logger.debug("Toolbar created")

    def create_treeview(self):
        """Create the treeview for displaying recipes."""
        # Create a frame to hold the treeview and scrollbar
        frame = ttk.Frame(self)
        frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Define columns
        columns = ("id", "name", "type", "description", "ingredients", "servings")

        # Create the treeview
        self.tree = ttk.Treeview(frame, columns=columns, show="headings")

        # Define headings
        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="Name")
        self.tree.heading("type", text="Type")
        self.tree.heading("description", text="Description")
        self.tree.heading("ingredients", text="Ingredients")
        self.tree.heading("servings", text="Servings")

        # Define column widths
        self.tree.column("id", width=50)
        self.tree.column("name", width=150)
        self.tree.column("type", width=100)
        self.tree.column("description", width=200)
        self.tree.column("ingredients", width=200)
        self.tree.column("servings", width=80)

        # Add scrollbars
        vsb = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # Pack scrollbars and treeview
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Bind events
        self.tree.bind("<Double-1>", self.on_double_click)

        logger.debug("Treeview created")

    def load_data(self):
        """Load recipes from the database and display them."""
        try:
            logger.info("Loading recipe data")

            # Clear existing items
            for item in self.tree.get_children():
                self.tree.delete(item)

            if not self.db_path:
                logger.error("Database file not found")
                self.set_status("Error: Database file not found")
                return

            # Connect to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Check if recipe table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='recipe';
            """)

            if not cursor.fetchone():
                logger.info("Recipe table doesn't exist. Creating sample data.")
                self.set_status("Recipe table doesn't exist - showing sample data")

                # Add sample data since table doesn't exist
                sample_data = [
                    (1, "Basic Bread", "Baking", "Simple bread recipe", "Flour, Water, Yeast, Salt", 4),
                    (2, "Chocolate Cake", "Dessert", "Rich chocolate cake", "Flour, Sugar, Cocoa, Eggs, Butter", 8),
                    (3, "Vegetable Soup", "Soup", "Healthy vegetable soup", "Carrot, Potato, Onion, Celery, Broth", 6),
                    (4, "Caesar Salad", "Salad", "Classic caesar salad", "Romaine Lettuce, Croutons, Parmesan, Caesar Dressing", 2),
                    (5, "Spaghetti Carbonara", "Pasta", "Italian pasta dish", "Spaghetti, Eggs, Bacon, Parmesan, Black Pepper", 4)
                ]

                # Add to treeview
                for recipe in sample_data:
                    self.tree.insert("", tk.END, values=recipe)

                return

            # Get recipe data
            cursor.execute("SELECT id, name, type, description, ingredients, servings FROM recipe;")
            rows = cursor.fetchall()

            # Add to treeview
            for row in rows:
                self.tree.insert("", tk.END, values=row)

            self.set_status(f"Loaded {len(rows)} recipes")
            logger.info(f"Loaded {len(rows)} recipes")

        except Exception as e:
            logger.error(f"Error loading recipe data: {str(e)}", exc_info=True)
            self.show_error("Data Load Error", f"Failed to load recipe data: {str(e)}")
        finally:
            if 'conn' in locals():
                conn.close()

    def show_add_dialog(self):
        """Show dialog to add a new recipe."""
        # Implementation would go here
        logger.debug("Add dialog requested but not implemented")
        self.show_info("Not Implemented", "Add recipe functionality is not yet implemented.")

    def on_double_click(self, event):
        """Handle double-click on a recipe item."""
        # Implementation would go here
        logger.debug("Double-click event received but not implemented")
        self.show_info("Not Implemented", "Edit recipe functionality is not yet implemented.")

    def delete_selected(self, event):
        """Delete the selected recipe."""
        # Implementation would go here
        logger.debug("Delete requested but not implemented")
        self.show_info("Not Implemented", "Delete recipe functionality is not yet implemented.")

    def show_search_dialog(self):
        """Show search dialog."""
        # Implementation would go here
        logger.debug("Search requested but not implemented")
        self.show_info("Not Implemented", "Search functionality is not yet implemented.")