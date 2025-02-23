# Path: tools/enable_all_tabs.py
"""
Script to enable all tabs in the main window.
"""
import os
import logging
import re

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("tab_enabler")


def create_recipe_view():
    """Create a basic recipe view."""
    recipe_view_dir = os.path.join('gui', 'recipe')
    recipe_view_path = os.path.join(recipe_view_dir, 'recipe_view.py')

    # Create directory if it doesn't exist
    os.makedirs(recipe_view_dir, exist_ok=True)

    # Project view content
    recipe_view_content = '''
# Path: gui/recipe/recipe_view.py
"""
Project view implementation that displays recipes.
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
        ttk.Button(toolbar, text="Add Project", command=self.show_add_dialog).pack(side=tk.LEFT, padx=2)
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
                logger.info("Project table doesn't exist. Creating sample data.")
                self.set_status("Project table doesn't exist - showing sample data")

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
'''

    with open(recipe_view_path, 'w') as f:
        f.write(recipe_view_content.strip())
    logger.info(f"Created recipe view at {recipe_view_path}")
    return True


def create_order_view():
    """Create a basic order view."""
    order_view_dir = os.path.join('gui', 'order')
    order_view_path = os.path.join(order_view_dir, 'order_view.py')

    # Create directory if it doesn't exist
    os.makedirs(order_view_dir, exist_ok=True)

    # Order view content
    order_view_content = '''
# Path: gui/order/order_view.py
"""
Order view implementation that displays orders.
"""
import tkinter as tk
from tkinter import ttk
import logging
import sqlite3
import os
from datetime import datetime

from gui.base_view import BaseView
from services.interfaces.order_service import IOrderService

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OrderView(BaseView):
    """
    View for displaying and managing orders.
    """

    def __init__(self, parent, app):
        """
        Initialize the order view.

        Args:
            parent: Parent widget
            app: Application instance
        """
        super().__init__(parent, app)
        self.db_path = self._find_database_file()
        logger.debug(f"OrderView initialized with database: {self.db_path}")
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
        ttk.Button(toolbar, text="Add Order", command=self.show_add_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Delete Selected", command=lambda e=None: self.delete_selected(e)).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Search", command=self.show_search_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Refresh", command=self.load_data).pack(side=tk.LEFT, padx=2)

        logger.debug("Toolbar created")

    def create_treeview(self):
        """Create the treeview for displaying orders."""
        # Create a frame to hold the treeview and scrollbar
        frame = ttk.Frame(self)
        frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Define columns
        columns = ("id", "order_number", "customer", "date", "status", "total")

        # Create the treeview
        self.tree = ttk.Treeview(frame, columns=columns, show="headings")

        # Define headings
        self.tree.heading("id", text="ID")
        self.tree.heading("order_number", text="Order #")
        self.tree.heading("customer", text="Customer")
        self.tree.heading("date", text="Date")
        self.tree.heading("status", text="Status")
        self.tree.heading("total", text="Total")

        # Define column widths
        self.tree.column("id", width=50)
        self.tree.column("order_number", width=100)
        self.tree.column("customer", width=200)
        self.tree.column("date", width=100)
        self.tree.column("status", width=100)
        self.tree.column("total", width=100)

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
        """Load orders from the database and display them."""
        try:
            logger.info("Loading order data")

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

            # Check if order table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='order';
            """)

            if not cursor.fetchone():
                logger.info("Order table doesn't exist. Creating sample data.")
                self.set_status("Order table doesn't exist - showing sample data")

                # Add sample data since table doesn't exist
                today = datetime.now().strftime("%Y-%m-%d")

                sample_data = [
                    (1, "ORD-001", "John Smith", today, "New", "$150.00"),
                    (2, "ORD-002", "Jane Doe", today, "Processing", "$275.50"),
                    (3, "ORD-003", "Robert Johnson", today, "Shipped", "$432.25"),
                    (4, "ORD-004", "Emily Williams", today, "Delivered", "$98.75"),
                    (5, "ORD-005", "Michael Brown", today, "Cancelled", "$0.00")
                ]

                # Add to treeview
                for order in sample_data:
                    self.tree.insert("", tk.END, values=order)

                return

            # Get order data
            cursor.execute("SELECT id, order_number, customer, date, status, total FROM 'order';")
            rows = cursor.fetchall()

            # Add to treeview
            for row in rows:
                self.tree.insert("", tk.END, values=row)

            self.set_status(f"Loaded {len(rows)} orders")
            logger.info(f"Loaded {len(rows)} orders")

        except Exception as e:
            logger.error(f"Error loading order data: {str(e)}", exc_info=True)
            self.show_error("Data Load Error", f"Failed to load order data: {str(e)}")
        finally:
            if 'conn' in locals():
                conn.close()

    def show_add_dialog(self):
        """Show dialog to add a new order."""
        # Implementation would go here
        logger.debug("Add dialog requested but not implemented")
        self.show_info("Not Implemented", "Add order functionality is not yet implemented.")

    def on_double_click(self, event):
        """Handle double-click on an order item."""
        # Implementation would go here
        logger.debug("Double-click event received but not implemented")
        self.show_info("Not Implemented", "Edit order functionality is not yet implemented.")

    def delete_selected(self, event):
        """Delete the selected order."""
        # Implementation would go here
        logger.debug("Delete requested but not implemented")
        self.show_info("Not Implemented", "Delete order functionality is not yet implemented.")

    def show_search_dialog(self):
        """Show search dialog."""
        # Implementation would go here
        logger.debug("Search requested but not implemented")
        self.show_info("Not Implemented", "Search functionality is not yet implemented.")
'''

    with open(order_view_path, 'w') as f:
        f.write(order_view_content.strip())
    logger.info(f"Created order view at {order_view_path}")
    return True


def create_shopping_list_view():
    """Create a basic shopping list view."""
    shopping_list_dir = os.path.join('gui', 'shopping_list')
    shopping_list_path = os.path.join(shopping_list_dir, 'shopping_list_view.py')

    # Create directory if it doesn't exist
    os.makedirs(shopping_list_dir, exist_ok=True)

    # Shopping list view content
    shopping_list_content = '''
# Path: gui/shopping_list/shopping_list_view.py
"""
Shopping list view implementation that displays shopping lists.
"""
import tkinter as tk
from tkinter import ttk
import logging
import sqlite3
import os
from datetime import datetime

from gui.base_view import BaseView
from services.interfaces.shopping_list_service import IShoppingListService

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ShoppingListView(BaseView):
    """
    View for displaying and managing shopping lists.
    """

    def __init__(self, parent, app):
        """
        Initialize the shopping list view.

        Args:
            parent: Parent widget
            app: Application instance
        """
        super().__init__(parent, app)
        self.db_path = self._find_database_file()
        logger.debug(f"ShoppingListView initialized with database: {self.db_path}")
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
        ttk.Button(toolbar, text="Add List", command=self.show_add_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Delete Selected", command=lambda e=None: self.delete_selected(e)).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Search", command=self.show_search_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Refresh", command=self.load_data).pack(side=tk.LEFT, padx=2)

        logger.debug("Toolbar created")

    def create_treeview(self):
        """Create the treeview for displaying shopping lists."""
        # Create a frame to hold the treeview and scrollbar
        frame = ttk.Frame(self)
        frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Define columns
        columns = ("id", "name", "date", "status", "priority", "items", "total")

        # Create the treeview
        self.tree = ttk.Treeview(frame, columns=columns, show="headings")

        # Define headings
        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="Name")
        self.tree.heading("date", text="Date")
        self.tree.heading("status", text="Status")
        self.tree.heading("priority", text="Priority")
        self.tree.heading("items", text="Items")
        self.tree.heading("total", text="Total")

        # Define column widths
        self.tree.column("id", width=50)
        self.tree.column("name", width=200)
        self.tree.column("date", width=100)
        self.tree.column("status", width=100)
        self.tree.column("priority", width=80)
        self.tree.column("items", width=80)
        self.tree.column("total", width=100)

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
        """Load shopping lists from the database and display them."""
        try:
            logger.info("Loading shopping list data")

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

            # Check if shopping_list table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='shopping_list';
            """)

            if not cursor.fetchone():
                logger.info("Shopping list table doesn't exist. Creating sample data.")
                self.set_status("Shopping list table doesn't exist - showing sample data")

                # Add sample data since table doesn't exist
                today = datetime.now().strftime("%Y-%m-%d")

                sample_data = [
                    (1, "Weekly Groceries", today, "Active", "High", 15, "$125.50"),
                    (2, "Office Supplies", today, "Pending", "Medium", 8, "$45.75"),
                    (3, "Party Supplies", today, "Complete", "Low", 12, "$78.25"),
                    (4, "Emergency Items", today, "Active", "Urgent", 5, "$32.99"),
                    (5, "Home Improvement", today, "Draft", "Low", 3, "$215.00")
                ]

                # Add to treeview
                for shopping_list in sample_data:
                    self.tree.insert("", tk.END, values=shopping_list)

                return

            # Get shopping list data
            cursor.execute("SELECT id, name, date, status, priority, items, total FROM shopping_list;")
            rows = cursor.fetchall()

            # Add to treeview
            for row in rows:
                self.tree.insert("", tk.END, values=row)

            self.set_status(f"Loaded {len(rows)} shopping lists")
            logger.info(f"Loaded {len(rows)} shopping lists")

        except Exception as e:
            logger.error(f"Error loading shopping list data: {str(e)}", exc_info=True)
            self.show_error("Data Load Error", f"Failed to load shopping list data: {str(e)}")
        finally:
            if 'conn' in locals():
                conn.close()

    def show_add_dialog(self):
        """Show dialog to add a new shopping list."""
        # Implementation would go here
        logger.debug("Add dialog requested but not implemented")
        self.show_info("Not Implemented", "Add shopping list functionality is not yet implemented.")

    def on_double_click(self, event):
        """Handle double-click on a shopping list item."""
        # Implementation would go here
        logger.debug("Double-click event received but not implemented")
        self.show_info("Not Implemented", "Edit shopping list functionality is not yet implemented.")

    def delete_selected(self, event):
        """Delete the selected shopping list."""
        # Implementation would go here
        logger.debug("Delete requested but not implemented")
        self.show_info("Not Implemented", "Delete shopping list functionality is not yet implemented.")

    def show_search_dialog(self):
        """Show search dialog."""
        # Implementation would go here
        logger.debug("Search requested but not implemented")
        self.show_info("Not Implemented", "Search functionality is not yet implemented.")
'''

    with open(shopping_list_path, 'w') as f:
        f.write(shopping_list_content.strip())
    logger.info(f"Created shopping list view at {shopping_list_path}")
    return True


def enable_tabs_in_main_window():
    """Enable all tabs in the main window."""
    main_window_path = os.path.join('gui', 'main_window.py')

    if not os.path.exists(main_window_path):
        logger.error(f"Main window file not found at {main_window_path}")
        return False

    # Read the main window content
    with open(main_window_path, 'r') as f:
        content = f.read()

    # Uncomment the import statements
    content = content.replace(
        "# from gui.recipe.recipe_view import RecipeView\n# from gui.order.order_view import OrderView\n# from gui.shopping_list.shopping_list_view import ShoppingListView",
        "from gui.recipe.recipe_view import RecipeView\nfrom gui.order.order_view import OrderView\nfrom gui.shopping_list.shopping_list_view import ShoppingListView"
    )

    # Uncomment the tab creation calls
    content = content.replace(
        "# self._add_recipes_tab()\n# self._add_orders_tab()\n# self._add_shopping_list_tab()",
        "self._add_recipes_tab()\nself._add_orders_tab()\nself._add_shopping_list_tab()"
    )

    # Write the updated content
    with open(main_window_path, 'w') as f:
        f.write(content)
    logger.info(f"Enabled all tabs in main window at {main_window_path}")
    return True


def main():
    """Main function."""
    logger.info("Starting tab enabler...")

    # First create the required views
    if create_recipe_view():
        logger.info("Project view created successfully")
    else:
        logger.error("Failed to create recipe view")

    if create_order_view():
        logger.info("Order view created successfully")
    else:
        logger.error("Failed to create order view")

    if create_shopping_list_view():
        logger.info("Shopping list view created successfully")
    else:
        logger.error("Failed to create shopping list view")

    # Then enable the tabs in the main window
    if enable_tabs_in_main_window():
        logger.info("All tabs enabled successfully")
    else:
        logger.error("Failed to enable tabs in main window")

    logger.info("Tab enabler completed. Run the application to see all tabs.")


if __name__ == "__main__":
    main()