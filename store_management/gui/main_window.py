# relative path: store_management/gui/main_window.py
"""
Main Window for the Leatherworking Store Management application.

Provides the primary application interface with tab-based navigation.
"""

import logging
import tkinter as tk
import tkinter.messagebox
import tkinter.ttk as ttk
from tkinter import messagebox
from typing import Any, Type, Optional

# Import views
from gui.inventory.hardware_inventory import HardwareInventoryView
from gui.inventory.product_inventory import ProductInventoryView
from gui.leatherworking.leather_inventory import LeatherInventoryView
from gui.leatherworking.pattern_library import PatternLibrary
from gui.order.order_view import OrderView
from gui.order.shopping_list_view import ShoppingListView
from gui.product.project_view import ProjectView
from gui.storage.storage_view import StorageView
from gui.leatherworking.project_dashboard import ProjectDashboard
from gui.leatherworking.timeline_viewer import TimelineViewer
from gui.order.supplier_view import SupplierView




# Import service interfaces
from services.interfaces.material_service import IMaterialService
from services.interfaces.order_service import IOrderService
from services.interfaces.project_service import IProjectService
from services.interfaces.shopping_list_service import IShoppingListService
from services.interfaces.storage_service import IStorageService
from services.interfaces.pattern_service import IPatternService
from services.interfaces.supplier_service import ISupplierService

logger = logging.getLogger(__name__)


class MainWindow:
    """
    Main application window managing multiple views and service retrieval.

    Provides a notebook-based interface with tabs for different
    functional areas of the leatherworking store management system.

    Attributes:
        root (tk.Tk): Root Tkinter window
        container (Any): Dependency injection container
        notebook (ttk.Notebook): Tabbed interface
    """

    def __init__(self, root: tk.Tk, container: Any):
        """
        Initialize the main window.

        Args:
            root (tk.Tk): The root Tkinter window
            container (Any): Dependency injection container
        """
        self.status_var = tk.StringVar(value="Ready")

        self.root = root
        self.container = container

        # Setup logging
        self.logger = logging.getLogger(self.__class__.__module__)

        # Configure window
        self._setup_window()

        # Create notebook for tabs
        self._create_notebook()

        # Create status bar
        self._create_status_bar()

        # Create menu
        self._create_menu()

    def _setup_window(self):
        """
        Configure basic window settings.
        """
        self.root.title("Leatherworking Store Management")
        self.root.geometry("1200x800")
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)


    def _create_notebook(self):
        """
        Create a notebook with tabs for different application modules.
        """
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill="both")

        # Define views with their configurations
        views = [
            {
                "name": "Leather Inventory",
                "view": LeatherInventoryView,
                "service": IMaterialService
            },
            {
                "name": "Hardware Inventory",
                "view": HardwareInventoryView,
                "service": IMaterialService
            },
            {
                "name": "Product Inventory",
                "view": ProductInventoryView,
                "service": IStorageService
            },
            {
                "name": "Pattern Library",
                "view": PatternLibrary,
                "service": IPatternService
            },
            {
                "name": "Projects",
                "view": ProjectView,
                "service": IProjectService
            },
            {
                "name": "Orders",
                "view": OrderView,
                "service": IOrderService
            },
            {
                "name": "Storage",
                "view": StorageView,
                "service": IStorageService
            },
            {
                "name": "Suppliers",
                "view": SupplierView,
                "service": ISupplierService
            },
            {
                "name": "Shopping List",
                "view": ShoppingListView,
                "service": IShoppingListService
            }
        ]

        # Create tabs with error handling
        for view_config in views:
            try:
                # Try to retrieve the service
                service = self.get_service(view_config['service'])

                # Create the view
                view = view_config['view'](self.notebook, self)
                self.notebook.add(view, text=view_config['name'])

                self.logger.info(f"{view_config['name']} view initialized")
            except Exception as e:
                self.logger.error(f"Failed to load {view_config['name']} view: {e}")
                # Optionally show a message to the user
                tkinter.messagebox.showwarning(
                    "View Initialization Error",
                    f"Could not load {view_config['name']} view: {e}"
                )

    def _create_status_bar(self):
        """
        Create a status bar at the bottom of the window.
        """
        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(
            self.root,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _create_menu(self):
        """Create the main application menu."""
        menu_bar = tk.Menu(self.root)
        self.root.config(menu=menu_bar)

        # File menu
        file_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New", command=self._on_new)
        file_menu.add_command(label="Open", command=self._on_open)
        file_menu.add_command(label="Save", command=self._on_save)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._on_closing)

        # Edit menu
        edit_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Undo", command=self._on_undo)
        edit_menu.add_command(label="Redo", command=self._on_redo)

        # Tools menu
        tools_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Tools", menu=tools_menu)

        # Leatherworking Tools (moved from submenu)
        tools_menu.add_command(label="Project Dashboard", command=self._open_project_dashboard)
        tools_menu.add_command(label="Timeline Viewer", command=self._open_timeline_viewer)
        tools_menu.add_command(label="Material Calculator", command=self._open_material_calculator)
        tools_menu.add_command(label="Cutting Layout", command=self._open_cutting_layout)
        tools_menu.add_command(label="Cost Analyzer", command=self._open_cost_analyzer)
        tools_menu.add_command(label="Material Usage Tracker", command=self._open_material_tracker)

        # Help menu
        help_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._show_about)



    def get_service(self, service_type: Type[Any]) -> Any:
        """
        Retrieve a service from the dependency injection container.

        Args:
            service_type (Type): The type/interface of the service to retrieve

        Returns:
            The requested service instance

        Raises:
            ValueError: If the service cannot be retrieved
        """
        try:
            # Attempt to get the service using container's get method
            return self.container.get(service_type)
        except Exception as e:
            self.logger.error(f"Error getting service {service_type}: {e}")
            raise ValueError(f"Service {service_type} not available") from e

    def _open_project_dashboard(self):
        """Open Project Dashboard in a separate window."""
        dashboard_window = tk.Toplevel(self.root)
        dashboard_window.title("Project Dashboard")

        from gui.leatherworking.project_dashboard import ProjectDashboard

        # Change self.app to self.container
        dashboard = ProjectDashboard(dashboard_window, self.container)
        dashboard.pack(fill=tk.BOTH, expand=True)

        dashboard_window.geometry("900x700")
        dashboard_window.minsize(600, 400)

    def _open_timeline_viewer(self):
        """Open Timeline Viewer in a separate window."""
        timeline_window = tk.Toplevel(self.root)
        timeline_window.title("Project Timeline Viewer")

        from gui.leatherworking.timeline_viewer import TimelineViewer

        # Change self.app to self.container
        viewer = TimelineViewer(timeline_window, self.container)
        viewer.pack(fill=tk.BOTH, expand=True)

        timeline_window.geometry("900x600")
        timeline_window.minsize(600, 400)

    def _open_material_tracker(self):
        """Open the Material Usage Tracker tool in a separate window."""
        # Use self.root instead of self for the Toplevel parent
        tracker_window = tk.Toplevel(self.root)
        tracker_window.title("Material Usage Tracker")

        # Import here to avoid circular imports
        from gui.leatherworking.material_tracker import MaterialUsageTracker

        tracker = MaterialUsageTracker(tracker_window, self.container)  # FIXED: self.container instead of self.app
        tracker.pack(fill=tk.BOTH, expand=True)

        # Set window size and make it resizable
        tracker_window.geometry("800x600")
        tracker_window.minsize(600, 400)

    def _open_material_calculator(self):
        """Open the material calculator tool in a new window."""
        calc_window = tk.Toplevel(self.root)
        calc_window.title("Material Calculator")

        from gui.leatherworking.material_calculator import MaterialCalculator

        # Change self.app to self.container
        calculator = MaterialCalculator(calc_window, self.container)
        calculator.pack(fill=tk.BOTH, expand=True)

        calc_window.geometry("800x600")
        calc_window.minsize(600, 400)

    def _open_cutting_layout(self):
        """Open the leather cutting layout tool in a new window."""
        layout_window = tk.Toplevel(self.root)
        layout_window.title("Leather Cutting Layout")

        from gui.leatherworking.cutting_layout import LeatherCuttingView

        # Change self.app to self.container
        layout_view = LeatherCuttingView(layout_window, self.container)
        layout_view.pack(fill=tk.BOTH, expand=True)

        layout_window.geometry("1000x700")
        layout_window.minsize(800, 600)



    def _create_tools_tab(self):
        """Create a notebook tab for project management tools."""
        tools_frame = ttk.Frame(self.notebook)
        self.notebook.add(tools_frame, text="Tools")

        # Create a grid layout for tool buttons
        tools_grid = ttk.Frame(tools_frame, padding=10)
        tools_grid.pack(fill=tk.BOTH, expand=True)

        # Create tool buttons
        btn_cost_analyzer = ttk.Button(
            tools_grid,
            text="Cost Analyzer",
            command=self._open_cost_analyzer,  # Make sure this is properly defined
            width=20
        )
        btn_cost_analyzer.grid(row=0, column=0, padx=10, pady=10)

        # Add other tool buttons as needed
        btn_material_calc = ttk.Button(
            tools_grid,
            text="Material Calculator",
            command=self._open_material_calculator,
            width=20
        )
        btn_material_calc.grid(row=0, column=1, padx=10, pady=10)

        # Configure grid weights
        for i in range(3):
            tools_grid.columnconfigure(i, weight=1)
        for i in range(3):
            tools_grid.rowconfigure(i, weight=1)

    def _open_cost_analyzer(self):
        """Open the project cost analyzer tool in a new window."""
        analyzer_window = tk.Toplevel(self.root)
        analyzer_window.title("Project Cost Analyzer")

        from gui.leatherworking.cost_analyzer import ProjectCostAnalyzer

        # Change self.app to self.container
        analyzer = ProjectCostAnalyzer(analyzer_window, self.container)
        analyzer.pack(fill=tk.BOTH, expand=True)

        analyzer_window.geometry("800x600")
        analyzer_window.minsize(600, 400)

    def _show_about(self):
        """Show about dialog."""
        messagebox.showinfo(
            "About Leatherworking Store Management",
            "Leatherworking Store Management\n"
            "Version 1.0\n\n"
            "A comprehensive tool for managing leatherworking "
            "materials, projects, inventory, and more."
        )

    def set_status(self, message):
        """Update the status bar with a message."""
        try:
            self.status_var.set(message)
            logger.info(message)
        except Exception as e:
            logger.error(f"Error updating status: {str(e)}")

    def _on_new(self):
        """Handle New action."""
        self.logger.info("New action triggered")
        self.set_status("Creating new item...")

    def _on_open(self):
        """Handle Open action."""
        self.logger.info("Open action triggered")
        self.set_status("Opening file...")

    def _on_save(self):
        """Handle Save action."""
        self.logger.info("Save action triggered")
        self.set_status("Saving...")

    def _on_undo(self):
        """Handle Undo action."""
        self.logger.info("Undo action triggered")
        self.set_status("Undoing last action...")

    def _on_redo(self):
        """Handle Redo action."""
        self.logger.info("Redo action triggered")
        self.set_status("Redoing last action...")

    def _on_closing(self):
        """
        Handle application closing.
        Provides confirmation dialog and cleanup.
        """
        if tkinter.messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.logger.info("Application closing")
            self.root.destroy()

    def mainloop(self):
        """
        Start the main event loop.
        """
        self.logger.info("Starting main event loop...")
        self.root.mainloop()