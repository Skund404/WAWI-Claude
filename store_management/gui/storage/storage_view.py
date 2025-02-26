# gui/storage/storage_view.py
"""
StorageView module for displaying and managing storage locations for leatherworking materials.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
import os
import sqlite3
from typing import Optional, List, Dict, Any, Tuple

from gui.base_view import BaseView
from services.interfaces.storage_service import IStorageService
from di.core import inject

# Configure logger
logger = logging.getLogger(__name__)


class StorageView(BaseView):
    """View for managing storage locations for leatherworking materials."""

    def __init__(self, parent: ttk.Frame, app: tk.Tk):
        """
        Initialize the storage view.

        Args:
            parent (ttk.Frame): Parent widget.
            app (tk.Tk): Application instance.
        """
        super().__init__(parent, app)

        # Get storage service from dependency injection
        self.storage_service = self.get_service(IStorageService)

        # UI components
        self.tree = None
        self.search_var = None
        self.filter_var = None
        self.status_bar = None

        # Selected item
        self.selected_id = None

        # Create UI
        self.setup_ui()

        # Load data
        self.load_data()

        logger.info("StorageView initialized")

    def setup_ui(self):
        """Set up the user interface."""
        self._setup_ui()

    def _setup_ui(self):
        """Set up the user interface."""
        # Control frame (top)
        control_frame = ttk.Frame(self)
        control_frame.pack(fill=tk.X, padx=5, pady=5)

        # Search
        ttk.Label(control_frame, text="Search:").pack(side=tk.LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(control_frame, textvariable=self.search_var, width=20)
        search_entry.pack(side=tk.LEFT, padx=(0, 5))
        search_entry.bind("<Return>", lambda e: self._search_storage())

        ttk.Button(control_frame, text="Search", command=self._search_storage).pack(side=tk.LEFT, padx=(0, 10))

        # Filter by type
        ttk.Label(control_frame, text="Type:").pack(side=tk.LEFT, padx=(0, 5))
        self.filter_var = tk.StringVar(value="All")
        storage_types = ["All", "SHELF", "BIN", "DRAWER", "CABINET", "RACK", "BOX", "OTHER"]
        filter_combo = ttk.Combobox(control_frame, textvariable=self.filter_var, values=storage_types, width=10)
        filter_combo.pack(side=tk.LEFT, padx=(0, 10))
        filter_combo.bind("<<ComboboxSelected>>", lambda e: self.load_data())

        # CRUD Buttons
        ttk.Button(control_frame, text="Add", command=self._add_storage).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="Edit", command=self._edit_storage).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="Delete", command=self._delete_storage).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="Refresh", command=self.load_data).pack(side=tk.LEFT, padx=2)

        # Main content - Treeview
        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Define columns
        columns = ("id", "name", "location", "type", "capacity", "used", "remaining", "notes")

        # Create treeview
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings")

        # Define column properties
        self.tree.column("id", width=50, minwidth=50)
        self.tree.column("name", width=150, minwidth=100)
        self.tree.column("location", width=150, minwidth=100)
        self.tree.column("type", width=100, minwidth=80)
        self.tree.column("capacity", width=80, minwidth=60)
        self.tree.column("used", width=80, minwidth=60)
        self.tree.column("remaining", width=80, minwidth=60)
        self.tree.column("notes", width=200, minwidth=100)

        # Define column headings
        for col in columns:
            self.tree.heading(col, text=col.title(), command=lambda _col=col: self._sort_column(_col))

        # Add scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # Pack scrollbars and treeview
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Bind events
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind("<Double-1>", self._on_double_click)

        # Status bar
        self.status_bar = ttk.Label(self, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def load_data(self):
        """Load storage data from the database."""
        try:
            # Clear existing data
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Get filter value
            filter_type = self.filter_var.get() if hasattr(self, 'filter_var') else "All"

            logger.info("Loading storage data directly from database")

            # Get data from service
            if self.storage_service:
                storage_locations = self.storage_service.get_all_storage_locations()
            else:
                # Fallback to direct database access if service is not available
                storage_locations = self._load_from_database()

            # Filter by type if needed
            if filter_type != "All":
                storage_locations = [loc for loc in storage_locations if loc.get('type') == filter_type]

            # Insert into treeview
            for location in storage_locations:
                # Calculate usage stats
                capacity = location.get('capacity', 0)
                used = location.get('used_capacity', 0)
                remaining = capacity - used if capacity > 0 else 0

                values = (
                    location.get('id', ''),
                    location.get('name', ''),
                    location.get('location', ''),
                    location.get('type', ''),
                    capacity,
                    used,
                    remaining,
                    location.get('notes', '')
                )

                self.tree.insert('', 'end', values=values)

            # Update status
            count = len(storage_locations)
            self.status_bar.config(text=f"Loaded {count} storage locations")
            logger.info(f"Loaded {count} storage locations")

        except Exception as e:
            logger.error(f"Error loading storage data: {str(e)}")
            messagebox.showerror("Error", f"Failed to load storage data: {str(e)}")
            self.status_bar.config(text="Error loading data")

    def _load_from_database(self) -> List[Dict[str, Any]]:
        """
        Fallback method to load storage data directly from the database.

        Returns:
            List of dictionaries with storage data
        """
        try:
            # Find database file
            db_path = self._find_database_file()
            if not db_path:
                logger.error("Database file not found")
                return []

            # Connect to database
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Query storage data
            cursor.execute("""
                SELECT id, name, location, type, capacity, COALESCE(used_capacity, 0) as used_capacity, notes
                FROM storage
            """)

            # Fetch results
            rows = cursor.fetchall()

            # Convert to list of dictionaries
            result = []
            for row in rows:
                result.append({
                    'id': row['id'],
                    'name': row['name'],
                    'location': row['location'],
                    'type': row['type'],
                    'capacity': row['capacity'],
                    'used_capacity': row['used_capacity'],
                    'notes': row['notes']
                })

            conn.close()
            return result

        except Exception as e:
            logger.error(f"Error loading from database: {str(e)}")
            return []

    def _find_database_file(self) -> Optional[str]:
        """
        Find the database file path.

        Returns:
            Path to the database file or None if not found
        """
        # Look for database in common locations
        possible_paths = [
            os.path.join(os.getcwd(), "data", "store_management.db"),
            os.path.join(os.getcwd(), "store_management.db"),
            os.path.join(os.path.dirname(os.getcwd()), "data", "store_management.db")
        ]

        for path in possible_paths:
            if os.path.exists(path):
                return path

        return None

    def _search_storage(self):
        """Search for storage locations matching the search term."""
        search_term = self.search_var.get().strip().lower()
        if not search_term:
            self.load_data()
            return

        try:
            # Clear existing data
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Get all data
            if self.storage_service:
                storage_locations = self.storage_service.get_all_storage_locations()
            else:
                storage_locations = self._load_from_database()

            # Filter by search term
            filtered_locations = []
            for location in storage_locations:
                # Search in name, location, and notes
                name = str(location.get('name', '')).lower()
                loc = str(location.get('location', '')).lower()
                notes = str(location.get('notes', '')).lower()

                if (search_term in name or search_term in loc or search_term in notes):
                    filtered_locations.append(location)

            # Insert into treeview
            for location in filtered_locations:
                # Calculate usage stats
                capacity = location.get('capacity', 0)
                used = location.get('used_capacity', 0)
                remaining = capacity - used if capacity > 0 else 0

                values = (
                    location.get('id', ''),
                    location.get('name', ''),
                    location.get('location', ''),
                    location.get('type', ''),
                    capacity,
                    used,
                    remaining,
                    location.get('notes', '')
                )

                self.tree.insert('', 'end', values=values)

            # Update status
            count = len(filtered_locations)
            self.status_bar.config(text=f"Found {count} locations matching '{search_term}'")

        except Exception as e:
            logger.error(f"Error searching storage: {str(e)}")
            messagebox.showerror("Error", f"Search failed: {str(e)}")

    def _sort_column(self, column):
        """
        Sort treeview by the specified column.

        Args:
            column: Column to sort by
        """
        # Get all items from treeview
        data = [(self.tree.set(item, column), item) for item in self.tree.get_children('')]

        # Check if column contains numbers
        is_numeric = column in ('id', 'capacity', 'used', 'remaining')

        # Sort data
        if is_numeric:
            # Convert to numbers for sorting
            data = [(float(val) if val.replace('.', '', 1).isdigit() else 0, item) for val, item in data]
        data.sort()

        # Rearrange items in the tree
        for idx, (_, item) in enumerate(data):
            self.tree.move(item, '', idx)

    def _on_select(self, event):
        """Handle selection of an item in the treeview."""
        selected_items = self.tree.selection()
        if selected_items:
            # Get ID of selected item
            item_values = self.tree.item(selected_items[0], 'values')
            self.selected_id = item_values[0]

    def _on_double_click(self, event):
        """Handle double-click on a treeview item."""
        region = self.tree.identify("region", event.x, event.y)
        if region == "cell" and self.selected_id:
            self._edit_storage()

    def _add_storage(self):
        """Show dialog to add a new storage location."""
        # This would typically open a dialog for adding a storage location
        # For now, let's display a placeholder message
        messagebox.showinfo("Add Storage", "This would open a dialog to add a new storage location")

    def _edit_storage(self):
        """Show dialog to edit the selected storage location."""
        if not self.selected_id:
            messagebox.showinfo("No Selection", "Please select a storage location to edit")
            return

        # This would typically open a dialog for editing the selected storage location
        messagebox.showinfo("Edit Storage", f"This would open a dialog to edit storage location {self.selected_id}")

    def _delete_storage(self):
        """Delete the selected storage location."""
        if not self.selected_id:
            messagebox.showinfo("No Selection", "Please select a storage location to delete")
            return

        # Confirm deletion
        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete this storage location?",
            icon=messagebox.WARNING
        )

        if confirm:
            try:
                if self.storage_service:
                    self.storage_service.delete_storage_location(self.selected_id)
                    messagebox.showinfo("Success", "Storage location deleted successfully")
                    self.load_data()
                else:
                    messagebox.showwarning("Not Implemented",
                                           "Delete functionality is not available in direct database mode")
            except Exception as e:
                logger.error(f"Error deleting storage location: {str(e)}")
                messagebox.showerror("Error", f"Failed to delete storage location: {str(e)}")