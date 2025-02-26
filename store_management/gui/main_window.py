# gui/main_window.py
"""
Main window module for the leatherworking store management application.
Coordinates all views and provides the main application interface.
"""

import logging
import tkinter as tk
from tkinter import messagebox, ttk

from di.container import DependencyContainer
from gui.inventory.hardware_inventory import HardwareInventoryView
from gui.inventory.product_inventory import ProductInventoryView
from gui.leatherworking.leather_inventory import LeatherInventoryView
from gui.leatherworking.pattern_library import PatternLibrary
from gui.leatherworking.project_dashboard import ProjectDashboard
from gui.leatherworking.cost_estimator import CostEstimator
from gui.leatherworking.material_calculator import MaterialCalculator
from gui.leatherworking.cutting_layout import LeatherCuttingView
from gui.leatherworking.timeline_viewer import TimelineViewer
from gui.leatherworking.advanced_pattern_library import AdvancedPatternLibrary
from gui.leatherworking.material_tracker import MaterialUsageTracker
from gui.order.order_view import OrderView
from gui.shopping_list.shopping_list_view import ShoppingListView
from services.interfaces.inventory_service import IInventoryService
from services.interfaces.material_service import IMaterialService
from services.interfaces.order_service import IOrderService
from services.interfaces.project_service import IProjectService

# Configure logger
logger = logging.getLogger(__name__)


class MainWindow:
    """Main application window handling the UI layout and navigation."""

    def __init__(self, root: tk.Tk, container: DependencyContainer):
        """Initialize the main application window.

        Args:
            root (tk.Tk): The root Tkinter window
            container (DependencyContainer): Dependency injection container
        """
        self.root = root
        self.container = container

        # Set up window properties
        self._setup_window()

        # Create the UI elements
        self._create_menu()
        self._create_notebook()
        self._create_status_bar()

        logger.info("Main window initialized successfully")

    def _setup_window(self):
        """Configure basic window settings."""
        self.root.title("Leatherworking Store Management")
        self.root.geometry("1024x768")
        self.root.minsize(800, 600)

        # Configure styles
        style = ttk.Style()
        style.configure("TNotebook", tabposition='n')
        style.configure("TNotebook.Tab", padding=[10, 2])

        # Configure grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=0)

    def _create_menu(self):
        """Create the main application menu."""
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)

        # File menu
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        file_menu.add_command(label="New", command=self._on_new)
        file_menu.add_command(label="Open", command=self._on_open)
        file_menu.add_command(label="Save", command=self._on_save)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        self.menu_bar.add_cascade(label="File", menu=file_menu)

        # Edit menu
        edit_menu = tk.Menu(self.menu_bar, tearoff=0)
        edit_menu.add_command(label="Undo", command=self._on_undo)
        edit_menu.add_command(label="Redo", command=self._on_redo)
        self.menu_bar.add_cascade(label="Edit", menu=edit_menu)

        # Leatherworking Tools menu
        tools_menu = tk.Menu(self.menu_bar, tearoff=0)
        tools_menu.add_command(label="Cost Estimator", command=self._open_cost_estimator)
        tools_menu.add_command(label="Material Calculator", command=self._open_material_calculator)
        tools_menu.add_command(label="Cutting Layout", command=self._open_cutting_layout)
        tools_menu.add_command(label="Timeline Viewer", command=self._open_timeline_viewer)
        tools_menu.add_command(label="Material Usage Tracker", command=self._open_material_tracker)
        tools_menu.add_command(label="Advanced Pattern Library", command=self._open_advanced_pattern_library)
        self.menu_bar.add_cascade(label="Leatherworking Tools", menu=tools_menu)

        # Help menu
        help_menu = tk.Menu(self.menu_bar, tearoff=0)
        help_menu.add_command(label="About", command=self._show_about)
        self.menu_bar.add_cascade(label="Help", menu=help_menu)

    def _create_notebook(self):
        """Create a notebook with different application views."""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # Create tabs for main functionality areas
        self._add_leather_inventory_tab()
        self._add_hardware_inventory_tab()
        self._add_product_inventory_tab()
        self._add_pattern_library_tab()
        self._add_project_dashboard_tab()
        self._add_order_tab()
        self._add_shopping_list_tab()

        # Additional leatherworking tools tabs
        self._add_cost_estimator_tab()
        self._add_material_calculator_tab()
        self._add_cutting_layout_tab()

    def _create_status_bar(self):
        """Create a status bar at the bottom of the window."""
        self.status_bar = ttk.Frame(self.root, relief=tk.SUNKEN, padding=(2, 2))
        self.status_bar.grid(row=1, column=0, sticky="ew")

        self.status_text = tk.StringVar(value="Ready")
        status_label = ttk.Label(self.status_bar, textvariable=self.status_text, anchor=tk.W)
        status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

    def _add_leather_inventory_tab(self):
        """Add the leather inventory tab to the notebook."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Leather Inventory")

        leather_view = LeatherInventoryView(tab, self)
        leather_view.pack(fill=tk.BOTH, expand=True)

        logger.debug("Added leather inventory tab")

    def _add_hardware_inventory_tab(self):
        """Add the hardware inventory tab to the notebook."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Hardware Inventory")

        hardware_view = HardwareInventoryView(tab, self)
        hardware_view.pack(fill=tk.BOTH, expand=True)

        logger.debug("Added hardware inventory tab")

    def _add_product_inventory_tab(self):
        """Add the product inventory tab to the notebook."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Products")

        product_view = ProductInventoryView(tab, self)
        product_view.pack(fill=tk.BOTH, expand=True)

        logger.debug("Added product inventory tab")

    def _add_pattern_library_tab(self):
        """Add the pattern library tab to the notebook."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Patterns")

        pattern_view = PatternLibrary(tab, self)
        pattern_view.pack(fill=tk.BOTH, expand=True)

        logger.debug("Added pattern library tab")

    def _add_project_dashboard_tab(self):
        """Add the project dashboard tab to the notebook."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Projects")

        project_view = ProjectDashboard(tab, self)
        project_view.pack(fill=tk.BOTH, expand=True)

        logger.debug("Added project dashboard tab")

    def _add_order_tab(self):
        """Add the orders tab to the notebook."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Orders")

        order_view = OrderView(tab, self)
        order_view.pack(fill=tk.BOTH, expand=True)

        logger.debug("Added orders tab")

    def _add_shopping_list_tab(self):
        """Add the shopping list tab to the notebook."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Shopping Lists")

        shopping_list_view = ShoppingListView(tab, self)
        shopping_list_view.pack(fill=tk.BOTH, expand=True)

        logger.debug("Added shopping list tab")

    def _add_cost_estimator_tab(self):
        """Add the cost estimator tab to the notebook."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Cost Estimator")

        cost_estimator = CostEstimator(tab, self)
        cost_estimator.pack(fill=tk.BOTH, expand=True)

        logger.debug("Added cost estimator tab")

    def _add_material_calculator_tab(self):
        """Add the material calculator tab to the notebook."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Material Calculator")

        material_calculator = MaterialCalculator(tab, self)
        material_calculator.pack(fill=tk.BOTH, expand=True)

        logger.debug("Added material calculator tab")

    def _add_cutting_layout_tab(self):
        """Add the cutting layout tab to the notebook."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Cutting Layout")

        cutting_layout = LeatherCuttingView(tab, self)
        cutting_layout.pack(fill=tk.BOTH, expand=True)

        logger.debug("Added cutting layout tab")

    def _open_cost_estimator(self):
        """Open the cost estimator in a separate window."""
        window = tk.Toplevel(self.root)
        window.title("Cost Estimator")
        window.geometry("800x600")
        window.minsize(600, 400)

        cost_estimator = CostEstimator(window, self)
        cost_estimator.pack(fill=tk.BOTH, expand=True)

        logger.info("Opened cost estimator in separate window")

    def _open_material_calculator(self):
        """Open the material calculator in a separate window."""
        window = tk.Toplevel(self.root)
        window.title("Material Calculator")
        window.geometry("800x600")
        window.minsize(600, 400)

        material_calculator = MaterialCalculator(window, self)
        material_calculator.pack(fill=tk.BOTH, expand=True)

        logger.info("Opened material calculator in separate window")

    def _open_cutting_layout(self):
        """Open the cutting layout tool in a separate window."""
        window = tk.Toplevel(self.root)
        window.title("Cutting Layout")
        window.geometry("900x700")
        window.minsize(700, 500)

        cutting_layout = LeatherCuttingView(window, self)
        cutting_layout.pack(fill=tk.BOTH, expand=True)

        logger.info("Opened cutting layout in separate window")

    def _open_timeline_viewer(self):
        """Open the timeline viewer in a separate window."""
        window = tk.Toplevel(self.root)
        window.title("Project Timeline Viewer")
        window.geometry("900x700")
        window.minsize(700, 500)

        timeline_viewer = TimelineViewer(window, self)
        timeline_viewer.pack(fill=tk.BOTH, expand=True)

        logger.info("Opened timeline viewer in separate window")

    def _open_material_tracker(self):
        """Open the material usage tracker in a separate window."""
        window = tk.Toplevel(self.root)
        window.title("Material Usage Tracker")
        window.geometry("800x600")
        window.minsize(600, 400)

        material_tracker = MaterialUsageTracker(window, self)
        material_tracker.pack(fill=tk.BOTH, expand=True)

        logger.info("Opened material usage tracker in separate window")

    def _open_advanced_pattern_library(self):
        """Open the advanced pattern library in a separate window."""
        window = tk.Toplevel(self.root)
        window.title("Advanced Pattern Library")
        window.geometry("1000x800")
        window.minsize(800, 600)

        pattern_library = AdvancedPatternLibrary(window, self)
        pattern_library.pack(fill=tk.BOTH, expand=True)

        logger.info("Opened advanced pattern library in separate window")

    def _show_about(self):
        """Show the about dialog."""
        messagebox.showinfo(
            "About Leatherworking Store Management",
            "Leatherworking Store Management\n"
            "Version 0.1.0\n\n"
            "A comprehensive tool for managing a leatherworking business."
        )

    def set_status(self, message: str):
        """Update the status bar message.

        Args:
            message (str): Status message to display
        """
        self.status_text.set(message)

    def get_service(self, service_type):
        """Retrieve a service from the dependency injection container.

        Args:
            service_type (type): Service interface to retrieve

        Returns:
            Service implementation
        """
        return self.container.get_service(service_type)

    def _on_new(self):
        """Handle New action in the menu."""
        current_tab = self.notebook.select()
        if current_tab:
            tab_id = self.notebook.index(current_tab)
            tab_text = self.notebook.tab(tab_id, "text")
            self.set_status(f"New {tab_text} item")

    def _on_open(self):
        """Handle Open action in the menu."""
        self.set_status("Open file")

    def _on_save(self):
        """Handle Save action in the menu."""
        self.set_status("Save file")

    def _on_undo(self):
        """Handle Undo action in the menu."""
        self.set_status("Undo action")

    def _on_redo(self):
        """Handle Redo action in the menu."""
        self.set_status("Redo action")

    def quit(self):
        """Close the application."""
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.root.destroy()