"""
Main application entry point for the Leatherworking Application.
This file initializes the application, sets up dependency injection,
and launches the main window.
"""
import logging
import sys
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

# Import dependency injection components
from di.container import DependencyContainer
from di.setup import setup_dependency_injection

# Import services
from services.interfaces.material_service import IMaterialService
from services.interfaces.project_service import IProjectService
from services.interfaces.pattern_service import IPatternService
from services.interfaces.sale_service import ISaleService
from services.interfaces.picking_list_service import IPickingListService
from services.interfaces.supplier_service import ISupplierService
from services.interfaces.storage_service import IStorageService
from services.interfaces.shopping_list_service import IShoppingListService
from services.interfaces.hardware_service import IHardwareService
from services.interfaces.inventory_service import IInventoryService

# Import the main window
from gui.main_window import MainWindow

# Import theme
from gui.theme import AppTheme

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("leatherwork.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class LeatherworkApp:
    """Main application class for the Leatherworking Application."""
    
    def __init__(self):
        """Initialize the application, setup DI and create the main window."""
        logger.info("Starting Leatherworking Application")
        
        # Create the root Tkinter window
        self.root = tk.Tk()
        self.root.title("Leatherworking Workshop Manager")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)
        
        # Set up dependency injection
        try:
            logger.info("Setting up dependency injection")
            self.container = setup_dependency_injection()
            logger.info("Dependency injection setup complete")
        except Exception as e:
            logger.critical(f"Failed to set up dependency injection: {e}")
            messagebox.showerror("Startup Error", 
                                "Failed to initialize application services.\n"
                                "Please check the logs for more information.")
            sys.exit(1)
        
        # Apply the application theme
        self.theme = AppTheme()
        self.theme.apply(self.root)
        
        # Create the main window
        try:
            logger.info("Creating main application window")
            self.main_window = MainWindow(self.root, self)
            logger.info("Main window created successfully")
        except Exception as e:
            logger.critical(f"Failed to create main window: {e}")
            messagebox.showerror("Startup Error", 
                                "Failed to create application window.\n"
                                "Please check the logs for more information.")
            sys.exit(1)
        
        # Set up window close handler
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # Report successful startup
        logger.info("Application initialized successfully")
    
    def get(self, service_type):
        """
        Get a service instance from the DI container.
        
        Args:
            service_type: The interface type of the service to retrieve
            
        Returns:
            The service instance or None if not found
        """
        try:
            return self.container.resolve(service_type)
        except Exception as e:
            logger.error(f"Failed to resolve service {service_type.__name__}: {e}")
            return None
    
    def run(self):
        """Run the application main loop."""
        logger.info("Starting application main loop")
        try:
            self.root.mainloop()
        except Exception as e:
            logger.critical(f"Unhandled exception in main loop: {e}")
            messagebox.showerror("Application Error", 
                                "An unhandled error occurred.\n"
                                "The application will now close.")
            sys.exit(1)
    
    def _on_close(self):
        """Handle application close event."""
        logger.info("Application close requested")
        try:
            # Ask for confirmation
            if messagebox.askokcancel("Quit", "Do you want to quit the application?"):
                logger.info("Shutting down application")
                # Perform cleanup
                self._cleanup()
                # Destroy the root window
                self.root.destroy()
        except Exception as e:
            logger.error(f"Error during application shutdown: {e}")
            self.root.destroy()
    
    def _cleanup(self):
        """Perform cleanup operations before closing."""
        logger.info("Performing application cleanup")
        try:
            # Clean up any resources
            if hasattr(self.main_window, 'cleanup'):
                self.main_window.cleanup()
            
            # Close any open database connections
            # This would typically be handled by the DI container
            pass
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


if __name__ == "__main__":
    app = LeatherworkApp()
    app.run()
