from di.core import inject
from services.interfaces import (
    MaterialService,
    ProjectService,
    InventoryService,
    OrderService,
)

"""
Fix for the base_view.py file to correct the syntax error.
"""
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("base_view_fix")


def fix_base_view():
    """Fix the base_view.py file."""
    base_view_path = os.path.join("gui", "base_view.py")
    if not os.path.exists(base_view_path):
        logger.error(f"Base view file not found at {base_view_path}")
        return False
    backup_path = base_view_path + ".bak"
    try:
        with open(base_view_path, "r") as src:
            with open(backup_path, "w") as dst:
                dst.write(src.read())
        logger.info(f"Created backup of base view at {backup_path}")
    except Exception as e:
        logger.error(f"Failed to create backup: {str(e)}")
        return False
    new_content = """
# Path: gui/base_view.py
""\"
Base view that all other views will inherit from.
This provides common functionality for all views.
""\"
import tkinter as tk
from tkinter import ttk, messagebox
import logging

logger = logging.getLogger(__name__)

class BaseView(ttk.Frame):
    ""\"
    Base view class that provides common functionality for all views.
    ""\"

    @inject(MaterialService)
        def __init__(self, parent, app):
        ""\"
        Initialize the base view.

        Args:
            parent: Parent widget
            app: Application instance
        ""\"
        super().__init__(parent)
        self.parent = parent
        self.app = app
        self.pack(fill=tk.BOTH, expand=True)

        logger.debug(f"BaseView initialized with app: {app}")

    @inject(MaterialService)
        def get_service(self, service_type):
        ""\"
        Get a service from the application.

        Args:
            service_type: Type of service to retrieve

        Returns:
            Service instance
        ""\"
        try:
            if self.app is not None and hasattr(self.app, 'get_service'):
                service = self.app.get_service(service_type)
                logger.debug(f"Service retrieved: {service_type}")
                return service
            else:
                logger.warning("App not available or doesn't have get_service method")
                return None
        except Exception as e:
            logger.error(f"Error getting service {service_type}: {str(e)}")
            return None

    @inject(MaterialService)
        def load_data(self):
        ""\"Load data for the view. To be implemented by subclasses.""\"
        pass

    @inject(MaterialService)
        def save(self):
        ""\"Save data from the view. To be implemented by subclasses.""\"
        pass

    @inject(MaterialService)
        def undo(self):
        ""\"Undo the last action. To be implemented by subclasses.""\"
        pass

    @inject(MaterialService)
        def redo(self):
        ""\"Redo the last undone action. To be implemented by subclasses.""\"
        pass

    @inject(MaterialService)
        def show_error(self, title, message):
        ""\"
        Show an error message.

        Args:
            title: Title of the message
            message: Error message
        ""\"
        messagebox.showerror(title, message)
        logger.error(f"Error: {title} - {message}")

    @inject(MaterialService)
        def show_info(self, title, message):
        ""\"
        Show an information message.

        Args:
            title: Title of the message
            message: Information message
        ""\"
        messagebox.showinfo(title, message)
        logger.info(f"Info: {title} - {message}")

    @inject(MaterialService)
        def show_warning(self, title, message):
        ""\"
        Show a warning message.

        Args:
            title: Title of the message
            message: Warning message
        ""\"
        messagebox.showwarning(title, message)
        logger.warning(f"Warning: {title} - {message}")

    @inject(MaterialService)
        def confirm(self, title, message):
        ""\"
        Show a confirmation dialog.

        Args:
            title: Title of the message
            message: Confirmation message

        Returns:
            bool: True if the user confirmed, False otherwise
        ""\"
        return messagebox.askyesno(title, message)

    @inject(MaterialService)
        def set_status(self, message):
        ""\"
        Set the status message in the status bar.

        Args:
            message: Status message
        ""\"
        try:
            # Try to set the status in the main window if it has a set_status method
            if hasattr(self.parent, 'set_status'):
                self.parent.set_status(message)
            elif hasattr(self.app, 'main_window') and hasattr(self.app.main_window, 'set_status'):
                self.app.main_window.set_status(message)
        except Exception as e:
            logger.warning(f"Could not set status: {str(e)}")
"""
    try:
        with open(base_view_path, "w") as f:
            f.write(new_content.strip())
        logger.info(f"Updated base view at {base_view_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to update base view: {str(e)}")
        return False


if __name__ == "__main__":
    if fix_base_view():
        logger.info(
            "Base view fixed successfully. Run the application to see the changes."
        )
    else:
        logger.error("Failed to fix base view.")
