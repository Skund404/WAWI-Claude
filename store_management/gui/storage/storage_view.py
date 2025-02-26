# gui/storage/storage_view.py
"""
View for managing storage locations in a leatherworking store management system.
Provides functionality to view, add, edit, and delete storage locations.
"""

import logging
import os
import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any, Dict, List, Optional, Tuple, Type

from gui.base_view import BaseView
from services.interfaces.storage_service import IStorageService

# Configure logger
logger = logging.getLogger(__name__)


class StorageView(BaseView):
    """
    View for displaying and managing storage locations.

    Provides a tabular interface for viewing storage locations, with functionality
    to add, edit, and delete entries. Includes search and filter capabilities.
    """

    def __init__(self, parent: ttk.Frame, app: tk.Tk):
        """
        Initialize the storage view.

        Args:
            parent (ttk.Frame): Parent widget.
            app (tk.Tk): Application instance.
        """
        super().__init__(parent, app)

        self._storage_service = None
        self._selected_storage_id = None

        # Initialize UI
        self.setup_ui()

        # Load initial data
        self.load_data()

        logger.info("Storage view initialized")

    def get_service(self, service_type: Type) -> Any:
        """
        Retrieve a service from the dependency container.

        Args:
            service_type (Type): Service interface to retrieve

        Returns:
            Any: Service implementation instance
        """
        try:
            return self._app.get_service(service_type)
        except Exception as e:
            logger.error(f"Failed to get service {service_type.__name__}: {str(e)}")
            raise

    @property
    def storage_service(self) -> IStorageService:
        """
        Lazy-loaded storage service property.

        Returns:
            IStorageService: Storage service instance
        """
        if self._storage_service is None:
            self._storage_service = self.get_service(IStorageService)
        return self._storage_service

    def setup_ui(self) -> None:
        """Set up the user interface."""
        # Configure grid
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # Create toolbar
        toolbar_frame = ttk.Frame(self, padding=5)
        toolbar_frame.grid(row=0, column=0, sticky="ew")

        # Add toolbar buttons
        ttk.Button(toolbar_frame, text="Add Location", command=self._add_storage).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar_frame, text="Edit", command=self._edit_storage).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar_frame, text="Delete", command=self._delete_storage).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar_frame, text="Refresh", command=self.load_data).pack(side=tk.LEFT, padx=2)
        ttk.Separator(toolbar_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)

        # Add search bar
        ttk.Label(toolbar_frame, text="Search:").pack(side=tk.LEFT, padx=(10, 2))
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(toolbar_frame, textvariable=self.search_var, width=20)
        search_entry.pack(side=tk.LEFT, padx=2)
        search_entry.bind("<Return>", self._search_storage)
        ttk.Button(toolbar_frame, text="Search", command=self._search_storage).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar_frame, text="Clear", command=self._clear_search).pack(side=tk.LEFT, padx=2)

        # Create treeview for storage locations
        columns = ("id", "name", "location_type", "capacity", "used_capacity", "description", "items_count")
        self.tree = ttk.Treeview(self, columns=columns, show="headings")

        # Configure column headings
        self.tree.heading("id", text="ID", command=lambda: self._sort_column("id"))
        self.tree.heading("name", text="Location Name", command=lambda: self._sort_column("name"))
        self.tree.heading("location_type", text="Type", command=lambda: self._sort_column("location_type"))
        self.tree.heading("capacity", text="Capacity", command=lambda: self._sort_column("capacity"))
        self.tree.heading("used_capacity", text="Used", command=lambda: self._sort_column("used_capacity"))
        self.tree.heading("description", text="Description", command=lambda: self._sort_column("description"))
        self.tree.heading("items_count", text="Items", command=lambda: self._sort_column("items_count"))

        # Configure column widths
        self.tree.column("id", width=50, stretch=False)
        self.tree.column("name", width=150)
        self.tree.column("location_type", width=100)
        self.tree.column("capacity", width=80, anchor=tk.E)
        self.tree.column("used_capacity", width=80, anchor=tk.E)
        self.tree.column("description", width=200)
        self.tree.column("items_count", width=60, anchor=tk.CENTER)

        # Add scrollbars
        y_scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview)
        x_scrollbar = ttk.Scrollbar(self, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscroll=y_scrollbar.set, xscroll=x_scrollbar.set)

        # Grid layout
        self.tree.grid(row=1, column=0, sticky="nsew")
        y_scrollbar.grid(row=1, column=1, sticky="ns")
        x_scrollbar.grid(row=2, column=0, sticky="ew")

        # Add status bar
        self.status_var = tk.StringVar()
        status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=3, column=0, columnspan=2, sticky="ew")

        # Bind events
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind("<Double-1>", self._on_double_click)

        # Set initial status
        self.status_var.set("Ready")

    def load_data(self) -> None:
        """
        Load storage data from the storage service and populate the treeview.
        """
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        try:
            # Get storage locations from service
            storage_locations = self.storage_service.get_all_storage_locations()

            if not storage_locations:
                self.status_var.set("No storage locations found")
                logger.info("No storage locations found")
                return

            # Populate treeview
            for location in storage_locations:
                # Calculate usage percentage
                capacity = location.get("capacity", 0)
                used_capacity = location.get("used_capacity", 0)

                # Count items in storage
                items_count = len(location.get("items", []))

                self.tree.insert("", tk.END, values=(
                    location.get("id", ""),
                    location.get("name", ""),
                    location.get("location_type", ""),
                    capacity,
                    used_capacity,
                    location.get("description", ""),
                    items_count
                ))

            # Update status
            self.status_var.set(f"Loaded {len(storage_locations)} storage locations")
            logger.info(f"Loaded {len(storage_locations)} storage locations")

        except Exception as e:
            error_message = f"Error loading storage locations: {str(e)}"
            self.show_error("Data Loading Error", error_message)
            logger.error(error_message, exc_info=True)
            self.status_var.set("Error loading data")

    def _search_storage(self, event=None) -> None:
        """
        Search for storage locations matching the search term.

        Args:
            event: Event that triggered the search (optional)
        """
        search_term = self.search_var.get().strip().lower()

        if not search_term:
            self.load_data()
            return

        try:
            # Clear current items
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Get all storage locations and filter locally
            storage_locations = self.storage_service.get_all_storage_locations()

            # Filter locations based on search term
            filtered_locations = []
            for location in storage_locations:
                # Check if the search term appears in any of the key fields
                for field in ["name", "location_type", "description"]:
                    value = str(location.get(field, "")).lower()
                    if search_term in value:
                        filtered_locations.append(location)
                        break

            # Populate treeview with filtered locations
            for location in filtered_locations:
                capacity = location.get("capacity", 0)
                used_capacity = location.get("used_capacity", 0)

                # Count items in storage
                items_count = len(location.get("items", []))

                self.tree.insert("", tk.END, values=(
                    location.get("id", ""),
                    location.get("name", ""),
                    location.get("location_type", ""),
                    capacity,
                    used_capacity,
                    location.get("description", ""),
                    items_count
                ))

            # Update status
            self.status_var.set(f"Found {len(filtered_locations)} storage locations matching '{search_term}'")
            logger.info(f"Search results: {len(filtered_locations)} locations for term '{search_term}'")

        except Exception as e:
            error_message = f"Error searching storage locations: {str(e)}"
            self.show_error("Search Error", error_message)
            logger.error(error_message, exc_info=True)

    def _clear_search(self) -> None:
        """Clear search field and reload all data."""
        self.search_var.set("")
        self.load_data()

    def _sort_column(self, column: str) -> None:
        """
        Sort treeview by the specified column.

        Args:
            column: Column to sort by
        """
        # Get current sorting direction
        if hasattr(self, "_sort_column_name") and self._sort_column_name == column:
            self._sort_asc = not self._sort_asc
        else:
            self._sort_column_name = column
            self._sort_asc = True

        # Sort function for different column types
        def sort_by_column(item):
            value = self.tree.set(item, column)
            # Try to convert to numeric if possible for numeric sorting
            try:
                return float(value)
            except (ValueError, TypeError):
                return value.lower()  # Otherwise sort as lowercase string

        # Get all items and sort
        items = self.tree.get_children("")
        items = sorted(items, key=sort_by_column, reverse=not self._sort_asc)

        # Move items in the tree
        for idx, item in enumerate(items):
            self.tree.move(item, "", idx)

        # Update column heading to show sort direction
        for col in self.tree["columns"]:
            if col == column:
                direction = "▲" if self._sort_asc else "▼"
                self.tree.heading(col, text=f"{self.tree.heading(col)['text'].split()[0]} {direction}")
            else:
                # Remove sort indicator from other columns
                self.tree.heading(col, text=self.tree.heading(col)["text"].split()[0])

    def _on_select(self, event=None) -> None:
        """
        Handle selection of an item in the treeview.

        Args:
            event: Selection event
        """
        selected_items = self.tree.selection()
        if not selected_items:
            self._selected_storage_id = None
            return

        # Get the first selected item
        item = selected_items[0]
        values = self.tree.item(item, "values")

        if values:
            self._selected_storage_id = values[0]  # ID is the first column

    def _on_double_click(self, event=None) -> None:
        """
        Handle double-click on a treeview item.

        Args:
            event: Double-click event
        """
        self._edit_storage()

    def _add_storage(self) -> None:
        """
        Show dialog to add a new storage location.
        """
        # This would typically open a storage location entry dialog
        # For now, display a placeholder message
        self.show_info("Add Storage Location", "Storage location entry dialog would open here.")
        logger.info("Add storage location functionality called")

    def _edit_storage(self) -> None:
        """
        Show dialog to edit the selected storage location.
        """
        if not self._selected_storage_id:
            self.show_warning("Warning", "Please select a storage location to edit.")
            return

        try:
            # Get details of the selected storage location
            location = self.storage_service.get_storage_location(self._selected_storage_id)

            if not location:
                self.show_error("Error", "Selected storage location not found.")
                self.load_data()  # Refresh to ensure view is up-to-date
                return

            # This would typically open a storage location edit dialog
            # For now, display a placeholder message
            self.show_info("Edit Storage Location",
                           f"Edit dialog for storage location '{location.get('name', '')}' would open here.")
            logger.info(f"Edit storage location called for ID: {self._selected_storage_id}")

        except Exception as e:
            error_message = f"Error editing storage location: {str(e)}"
            self.show_error("Edit Error", error_message)
            logger.error(error_message, exc_info=True)

    def _delete_storage(self) -> None:
        """
        Delete the selected storage location after confirmation.
        """
        if not self._selected_storage_id:
            self.show_warning("Warning", "Please select a storage location to delete.")
            return

        # Confirm deletion
        if not messagebox.askyesno("Confirm Deletion",
                                   "Are you sure you want to delete this storage location?\n"
                                   "This action cannot be undone."):
            return

        try:
            # Check if storage contains items
            location = self.storage_service.get_storage_location(self._selected_storage_id)

            if location and location.get("items", []):
                # Warn about deleting non-empty storage
                if not messagebox.askyesno("Warning",
                                           f"This storage location contains {len(location.get('items', []))} items. "
                                           "Deleting it will remove these assignments.\n\n"
                                           "Do you want to continue?",
                                           icon=messagebox.WARNING):
                    return

            # Delete location through service
            result = self.storage_service.delete_storage_location(self._selected_storage_id)

            if result:
                self.show_info("Success", "Storage location deleted successfully!")
                self._selected_storage_id = None
                self.load_data()  # Refresh the view
            else:
                self.show_error("Error", "Failed to delete storage location.")

        except Exception as e:
            error_message = f"Error deleting storage location: {str(e)}"
            self.show_error("Delete Error", error_message)
            logger.error(error_message, exc_info=True)