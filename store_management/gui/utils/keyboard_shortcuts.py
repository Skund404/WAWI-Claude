# utils/keyboard_shortcuts.py
"""
Keyboard shortcut manager for the leatherworking ERP application.

This module provides a centralized system for registering and handling
keyboard shortcuts throughout the application. It includes a shortcut manager
class and helper functions for shortcut management.
"""

import tkinter as tk
from tkinter import ttk
import logging
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class KeyboardShortcutManager:
    """
    Manages keyboard shortcuts for the application.

    Provides a centralized system for registering, unregistering, and
    handling keyboard shortcuts. Supports context-aware shortcuts and
    displaying help information.
    """

    def __init__(self, root_window):
        """
        Initialize the keyboard shortcut manager.

        Args:
            root_window: The root window of the application
        """
        self.root = root_window
        self.shortcuts = {}  # All shortcuts
        self.active_context = None  # Current active context
        self.context_shortcuts = {}  # Shortcuts by context

        # For sequence shortcuts (e.g., Ctrl+N, P)
        self.sequence_mode = False
        self.current_sequence = None
        self.sequence_timeout_id = None
        self.sequence_timeout = 2000  # ms

        # Create logger
        self.logger = logging.getLogger(__name__)

        # Initialize with default global shortcuts
        self._register_global_shortcuts()

    def register_shortcut(self, key_combination: str, command: Callable,
                          description: str = None, context: str = "global") -> None:
        """
        Register a keyboard shortcut.

        Args:
            key_combination: The key combination for the shortcut (e.g., "<Control-s>")
            command: The function to call when the shortcut is triggered
            description: A description of what the shortcut does
            context: The context in which this shortcut is valid (default: "global")
        """
        # Handle multi-key sequences
        if "," in key_combination:
            parts = key_combination.split(",")
            first_key = parts[0].strip()
            rest_keys = ",".join(parts[1:]).strip()

            # Register first part of sequence
            self._register_sequence_starter(first_key, rest_keys, command, description, context)
            return

        # Format key combination for Tkinter
        if not key_combination.startswith("<") and not key_combination.endswith(">"):
            # Convert Ctrl+S format to <Control-s> format
            key_combination = self._format_key_combination(key_combination)

        # Store the shortcut
        shortcut_info = {
            "command": command,
            "description": description or "No description",
            "context": context
        }
        self.shortcuts[key_combination] = shortcut_info

        # Store by context for easy management
        if context not in self.context_shortcuts:
            self.context_shortcuts[context] = {}
        self.context_shortcuts[context][key_combination] = shortcut_info

        # Only bind global shortcuts or shortcuts for the active context
        if context == "global" or context == self.active_context:
            self.root.bind(key_combination, lambda e, cmd=command: self._execute_command(cmd, e))
            self.logger.debug(f"Registered shortcut: {key_combination} ({description}) in context {context}")

    def _register_sequence_starter(self, first_key: str, rest_keys: str,
                                   command: Callable, description: str, context: str) -> None:
        """
        Register the first part of a sequence shortcut.

        Args:
            first_key: The first key in the sequence
            rest_keys: The rest of the keys in the sequence
            command: The function to call when the full sequence is triggered
            description: A description of what the shortcut does
            context: The context in which this shortcut is valid
        """
        first_key = self._format_key_combination(first_key)

        # Create a handler for the first key
        def sequence_handler(event):
            # Cancel any existing timeout
            if self.sequence_timeout_id:
                self.root.after_cancel(self.sequence_timeout_id)

            # Start sequence mode
            self.sequence_mode = True
            self.current_sequence = (rest_keys, command, description)

            # Show a temporary tooltip or status message
            self._show_sequence_hint(rest_keys)

            # Set timeout to exit sequence mode
            self.sequence_timeout_id = self.root.after(
                self.sequence_timeout, self._exit_sequence_mode)

            return "break"  # Prevent default handling

        # Register the first key
        sequence_info = {
            "command": sequence_handler,
            "description": f"{description} (press {first_key}, then {rest_keys})",
            "context": context,
            "is_sequence": True
        }

        self.shortcuts[first_key] = sequence_info

        # Store by context
        if context not in self.context_shortcuts:
            self.context_shortcuts[context] = {}
        self.context_shortcuts[context][first_key] = sequence_info

        # Bind the first key
        if context == "global" or context == self.active_context:
            self.root.bind(first_key, sequence_handler)

        # Also register the second part of the sequence
        self._register_sequence_completion(rest_keys, command, context)

    def _register_sequence_completion(self, key: str, command: Callable, context: str) -> None:
        """
        Register the completion handler for a key sequence.

        Args:
            key: The key that completes the sequence
            command: The function to call when the sequence is completed
            context: The context in which this shortcut is valid
        """
        key = self._format_key_combination(key)

        # Create a special handler for sequence completion
        def completion_handler(event):
            if self.sequence_mode and self.current_sequence and self.current_sequence[0] == key:
                self._exit_sequence_mode()
                return self._execute_command(command, event)
            return None

        # Create a special binding for sequence completion
        sequence_binding = f"sequence_{key}"
        self.root.bind_all(key, completion_handler, add="+")

    def _show_sequence_hint(self, next_key: str) -> None:
        """
        Show a hint for the next key in a sequence.

        Args:
            next_key: The next key in the sequence
        """
        # In a real implementation, this would show a small popup or
        # update a status bar with the next expected key
        self.logger.debug(f"Sequence started, next key: {next_key}")

        # Here we would update some UI element to show the hint
        status_bar = getattr(self.root, "status_bar", None)
        if status_bar:
            status_bar.set_status(f"Press {next_key} to complete command...")

    def _exit_sequence_mode(self) -> None:
        """Exit the sequence mode and clear any related state."""
        self.sequence_mode = False
        self.current_sequence = None

        # Clear any UI hints
        status_bar = getattr(self.root, "status_bar", None)
        if status_bar:
            status_bar.clear_status()

        # Clear timeout
        if self.sequence_timeout_id:
            self.root.after_cancel(self.sequence_timeout_id)
            self.sequence_timeout_id = None

    def _execute_command(self, command: Callable, event: tk.Event = None) -> str:
        """
        Execute the command associated with a shortcut.

        Args:
            command: The command to execute
            event: The event that triggered the command

        Returns:
            "break" to prevent further event processing
        """
        try:
            if event:
                command(event)
            else:
                command()
            return "break"  # Prevent default handling
        except Exception as e:
            self.logger.error(f"Error executing shortcut command: {e}")
            return None

    def unregister_shortcut(self, key_combination: str, context: str = "global") -> bool:
        """
        Unregister a keyboard shortcut.

        Args:
            key_combination: The key combination to unregister
            context: The context from which to unregister the shortcut

        Returns:
            True if the shortcut was unregistered, False otherwise
        """
        # Format key combination for Tkinter
        key_combination = self._format_key_combination(key_combination)

        # Check if shortcut exists in context
        if (context in self.context_shortcuts and
                key_combination in self.context_shortcuts[context]):

            # Unbind the shortcut if it's for the active context or global
            if context == "global" or context == self.active_context:
                self.root.unbind(key_combination)

            # Remove from dictionaries
            del self.context_shortcuts[context][key_combination]
            if key_combination in self.shortcuts:
                del self.shortcuts[key_combination]

            self.logger.debug(f"Unregistered shortcut: {key_combination} in context {context}")
            return True

        return False

    def set_context(self, context: str) -> None:
        """
        Set the active shortcut context.

        When the context changes, shortcuts from the previous context are
        unbound and shortcuts for the new context are bound.

        Args:
            context: The new active context
        """
        if context == self.active_context:
            return

        # Unbind shortcuts from the old context
        if self.active_context in self.context_shortcuts:
            for key_combination in self.context_shortcuts[self.active_context]:
                if key_combination in self.shortcuts:
                    self.root.unbind(key_combination)

        # Update active context
        self.active_context = context

        # Bind global shortcuts and shortcuts for the new context
        self._bind_context_shortcuts("global")
        if context in self.context_shortcuts:
            self._bind_context_shortcuts(context)

        self.logger.debug(f"Set active shortcut context to: {context}")

    def _bind_context_shortcuts(self, context: str) -> None:
        """
        Bind all shortcuts for a given context.

        Args:
            context: The context whose shortcuts should be bound
        """
        if context not in self.context_shortcuts:
            return

        for key_combination, shortcut_info in self.context_shortcuts[context].items():
            if "is_sequence" in shortcut_info and shortcut_info["is_sequence"]:
                # For sequence starters, use the special handler
                self.root.bind(key_combination, shortcut_info["command"])
            else:
                # For normal shortcuts, wrap with _execute_command
                self.root.bind(
                    key_combination,
                    lambda e, cmd=shortcut_info["command"]: self._execute_command(cmd, e)
                )

    def get_all_shortcuts(self) -> Dict[str, str]:
        """
        Get all registered shortcuts with descriptions.

        Returns:
            Dictionary mapping key combinations to descriptions
        """
        return {k: v["description"] for k, v in self.shortcuts.items()}

    def get_context_shortcuts(self, context: str = None) -> Dict[str, str]:
        """
        Get shortcuts for a specific context with descriptions.

        Args:
            context: The context to get shortcuts for, or None for active context

        Returns:
            Dictionary mapping key combinations to descriptions
        """
        context = context or self.active_context
        if context not in self.context_shortcuts:
            return {}

        return {
            k: v["description"]
            for k, v in self.context_shortcuts[context].items()
        }

    def _format_key_combination(self, key_combination: str) -> str:
        """
        Format a key combination string for Tkinter binding.

        Converts from "Ctrl+S" format to "<Control-s>" format.

        Args:
            key_combination: Key combination to format

        Returns:
            Formatted key combination
        """
        if key_combination.startswith("<") and key_combination.endswith(">"):
            return key_combination

        parts = key_combination.split("+")
        modifier_map = {
            "Ctrl": "Control",
            "Alt": "Alt",
            "Shift": "Shift",
            "Command": "Command",
            "Option": "Option"
        }

        # Handle function keys and special keys
        if len(parts) == 1 and parts[0].startswith("F") and parts[0][1:].isdigit():
            return f"<{parts[0]}>"

        # Handle modifier combinations
        modifiers = []
        key = parts[-1]

        for mod in parts[:-1]:
            if mod in modifier_map:
                modifiers.append(modifier_map[mod])

        # Format key - keep function keys as-is, convert others to lowercase
        if key.startswith("F") and key[1:].isdigit():
            formatted_key = key
        else:
            formatted_key = key.lower()

        if modifiers:
            return f"<{'-'.join(modifiers)}-{formatted_key}>"
        else:
            return f"<{formatted_key}>"

    def _register_global_shortcuts(self) -> None:
        """Register the default global shortcuts."""
        # Navigation shortcuts
        self.register_shortcut("Ctrl+D", self._navigate_to_dashboard,
                               "Go to Dashboard", "global")
        self.register_shortcut("Ctrl+A", self._navigate_to_analytics,
                               "Go to Analytics Dashboard", "global")
        self.register_shortcut("Ctrl+I",
                               lambda: self._navigate_to_view("inventory"),
                               "Go to Inventory", "global")
        self.register_shortcut("Ctrl+P",
                               lambda: self._navigate_to_view("projects"),
                               "Go to Projects", "global")
        self.register_shortcut("Ctrl+S",
                               lambda: self._navigate_to_view("sales"),
                               "Go to Sales", "global")

        # Dashboard action shortcuts
        self.register_shortcut("Ctrl+N, P", self._new_project,
                               "New Project", "dashboard")
        self.register_shortcut("Ctrl+N, S", self._new_sale,
                               "New Sale", "dashboard")
        self.register_shortcut("Ctrl+N, I", self._add_inventory,
                               "Add Inventory", "dashboard")
        self.register_shortcut("Ctrl+N, O", self._new_purchase,
                               "New Purchase Order", "dashboard")
        self.register_shortcut("F5", self._refresh,
                               "Refresh Current View", "global")

        # Analytics navigation shortcuts
        self.register_shortcut("Alt+1",
                               lambda: self._navigate_to_analytics_view("customer"),
                               "Go to Customer Analytics", "analytics")
        self.register_shortcut("Alt+2",
                               lambda: self._navigate_to_analytics_view("profitability"),
                               "Go to Profitability Analytics", "analytics")
        self.register_shortcut("Alt+3",
                               lambda: self._navigate_to_analytics_view("material_usage"),
                               "Go to Material Usage Analytics", "analytics")
        self.register_shortcut("Alt+4",
                               lambda: self._navigate_to_analytics_view("project_metrics"),
                               "Go to Project Metrics Analytics", "analytics")

        # Common action shortcuts
        self.register_shortcut("Ctrl+E", self._export_current_view,
                               "Export Current View", "global")
        self.register_shortcut("Escape", self._go_back,
                               "Close Dialog/Return to Previous View", "global")
        self.register_shortcut("F1", self.show_shortcut_help,
                               "Show Keyboard Shortcuts", "global")

    # Shortcut handler methods - these would be implemented to integrate
    # with the actual application navigation

    def _navigate_to_dashboard(self, event=None):
        """Navigate to the dashboard view."""
        self.logger.debug("Shortcut: Navigate to Dashboard")
        main_window = self.root
        try:
            main_window.show_view("dashboard")
        except (AttributeError, Exception) as e:
            self.logger.error(f"Error navigating to dashboard: {e}")

    def _navigate_to_analytics(self, event=None):
        """Navigate to the analytics dashboard."""
        self.logger.debug("Shortcut: Navigate to Analytics Dashboard")
        main_window = self.root
        try:
            main_window.show_view("analytics")
        except (AttributeError, Exception) as e:
            self.logger.error(f"Error navigating to analytics: {e}")

    def _navigate_to_view(self, view_name, event=None):
        """
        Navigate to a specific view.

        Args:
            view_name: The name of the view to navigate to
            event: The event that triggered the navigation
        """
        self.logger.debug(f"Shortcut: Navigate to {view_name}")
        main_window = self.root
        try:
            main_window.show_view(view_name)
        except (AttributeError, Exception) as e:
            self.logger.error(f"Error navigating to {view_name}: {e}")

    def _navigate_to_analytics_view(self, view_name, event=None):
        """
        Navigate to a specific analytics view.

        Args:
            view_name: The name of the analytics view to navigate to
            event: The event that triggered the navigation
        """
        self.logger.debug(f"Shortcut: Navigate to analytics view {view_name}")
        main_window = self.root
        try:
            if hasattr(main_window, "show_analytics_view"):
                main_window.show_analytics_view(view_name)
            else:
                main_window.show_view("analytics")
        except (AttributeError, Exception) as e:
            self.logger.error(f"Error navigating to analytics view {view_name}: {e}")

    def _new_project(self, event=None):
        """Create a new project."""
        self.logger.debug("Shortcut: New Project")
        main_window = self.root
        try:
            main_window.create_new_project()
        except (AttributeError, Exception) as e:
            self.logger.error(f"Error creating new project: {e}")

    def _new_sale(self, event=None):
        """Create a new sale."""
        self.logger.debug("Shortcut: New Sale")
        main_window = self.root
        try:
            main_window.create_new_sale()
        except (AttributeError, Exception) as e:
            self.logger.error(f"Error creating new sale: {e}")

    def _add_inventory(self, event=None):
        """Add inventory."""
        self.logger.debug("Shortcut: Add Inventory")
        main_window = self.root
        try:
            if hasattr(main_window, "add_inventory"):
                main_window.add_inventory()
            else:
                main_window.show_view("inventory")
        except (AttributeError, Exception) as e:
            self.logger.error(f"Error adding inventory: {e}")

    def _new_purchase(self, event=None):
        """Create a new purchase order."""
        self.logger.debug("Shortcut: New Purchase Order")
        main_window = self.root
        try:
            main_window.create_new_purchase()
        except (AttributeError, Exception) as e:
            self.logger.error(f"Error creating new purchase: {e}")

    def _refresh(self, event=None):
        """Refresh the current view."""
        self.logger.debug("Shortcut: Refresh")
        main_window = self.root
        try:
            current_view = getattr(main_window, "current_view", None)
            if current_view and hasattr(current_view, "refresh"):
                current_view.refresh()
        except (AttributeError, Exception) as e:
            self.logger.error(f"Error refreshing current view: {e}")

    def _export_current_view(self, event=None):
        """Export the current view."""
        self.logger.debug("Shortcut: Export Current View")
        main_window = self.root
        try:
            current_view = getattr(main_window, "current_view", None)
            if current_view:
                if hasattr(current_view, "export_pdf"):
                    current_view.export_pdf()
                elif hasattr(current_view, "export_excel"):
                    current_view.export_excel()
                elif hasattr(current_view, "export"):
                    current_view.export()
        except (AttributeError, Exception) as e:
            self.logger.error(f"Error exporting current view: {e}")

    def _go_back(self, event=None):
        """Close dialog or return to previous view."""
        self.logger.debug("Shortcut: Go Back/Close Dialog")
        # Check if there's an active dialog
        for widget in self.root.winfo_children():
            if widget.winfo_class() == "Toplevel" and widget.winfo_viewable():
                widget.destroy()
                return

        # Else try to go back in view history
        main_window = self.root
        try:
            if hasattr(main_window, "go_back"):
                main_window.go_back()
        except (AttributeError, Exception) as e:
            self.logger.error(f"Error going back: {e}")

    def show_shortcut_help(self, event=None):
        """Show a dialog with keyboard shortcut help."""
        self.logger.debug("Showing keyboard shortcut help")

        # Create a dialog window
        dialog = tk.Toplevel(self.root)
        dialog.title("Keyboard Shortcuts")
        dialog.geometry("600x500")
        dialog.resizable(True, True)
        dialog.transient(self.root)
        dialog.grab_set()

        # Add some padding
        main_frame = ttk.Frame(dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Create a notebook for organizing shortcuts by context
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)

        # Add a tab for global shortcuts
        global_frame = ttk.Frame(notebook, padding=5)
        notebook.add(global_frame, text="Global")

        # Create a frame for each context
        context_frames = {"global": global_frame}

        for context in self.context_shortcuts:
            if context != "global":
                frame = ttk.Frame(notebook, padding=5)
                notebook.add(frame, text=context.capitalize())
                context_frames[context] = frame

        # Add shortcuts to each tab
        for context, frame in context_frames.items():
            self._populate_shortcut_list(frame, context)

        # Add close button
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        close_button = ttk.Button(
            button_frame,
            text="Close",
            command=dialog.destroy
        )
        close_button.pack(side=tk.RIGHT)

    def _populate_shortcut_list(self, parent, context):
        """
        Populate a frame with shortcuts for a given context.

        Args:
            parent: The parent frame
            context: The context to show shortcuts for
        """
        # Get shortcuts for this context
        if context not in self.context_shortcuts:
            ttk.Label(parent, text="No shortcuts defined").pack()
            return

        shortcuts = self.context_shortcuts[context]

        # Create a treeview for the shortcuts
        columns = ("shortcut", "description")
        tree = ttk.Treeview(parent, columns=columns, show="headings", height=15)

        # Set column headings
        tree.heading("shortcut", text="Shortcut")
        tree.heading("description", text="Description")

        # Set column widths
        tree.column("shortcut", width=150, anchor="w")
        tree.column("description", width=400, anchor="w")

        # Add scrollbar
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        # Pack widgets
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Add shortcuts to the treeview
        for key_combination, info in shortcuts.items():
            # Format the key combination for display
            display_key = self._format_for_display(key_combination)

            tree.insert("", "end", values=(display_key, info["description"]))

    def _format_for_display(self, key_combination):
        """
        Format a key combination for display in the UI.

        Args:
            key_combination: The key combination to format

        Returns:
            Formatted key combination string
        """
        # Handle multi-key sequences
        if isinstance(key_combination, str) and "," in key_combination:
            return key_combination

        # Format <Control-s> to Ctrl+S etc.
        if isinstance(key_combination, str) and key_combination.startswith("<") and key_combination.endswith(">"):
            # Strip the < and >
            key = key_combination[1:-1]

            # Split into parts
            parts = key.split("-")

            # Format modifiers
            modifier_map = {
                "Control": "Ctrl",
                "Alt": "Alt",
                "Shift": "Shift",
                "Command": "⌘",
                "Option": "Option"
            }

            # Handle function keys
            if len(parts) == 1 and parts[0].startswith("F") and parts[0][1:].isdigit():
                return parts[0]

            # Format last part (the key)
            if len(parts) > 1:
                key_part = parts[-1].upper()
                modifiers = [modifier_map.get(mod, mod) for mod in parts[:-1]]
                return "+".join(modifiers + [key_part])
            else:
                return parts[0].upper()

        return key_combination


# Helper functions to make shortcuts easier to work with in the application

def setup_shortcuts(root_window):
    """
    Set up the keyboard shortcut manager for the application.

    Args:
        root_window: The root window of the application

    Returns:
        KeyboardShortcutManager instance
    """
    shortcut_manager = KeyboardShortcutManager(root_window)
    # Store in the root window for global access
    root_window.shortcut_manager = shortcut_manager
    return shortcut_manager


def register_view_shortcuts(root_window, view_name, shortcuts):
    """
    Register shortcuts for a specific view.

    Args:
        root_window: The root window of the application
        view_name: The name of the view
        shortcuts: Dictionary of key combinations to (command, description) tuples
    """
    if not hasattr(root_window, "shortcut_manager"):
        logger.warning("Shortcut manager not initialized")
        return

    manager = root_window.shortcut_manager

    for key_combination, (command, description) in shortcuts.items():
        manager.register_shortcut(key_combination, command, description, view_name)


def set_shortcut_context(root_window, context):
    """
    Set the active shortcut context.

    Args:
        root_window: The root window of the application
        context: The context to set as active
    """
    if not hasattr(root_window, "shortcut_manager"):
        logger.warning("Shortcut manager not initialized")
        return

    root_window.shortcut_manager.set_context(context)


def show_shortcut_help(root_window):
    """
    Show the keyboard shortcut help dialog.

    Args:
        root_window: The root window of the application
    """
    if not hasattr(root_window, "shortcut_manager"):
        logger.warning("Shortcut manager not initialized")
        return

    root_window.shortcut_manager.show_shortcut_help()