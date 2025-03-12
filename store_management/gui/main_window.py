# gui/main_window.py
"""
Main window for the leatherworking application.

Contains the main window implementation with navigation, view management,
and integration with the navigation service.
"""

import logging
import tkinter as tk
from tkinter import ttk, messagebox

logger = logging.getLogger(__name__)

from gui import theme
from gui.widgets.breadcrumb_navigation import BreadcrumbNavigation
from gui.utils.view_history_manager import ViewHistoryManager
from gui.utils.navigation_service import NavigationService

# Try to import the utils service provider bridge, with better error handling
try:
    from gui.utils import utils_service_provider_bridge

    logger.info("Loaded utils service provider bridge")
except ImportError as e:
    logger.error(f"Failed to load utils service provider bridge: {str(e)}")
    # Try to initialize the bridge explicitly if the import fails
    try:
        from gui.utils.utils_service_provider_bridge import install_import_hook

        install_import_hook()
        logger.info("Manually installed utils service provider bridge hook")
    except Exception as bridge_error:
        logger.error(f"Could not initialize utils service provider bridge: {str(bridge_error)}")


class MainWindow:
    """
    Main window for the leatherworking application.

    Manages the application's main interface, view switching,
    navigation history, and integrates with navigation services.
    """

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

        # Initialize and set up navigation service
        nav_service = NavigationService.get_instance()
        nav_service.initialize(self, self.view_history)

        # Keep track of modal dialogs
        self.active_dialogs = []

    def build(self):
        """Build and initialize the main window components."""
        # Configure grid
        self.root.columnconfigure(0, weight=0)  # Sidebar column
        self.root.columnconfigure(1, weight=1)  # Content column
        self.root.rowconfigure(0, weight=0)  # Toolbar row
        self.root.rowconfigure(1, weight=1)  # Content row
        self.root.rowconfigure(2, weight=0)  # Status bar row

        # Create components
        self.create_toolbar()
        self.create_content_area()

        # Set up status bar
        self.statusbar = ttk.Label(self.root, text="Ready", relief=tk.SUNKEN, anchor=tk.W, padding=(5, 2))
        self.statusbar.grid(row=2, column=0, columnspan=2, sticky="ew")

        # Set up keyboard shortcuts
        self._setup_keyboard_shortcuts()

        # Show the dashboard initially
        self.show_dashboard()

        self.logger.info("Main window built successfully")

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

        # Add reports button
        btn_reports = ttk.Button(
            self.toolbar,
            text="Reports",
            command=self.show_reports_menu)
        btn_reports.pack(side=tk.LEFT, padx=5, pady=5)

        # Add help button to the right side
        btn_help = ttk.Button(
            self.toolbar,
            text="Help",
            command=self.show_help)
        btn_help.pack(side=tk.RIGHT, padx=5, pady=5)

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
        """
        Navigate back in view history.

        Returns:
            True if navigation was successful, False otherwise
        """
        if not self.view_history.can_go_back():
            return False

        self.view_history.go_back()
        self._update_navigation_buttons()
        return True

    def navigate_forward(self):
        """
        Navigate forward in view history.

        Returns:
            True if navigation was successful, False otherwise
        """
        if not self.view_history.can_go_forward():
            return False

        self.view_history.go_forward()
        self._update_navigation_buttons()
        return True

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

        elif view_name.endswith("_reports"):
            report_type = view_name.replace("_reports", "").title()
            self.breadcrumb_nav.update_breadcrumbs([
                {"title": "Dashboard", "view": "dashboard"},
                {"title": "Reports", "view": "reports"},
                {"title": f"{report_type} Reports", "view": view_name}
            ])

        # Handle entity details with ID
        elif view_data and "entity_id" in view_data and "details_mode" in view_data and view_data["details_mode"]:
            # Get the base view name without any suffixes
            base_view = view_name.split("_details")[0] if "_details" in view_name else view_name

            # Format entity ID for display
            entity_id = view_data["entity_id"]
            entity_display = f"#{entity_id}" if isinstance(entity_id, int) else str(entity_id)

            # Get previous breadcrumbs and add the detail view
            current_breadcrumbs = self.breadcrumb_nav.breadcrumbs.copy()

            # If we have proper breadcrumbs already
            if current_breadcrumbs and len(current_breadcrumbs) > 1:
                self.breadcrumb_nav.add_breadcrumb(f"{title} {entity_display}", view_name, view_data)
            else:
                # Default hierarchy for detail views
                self.breadcrumb_nav.update_breadcrumbs([
                    {"title": "Dashboard", "view": "dashboard"},
                    {"title": title, "view": base_view},
                    {"title": f"{title} {entity_display}", "view": view_name, "data": view_data}
                ])

        # Handle any other view
        else:
            # If we don't have a specific mapping, add to the current path
            self.breadcrumb_nav.add_breadcrumb(title, view_name, view_data)

    def _setup_keyboard_shortcuts(self):
        """Set up keyboard shortcuts for the application."""
        # Navigation shortcuts
        self.root.bind("<Alt-Left>", lambda e: self.navigate_back())
        self.root.bind("<Alt-Right>", lambda e: self.navigate_forward())
        self.root.bind("<F5>", lambda e: self.refresh_current_view())

        # View shortcuts
        self.root.bind("<Alt-d>", lambda e: self.show_dashboard())
        self.root.bind("<Alt-i>", lambda e: self.show_view("inventory"))
        self.root.bind("<Alt-p>", lambda e: self.show_view("projects"))
        self.root.bind("<Alt-s>", lambda e: self.show_view("sales"))
        self.root.bind("<Alt-u>", lambda e: self.show_view("purchases"))

        # Help shortcut
        self.root.bind("<F1>", lambda e: self.show_help())

        # Standard shortcuts
        self.root.bind("<Control-n>", lambda e: self.create_new_item())
        self.root.bind("<Control-f>", lambda e: self.show_search())
        self.root.bind("<Control-r>", lambda e: self.show_reports_menu())

    # Update the show_view method to support breadcrumbs and history
    def show_view(self, view_name, add_to_history=True, view_data=None):
        """
        Show a specific view in the content area.

        Args:
            view_name: The name of the view to show
            add_to_history: Whether to add this view to navigation history
            view_data: Optional data to pass to the view

        Returns:
            The view instance that was created
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
            elif view_name == "reports":
                # Check if the reports dashboard view exists
                try:
                    from gui.views.reports.reports_dashboard import ReportsDashboardView
                    self.current_view = ReportsDashboardView(content_container)
                except ImportError:
                    # If not available, redirect to inventory reports as fallback
                    self.logger.warning("Reports dashboard not found, showing inventory reports instead")
                    from gui.views.reports.inventory_reports import InventoryReportsView
                    self.current_view = InventoryReportsView(content_container)
            elif view_name == "tools":
                from gui.views.tools.tool_list_view import ToolListView
                self.current_view = ToolListView(content_container)
            else:
                self.logger.warning(f"Unknown view requested: {view_name}")
                self.show_dashboard()
                return None

            # Pass view data to the view if it has a set_view_data method
            if view_data and hasattr(self.current_view, 'set_view_data'):
                self.current_view.set_view_data(view_data)

            # Update the breadcrumbs
            self._update_breadcrumbs(view_name, view_data)

            # Build and pack the view
            self.current_view.build()

            # Update status bar
            self.update_status(f"Viewing: {view_name}")

            return self.current_view

        except Exception as e:
            self.logger.error(f"Error loading view {view_name}: {str(e)}", exc_info=True)
            messagebox.showerror("View Error", f"Failed to load {view_name} view: {str(e)}")
            # Show a placeholder frame as fallback
            placeholder = ttk.Frame(self.frame_content)
            ttk.Label(placeholder, text=f"Error loading {view_name} view").pack(pady=20)
            placeholder.pack(fill=tk.BOTH, expand=True)
            return None

    # Update the show_dashboard method to support breadcrumbs and history
    def show_dashboard(self, add_to_history=True):
        """
        Show the dashboard view.

        Args:
            add_to_history: Whether to add this view to navigation history

        Returns:
            The dashboard view instance
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

            return self.current_view

        except Exception as e:
            self.logger.error(f"Error loading dashboard: {str(e)}", exc_info=True)
            # Create a simple placeholder dashboard
            placeholder = ttk.Frame(self.frame_content)
            ttk.Label(placeholder, text="Leatherworking Management System",
                      font=theme.create_custom_font(theme.FONTS["header"])).pack(pady=20)
            ttk.Label(placeholder, text="Welcome to the dashboard").pack(pady=10)
            placeholder.pack(fill=tk.BOTH, expand=True)
            return None

    def show_reports_menu(self, event=None):
        """Show the reports menu or navigate to reports dashboard."""
        self.show_view("reports")

    def show_help(self, event=None):
        """Show the help dialog or documentation."""
        # Create help window or dialog
        help_dialog = tk.Toplevel(self.root)
        help_dialog.title("Leatherworking ERP Help")
        help_dialog.transient(self.root)
        help_dialog.grab_set()

        # Track this dialog
        self.active_dialogs.append(help_dialog)

        # Position the dialog
        help_dialog.geometry("600x500")
        help_dialog.resizable(True, True)

        # Add help content
        content_frame = ttk.Frame(help_dialog, padding=10)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        ttk.Label(content_frame, text="Leatherworking ERP Help",
                  font=theme.create_custom_font(theme.FONTS["header"])).pack(pady=(0, 10))

        # Create notebook for help sections
        notebook = ttk.Notebook(content_frame)
        notebook.pack(fill=tk.BOTH, expand=True, pady=10)

        # Overview tab
        overview_frame = ttk.Frame(notebook, padding=10)
        ttk.Label(overview_frame, text="System Overview",
                  font=theme.create_custom_font(theme.FONTS["subheader"])).pack(anchor=tk.W)
        ttk.Label(overview_frame, text="This ERP system helps manage your leatherworking business "
                                       "including inventory, projects, sales, and purchases.", wraplength=550).pack(
            fill=tk.X, pady=5)
        notebook.add(overview_frame, text="Overview")

        # Navigation tab
        nav_frame = ttk.Frame(notebook, padding=10)
        ttk.Label(nav_frame, text="Navigation", font=theme.create_custom_font(theme.FONTS["subheader"])).pack(
            anchor=tk.W)
        ttk.Label(nav_frame, text="- Use the toolbar buttons to switch between major sections\n"
                                  "- Use Back and Forward buttons to navigate your history\n"
                                  "- Use breadcrumbs to see your location and navigate up\n"
                                  "- Alt+Left: Go back\n"
                                  "- Alt+Right: Go forward\n"
                                  "- F5: Refresh current view",
                  justify=tk.LEFT).pack(fill=tk.X, pady=5)
        notebook.add(nav_frame, text="Navigation")

        # Shortcuts tab
        shortcuts_frame = ttk.Frame(notebook, padding=10)
        ttk.Label(shortcuts_frame, text="Keyboard Shortcuts",
                  font=theme.create_custom_font(theme.FONTS["subheader"])).pack(anchor=tk.W)

        shortcuts_text = ttk.Treeview(shortcuts_frame, columns=("key", "description"), show="headings")
        shortcuts_text.heading("key", text="Shortcut")
        shortcuts_text.heading("description", text="Description")
        shortcuts_text.column("key", width=150, anchor=tk.W)
        shortcuts_text.column("description", width=350, anchor=tk.W)

        # Add shortcut data
        shortcuts = [
            ("Alt+D", "Go to Dashboard"),
            ("Alt+I", "Go to Inventory"),
            ("Alt+P", "Go to Projects"),
            ("Alt+S", "Go to Sales"),
            ("Alt+U", "Go to Purchases"),
            ("F5", "Refresh current view"),
            ("Alt+Left", "Navigate back"),
            ("Alt+Right", "Navigate forward"),
            ("Ctrl+N", "Create new item"),
            ("Ctrl+F", "Search"),
            ("Ctrl+R", "Reports"),
            ("F1", "Show this help")
        ]

        for key, desc in shortcuts:
            shortcuts_text.insert("", "end", values=(key, desc))

        shortcuts_text.pack(fill=tk.BOTH, expand=True, pady=5)
        notebook.add(shortcuts_frame, text="Shortcuts")

        # Close button
        def on_close():
            if help_dialog in self.active_dialogs:
                self.active_dialogs.remove(help_dialog)
            help_dialog.destroy()

        ttk.Button(content_frame, text="Close", command=on_close).pack(pady=10)

        # Handle dialog close
        help_dialog.protocol("WM_DELETE_WINDOW", on_close)

    def create_new_item(self, event=None):
        """
        Create a new item based on the current view context.
        This is a convenience method for keyboard shortcuts.
        """
        if not self.current_view:
            return

        # Try to call the on_add method if it exists
        if hasattr(self.current_view, 'on_add'):
            self.current_view.on_add()

    def show_search(self, event=None):
        """
        Show the search interface for the current view.
        """
        if not self.current_view:
            return

        # If the view has a search field, try to focus it
        if hasattr(self.current_view, 'search_frame'):
            search_frame = getattr(self.current_view, 'search_frame')
            if hasattr(search_frame, 'search_entry'):
                search_frame.search_entry.focus_set()

    def refresh_current_view(self, event=None):
        """
        Refresh the current view if it has a refresh method.
        """
        if self.current_view and hasattr(self.current_view, 'refresh'):
            self.current_view.refresh()
            self.update_status("View refreshed")

    def update_status(self, message):
        """
        Update the status bar message.

        Args:
            message: The message to display
        """
        if hasattr(self, 'statusbar') and self.statusbar:
            self.statusbar.config(text=message)

    def register_dialog(self, dialog):
        """
        Register a modal dialog with the main window.
        This allows tracking active dialogs.

        Args:
            dialog: The dialog to register
        """
        if dialog not in self.active_dialogs:
            self.active_dialogs.append(dialog)

    def unregister_dialog(self, dialog):
        """
        Unregister a modal dialog from the main window.

        Args:
            dialog: The dialog to unregister
        """
        if dialog in self.active_dialogs:
            self.active_dialogs.remove(dialog)

    def close_all_dialogs(self):
        """
        Close all active dialogs.
        This is useful when the application is closing.
        """
        for dialog in self.active_dialogs[:]:  # Create a copy to avoid modification during iteration
            try:
                dialog.destroy()
            except:
                pass
        self.active_dialogs.clear()