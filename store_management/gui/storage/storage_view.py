# gui/storage/storage_view.py
import logging
import os
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any, Dict, List, Optional, Tuple, Type, Union

from gui.base_view import BaseView
from services.interfaces.storage_service import IStorageService


class StorageView(BaseView):
    """
    View for managing storage locations in the leatherworking store.
    Provides functionality to create, edit, and delete storage locations,
    and to assign products to storage locations.
    """

    def __init__(self, parent: ttk.Frame, app: tk.Tk):
        """
        Initialize the storage view.

        Args:
            parent (ttk.Frame): Parent widget.
            app (tk.Tk): Application instance.
        """
        super().__init__(parent, app)
        self._setup_ui()
        self.load_data()

    def _create_toolbar(self, parent):
        """
        Create toolbar with action buttons.

        Args:
            parent: Parent widget for the toolbar
        """
        toolbar = ttk.Frame(parent)
        toolbar.pack(fill=tk.X, padx=5, pady=5)

        # Add toolbar buttons
        self.btn_new = ttk.Button(toolbar, text="New", command=self._on_new)
        self.btn_new.pack(side=tk.LEFT, padx=2)

        self.btn_edit = ttk.Button(toolbar, text="Edit", command=self._on_edit)
        self.btn_edit.pack(side=tk.LEFT, padx=2)

        self.btn_delete = ttk.Button(toolbar, text="Delete", command=self._on_delete)
        self.btn_delete.pack(side=tk.LEFT, padx=2)

        # Add search box
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self._on_search)
        ttk.Label(toolbar, text="Search:").pack(side=tk.LEFT, padx=(10, 2))
        self.search_entry = ttk.Entry(toolbar, textvariable=self.search_var, width=20)
        self.search_entry.pack(side=tk.LEFT, padx=2)

        # Add refresh button
        self.btn_refresh = ttk.Button(toolbar, text="Refresh", command=self.load_data)
        self.btn_refresh.pack(side=tk.RIGHT, padx=2)

        return toolbar

    def _create_treeview(self, parent):
        """
        Create treeview for displaying storage locations.

        Args:
            parent: Parent widget for the treeview
        """
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create treeview with scrollbar
        self.tree = ttk.Treeview(frame, columns=("id", "name", "type", "capacity", "location"))
        self.tree.heading("#0", text="")
        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="Name")
        self.tree.heading("type", text="Type")
        self.tree.heading("capacity", text="Capacity")
        self.tree.heading("location", text="Location")

        self.tree.column("#0", width=0, stretch=tk.NO)
        self.tree.column("id", width=50, anchor=tk.CENTER)
        self.tree.column("name", width=150, anchor=tk.W)
        self.tree.column("type", width=100, anchor=tk.W)
        self.tree.column("capacity", width=80, anchor=tk.CENTER)
        self.tree.column("location", width=150, anchor=tk.W)

        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind events
        self.tree.bind("<Double-1>", self._on_double_click)

        return frame

    def _create_details_frame(self, parent):
        """
        Create frame for storage location details.

        Args:
            parent: Parent widget for the details frame
        """
        frame = ttk.LabelFrame(parent, text="Storage Details")
        frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Form for editing storage details
        form_frame = ttk.Frame(frame)
        form_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Storage ID (hidden)
        self.storage_id_var = tk.StringVar()

        # Storage Name
        ttk.Label(form_frame, text="Name:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.name_var = tk.StringVar()
        self.name_entry = ttk.Entry(form_frame, textvariable=self.name_var, width=30)
        self.name_entry.grid(row=0, column=1, sticky=tk.W + tk.E, pady=5)

        # Storage Type
        ttk.Label(form_frame, text="Type:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.type_var = tk.StringVar()
        self.type_combo = ttk.Combobox(form_frame, textvariable=self.type_var, width=28)
        self.type_combo["values"] = ("SHELF", "BIN", "DRAWER", "CABINET", "RACK", "BOX", "WAREHOUSE", "OTHER")
        self.type_combo.grid(row=1, column=1, sticky=tk.W + tk.E, pady=5)

        # Capacity
        ttk.Label(form_frame, text="Capacity:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.capacity_var = tk.StringVar()
        self.capacity_entry = ttk.Entry(form_frame, textvariable=self.capacity_var, width=30)
        self.capacity_entry.grid(row=2, column=1, sticky=tk.W + tk.E, pady=5)

        # Location
        ttk.Label(form_frame, text="Location:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.location_var = tk.StringVar()
        self.location_entry = ttk.Entry(form_frame, textvariable=self.location_var, width=30)
        self.location_entry.grid(row=3, column=1, sticky=tk.W + tk.E, pady=5)

        # Description
        ttk.Label(form_frame, text="Description:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.description_var = tk.StringVar()
        self.description_entry = ttk.Entry(form_frame, textvariable=self.description_var, width=30)
        self.description_entry.grid(row=4, column=1, sticky=tk.W + tk.E, pady=5)

        # Note
        ttk.Label(form_frame, text="Note:").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.note_var = tk.StringVar()
        self.note_entry = ttk.Entry(form_frame, textvariable=self.note_var, width=30)
        self.note_entry.grid(row=5, column=1, sticky=tk.W + tk.E, pady=5)

        # Action buttons
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=6, column=0, columnspan=2, pady=10)

        self.save_btn = ttk.Button(button_frame, text="Save", command=self._on_save)
        self.save_btn.pack(side=tk.LEFT, padx=5)

        self.cancel_btn = ttk.Button(button_frame, text="Cancel", command=self._clear_form)
        self.cancel_btn.pack(side=tk.LEFT, padx=5)

        # Configure grid weights
        form_frame.columnconfigure(1, weight=1)

        # Initially disable form
        self._toggle_form(False)

        return frame

    def _setup_ui(self):
        """Set up the UI components."""
        # Main layout frame
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Create toolbar
        self._create_toolbar(main_frame)

        # Split view with treeview and details
        split_frame = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        split_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create treeview for storage locations
        tree_frame = self._create_treeview(split_frame)

        # Create details frame
        details_frame = self._create_details_frame(split_frame)

        # Add both frames to the paned window
        split_frame.add(tree_frame, weight=3)
        split_frame.add(details_frame, weight=2)

    def _toggle_form(self, enable=True):
        """
        Enable or disable form fields.

        Args:
            enable (bool): Whether to enable the form
        """
        state = "normal" if enable else "disabled"
        self.name_entry.configure(state=state)
        self.type_combo.configure(state=state)
        self.capacity_entry.configure(state=state)
        self.location_entry.configure(state=state)
        self.description_entry.configure(state=state)
        self.note_entry.configure(state=state)
        self.save_btn.configure(state=state)
        self.cancel_btn.configure(state=state)

    def get_service(self, service_type: Type) -> Any:
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
            if hasattr(self.app, 'get_service'):
                return self.app.get_service(service_type)
            raise ValueError(f"Application does not support service retrieval")
        except Exception as e:
            logging.error(f"Failed to get service {service_type.__name__}: {str(e)}")
            raise ValueError(f"Service retrieval failed: {str(e)}")

    def storage_service(self) -> IStorageService:
        """
        Get the storage service.

        Returns:
            IStorageService: The storage service instance
        """
        try:
            from services.interfaces.storage_service import IStorageService
            return self.get_service(IStorageService)
        except Exception as e:
            logging.error(f"Failed to get storage service: {str(e)}")
            messagebox.showerror("Service Error", f"Failed to access storage service: {str(e)}")
            raise

    def load_data(self):
        """Load storage locations from the service."""
        try:
            self.tree.delete(*self.tree.get_children())
            storage_service = self.storage_service()

            if self.set_status:
                self.set_status("Loading storage locations...")

            locations = storage_service.get_all_storage_locations()

            for location in locations:
                self.tree.insert("", tk.END, values=(
                    location.get("id", ""),
                    location.get("name", ""),
                    location.get("type", ""),
                    location.get("capacity", ""),
                    location.get("location", "")
                ))

            if self.set_status:
                self.set_status(f"Loaded {len(locations)} storage locations")

        except Exception as e:
            logging.error(f"Error loading storage locations: {str(e)}")
            messagebox.showerror("Error", f"Failed to load storage locations: {str(e)}")
            if self.set_status:
                self.set_status("Error loading storage locations")

    def _on_new(self):
        """Handle adding a new storage location."""
        self.storage_id_var.set("")
        self.name_var.set("")
        self.type_var.set("")
        self.capacity_var.set("")
        self.location_var.set("")
        self.description_var.set("")
        self.note_var.set("")
        self._toggle_form(True)

    def _on_edit(self):
        """Handle editing the selected storage location."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a storage location to edit.")
            return

        try:
            item_id = self.tree.item(selected[0], "values")[0]
            storage_service = self.storage_service()
            location = storage_service.get_storage_location_by_id(item_id)

            if location:
                self.storage_id_var.set(location.get("id", ""))
                self.name_var.set(location.get("name", ""))
                self.type_var.set(location.get("type", ""))
                self.capacity_var.set(location.get("capacity", ""))
                self.location_var.set(location.get("location", ""))
                self.description_var.set(location.get("description", ""))
                self.note_var.set(location.get("note", ""))
                self._toggle_form(True)
            else:
                messagebox.showerror("Error", f"Storage location with ID {item_id} not found.")
        except Exception as e:
            logging.error(f"Error loading storage location details: {str(e)}")
            messagebox.showerror("Error", f"Failed to load storage location details: {str(e)}")

    def _on_delete(self):
        """Handle deleting a storage location."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a storage location to delete.")
            return

        item_id = self.tree.item(selected[0], "values")[0]
        name = self.tree.item(selected[0], "values")[1]

        confirm = messagebox.askyesno("Confirm Delete",
                                      f"Are you sure you want to delete the storage location '{name}'?")
        if not confirm:
            return

        try:
            storage_service = self.storage_service()
            storage_service.delete_storage_location(item_id)
            self.tree.delete(selected[0])
            self._clear_form()
            if self.set_status:
                self.set_status(f"Deleted storage location '{name}'")
        except Exception as e:
            logging.error(f"Error deleting storage location: {str(e)}")
            messagebox.showerror("Error", f"Failed to delete storage location: {str(e)}")

    def _on_save(self):
        """Handle saving storage location details."""
        try:
            storage_service = self.storage_service()

            # Prepare data
            data = {
                "name": self.name_var.get(),
                "type": self.type_var.get(),
                "capacity": self.capacity_var.get(),
                "location": self.location_var.get(),
                "description": self.description_var.get(),
                "note": self.note_var.get()
            }

            storage_id = self.storage_id_var.get()

            # Update or create
            if storage_id:
                data["id"] = storage_id
                storage_service.update_storage_location(data)
                if self.set_status:
                    self.set_status(f"Updated storage location '{data['name']}'")
            else:
                result = storage_service.create_storage_location(data)
                storage_id = result.get("id", "")
                if self.set_status:
                    self.set_status(f"Created storage location '{data['name']}'")

            # Refresh data
            self.load_data()
            self._clear_form()

        except Exception as e:
            logging.error(f"Error saving storage location: {str(e)}")
            messagebox.showerror("Error", f"Failed to save storage location: {str(e)}")

    def _clear_form(self):
        """Clear the form and disable editing."""
        self.storage_id_var.set("")
        self.name_var.set("")
        self.type_var.set("")
        self.capacity_var.set("")
        self.location_var.set("")
        self.description_var.set("")
        self.note_var.set("")
        self._toggle_form(False)

    def _on_double_click(self, event):
        """Handle double-click on a storage location."""
        self._on_edit()

    def _on_search(self, event=None):
        """Handle search operation."""
        search_text = self.search_var.get().lower()
        if not search_text:
            self.load_data()
            return

        try:
            self.tree.delete(*self.tree.get_children())
            storage_service = self.storage_service()

            # Get all locations and filter locally
            all_locations = storage_service.get_all_storage_locations()
            filtered = []

            for location in all_locations:
                # Search in name, type, and location fields
                if any(search_text in str(location.get(field, "")).lower()
                       for field in ["name", "type", "location"]):
                    filtered.append(location)

            # Update tree
            for location in filtered:
                self.tree.insert("", tk.END, values=(
                    location.get("id", ""),
                    location.get("name", ""),
                    location.get("type", ""),
                    location.get("capacity", ""),
                    location.get("location", "")
                ))

            if self.set_status:
                self.set_status(f"Found {len(filtered)} matching storage locations")

        except Exception as e:
            logging.error(f"Error searching storage locations: {str(e)}")
            messagebox.showerror("Error", f"Failed to search storage locations: {str(e)}")

    def set_status(self, message: str) -> None:
        """
        Set a status message in the status bar.

        Args:
            message (str): The message to display in the status bar
        """
        try:
            # Try to update status through the main application
            if hasattr(self, 'app') and hasattr(self.app, 'set_status'):
                self.app.set_status(message)
            # Fallback to logger
            else:
                logging.info(f"Status update: {message}")
        except Exception as e:
            # Log any errors that occur during status update
            logging.error(f"Error updating status: {e}")