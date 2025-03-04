# gui/inventory/hardware_inventory.py
"""
Hardware inventory view implementation for managing hardware items.
"""
import logging
from typing import Any, Dict, List, Optional, Tuple, Type

import tkinter as tk
import tkinter.messagebox
from tkinter import ttk

from gui.base_view import BaseView
from services.interfaces.material_service import IMaterialService, MaterialType


class HardwareInventoryView(BaseView):
    """View for managing hardware inventory."""

    def __init__(self, parent: tk.Widget, app: Any):
        """Initialize the Hardware Inventory View.

        Args:
            parent (tk.Widget): Parent widget
            app (Any): Application context providing access to services
        """
        super().__init__(parent, app)
        self._logger = logging.getLogger(self.__class__.__module__)
        self._logger.info("Initializing Hardware Inventory View")

        # Set up the layout
        self._setup_ui()

        # Load initial data
        self._load_data()

    def debug_model_registration(self):
        """
        Debug method to investigate model registration issues.
        """
        try:
            from database.models.base import Base

            # Get registered models
            registered_models = Base.debug_registered_models()

            # Log each registered model
            for model_name in registered_models:
                self._logger.info(f"Registered Model: {model_name}")

        except Exception as e:
            self._logger.error(f"Error debugging model registration: {str(e)}")

    def _setup_ui(self):
        """Set up the UI components."""
        # Main layout
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=0)  # Toolbar
        self.rowconfigure(1, weight=1)  # Content

        # Create toolbar
        toolbar = ttk.Frame(self, padding=(5, 5, 5, 5))
        toolbar.grid(row=0, column=0, sticky="ew")

        ttk.Button(toolbar, text="New", command=self.on_new).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="Edit", command=self.on_edit).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Delete", command=self.on_delete).pack(side=tk.LEFT, padx=5)
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=10, fill=tk.Y)
        ttk.Button(toolbar, text="Refresh", command=self.on_refresh).pack(side=tk.LEFT, padx=5)

        # Search frame (right side of toolbar)
        search_frame = ttk.Frame(toolbar)
        search_frame.pack(side=tk.RIGHT)

        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=20)
        search_entry.pack(side=tk.LEFT, padx=(0, 5))
        search_entry.bind("<Return>", self._on_search)

        ttk.Button(search_frame, text="Search", command=self._on_search).pack(side=tk.LEFT)

        # Create content area
        content = ttk.Frame(self, padding=5)
        content.grid(row=1, column=0, sticky="nsew")
        content.columnconfigure(0, weight=1)
        content.rowconfigure(0, weight=1)

        # Create treeview for hardware inventory
        self.tree = ttk.Treeview(
            content,
            columns=("id", "name", "type", "material", "finish", "quantity", "price"),
            show="headings",
            selectmode="browse"
        )

        # Configure column headings
        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="Name")
        self.tree.heading("type", text="Type")
        self.tree.heading("material", text="Material")
        self.tree.heading("finish", text="Finish")
        self.tree.heading("quantity", text="Quantity")
        self.tree.heading("price", text="Price")

        # Configure column widths
        self.tree.column("id", width=50, anchor="center")
        self.tree.column("name", width=150)
        self.tree.column("type", width=100)
        self.tree.column("material", width=100)
        self.tree.column("finish", width=100)
        self.tree.column("quantity", width=80, anchor="center")
        self.tree.column("price", width=80, anchor="e")

        # Add scrollbars
        vsb = ttk.Scrollbar(content, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(content, orient="horizontal", command=self.tree.xview)

        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # Grid layout for treeview and scrollbars
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        # Bind events
        self.tree.bind("<Double-1>", self.on_edit)

    def _load_data(self):
        """Load hardware inventory data."""
        try:
            material_service = self.get_service(IMaterialService)

            # Get hardware materials (type HARDWARE)
            materials = material_service.get_materials(MaterialType.HARDWARE)

            # Clear existing items
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Add materials to the treeview
            for material in materials:
                self.tree.insert(
                    "",
                    "end",
                    values=(
                        material.get("id", ""),
                        material.get("name", ""),
                        material.get("hardware_type", ""),
                        material.get("hardware_material", ""),
                        material.get("finish", ""),
                        material.get("quantity", 0),
                        f"${material.get('unit_price', 0):.2f}"
                    )
                )

            self._logger.info(f"Loaded {len(materials)} hardware items")

        except Exception as e:
            self._logger.error(f"Error loading hardware inventory: {str(e)}")
            self.show_error("Data Load Error", f"Failed to load hardware inventory: {str(e)}")

    def _on_search(self, event=None):
        """Handle search functionality.

        Args:
            event: The event that triggered the search (optional)
        """
        search_text = self.search_var.get().strip()
        if not search_text:
            # If search is empty, reload all data
            self._load_data()
            return

        try:
            material_service = self.get_service(IMaterialService)

            # Search hardware materials
            # Note: This assumes the service has a search functionality
            materials = material_service.search_materials(search_text, material_type=MaterialType.HARDWARE)

            # Clear existing items
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Add materials to the treeview
            for material in materials:
                self.tree.insert(
                    "",
                    "end",
                    values=(
                        material.get("id", ""),
                        material.get("name", ""),
                        material.get("hardware_type", ""),
                        material.get("hardware_material", ""),
                        material.get("finish", ""),
                        material.get("quantity", 0),
                        f"${material.get('unit_price', 0):.2f}"
                    )
                )

            self._logger.info(f"Found {len(materials)} matching hardware items")

        except Exception as e:
            self._logger.error(f"Error searching hardware inventory: {str(e)}")
            self.show_error("Search Error", f"Failed to search hardware inventory: {str(e)}")

    def on_new(self):
        """Handle creating a new hardware item."""
        self._logger.info("Create new hardware item")
        # This would be implemented to open a dialog for creating a new hardware item
        self.show_info("New Hardware", "Hardware creation not implemented yet")

    def on_edit(self, event=None):
        """Handle editing an existing hardware item."""
        selection = self.tree.selection()
        if not selection:
            self.show_info("No Selection", "Please select a hardware item to edit.")
            return

        # Get selected item ID
        item_id = self.tree.item(selection[0], "values")[0]
        self._logger.info(f"Edit hardware ID: {item_id}")

        # This would be implemented to open a dialog for editing a hardware item
        self.show_info("Edit Hardware", "Hardware editing not implemented yet")

    def on_delete(self):
        """Handle deleting a hardware item."""
        selection = self.tree.selection()
        if not selection:
            self.show_info("No Selection", "Please select a hardware item to delete.")
            return

        # Get selected item ID and name
        values = self.tree.item(selection[0], "values")
        item_id = values[0]
        item_name = values[1]

        # Confirm deletion
        confirm = self.show_message(
            f"Are you sure you want to delete the hardware item '{item_name}'?",
            message_type="question"
        )

        if confirm:
            try:
                material_service = self.get_service(IMaterialService)
                success = material_service.delete(int(item_id))

                if success:
                    self._logger.info(f"Deleted hardware item ID: {item_id}, Name: {item_name}")
                    self.show_info("Success", f"Hardware item '{item_name}' deleted successfully.")
                    self._load_data()  # Refresh the view
                else:
                    self.show_error("Delete Failed", f"Failed to delete hardware item '{item_name}'.")
            except Exception as e:
                self._logger.error(f"Error deleting hardware item: {str(e)}")
                self.show_error("Delete Error", f"Failed to delete hardware item: {str(e)}")

    def on_refresh(self):
        """Refresh the inventory view."""
        self._load_data()