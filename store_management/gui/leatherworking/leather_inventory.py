# gui/leatherworking/leather_inventory.py
"""
Leather inventory view implementation for managing leather materials.
"""
import logging
from typing import Any, Dict, List, Optional, Tuple, Type

import tkinter as tk
import tkinter.messagebox
from tkinter import ttk

from gui.base_view import BaseView
from gui.leatherworking.leather_dialog import LeatherDetailsDialog
from services.interfaces.material_service import IMaterialService, MaterialType
from services.interfaces.project_service import IProjectService


class LeatherInventoryView(BaseView):
    """View for managing leather inventory."""

    def __init__(self, parent: tk.Widget, app: Any):
        """Initialize the Leather Inventory View.

        Args:
            parent (tk.Widget): Parent widget
            app (Any): Application context providing access to services
        """
        super().__init__(parent, app)
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing Leather Inventory View")

        # Set up the layout
        self._setup_ui()

        # Load initial data
        self._load_data()

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

        # Create treeview for leather inventory
        self.tree = ttk.Treeview(
            content,
            columns=("id", "name", "type", "quantity", "price", "grade", "thickness"),
            show="headings",
            selectmode="browse"
        )

        # Configure column headings
        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="Name")
        self.tree.heading("type", text="Type")
        self.tree.heading("quantity", text="Quantity")
        self.tree.heading("price", text="Price")
        self.tree.heading("grade", text="Grade")
        self.tree.heading("thickness", text="Thickness")

        # Configure column widths
        self.tree.column("id", width=50, anchor="center")
        self.tree.column("name", width=150)
        self.tree.column("type", width=100)
        self.tree.column("quantity", width=80, anchor="center")
        self.tree.column("price", width=80, anchor="e")
        self.tree.column("grade", width=80, anchor="center")
        self.tree.column("thickness", width=80, anchor="center")

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
        """Load leather inventory data."""
        try:
            material_service = self.get_service(IMaterialService)

            # Get leather materials (type LEATHER)
            materials = material_service.get_materials(MaterialType.LEATHER)

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
                        material.get("type", "LEATHER"),
                        material.get("quantity", 0),
                        f"${material.get('unit_price', 0):.2f}",
                        material.get("quality_grade", ""),
                        material.get("thickness", "")
                    )
                )

            self.logger.info(f"Loaded {len(materials)} leather materials")

        except Exception as e:
            self.logger.error(f"Error loading leather inventory: {str(e)}")
            self.show_error("Data Load Error", f"Failed to load leather inventory: {str(e)}")

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

            # Search leather materials
            # Note: This assumes the service has a search functionality
            materials = material_service.search_materials(search_text, material_type=MaterialType.LEATHER)

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
                        material.get("type", "LEATHER"),
                        material.get("quantity", 0),
                        f"${material.get('unit_price', 0):.2f}",
                        material.get("quality_grade", ""),
                        material.get("thickness", "")
                    )
                )

            self.logger.info(f"Found {len(materials)} matching leather materials")

        except Exception as e:
            self.logger.error(f"Error searching leather inventory: {str(e)}")
            self.show_error("Search Error", f"Failed to search leather inventory: {str(e)}")

    def on_new(self):
        """Handle creating a new leather material."""
        # Open dialog to create a new leather material
        dialog = LeatherDetailsDialog(self, "Add Leather Material", None)

        if dialog.result:
            try:
                # Set material type to LEATHER
                dialog.result["type"] = MaterialType.LEATHER

                # Add material to inventory
                material_service = self.get_service(IMaterialService)
                material = material_service.create(dialog.result)

                # Refresh view
                self._load_data()

                # Select the new material
                for item in self.tree.get_children():
                    if self.tree.item(item, "values")[0] == str(material.get("id")):
                        self.tree.selection_set(item)
                        self.tree.see(item)
                        break

                self.logger.info(f"Created new leather material: {material.get('name')}")

            except Exception as e:
                self.logger.error(f"Error creating leather material: {str(e)}")
                self.show_error("Creation Error", f"Failed to create leather material: {str(e)}")

    def on_edit(self, event=None):
        """Handle editing an existing leather material."""
        selection = self.tree.selection()
        if not selection:
            self.show_info("No Selection", "Please select a leather material to edit.")
            return

        # Get selected item ID
        item_id = self.tree.item(selection[0], "values")[0]

        try:
            # Get material details
            material_service = self.get_service(IMaterialService)
            material = material_service.get_by_id(int(item_id))

            if not material:
                self.show_error("Not Found", f"Leather material with ID {item_id} not found.")
                return

            # Open dialog with existing data
            dialog = LeatherDetailsDialog(self, "Edit Leather Material", material)

            if dialog.result:
                # Update material
                updated_material = material_service.update(int(item_id), dialog.result)

                # Refresh view
                self._load_data()

                # Re-select the edited material
                for item in self.tree.get_children():
                    if self.tree.item(item, "values")[0] == str(updated_material.get("id")):
                        self.tree.selection_set(item)
                        self.tree.see(item)
                        break

                self.logger.info(f"Updated leather material: {updated_material.get('name')}")

        except Exception as e:
            self.logger.error(f"Error editing leather material: {str(e)}")
            self.show_error("Edit Error", f"Failed to edit leather material: {str(e)}")

    def on_delete(self):
        """Handle deleting a leather material."""
        selection = self.tree.selection()
        if not selection:
            self.show_info("No Selection", "Please select a leather material to delete.")
            return

        # Get selected item ID
        item_id = self.tree.item(selection[0], "values")[0]
        item_name = self.tree.item(selection[0], "values")[1]

        # Confirm deletion
        if not self.confirm("Confirm Delete", f"Are you sure you want to delete the leather material '{item_name}'?"):
            return

        try:
            # Delete material
            material_service = self.get_service(IMaterialService)
            success = material_service.delete(int(item_id))

            if success:
                # Refresh view
                self._load_data()
                self.logger.info(f"Deleted leather material: {item_name}")
            else:
                self.show_error("Delete Failed", f"Failed to delete leather material '{item_name}'.")

        except Exception as e:
            self.logger.error(f"Error deleting leather material: {str(e)}")
            self.show_error("Delete Error", f"Failed to delete leather material: {str(e)}")

    def on_refresh(self):
        """Refresh the inventory view."""
        self._load_data()