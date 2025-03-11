# Main Window Integration
from tkinter import ttk

from PIL._tkinter_finder import tk

from gui import theme
# Add these imports to the top of main_window.py
from gui.widgets.breadcrumb_navigation import BreadcrumbNavigation
from gui.utils.view_history_manager import ViewHistoryManager


# Add these methods and updates to the MainWindow class

def __init__(self, root):
    """
    Initialize the main window.

    Args:
        root: The root Tkinter window
    """
    self.root = root
    self.logger = logging.getLogger(__name__)
    self.current_view = None
    self.views = {}
    self.frame_content = None
    self.statusbar = None
    self.menubar = None
    self.toolbar = None

    # Initialize breadcrumbs container
    self.breadcrumb_container = None
    self.breadcrumb_nav = None

    # Initialize view history manager
    self.view_history = ViewHistoryManager()
    self.view_history.set_navigation_callback(self._navigate_to_view)


def create_toolbar(self):
    """Create the application toolbar."""
    self.toolbar = ttk.Frame(self.root, style="TFrame", padding=5)

    # Add back/forward navigation
    self.back_button = ttk.Button(
        self.toolbar,
        text="Back",
        command=self.navigate_back,
        state="disabled"
    )
    self.back_button.pack(side=tk.LEFT, padx=(0, 2))

    self.forward_button = ttk.Button(
        self.toolbar,
        text="Forward",
        command=self.navigate_forward,
        state="disabled"
    )
    self.forward_button.pack(side=tk.LEFT, padx=(0, 5))

    # Add separator
    ttk.Separator(self.toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)

    # Add toolbar buttons
    btn_dashboard = ttk.Button(
        self.toolbar,
        text="Dashboard",
        command=self.show_dashboard)
    btn_dashboard.pack(side=tk.LEFT, padx=5, pady=5)

    btn_inventory = ttk.Button(
        self.toolbar,
        text="Inventory",
        command=lambda: self.show_view("inventory"))
    btn_inventory.pack(side=tk.LEFT, padx=5, pady=5)

    btn_projects = ttk.Button(
        self.toolbar,
        text="Projects",
        command=lambda: self.show_view("projects"))
    btn_projects.pack(side=tk.LEFT, padx=5, pady=5)

    btn_sales = ttk.Button(
        self.toolbar,
        text="Sales",
        command=lambda: self.show_view("sales"))
    btn_sales.pack(side=tk.LEFT, padx=5, pady=5)

    btn_purchases = ttk.Button(
        self.toolbar,
        text="Purchases",
        command=lambda: self.show_view("purchases"))
    btn_purchases.pack(side=tk.LEFT, padx=5, pady=5)

    self.toolbar.grid(row=0, column=0, columnspan=2, sticky="ew")


def create_content_area(self):
    """Create the main content area."""
    # Create the content frame
    self.frame_content = ttk.Frame(self.root, style="TFrame")
    self.frame_content.grid(row=1, column=1, sticky="nsew")

    # Create breadcrumb container
    self.breadcrumb_container = ttk.Frame(self.frame_content, style="TFrame", padding=(5, 5, 5, 10))
    self.breadcrumb_container.pack(fill=tk.X, expand=False)

    # Create breadcrumb navigation
    self.breadcrumb_nav = BreadcrumbNavigation(self.breadcrumb_container)
    self.breadcrumb_nav.set_callback(self._on_breadcrumb_click)
    self.breadcrumb_nav.pack(fill=tk.X, expand=True)

    # Set initial breadcrumb
    self.breadcrumb_nav.set_home_breadcrumb("Dashboard", "dashboard")


def navigate_back(self):
    """Navigate back in view history."""
    self.view_history.go_back()
    self._update_navigation_buttons()


def navigate_forward(self):
    """Navigate forward in view history."""
    self.view_history.go_forward()
    self._update_navigation_buttons()


def _on_breadcrumb_click(self, view_name, view_data=None):
    """
    Handle breadcrumb click events.

    Args:
        view_name: Name of the view to navigate to
        view_data: Optional data for the view
    """
    # Use a special method to navigate without adding to history
    self._navigate_to_view(view_name, view_data)

    # Update navigation buttons
    self._update_navigation_buttons()


def _navigate_to_view(self, view_name, view_data=None):
    """
    Navigate to a view without adding to history.
    Used by the history manager for back/forward navigation.

    Args:
        view_name: The name of the view to navigate to
        view_data: Optional data to pass to the view
    """
    self.logger.info(f"Navigating to view: {view_name}")

    if view_name == "dashboard":
        self.show_dashboard(add_to_history=False)
    else:
        self.show_view(view_name, add_to_history=False, view_data=view_data)


def _update_navigation_buttons(self):
    """Update the state of navigation buttons based on history."""
    # Update back button
    if self.view_history.can_go_back():
        self.back_button.configure(state="normal")
    else:
        self.back_button.configure(state="disabled")

    # Update forward button
    if self.view_history.can_go_forward():
        self.forward_button.configure(state="normal")
    else:
        self.forward_button.configure(state="disabled")


def _update_breadcrumbs(self, view_name, view_data=None):
    """
    Update breadcrumb navigation for the current view.

    Args:
        view_name: The name of the current view
        view_data: Optional data associated with the view
    """
    # Determine breadcrumb title from view name
    title = view_name.replace("_", " ").title()

    # Handle main level views
    if view_name in ["dashboard"]:
        # Main level view - reset breadcrumbs to just this view
        self.breadcrumb_nav.set_home_breadcrumb("Dashboard", "dashboard")

    elif view_name in ["inventory", "materials", "patterns", "projects",
                       "sales", "purchases", "customers", "suppliers",
                       "inventory_reports", "sales_reports", "project_reports",
                       "products"]:
        # Top level navigation items
        self.breadcrumb_nav.update_breadcrumbs([
            {"title": "Dashboard", "view": "dashboard"},
            {"title": title, "view": view_name}
        ])

    # Handle detail views with proper hierarchies
    elif view_name == "storage":
        self.breadcrumb_nav.update_breadcrumbs([
            {"title": "Dashboard", "view": "dashboard"},
            {"title": "Inventory", "view": "inventory"},
            {"title": "Storage Locations", "view": "storage"}
        ])

    elif view_name in ["leather", "hardware", "supplies"]:
        self.breadcrumb_nav.update_breadcrumbs([
            {"title": "Dashboard", "view": "dashboard"},
            {"title": "Materials", "view": "materials"},
            {"title": title, "view": view_name}
        ])

    elif view_name == "components":
        self.breadcrumb_nav.update_breadcrumbs([
            {"title": "Dashboard", "view": "dashboard"},
            {"title": "Patterns", "view": "patterns"},
            {"title": "Components", "view": view_name}
        ])

    elif view_name in ["picking_lists", "tool_lists"]:
        self.breadcrumb_nav.update_breadcrumbs([
            {"title": "Dashboard", "view": "dashboard"},
            {"title": "Projects", "view": "projects"},
            {"title": title, "view": view_name}
        ])

    # Handle any other view
    else:
        # If we don't have a specific mapping, add to the current path
        self.breadcrumb_nav.add_breadcrumb(title, view_name, view_data)


# Update the show_view method to support breadcrumbs and history
def show_view(self, view_name, add_to_history=True, view_data=None):
    """
    Show a specific view in the content area.

    Args:
        view_name: The name of the view to show
        add_to_history: Whether to add this view to navigation history
        view_data: Optional data to pass to the view
    """
    self.logger.info(f"Showing view: {view_name}")

    # Add to view history if requested
    if add_to_history:
        self.view_history.add_view(view_name, view_data)
        self._update_navigation_buttons()

    # Clear the current view (keep breadcrumbs)
    if self.current_view:
        for widget in self.frame_content.winfo_children():
            if widget != self.breadcrumb_container:
                widget.destroy()

    # Show the requested view
    try:
        # Create a frame to contain the view
        content_container = ttk.Frame(self.frame_content)
        content_container.pack(fill=tk.BOTH, expand=True)

        # Load views on demand to prevent circular imports
        if view_name == "materials":
            from gui.views.materials.material_list_view import MaterialListView
            self.current_view = MaterialListView(content_container)
        elif view_name == "leather":
            from gui.views.materials.leather_view import LeatherView
            self.current_view = LeatherView(content_container)
        elif view_name == "hardware":
            from gui.views.materials.hardware_view import HardwareView
            self.current_view = HardwareView(content_container)
        elif view_name == "supplies":
            from gui.views.materials.supplies_view import SuppliesView
            self.current_view = SuppliesView(content_container)
        elif view_name == "inventory":
            from gui.views.inventory.inventory_view import InventoryView
            self.current_view = InventoryView(content_container)
        elif view_name == "storage":
            from gui.views.inventory.storage_location_view import StorageLocationView
            self.current_view = StorageLocationView(content_container)
        elif view_name == "projects":
            from gui.views.projects.project_list_view import ProjectListView
            self.current_view = ProjectListView(content_container)
        elif view_name == "picking_lists":
            from gui.views.projects.picking_list_view import PickingListView
            self.current_view = PickingListView(content_container)
        elif view_name == "tool_lists":
            from gui.views.projects.tool_list_view import ToolListView
            self.current_view = ToolListView(content_container)
        elif view_name == "sales":
            from gui.views.sales.sales_view import SalesView
            self.current_view = SalesView(content_container)
        elif view_name == "customers":
            from gui.views.sales.customer_view import CustomerView
            self.current_view = CustomerView(content_container)
        elif view_name == "purchases":
            from gui.views.purchases.purchase_view import PurchaseView
            self.current_view = PurchaseView(content_container)
        elif view_name == "suppliers":
            from gui.views.purchases.supplier_view import SupplierView
            self.current_view = SupplierView(content_container)
        elif view_name == "patterns":
            from gui.views.patterns.pattern_list_view import PatternListView
            self.current_view = PatternListView(content_container)
        elif view_name == "components":
            from gui.views.patterns.component_view import ComponentView
            self.current_view = ComponentView(content_container)
        elif view_name == "products":
            from gui.views.products.product_list_view import ProductListView
            self.current_view = ProductListView(content_container)
        elif view_name == "inventory_reports":
            from gui.views.reports.inventory_reports import InventoryReportsView
            self.current_view = InventoryReportsView(content_container)
        elif view_name == "sales_reports":
            from gui.views.reports.sales_reports import SalesReportsView
            self.current_view = SalesReportsView(content_container)
        elif view_name == "project_reports":
            from gui.views.reports.project_reports import ProjectReportsView
            self.current_view = ProjectReportsView(content_container)
        else:
            self.logger.warning(f"Unknown view requested: {view_name}")
            self.show_dashboard()
            return

        # Update the breadcrumbs
        self._update_breadcrumbs(view_name, view_data)

        # Build and pack the view
        self.current_view.build()

        # Update status bar
        self.update_status(f"Viewing: {view_name}")

    except Exception as e:
        self.logger.error(f"Error loading view {view_name}: {str(e)}")
        messagebox.showerror("View Error", f"Failed to load {view_name} view: {str(e)}")
        # Show a placeholder frame as fallback
        placeholder = ttk.Frame(self.frame_content)
        ttk.Label(placeholder, text=f"Error loading {view_name} view").pack(pady=20)
        placeholder.pack(fill=tk.BOTH, expand=True)


# Update the show_dashboard method to support breadcrumbs and history
def show_dashboard(self, add_to_history=True):
    """
    Show the dashboard view.

    Args:
        add_to_history: Whether to add this view to navigation history
    """
    self.logger.info("Showing dashboard")

    # Add to view history if requested
    if add_to_history:
        self.view_history.add_view("dashboard")
        self._update_navigation_buttons()

    # Clear the current view (keep breadcrumbs)
    if self.current_view:
        for widget in self.frame_content.winfo_children():
            if widget != self.breadcrumb_container:
                widget.destroy()

    try:
        # Create a container for the dashboard
        dashboard_container = ttk.Frame(self.frame_content)
        dashboard_container.pack(fill=tk.BOTH, expand=True)

        # Create the dashboard view
        from gui.views.dashboard.main_dashboard import DashboardView
        self.current_view = DashboardView(dashboard_container)
        self.current_view.build()

        # Update breadcrumbs
        self.breadcrumb_nav.set_home_breadcrumb("Dashboard", "dashboard")

        # Update status bar
        self.update_status("Dashboard")

    except Exception as e:
        self.logger.error(f"Error loading dashboard: {str(e)}")
        # Create a simple placeholder dashboard
        placeholder = ttk.Frame(self.frame_content)
        ttk.Label(placeholder, text="Leatherworking Management System",
                  font=theme.create_custom_font(theme.FONTS["header"])).pack(pady=20)
        ttk.Label(placeholder, text="Welcome to the dashboard").pack(pady=10)
        placeholder.pack(fill=tk.BOTH, expand=True)