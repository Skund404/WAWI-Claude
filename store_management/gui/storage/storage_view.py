# gui/storage/storage_view.py

import logging
import os
import sqlite3
from typing import Any, Dict, List, Optional, Tuple, Type

import tkinter as tk
from tkinter import messagebox, ttk

from gui.base_view import BaseView
from services.interfaces.storage_service import IStorageService


class StorageView(BaseView):
    """
    View for managing storage locations in the leatherworking store.
    Allows viewing, adding, editing, and deleting storage locations.
    """

    def __init__(self, parent: ttk.Frame, app: tk.Tk):
        """
        Initialize the storage view.

        Args:
            parent (ttk.Frame): Parent widget.
            app (tk.Tk): Application instance.
        """
        super().__init__(parent, app)

        # Store reference to app for service access
        self.app = app  # Use consistent naming as in other views

        # Set up UI elements
        self._create_toolbar(self)
        self._create_treeview(self)
        self._create_details_frame(self)

        # Load initial data
        self.load_data()

        logging.info("Storage view initialized")

    def _create_toolbar(self, parent):
        """
        Create toolbar with action buttons.

        Args:
            parent: Parent widget for the toolbar
        """
        toolbar_frame = ttk.Frame(parent)
        toolbar_frame.pack(fill=tk.X, padx=5, pady=5)

        # Add New button
        btn_new = ttk.Button(toolbar_frame, text="New Location", command=self._on_new)
        btn_new.pack(side=tk.LEFT, padx=(0, 5))

        # Add Edit button
        btn_edit = ttk.Button(toolbar_frame, text="Edit", command=self._on_edit)
        btn_edit.pack(side=tk.LEFT, padx=5)

        # Add Delete button
        btn_delete = ttk.Button(toolbar_frame, text="Delete", command=self._on_delete)
        btn_delete.pack(side=tk.LEFT, padx=5)

        # Add Refresh button
        btn_refresh = ttk.Button(toolbar_frame, text="Refresh", command=self.load_data)
        btn_refresh.pack(side=tk.LEFT, padx=5)

        # Add Search field
        self.search_var = tk.StringVar()
        ttk.Label(toolbar_frame, text="Search:").pack(side=tk.LEFT, padx=(20, 5))
        self.search_entry = ttk.Entry(toolbar_frame, textvariable=self.search_var, width=20)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        self.search_entry.bind("<Return>", self._on_search)

        # Add Search button
        btn_search = ttk.Button(toolbar_frame, text="Search", command=self._on_search)
        btn_search.pack(side=tk.LEFT, padx=5)

    def _create_treeview(self, parent):
        """
        Create treeview for displaying storage locations.

        Args:
            parent: Parent widget for the treeview
        """
        # Create frame for treeview with scrollbar
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create scrollbar
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Define columns
        columns = ("id", "name", "location_type", "capacity", "description")

        # Create treeview
        self.tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            yscrollcommand=scrollbar.set
        )

        # Set column headings and widths
        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="Name")
        self.tree.heading("location_type", text="Type")
        self.tree.heading("capacity", text="Capacity")
        self.tree.heading("description", text="Description")

        self.tree.column("id", width=50, anchor=tk.CENTER)
        self.tree.column("name", width=150)
        self.tree.column("location_type", width=100)
        self.tree.column("capacity", width=80, anchor=tk.CENTER)
        self.tree.column("description", width=300)

        # Pack treeview and connect scrollbar
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.tree.yview)

        # Bind double click event
        self.tree.bind("<Double-1>", self._on_double_click)

    def _create_details_frame(self, parent):
        """
        Create frame for storage location details.

        Args:
            parent: Parent widget for the details frame
        """
        details_frame = ttk.LabelFrame(parent, text="Storage Location Details")
        details_frame.pack(fill=tk.X, padx=5, pady=5)

        # Create form fields
        form_frame = ttk.Frame(details_frame)
        form_frame.pack(fill=tk.X, padx=5, pady=5)

        # Create a 2-column grid layout
        form_frame.columnconfigure(0, weight=0)  # Label column
        form_frame.columnconfigure(1, weight=1)  # Entry column

        # Name field
        ttk.Label(form_frame, text="Name:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.name_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.name_var).grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)

        # Type field
        ttk.Label(form_frame, text="Type:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.type_var = tk.StringVar()
        type_combo = ttk.Combobox(form_frame, textvariable=self.type_var, state="readonly")
        type_combo["values"] = ("SHELF", "BIN", "DRAWER", "CABINET", "RACK", "BOX", "OTHER")
        type_combo.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)

        # Capacity field
        ttk.Label(form_frame, text="Capacity:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.capacity_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.capacity_var).grid(row=2, column=1, sticky=tk.EW, padx=5, pady=5)

        # Description field
        ttk.Label(form_frame, text="Description:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.description_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.description_var).grid(row=3, column=1, sticky=tk.EW, padx=5, pady=5)

        # Button frame
        button_frame = ttk.Frame(details_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)

        # Save button
        self.save_button = ttk.Button(button_frame, text="Save", command=self._on_save)
        self.save_button.pack(side=tk.LEFT, padx=5)

        # Cancel button
        self.cancel_button = ttk.Button(button_frame, text="Cancel", command=self._clear_form)
        self.cancel_button.pack(side=tk.LEFT, padx=5)

        # Initially disable the form until Edit or New is clicked
        self._toggle_form(False)

    def _toggle_form(self, enable=True):
        """
        Enable or disable form fields.

        Args:
            enable (bool): Whether to enable the form
        """
        state = "normal" if enable else "disabled"
        for widget in self.winfo_children():
            if isinstance(widget, ttk.LabelFrame):  # This is our details frame
                for frame in widget.winfo_children():
                    if isinstance(frame, ttk.Frame):
                        for child in frame.winfo_children():
                            if isinstance(child, (ttk.Entry, ttk.Combobox)):
                                child.config(state=state)

        self.save_button.config(state=state)
        self.cancel_button.config(state=state)

    def get_service(self, service_type: Type):
        """
        Get a service from the application's dependency container.

        Args:
            service_type (Type): The type of service to retrieve

        Returns:
            Any: The requested service instance

        Raises:
            ValueError: If service retrieval fails
        """
        try:
            return self.app.get_service(service_type)
        except Exception as e:
            logging.error(f"Failed to get service {service_type}: {e}")
            raise ValueError(f"Service {service_type} not available")

    @property
    def storage_service(self):
        """
        Get the storage service.

        Returns:
            IStorageService: The storage service instance
        """
        if not hasattr(self, "_storage_service"):
            self._storage_service = self.get_service(IStorageService)
        return self._storage_service

    def load_data(self):
        """Load storage locations from the service."""
        try:
            # Clear existing items
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Get locations from service
            storage_locations = self.storage_service.get_all_storage_locations()

            # Populate treeview
            for location in storage_locations:
                self.tree.insert(
                    "",
                    tk.END,
                    values=(
                        location["id"],
                        location["name"],
                        location["location_type"],
                        location["capacity"],
                        location["description"]
                    )
                )

            self.set_status(f"Loaded {len(storage_locations)} storage locations")
        except Exception as e:
            logging.error(f"Error loading storage locations: {e}")
            messagebox.showerror("Error", f"Failed to load storage locations: {e}")

    def _on_new(self):
        """Handle adding a new storage location."""
        self._clear_form()
        self._toggle_form(True)
        self.set_status("Adding new storage location...")

    def _on_edit(self):
        """Handle editing the selected storage location."""
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("Information", "Please select a storage location to edit.")
            return

        item = self.tree.item(selection[0])
        values = item["values"]

        # Populate form with selected item's data
        self.selected_id = values[0]
        self.name_var.set(values[1])
        self.type_var.set(values[2])
        self.capacity_var.set(values[3])
        self.description_var.set(values[4])

        self._toggle_form(True)
        self.set_status(f"Editing storage location {values[1]}")

    def _on_delete(self):
        """Handle deleting the selected storage location."""
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("Information", "Please select a storage location to delete.")
            return

        item = self.tree.item(selection[0])
        location_id = item["values"][0]
        name = item["values"][1]

        # Confirm deletion
        if messagebox.askyesno("Confirm", f"Are you sure you want to delete '{name}'?"):
            try:
                self.storage_service.delete_storage_location(location_id)
                self.tree.delete(selection[0])
                self.set_status(f"Deleted storage location {name}")
            except Exception as e:
                logging.error(f"Error deleting storage location: {e}")
                messagebox.showerror("Error", f"Failed to delete storage location: {e}")

    def _on_save(self):
        """Handle saving storage location details."""
        try:
            # Get data from form
            data = {
                "name": self.name_var.get(),
                "location_type": self.type_var.get(),
                "capacity": int(self.capacity_var.get()) if self.capacity_var.get().isdigit() else 0,
                "description": self.description_var.get()
            }

            # Validate data
            if not data["name"]:
                messagebox.showwarning("Validation Error", "Name is required.")
                return

            if not data["location_type"]:
                messagebox.showwarning("Validation Error", "Type is required.")
                return

            # Determine if it's an update or create operation
            if hasattr(self, 'selected_id'):
                # Update existing location
                data["id"] = self.selected_id
                self.storage_service.update_storage_location(data)
                message = f"Updated storage location {data['name']}"
            else:
                # Create new location
                new_id = self.storage_service.create_storage_location(data)
                data["id"] = new_id
                message = f"Created new storage location {data['name']}"

            # Refresh the data
            self.load_data()
            self._clear_form()
            self._toggle_form(False)
            self.set_status(message)

        except Exception as e:
            logging.error(f"Error saving storage location: {e}")
            messagebox.showerror("Error", f"Failed to save storage location: {e}")

    def _clear_form(self):
        """Clear the form and disable editing."""
        self.name_var.set("")
        self.type_var.set("")
        self.capacity_var.set("")
        self.description_var.set("")

        if hasattr(self, 'selected_id'):
            delattr(self, 'selected_id')

        self._toggle_form(False)

    def _on_double_click(self, event):
        """Handle double-click on a storage location."""
        self._on_edit()

    def _on_search(self, event=None):
        """Handle search operation."""
        search_text = self.search_var.get().strip().lower()
        if not search_text:
            self.load_data()  # Reset to full list
            return

        try:
            # Get all locations and filter locally
            storage_locations = self.storage_service.get_all_storage_locations()
            filtered_locations = []

            for location in storage_locations:
                # Check if search text appears in any field
                if (search_text in str(location["id"]).lower() or
                        search_text in location["name"].lower() or
                        search_text in location["location_type"].lower() or
                        search_text in str(location["capacity"]).lower() or
                        (location["description"] and search_text in location["description"].lower())):
                    filtered_locations.append(location)

            # Clear existing items
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Populate treeview with filtered results
            for location in filtered_locations:
                self.tree.insert(
                    "",
                    tk.END,
                    values=(
                        location["id"],
                        location["name"],
                        location["location_type"],
                        location["capacity"],
                        location["description"]
                    )
                )

            self.set_status(f"Found {len(filtered_locations)} matching storage locations")
        except Exception as e:
            logging.error(f"Error searching storage locations: {e}")
            messagebox.showerror("Error", f"Failed to search storage locations: {e}")