"""
Base view for all application views.
Provides common functionality and standardized layout.
"""
import abc
import logging
import tkinter as tk
from tkinter import ttk, messagebox

# Import exceptions from services
from services.base_service import (
    BaseApplicationException,
    NotFoundError,
    ValidationError,
    ServiceError
)

logger = logging.getLogger(__name__)


class BaseView(ttk.Frame, abc.ABC):
    """
    Abstract base class for all application views.
    
    This class provides common functionality and a standardized layout
    for all views in the application. It handles error management,
    service access, and other shared behaviors.
    
    Subclasses should override _create_view_specific_elements to
    implement their specific UI elements.
    """
    
    def __init__(self, parent, app):
        """
        Initialize the base view with common structure and functionality.
        
        Args:
            parent (tk.Widget): Parent widget
            app: Application instance with dependency container
        """
        super().__init__(parent)
        
        # Store references
        self._parent = parent
        self._app = app
        
        # Initialize action history for undo/redo
        self._undo_stack = []
        self._redo_stack = []
        
        # Track changes
        self._has_unsaved_changes = False
        
        # Setup keyboard shortcuts
        self._setup_keyboard_shortcuts()
        
        # Setup the view layout
        self._setup_common_elements()
        
        # Call implementation-specific setup
        self._create_view_specific_elements()
        
        logger.debug(f"Initialized view: {self.__class__.__name__}")
    
    def _setup_keyboard_shortcuts(self):
        """Set up keyboard shortcuts for common actions."""
        # Undo/Redo shortcuts
        self.bind("<Control-z>", self.undo)
        self.bind("<Control-y>", self.redo)
        
        # Save shortcut
        self.bind("<Control-s>", lambda event: self.on_save())
        
        # Refresh shortcut
        self.bind("<F5>", lambda event: self.on_refresh())
    
    def _setup_common_elements(self):
        """Set up common UI elements for all views."""
        # Configure the frame to fill its container
        self.pack(fill=tk.BOTH, expand=True)
        
        # Configure grid layout
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=0)  # Header
        self.rowconfigure(1, weight=1)  # Content
        self.rowconfigure(2, weight=0)  # Footer
        
        # Create a header frame
        self.header_frame = ttk.Frame(self)
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        # Create the main content frame
        self.content_frame = ttk.Frame(self)
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
        # Configure the content frame layout
        self.content_frame.columnconfigure(0, weight=1)
        self.content_frame.rowconfigure(0, weight=1)
        
        # Create an optional footer frame
        self.footer_frame = ttk.Frame(self)
        self.footer_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
    
    @abc.abstractmethod
    def _create_view_specific_elements(self):
        """
        Create view-specific UI elements.
        
        This method must be implemented by subclasses to set up their
        specific UI components within the common layout.
        """
        pass
    
    def get_service(self, service_type):
        """
        Get a service from the application container.
        
        Args:
            service_type: The type of service to retrieve
            
        Returns:
            The service instance or None if not found
        """
        try:
            service = self._app.get(service_type)
            if service is None:
                logger.warning(f"Service not found: {service_type.__name__}")
                self.show_warning("Service Not Available", 
                                 f"The {service_type.__name__} service is not available.")
            return service
        except Exception as e:
            logger.error(f"Error getting service {service_type.__name__}: {e}")
            self.show_error("Service Error", 
                           f"Error accessing {service_type.__name__} service: {str(e)}")
            return None
    
    def show_error(self, title, message):
        """
        Show an error message dialog.
        
        Args:
            title (str): Dialog title
            message (str): Error message to display
        """
        logger.error(f"Error - {title}: {message}")
        messagebox.showerror(title, message)
    
    def show_warning(self, title, message):
        """
        Show a warning message dialog.
        
        Args:
            title (str): Dialog title
            message (str): Warning message to display
        """
        logger.warning(f"Warning - {title}: {message}")
        messagebox.showwarning(title, message)
    
    def show_info(self, title, message):
        """
        Show an information message dialog.
        
        Args:
            title (str): Dialog title
            message (str): Information message to display
        """
        logger.info(f"Info - {title}: {message}")
        messagebox.showinfo(title, message)
    
    def show_confirmation(self, title, message):
        """
        Show a confirmation dialog.
        
        Args:
            title (str): Dialog title
            message (str): Confirmation message to display
            
        Returns:
            bool: True if confirmed, False otherwise
        """
        logger.debug(f"Confirmation request - {title}: {message}")
        return messagebox.askyesno(title, message)
    
    def handle_error(self, error, message=None):
        """
        Handle exceptions in a standardized way.
        
        Args:
            error: The exception that occurred
            message: Optional custom message to display
        """
        if message is None:
            message = str(error)
        
        logger.error(f"Error: {message}", exc_info=error)
        
        if isinstance(error, NotFoundError):
            self.show_warning("Not Found", message)
        elif isinstance(error, ValidationError):
            self.show_warning("Validation Error", message)
        elif isinstance(error, ServiceError):
            self.show_error("Service Error", message)
        elif isinstance(error, BaseApplicationException):
            self.show_error("Application Error", message)
        else:
            self.show_error("Unexpected Error", message)
    
    def set_status(self, message):
        """
        Set the status message in the application.
        
        Args:
            message (str): Status message to display
        """
        # Try to find the main window's set_status method
        if hasattr(self._app, 'set_status'):
            self._app.set_status(message)
        # If not found, try to find the main window
        elif hasattr(self._app, 'main_window') and hasattr(self._app.main_window, 'set_status'):
            self._app.main_window.set_status(message)
        # If all else fails, just log the message
        else:
            logger.info(f"Status: {message}")
    
    def add_undo_action(self, action, description="Unnamed action"):
        """
        Add an action to the undo stack.
        
        Args:
            action (callable): Function to be called to undo the action
            description (str): Description of the action for logging
        """
        logger.debug(f"Adding to undo stack: {description}")
        self._undo_stack.append((action, description))
        self._redo_stack.clear()  # Clear redo stack when a new action is added
        self._has_unsaved_changes = True
    
    def undo(self, event=None):
        """
        Undo the last action if possible.
        
        Args:
            event: Optional event that triggered the undo
        """
        if not self._undo_stack:
            self.set_status("Nothing to undo")
            return
        
        try:
            action, description = self._undo_stack.pop()
            logger.debug(f"Undoing: {description}")
            
            # Call the undo action
            action()
            
            # Add to redo stack
            self._redo_stack.append((action, description))
            
            self.set_status(f"Undid: {description}")
        except Exception as e:
            logger.error(f"Error during undo: {e}")
            self.show_error("Undo Error", f"An error occurred while undoing: {str(e)}")
    
    def redo(self, event=None):
        """
        Redo the last undone action if possible.
        
        Args:
            event: Optional event that triggered the redo
        """
        if not self._redo_stack:
            self.set_status("Nothing to redo")
            return
        
        try:
            action, description = self._redo_stack.pop()
            logger.debug(f"Redoing: {description}")
            
            # Call the redo action
            action()
            
            # Add back to undo stack
            self._undo_stack.append((action, description))
            
            self.set_status(f"Redid: {description}")
        except Exception as e:
            logger.error(f"Error during redo: {e}")
            self.show_error("Redo Error", f"An error occurred while redoing: {str(e)}")
    
    def clear_history(self):
        """Clear undo/redo history."""
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._has_unsaved_changes = False
    
    def has_unsaved_changes(self):
        """
        Check if there are unsaved changes.
        
        Returns:
            bool: True if there are unsaved changes, False otherwise
        """
        return self._has_unsaved_changes
    
    def prompt_save_changes(self):
        """
        Prompt the user to save changes if there are any.
        
        Returns:
            bool: True if it's OK to continue, False if the operation should be cancelled
        """
        if not self.has_unsaved_changes():
            return True
        
        response = messagebox.askyesnocancel(
            "Unsaved Changes",
            "There are unsaved changes. Would you like to save them before continuing?"
        )
        
        if response is None:  # Cancel
            return False
        
        if response:  # Yes
            return self.on_save()
        
        return True  # No, continue without saving
    
    # Default implementations of common actions
    
    def on_new(self):
        """Default handler for new item creation."""
        logger.debug("Base on_new called - should be overridden by subclass")
        self.set_status("New item function not implemented")
    
    def on_edit(self):
        """Default handler for item editing."""
        logger.debug("Base on_edit called - should be overridden by subclass")
        self.set_status("Edit function not implemented")
    
    def on_delete(self):
        """Default handler for item deletion."""
        logger.debug("Base on_delete called - should be overridden by subclass")
        self.set_status("Delete function not implemented")
    
    def on_save(self):
        """Default handler for saving data."""
        logger.debug("Base on_save called - should be overridden by subclass")
        self._has_unsaved_changes = False
        self.set_status("Save function not implemented")
        return True
    
    def on_refresh(self):
        """Default handler for refreshing view data."""
        logger.debug("Base on_refresh called - should be overridden by subclass")
        self.set_status("Refresh function not implemented")
    
    def search(self, query, **filters):
        """
        Perform a search with filters.
        
        Args:
            query (str): Text search query
            **filters: Additional filters to apply
            
        Returns:
            List[Any]: Search results
        """
        logger.debug(f"Base search called with query: {query}, filters: {filters}")
        return self._internal_search()
    
    def _internal_search(self):
        """
        Internal search implementation to be overridden by subclasses.
        
        Returns:
            List[Any]: Search results
        """
        logger.debug("Base _internal_search called - should be overridden by subclass")
        return []
    
    def cleanup(self):
        """
        Clean up resources before destroying the view.
        
        This method should be overridden by subclasses that need to
        perform additional cleanup operations.
        """
        logger.debug(f"Cleaning up view: {self.__class__.__name__}")
        
        # Perform basic cleanup
        self.clear_history()
        
        # Custom cleanup can be added by subclasses