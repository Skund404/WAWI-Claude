# store_management/gui/storage/storage_view.py
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, List, Dict, Any

from store_management.application import Application
from store_management.gui.base_view import BaseView
from store_management.services.interfaces.storage_service import IStorageService


class StorageView(BaseView):
    """Storage view for managing storage locations."""

    def __init__(self, parent, app: Application):
        """
        Initialize the storage view.

        Args:
            parent: Parent widget
            app: Application instance
        """
        super().__init__(parent, app)

        # Get storage service
        self.storage_service = self.get_service(IStorageService)

        # Set up UI
        self.setup_ui()

    def setup_ui(self):
        """Set up the UI components."""
        # Create main frame
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Create toolbar
        self.create_toolbar()

        # Create treeview
        self.create_treeview()

        # Load initial data
        self.load_data()

    def create_toolbar(self):
        """Create the toolbar with action buttons."""
        toolbar = ttk.Frame(self.main_frame)
        toolbar.pack(fill=tk.X, padx=5, pady=5)

        # Add buttons
        add_btn = ttk.Button(toolbar, text="Add", command=self.show_add_dialog)
        add_btn.pack(side=tk.LEFT, padx=2)

        delete_btn = ttk.Button(toolbar, text="Delete", command=lambda: self.delete_selected(None))
        delete_btn.pack(side=tk.LEFT, padx=2)

        refresh_btn = ttk.Button(toolbar, text="Refresh", command=self.load_data)
        refresh_btn.pack(side=tk.LEFT, padx=2)

        search_btn = ttk.Button(toolbar, text="Search", command=self.show_search_dialog)
        search_btn.pack(side=tk.LEFT, padx=2)

    def create_treeview(self):
        """Create the treeview for displaying storage locations."""
        # Create frame for treeview
        tree_frame = ttk.Frame(self.main_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create treeview with scrollbar
        columns = ("id", "location", "description", "capacity", "current_usage")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings")

        # Define column headings
        self.tree.heading("id", text="ID")
        self.tree.heading("location", text="Location")
        self.tree.heading("description", text="Description")
        self.tree.heading("capacity", text="Capacity")
        self.tree.heading("current_usage", text="Current Usage")

        # Define column widths
        self.tree.column("id", width=50)
        self.tree.column("location", width=150)
        self.tree.column("description", width=250)
        self.tree.column("capacity", width=100)
        self.tree.column("current_usage", width=100)

        # Add scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # Grid layout
        self.tree.grid(column=0, row=0, sticky='nsew')
        vsb.grid(column=1, row=0, sticky='ns')
        hsb.grid(column=0, row=1, sticky='ew')

        # Configure grid weights
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)

        # Bind events
        self.tree.bind("<Double-1>", self.on_double_click)

    def load_data(self):
        """Load storage data from service."""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        try:
            # Get data from service
            storage_locations = self.storage_service.get_all_storage_locations()

            # Populate treeview
            for location in storage_locations:
                self.tree.insert("", "end", values=(
                    location.get("id", ""),
                    location.get("location", ""),
                    location.get("description", ""),
                    location.get("capacity", 0),
                    location.get("current_usage", 0)
                ))

            self.set_status(f"Loaded {len(storage_locations)} storage locations")

        except Exception as e:
            self.show_error("Error Loading Data", str(e))

    def show_add_dialog(self):
        """Show dialog for adding a new storage location."""
        # This would typically be implemented with a dialog class
        # For this example, we'll use a simplified implementation

        dialog = tk.Toplevel(self)
        dialog.title("Add Storage Location")
        dialog.geometry("400x300")
        dialog.transient(self)
        dialog.grab_set()

        # Create form fields
        ttk.Label(dialog, text="Location:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        location_entry = ttk.Entry(dialog, width=30)
        location_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(dialog, text="Description:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        description_entry = ttk.Entry(dialog, width=30)
        description_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(dialog, text="Capacity:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        capacity_entry = ttk.Entry(dialog, width=30)
        capacity_entry.grid(row=2, column=1, padx=5, pady=5)

        # Add buttons
        def on_save():
            try:
                # Get values
                location = location_entry.get()
                description = description_entry.get()
                capacity = float(capacity_entry.get() or 0)

                # Validate
                if not location:
                    self.show_error("Validation Error", "Location is required")
                    return

                # Save the data (implementation depends on service)
                # For now, we'll just show a confirmation
                messagebox.showinfo("Success", "Storage location added")
                dialog.destroy()

                # Refresh data
                self.load_data()

            except ValueError:
                self.show_error("Validation Error", "Capacity must be a number")

        def on_cancel():
            dialog.destroy()

        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=3, column=0, columnspan=2, pady=10)
        # store_management/gui/storage/storage_view.py (continued)
        # Continuing from where we left off in the show_add_dialog method

        save_btn = ttk.Button(button_frame, text="Save", command=on_save)
        save_btn.pack(side=tk.LEFT, padx=5)

        cancel_btn = ttk.Button(button_frame, text="Cancel", command=on_cancel)
        cancel_btn.pack(side=tk.LEFT, padx=5)

        # Set focus to first field
        location_entry.focus_set()

    def on_double_click(self, event):
        """Handle double-click event for editing."""
        # Get the selected item
        selection = self.tree.selection()
        if not selection:
            return

        # Get item ID and column
        item = selection[0]
        column = self.tree.identify_column(event.x)

        # Start cell editing
        if column:
            column_id = column.replace("#", "")
            column_name = self.tree.column(column_id, "id")
            self.start_cell_edit(item, column_name)

    def start_cell_edit(self, item, column):
        """Start editing a cell."""
        # Get current value
        values = self.tree.item(item, "values")
        item_id = values[0]

        # Get column index
        columns = self.tree.cget("columns")
        column_idx = columns.index(column)
        current_value = values[column_idx]

        # Create editing window
        edit_window = tk.Toplevel(self)
        edit_window.title("Edit Value")
        edit_window.geometry("300x100")
        edit_window.transient(self)
        edit_window.grab_set()

        # Create widgets
        ttk.Label(edit_window, text=f"Edit {column}:").pack(pady=5)
        entry = ttk.Entry(edit_window, width=30)
        entry.insert(0, current_value)
        entry.pack(pady=5)
        entry.select_range(0, tk.END)
        entry.focus_set()

        # Save function
        def save_edit():
            new_value = entry.get()

            # Update values
            new_values = list(values)
            new_values[column_idx] = new_value

            # Update tree
            self.tree.item(item, values=new_values)

            # Update in database (implementation depends on service)
            # Here we would call the appropriate service method

            # Close window
            edit_window.destroy()

        # Buttons
        button_frame = ttk.Frame(edit_window)
        button_frame.pack(pady=5)

        save_btn = ttk.Button(button_frame, text="Save", command=save_edit)
        save_btn.pack(side=tk.LEFT, padx=5)

        cancel_btn = ttk.Button(button_frame, text="Cancel", command=edit_window.destroy)
        cancel_btn.pack(side=tk.LEFT, padx=5)

        # Bind Enter key to save
        entry.bind("<Return>", lambda event: save_edit())

    def delete_selected(self, event):
        """Delete selected storage locations."""
        selection = self.tree.selection()
        if not selection:
            self.show_info("Selection Required", "Please select an item to delete")
            return

        # Confirm deletion
        if not self.confirm("Confirm Delete", "Are you sure you want to delete the selected item(s)?"):
            return

        # Delete selected items
        for item in selection:
            values = self.tree.item(item, "values")
            item_id = values[0]

            # Delete from database (implementation depends on service)
            # Here we would call the appropriate service method

            # Remove from tree
            self.tree.delete(item)

        self.set_status(f"Deleted {len(selection)} item(s)")

    def show_search_dialog(self):
        """Show search dialog."""
        # This would typically be implemented with a dialog class
        # For this example, we'll use a simplified implementation

        dialog = tk.Toplevel(self)
        dialog.title("Search Storage Locations")
        dialog.geometry("400x150")
        dialog.transient(self)
        dialog.grab_set()

        # Create search field
        ttk.Label(dialog, text="Search Term:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        search_entry = ttk.Entry(dialog, width=30)
        search_entry.grid(row=0, column=1, padx=5, pady=5)
        search_entry.focus_set()

        # Create search options
        ttk.Label(dialog, text="Search In:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)

        search_location_var = tk.BooleanVar(value=True)
        search_description_var = tk.BooleanVar(value=True)

        options_frame = ttk.Frame(dialog)
        options_frame.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)

        ttk.Checkbutton(options_frame, text="Location", variable=search_location_var).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(options_frame, text="Description", variable=search_description_var).pack(side=tk.LEFT, padx=5)

        # Search function
        def do_search():
            search_term = search_entry.get().strip().lower()
            if not search_term:
                self.show_info("Search Term Required", "Please enter a search term")
                return

            # Clear selection
            self.tree.selection_remove(self.tree.selection())

            # Search in tree
            found_items = []
            for item in self.tree.get_children():
                values = self.tree.item(item, "values")

                # Check location
                if search_location_var.get() and search_term in str(values[1]).lower():
                    found_items.append(item)
                    continue

                # Check description
                if search_description_var.get() and search_term in str(values[2]).lower():
                    found_items.append(item)
                    continue

            # Select found items
            for item in found_items:
                self.tree.selection_add(item)
                self.tree.see(item)  # Ensure it's visible

            # Show results
            dialog.destroy()
            self.set_status(f"Found {len(found_items)} matching item(s)")

        # Add buttons
        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=2, column=0, columnspan=2, pady=10)

        search_btn = ttk.Button(button_frame, text="Search", command=do_search)
        search_btn.pack(side=tk.LEFT, padx=5)

        cancel_btn = ttk.Button(button_frame, text="Cancel", command=dialog.destroy)
        cancel_btn.pack(side=tk.LEFT, padx=5)

        # Bind Enter key to search
        search_entry.bind("<Return>", lambda event: do_search())