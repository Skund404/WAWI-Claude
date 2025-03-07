"""
Main application window for the Leatherworking Application.
Provides navigation and hosts all view components.
"""
import logging
import threading
import tkinter as tk
from tkinter import ttk, messagebox

# Import services
from services.interfaces.material_service import IMaterialService
from services.interfaces.project_service import IProjectService
from services.interfaces.pattern_service import IPatternService
from services.interfaces.sale_service import ISaleService
from services.interfaces.picking_list_service import IPickingListService
from services.interfaces.supplier_service import ISupplierService
from services.interfaces.storage_service import IStorageService
from services.interfaces.inventory_service import IInventoryService

logger = logging.getLogger(__name__)


class MainWindow:
    """
    Main application window for the Leatherworking Workshop Manager.
    Hosts all views and provides navigation between them.
    """
    
    def __init__(self, root, app):
        """
        Initialize the main window.
        
        Args:
            root (tk.Tk): The root Tkinter window
            app: Application controller with dependency container
        """
        self.root = root
        self.app = app
        self._active_views = {}
        self._current_view = None
        
        logger.info("Setting up main window")
        
        # Setup basic window layout
        self._setup_window()
        self._create_menu()
        self._create_toolbar()
        self._create_sidebar()
        self._create_main_frame()
        self._create_status_bar()
        
        # Show the default view (dashboard)
        self.show_view("dashboard")
        
        logger.info("Main window setup complete")
    
    def _setup_window(self):
        """Configure basic window settings."""
        # Set window icon
        # self.root.iconbitmap("assets/icon.ico")  # Uncomment if you have an icon
        
        # Configure the grid layout for the main sections
        self.root.columnconfigure(0, weight=0)  # Sidebar
        self.root.columnconfigure(1, weight=1)  # Main content
        self.root.rowconfigure(0, weight=0)  # Toolbar
        self.root.rowconfigure(1, weight=1)  # Content area
        self.root.rowconfigure(2, weight=0)  # Status bar
    
    def _create_menu(self):
        """Create the main application menu."""
        logger.debug("Creating main menu")
        
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)
        
        # File menu
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        file_menu.add_command(label="New Project", command=self._on_new_project)
        file_menu.add_command(label="Open Project", command=self._on_open_project)
        file_menu.add_separator()
        file_menu.add_command(label="Import", command=self._on_import)
        file_menu.add_command(label="Export", command=self._on_export)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        self.menu_bar.add_cascade(label="File", menu=file_menu)
        
        # Edit menu
        edit_menu = tk.Menu(self.menu_bar, tearoff=0)
        edit_menu.add_command(label="Undo", command=self._on_undo)
        edit_menu.add_command(label="Redo", command=self._on_redo)
        edit_menu.add_separator()
        edit_menu.add_command(label="Cut", command=self._on_cut)
        edit_menu.add_command(label="Copy", command=self._on_copy)
        edit_menu.add_command(label="Paste", command=self._on_paste)
        self.menu_bar.add_cascade(label="Edit", menu=edit_menu)
        
        # View menu
        view_menu = tk.Menu(self.menu_bar, tearoff=0)
        view_menu.add_command(label="Dashboard", command=lambda: self.show_view("dashboard"))
        view_menu.add_command(label="Projects", command=lambda: self.show_view("projects"))
        view_menu.add_command(label="Inventory", command=lambda: self.show_view("inventory"))
        view_menu.add_command(label="Sales", command=lambda: self.show_view("sales"))
        view_menu.add_command(label="Purchases", command=lambda: self.show_view("purchases"))
        view_menu.add_command(label="Patterns", command=lambda: self.show_view("patterns"))
        view_menu.add_separator()
        view_menu.add_command(label="Refresh", command=self._on_refresh)
        self.menu_bar.add_cascade(label="View", menu=view_menu)
        
        # Tools menu
        tools_menu = tk.Menu(self.menu_bar, tearoff=0)
        tools_menu.add_command(label="Material Calculator", command=self._open_material_calculator)
        tools_menu.add_command(label="Cutting Layout", command=self._open_cutting_layout)
        tools_menu.add_command(label="Cost Analyzer", command=self._open_cost_analyzer)
        tools_menu.add_separator()
        tools_menu.add_command(label="Settings", command=self._open_settings)
        self.menu_bar.add_cascade(label="Tools", menu=tools_menu)
        
        # Help menu
        help_menu = tk.Menu(self.menu_bar, tearoff=0)
        help_menu.add_command(label="Documentation", command=self._show_documentation)
        help_menu.add_command(label="About", command=self._show_about)
        self.menu_bar.add_cascade(label="Help", menu=help_menu)
    
    def _create_toolbar(self):
        """Create a toolbar with frequently used actions."""
        logger.debug("Creating toolbar")
        
        self.toolbar_frame = ttk.Frame(self.root, style='Toolbar.TFrame')
        self.toolbar_frame.grid(row=0, column=0, columnspan=2, sticky="ew")
        
        # Add toolbar buttons
        btn_new = ttk.Button(self.toolbar_frame, text="New", 
                             style="Primary.TButton", command=self._on_new_project)
        btn_new.pack(side=tk.LEFT, padx=5, pady=5)
        
        btn_open = ttk.Button(self.toolbar_frame, text="Open", 
                              command=self._on_open_project)
        btn_open.pack(side=tk.LEFT, padx=5, pady=5)
        
        btn_save = ttk.Button(self.toolbar_frame, text="Save", 
                              command=self._on_save)
        btn_save.pack(side=tk.LEFT, padx=5, pady=5)
        
        ttk.Separator(self.toolbar_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, 
                                                                   padx=5, 
                                                                   pady=5, 
                                                                   fill=tk.Y)
        
        btn_refresh = ttk.Button(self.toolbar_frame, text="Refresh", 
                                 command=self._on_refresh)
        btn_refresh.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Add a search field on the right
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(self.toolbar_frame, textvariable=self.search_var,
                                     style='Search.TEntry', width=20)
        self.search_entry.pack(side=tk.RIGHT, padx=5, pady=5)
        
        btn_search = ttk.Button(self.toolbar_frame, text="Search", 
                                command=self._on_search)
        btn_search.pack(side=tk.RIGHT, padx=5, pady=5)
        
        # Bind Enter key to search
        self.search_entry.bind("<Return>", lambda event: self._on_search())
    
    def _create_sidebar(self):
        """Create a sidebar with navigation links."""
        logger.debug("Creating sidebar")
        
        self.sidebar_frame = ttk.Frame(self.root, style='Card.TFrame', width=200)
        self.sidebar_frame.grid(row=1, column=0, sticky="ns")
        self.sidebar_frame.pack_propagate(False)  # Don't shrink
        
        # Add sidebar title
        ttk.Label(self.sidebar_frame, text="Navigation", 
                 style='Heading.TLabel').pack(fill=tk.X, padx=10, pady=10)
        
        # Create navigation buttons
        nav_buttons = [
            ("Dashboard", "dashboard"),
            ("Projects", "projects"),
            ("Inventory", "inventory"),
            ("Materials", "materials"),
            ("Leather", "leather"),
            ("Hardware", "hardware"),
            ("Tools", "tools"),
            ("Patterns", "patterns"),
            ("Sales", "sales"),
            ("Customers", "customers"),
            ("Purchases", "purchases"),
            ("Suppliers", "suppliers"),
            ("Storage", "storage"),
        ]
        
        # Create a frame for the buttons
        buttons_frame = ttk.Frame(self.sidebar_frame)
        buttons_frame.pack(fill=tk.BOTH, expand=True)
        
        # Add the navigation buttons
        for text, view_name in nav_buttons:
            btn = ttk.Button(buttons_frame, text=text, 
                             command=lambda vn=view_name: self.show_view(vn))
            btn.pack(fill=tk.X, padx=10, pady=2)
        
        # Add some information at the bottom of the sidebar
        info_frame = ttk.Frame(self.sidebar_frame)
        info_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=10)
        
        ttk.Label(info_frame, text="Workshop Manager", 
                 style='Subheading.TLabel').pack(fill=tk.X)
        ttk.Label(info_frame, text="Version 1.0", 
                 style='TLabel').pack(fill=tk.X)
    
    def _create_main_frame(self):
        """Create the main content frame where views will be displayed."""
        logger.debug("Creating main content frame")
        
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
        
        # Configure the main frame to expand and fill the space
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure(0, weight=1)
        
        # Create a placeholder for the view container
        self.view_container = ttk.Frame(self.main_frame)
        self.view_container.grid(row=0, column=0, sticky="nsew")
        
        # This is where the active view will be displayed
        self.active_view_frame = ttk.Frame(self.view_container)
        self.active_view_frame.pack(fill=tk.BOTH, expand=True)
    
    def _create_status_bar(self):
        """Create a status bar at the bottom of the window."""
        logger.debug("Creating status bar")
        
        self.status_bar = ttk.Frame(self.root, style='Statusbar.TFrame', height=25)
        self.status_bar.grid(row=2, column=0, columnspan=2, sticky="ew")
        
        # Status message label
        self.status_message = ttk.Label(self.status_bar, text="Ready", padding=(10, 2))
        self.status_message.pack(side=tk.LEFT)
        
        # Add the current user on the right (placeholder for now)
        self.user_label = ttk.Label(self.status_bar, text="User: Admin", padding=(10, 2))
        self.user_label.pack(side=tk.RIGHT)
    
    def show_view(self, view_name):
        """
        Show the specified view in the main content area.
        
        Args:
            view_name: The name of the view to show
        """
        logger.info(f"Showing view: {view_name}")
        
        # Save previous view if needed
        if self._current_view and hasattr(self._current_view, 'on_save'):
            try:
                self._current_view.on_save()
            except Exception as e:
                logger.error(f"Error saving previous view: {e}")
        
        # Clear existing view
        for widget in self.active_view_frame.winfo_children():
            widget.destroy()
        
        try:
            # Check if we've already created this view
            if view_name in self._active_views:
                view = self._active_views[view_name]
                view.pack(in_=self.active_view_frame, fill=tk.BOTH, expand=True)
                self._current_view = view
                
                # Refresh the view
                if hasattr(view, 'on_refresh'):
                    view.on_refresh()
            else:
                # Create a new view instance based on the name
                view = self._create_view(view_name)
                if view:
                    self._active_views[view_name] = view
                    view.pack(in_=self.active_view_frame, fill=tk.BOTH, expand=True)
                    self._current_view = view
                else:
                    self.set_status(f"View '{view_name}' is not implemented yet")
            
            # Update the status bar
            self.set_status(f"Viewing: {view_name.capitalize()}")
            
        except Exception as e:
            logger.error(f"Error showing view {view_name}: {e}")
            messagebox.showerror("View Error", 
                                f"An error occurred while loading the {view_name} view.\n{str(e)}")
    
    def _create_view(self, view_name):
        """
        Create a view instance based on the view name.
        
        Args:
            view_name: The name of the view to create
            
        Returns:
            The created view instance or None if not found
        """
        try:
            # Import the appropriate view class - we'll use lazy importing
            # to avoid circular imports
            if view_name == "dashboard":
                from gui.analytics.dashboard import AnalyticsDashboard
                return AnalyticsDashboard(self.active_view_frame, self.app)
            
            elif view_name == "projects":
                from gui.projects.project_view import ProjectView
                return ProjectView(self.active_view_frame, self.app)
            
            elif view_name == "inventory":
                from gui.inventory.base_inventory_view import BaseInventoryView
                return BaseInventoryView(self.active_view_frame, self.app)
            
            elif view_name == "materials":
                from gui.inventory.material_inventory import MaterialInventoryView
                return MaterialInventoryView(self.active_view_frame, self.app)
            
            elif view_name == "leather":
                from gui.inventory.leather_inventory import LeatherInventoryView
                return LeatherInventoryView(self.active_view_frame, self.app)
            
            elif view_name == "hardware":
                from gui.inventory.hardware_inventory import HardwareInventoryView
                return HardwareInventoryView(self.active_view_frame, self.app)
            
            elif view_name == "tools":
                from gui.inventory.tool_inventory import ToolInventoryView
                return ToolInventoryView(self.active_view_frame, self.app)
            
            elif view_name == "patterns":
                from gui.patterns.pattern_library import PatternLibrary
                return PatternLibrary(self.active_view_frame, self.app)
            
            elif view_name == "sales":
                from gui.sales.sale_view import SaleView
                return SaleView(self.active_view_frame, self.app)
            
            elif view_name == "customers":
                from gui.sales.customer_view import CustomerView
                return CustomerView(self.active_view_frame, self.app)
            
            elif view_name == "purchases":
                from gui.purchases.purchase_view import PurchaseView
                return PurchaseView(self.active_view_frame, self.app)
            
            elif view_name == "suppliers":
                from gui.purchases.supplier_view import SupplierView
                return SupplierView(self.active_view_frame, self.app)
            
            elif view_name == "storage":
                from gui.storage.storage_view import StorageView
                return StorageView(self.active_view_frame, self.app)
            
            else:
                logger.warning(f"Unknown view name: {view_name}")
                return None
                
        except ImportError as e:
            logger.error(f"Failed to import view {view_name}: {e}")
            self.set_status(f"View '{view_name}' is not implemented yet")
            return None
        except Exception as e:
            logger.error(f"Error creating view {view_name}: {e}")
            return None
    
    def _open_material_calculator(self):
        """Open the material calculator tool in a new window."""
        try:
            from gui.tools.material_calculator import MaterialCalculator
            
            # Create new toplevel window
            calculator_window = tk.Toplevel(self.root)
            calculator_window.title("Material Calculator")
            calculator_window.geometry("800x600")
            
            # Create the calculator view
            calculator = MaterialCalculator(calculator_window, self.app)
            calculator.pack(fill=tk.BOTH, expand=True)
            
            # Make the window modal
            calculator_window.transient(self.root)
            calculator_window.grab_set()
            
            # Center the window
            self._center_window(calculator_window)
            
            self.set_status("Material Calculator opened")
            
        except ImportError:
            logger.error("Material Calculator not implemented yet")
            self.set_status("Material Calculator not implemented yet")
    
    def _open_cutting_layout(self):
        """Open the cutting layout tool in a new window."""
        try:
            from gui.patterns.cutting_layout import CuttingLayout
            
            # Create new toplevel window
            cutting_window = tk.Toplevel(self.root)
            cutting_window.title("Cutting Layout Tool")
            cutting_window.geometry("1000x700")
            
            # Create the cutting layout view
            cutting = CuttingLayout(cutting_window, self.app)
            cutting.pack(fill=tk.BOTH, expand=True)
            
            # Make the window modal
            cutting_window.transient(self.root)
            cutting_window.grab_set()
            
            # Center the window
            self._center_window(cutting_window)
            
            self.set_status("Cutting Layout Tool opened")
            
        except ImportError:
            logger.error("Cutting Layout not implemented yet")
            self.set_status("Cutting Layout not implemented yet")
    
    def _open_cost_analyzer(self):
        """Open the project cost analyzer tool in a new window."""
        try:
            from gui.projects.cost_analyzer import CostAnalyzer
            
            # Create new toplevel window
            analyzer_window = tk.Toplevel(self.root)
            analyzer_window.title("Project Cost Analyzer")
            analyzer_window.geometry("900x700")
            
            # Create the cost analyzer view
            analyzer = CostAnalyzer(analyzer_window, self.app)
            analyzer.pack(fill=tk.BOTH, expand=True)
            
            # Make the window modal
            analyzer_window.transient(self.root)
            analyzer_window.grab_set()
            
            # Center the window
            self._center_window(analyzer_window)
            
            self.set_status("Project Cost Analyzer opened")
            
        except ImportError:
            logger.error("Cost Analyzer not implemented yet")
            self.set_status("Cost Analyzer not implemented yet")
    
    def _open_settings(self):
        """Open the application settings dialog."""
        messagebox.showinfo("Settings", "Settings dialog not implemented yet.")
    
    def _show_documentation(self):
        """Show the application documentation."""
        messagebox.showinfo("Documentation", 
                          "Documentation not available. Please refer to the user manual.")
    
    def _show_about(self):
        """Show the About dialog."""
        about_text = """
        Leatherworking Workshop Manager
        Version 1.0
        
        A comprehensive tool for managing your leatherworking business.
        
        Features:
        - Inventory management
        - Project tracking
        - Pattern library
        - Sales and purchases
        - Cost analysis
        
        © 2025 Leatherworkers Guild
        """
        messagebox.showinfo("About", about_text)
    
    def _on_new_project(self):
        """Handle New Project action."""
        self.set_status("Creating new project...")
        
        # Switch to the projects view
        self.show_view("projects")
        
        # Trigger the new project action in the projects view
        if hasattr(self._current_view, 'on_new'):
            self._current_view.on_new()
    
    def _on_open_project(self):
        """Handle Open Project action."""
        self.set_status("Opening project...")
        
        # Switch to the projects view
        self.show_view("projects")
        
        # Let the projects view handle opening
    
    def _on_save(self):
        """Handle Save action."""
        self.set_status("Saving changes...")
        
        # Delegate to the current view
        if self._current_view and hasattr(self._current_view, 'on_save'):
            try:
                self._current_view.on_save()
                self.set_status("Changes saved")
            except Exception as e:
                logger.error(f"Error saving: {e}")
                messagebox.showerror("Save Error", f"An error occurred while saving: {str(e)}")
                self.set_status("Save failed")
        else:
            self.set_status("Nothing to save")
    
    def _on_import(self):
        """Handle Import action."""
        messagebox.showinfo("Import", "Import functionality not implemented yet.")
    
    def _on_export(self):
        """Handle Export action."""
        messagebox.showinfo("Export", "Export functionality not implemented yet.")
    
    def _on_undo(self):
        """Handle Undo action."""
        # Delegate to the current view
        if self._current_view and hasattr(self._current_view, 'undo'):
            try:
                self._current_view.undo()
                self.set_status("Undo completed")
            except Exception as e:
                logger.error(f"Error undoing: {e}")
                self.set_status("Undo failed")
        else:
            self.set_status("Nothing to undo")
    
    def _on_redo(self):
        """Handle Redo action."""
        # Delegate to the current view
        if self._current_view and hasattr(self._current_view, 'redo'):
            try:
                self._current_view.redo()
                self.set_status("Redo completed")
            except Exception as e:
                logger.error(f"Error redoing: {e}")
                self.set_status("Redo failed")
        else:
            self.set_status("Nothing to redo")
    
    def _on_cut(self):
        """Handle Cut action."""
        # Get the currently focused widget
        focused = self.root.focus_get()
        if hasattr(focused, 'cut'):
            focused.event_generate("<<Cut>>")
    
    def _on_copy(self):
        """Handle Copy action."""
        # Get the currently focused widget
        focused = self.root.focus_get()
        if hasattr(focused, 'copy'):
            focused.event_generate("<<Copy>>")
    
    def _on_paste(self):
        """Handle Paste action."""
        # Get the currently focused widget
        focused = self.root.focus_get()
        if hasattr(focused, 'paste'):
            focused.event_generate("<<Paste>>")
    
    def _on_refresh(self):
        """Handle Refresh action."""
        self.set_status("Refreshing view...")
        
        # Delegate to the current view
        if self._current_view and hasattr(self._current_view, 'on_refresh'):
            try:
                self._current_view.on_refresh()
                self.set_status("View refreshed")
            except Exception as e:
                logger.error(f"Error refreshing: {e}")
                self.set_status("Refresh failed")
        else:
            self.set_status("Nothing to refresh")
    
    def _on_search(self):
        """Handle Search action."""
        search_text = self.search_var.get().strip()
        if not search_text:
            return
        
        self.set_status(f"Searching for '{search_text}'...")
        
        # Delegate to the current view
        if self._current_view and hasattr(self._current_view, 'search'):
            try:
                results = self._current_view.search(search_text)
                if results:
                    self.set_status(f"Found {len(results)} results")
                else:
                    self.set_status("No results found")
            except Exception as e:
                logger.error(f"Error searching: {e}")
                self.set_status("Search failed")
        else:
            self.set_status("Search not supported in current view")
    
    def set_status(self, message):
        """
        Set the status bar message.
        
        Args:
            message: The message to display
        """
        self.status_message.config(text=message)
        logger.debug(f"Status: {message}")
    
    def get_service(self, service_type):
        """
        Get a service from the application container.
        
        Args:
            service_type: The type of service to get
            
        Returns:
            The service instance or None if not found
        """
        return self.app.get(service_type)
    
    def _center_window(self, window):
        """
        Center a window on the screen.
        
        Args:
            window: The window to center
        """
        window.update_idletasks()
        width = window.winfo_width()
        height = window.winfo_height()
        x = (window.winfo_screenwidth() // 2) - (width // 2)
        y = (window.winfo_screenheight() // 2) - (height // 2)
        window.geometry('{}x{}+{}+{}'.format(width, height, x, y))
    
    def cleanup(self):
        """Perform cleanup operations before closing."""
        logger.info("Cleaning up main window resources")
        
        # Save all views
        for view_name, view in self._active_views.items():
            if hasattr(view, 'on_save'):
                try:
                    logger.debug(f"Saving view: {view_name}")
                    view.on_save()
                except Exception as e:
                    logger.error(f"Error saving view {view_name}: {e}")
            
            # Clean up view resources
            if hasattr(view, 'cleanup'):
                try:
                    logger.debug(f"Cleaning up view: {view_name}")
                    view.cleanup()
                except Exception as e:
                    logger.error(f"Error cleaning up view {view_name}: {e}")
        
        logger.info("Main window cleanup complete")