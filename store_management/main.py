import tkinter as tk
from tkinter import ttk, messagebox
import sys
from pathlib import Path

from config import APP_NAME, WINDOW_SIZE, DATABASE_PATH
from database.db_manager import DatabaseManager
from gui.order.order_management import OrderManagementSystem, OrderManagementToolbar, OrderManagementStatusBar
from gui.product.product_management import ProductManagementSystem
from gui.storage.storage_management import StorageManagementSystem


class StoreManagementApplication:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(APP_NAME)
        self.root.geometry(WINDOW_SIZE)

        # Initialize database
        self.check_database()

        # Create main menu
        self.create_menu()

        # Create main toolbar
        self.create_toolbar()

        # Create main notebook for sections
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill='both')

        # Initialize management systems
        self.setup_management_systems()

        # Create status bar
        self.status_bar = self.create_status_bar()

        # Bind global shortcuts
        self.bind_global_shortcuts()

        # Initialize state
        self.undo_stack = []
        self.redo_stack = []

    def check_database(self):
        """Check if database exists and is accessible"""
        if not Path(DATABASE_PATH).exists():
            if messagebox.askyesno(
                    "Database Not Found",
                    "Database not found. Would you like to create it now?"
            ):
                try:
                    from database.database_setup import setup_database
                    setup_database()
                    messagebox.showinfo(
                        "Success",
                        "Database created successfully!"
                    )
                except Exception as e:
                    messagebox.showerror(
                        "Error",
                        f"Failed to create database: {str(e)}"
                    )
                    sys.exit(1)
            else:
                sys.exit(1)

    def create_menu(self):
        """Create application menu"""
        self.menubar = tk.Menu(self.root)
        self.root.config(menu=self.menubar)

        # File menu
        file_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Save All", command=self.save_all)
        file_menu.add_command(label="Export Database", command=self.export_database)
        file_menu.add_command(label="Import Database", command=self.import_database)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit_application)

        # Edit menu
        edit_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Undo", command=self.global_undo)
        edit_menu.add_command(label="Redo", command=self.global_redo)
        edit_menu.add_separator()
        edit_menu.add_command(label="Preferences", command=self.show_preferences)

        # View menu
        view_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Refresh All", command=self.refresh_all)
        view_menu.add_command(label="Reset Layout", command=self.reset_layout)

        # Tools menu
        tools_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Database Maintenance", command=self.database_maintenance)
        tools_menu.add_command(label="Generate Reports", command=self.generate_reports)

        # Help menu
        help_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="User Guide", command=self.show_user_guide)
        help_menu.add_command(label="About", command=self.show_about)

    def create_toolbar(self):
        """Create main application toolbar"""
        toolbar_frame = ttk.Frame(self.root)
        toolbar_frame.pack(fill=tk.X, padx=5, pady=2)

        # Quick access buttons
        ttk.Button(toolbar_frame, text="Save All",
                   command=self.save_all).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar_frame, text="Refresh",
                   command=self.refresh_all).pack(side=tk.LEFT, padx=2)

        # Separator
        ttk.Separator(toolbar_frame, orient=tk.VERTICAL).pack(
            side=tk.LEFT, padx=5, fill=tk.Y
        )

        # Section-specific toolbars will be added by their respective management systems

    def setup_management_systems(self):
        """Initialize and setup all management systems"""
        # Product Management
        product_frame = ttk.Frame(self.notebook)
        self.notebook.add(product_frame, text='Product')
        self.product_system = ProductManagementSystem(product_frame)

        # Storage Management
        storage_frame = ttk.Frame(self.notebook)
        self.notebook.add(storage_frame, text='Storage')
        self.storage_system = StorageManagementSystem(storage_frame)

        # Order Management
        order_frame = ttk.Frame(self.notebook)
        self.notebook.add(order_frame, text='Order')
        self.order_system = OrderManagementSystem(order_frame)

        # Add specific toolbars
        self.order_toolbar = OrderManagementToolbar(
            self.root, self.order_system
        )
        self.order_toolbar.pack(fill=tk.X, padx=5, pady=2)

        # Initially hide section-specific toolbars
        self.order_toolbar.pack_forget()

        # Bind notebook tab change
        self.notebook.bind('<<NotebookTabChanged>>', self.on_tab_change)

    def create_status_bar(self):
        """Create application status bar"""
        status_bar = ttk.Frame(self.root)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)

        # Add common status information
        ttk.Label(status_bar, text="Ready").pack(side=tk.LEFT, padx=5)

        # Add section-specific status bars
        self.order_status = OrderManagementStatusBar(status_bar)
        self.order_status.pack(fill=tk.X, expand=True)

        # Initially hide section-specific status bars
        self.order_status.pack_forget()

        return status_bar

    def bind_global_shortcuts(self):
        """Bind global keyboard shortcuts"""
        self.root.bind('<Control-s>', lambda e: self.save_all())
        self.root.bind('<Control-z>', lambda e: self.global_undo())
        self.root.bind('<Control-y>', lambda e: self.global_redo())
        self.root.bind('<F5>', lambda e: self.refresh_all())
        self.root.bind('<Control-q>', lambda e: self.quit_application())

    def on_tab_change(self, event):
        """Handle notebook tab changes"""
        current_tab = self.notebook.select()
        tab_id = self.notebook.index(current_tab)

        # Hide all section-specific toolbars and status bars
        self.order_toolbar.pack_forget()
        self.order_status.pack_forget()

        # Show relevant toolbar and status bar
        if tab_id == 2:  # Order tab
            self.order_toolbar.pack(fill=tk.X, padx=5, pady=2)
            self.order_status.pack(fill=tk.X, expand=True)
            self.order_status.update_counts()

    def save_all(self):
        """Save all changes in all systems"""
        try:
            self.product_system.save_all()
            self.storage_system.save_all()
            self.order_system.save_current_view()
            messagebox.showinfo("Success", "All changes saved successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save changes: {str(e)}")

    def refresh_all(self):
        """Refresh all views"""
        self.product_system.refresh_all_views()
        self.storage_system.refresh_all_views()
        self.order_system.refresh_all_views()
        self.order_status.update_counts()

    def global_undo(self):
        """Handle global undo"""
        current_tab = self.notebook.select()
        tab_id = self.notebook.index(current_tab)

        if tab_id == 0:  # Product
            self.product_system.undo_current_view()
        elif tab_id == 1:  # Storage
            self.storage_system.undo_current_view()
        elif tab_id == 2:  # Order
            self.order_system.undo_current_view()

    def global_redo(self):
        """Handle global redo"""
        current_tab = self.notebook.select()
        tab_id = self.notebook.index(current_tab)

        if tab_id == 0:  # Product
            self.product_system.redo_current_view()
        elif tab_id == 1:  # Storage
            self.storage_system.redo_current_view()
        elif tab_id == 2:  # Order
            self.order_system.redo_current_view()

    def export_database(self):
        """Export entire database"""
        # To be implemented
        pass

    def import_database(self):
        """Import database"""
        # To be implemented
        pass

    def show_preferences(self):
        """Show preferences dialog"""
        # To be implemented
        pass

    def reset_layout(self):
        """Reset application layout"""
        # To be implemented
        pass

    def database_maintenance(self):
        """Show database maintenance dialog"""
        # To be implemented
        pass

    def generate_reports(self):
        """Show report generation dialog"""
        # To be implemented
        pass

    def show_user_guide(self):
        """Show user guide"""
        # To be implemented
        pass

    def show_about(self):
        """Show about dialog"""
        about_text = f"""
        {APP_NAME}
        Version: 1.0.0

        A comprehensive store management system for
        tracking inventory, recipes, and orders.

        © 2024 Your Company
        """
        messagebox.showinfo("About", about_text)

    def quit_application(self):
        """Quit application with confirmation"""
        if messagebox.askyesno("Quit", "Are you sure you want to quit?"):
            self.root.quit()

    def run(self):
        """Start the application"""
        self.root.mainloop()


if __name__ == "__main__":
    try:
        app = StoreManagementApplication()
        app.run()
    except Exception as e:
        print(f"Error initializing application: {e}")
        import traceback
        traceback.print_exc()