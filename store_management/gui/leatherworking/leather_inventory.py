# gui/leatherworking/leather_inventory.py
"""
View for managing leather inventory in a leatherworking store management system.
Provides functionality to view, add, edit, and delete leather materials.
"""

import logging
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any, Dict, List, Optional, Tuple, Type

from gui.base_view import BaseView
from gui.leatherworking.leather_dialog import LeatherDetailsDialog
from services.interfaces.material_service import IMaterialService, MaterialType
from services.interfaces.project_service import IProjectService

# Configure logger
logger = logging.getLogger(__name__)


class LeatherInventoryView(BaseView):
    """
    View for displaying and managing leather inventory.

    Provides a tabular interface for viewing leather materials, with functionality
    to add, edit, and delete entries. Includes search and filter capabilities.
    """

    def __init__(self, parent: tk.Widget, app: Any):
        """
        Initialize the Leather Inventory View.

        Args:
            parent (tk.Widget): Parent widget
            app (Any): Application context providing access to services
        """
        super().__init__(parent, app)

        self._material_service = None
        self._project_service = None

        self._search_var = tk.StringVar()
        self._selected_material_id = None

        # Initialize UI components
        self._create_ui()
        self._load_data()

        logger.info("Leather inventory view initialized")

    def get_service(self, service_type: Type) -> Any:
        """Get a service from the application.

        Args:
            service_type (Type): The service interface type to retrieve

        Returns:
            Any: The service instance
        """
        return self.app.get_service(service_type)

    @property
    def material_service(self) -> IMaterialService:
        """
        Lazy-loaded material service property.

        Returns:
            IMaterialService: Material service instance
        """
        if self._material_service is None:
            self._material_service = self.get_service(IMaterialService)
        return self._material_service

    @property
    def project_service(self) -> IProjectService:
        """
        Lazy-loaded project service property.

        Returns:
            IProjectService: Project service instance
        """
        if self._project_service is None:
            self._project_service = self.get_service(IProjectService)
        return self._project_service

    def _create_ui(self) -> None:
        """Create and configure UI components."""
        # Create frame layout
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # Toolbar frame
        toolbar_frame = ttk.Frame(self, padding="5")
        toolbar_frame.grid(row=0, column=0, sticky="ew")

        # Search bar
        ttk.Label(toolbar_frame, text="Search:").pack(side=tk.LEFT, padx=(0, 5))
        search_entry = ttk.Entry(toolbar_frame, textvariable=self._search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=(0, 5))
        search_entry.bind("<Return>", self._on_search)

        ttk.Button(toolbar_frame, text="Search", command=self._on_search).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(toolbar_frame, text="Add Leather", command=self._add_leather).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar_frame, text="Edit", command=self._edit_selected).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar_frame, text="Delete", command=self._delete_selected).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar_frame, text="Refresh", command=self._load_data).pack(side=tk.LEFT, padx=(0, 5))

        # Treeview for data display
        self.tree = ttk.Treeview(self, columns=(
            "id", "name", "leather_type", "quality", "area", "thickness",
            "color", "supplier", "price", "location"
        ), show="headings")

        # Configure column headings
        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="Name")
        self.tree.heading("leather_type", text="Type")
        self.tree.heading("quality", text="Quality")
        self.tree.heading("area", text="Area (ft²)")
        self.tree.heading("thickness", text="Thickness (mm)")
        self.tree.heading("color", text="Color")
        self.tree.heading("supplier", text="Supplier")
        self.tree.heading("price", text="Price ($)")
        self.tree.heading("location", text="Storage Location")

        # Configure column widths
        self.tree.column("id", width=50, stretch=False)
        self.tree.column("name", width=150)
        self.tree.column("leather_type", width=100)
        self.tree.column("quality", width=100)
        self.tree.column("area", width=80, anchor=tk.E)
        self.tree.column("thickness", width=100, anchor=tk.E)
        self.tree.column("color", width=100)
        self.tree.column("supplier", width=120)
        self.tree.column("price", width=80, anchor=tk.E)
        self.tree.column("location", width=120)

        # Setup scrollbars
        y_scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview)
        x_scrollbar = ttk.Scrollbar(self, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)

        # Grid layout
        self.tree.grid(row=1, column=0, sticky="nsew")
        y_scrollbar.grid(row=1, column=1, sticky="ns")
        x_scrollbar.grid(row=2, column=0, sticky="ew")

        # Bind events
        self.tree.bind("<Double-1>", self._on_double_click)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        # Status bar
        self.status_var = tk.StringVar()
        status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=3, column=0, columnspan=2, sticky="ew")

        self.status_var.set("Ready")

    def _load_data(self) -> None:
        """
        Load leather data from the material service and populate the treeview.
        """
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        try:
            # Get leather materials from service
            materials = self.material_service.list_materials(material_type=MaterialType.LEATHER)

            if not materials:
                self.status_var.set("No leather materials found")
                logger.info("No leather materials found")
                return

            # Populate treeview
            for material in materials:
                self.tree.insert("", tk.END, values=(
                    material.get("id", ""),
                    material.get("name", ""),
                    material.get("leather_type", ""),
                    material.get("quality_grade", ""),
                    f"{material.get('area', 0):.2f}",
                    f"{material.get('thickness', 0):.1f}",
                    material.get("color", ""),
                    material.get("supplier_name", ""),
                    f"${material.get('price_per_unit', 0):.2f}",
                    material.get("storage_location", "")
                ))

            # Update status
            self.status_var.set(f"Loaded {len(materials)} leather materials")
            logger.info(f"Loaded {len(materials)} leather materials")

        except Exception as e:
            error_message = f"Error loading leather materials: {str(e)}"
            self.show_error("Data Loading Error", error_message)
            logger.error(error_message, exc_info=True)
            self.status_var.set("Error loading data")

    def _on_search(self, event=None) -> None:
        """
        Handle search functionality.

        Args:
            event: Event triggering the search (optional)
        """
        search_term = self._search_var.get().strip().lower()

        if not search_term:
            self._load_data()
            return

        try:
            # Clear current items
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Get all materials and filter locally
            materials = self.material_service.list_materials(material_type=MaterialType.LEATHER)

            # Filter materials based on search term
            filtered_materials = []
            for material in materials:
                # Check if the search term appears in any of the key fields
                for field in ["name", "leather_type", "color", "supplier_name", "storage_location"]:
                    value = str(material.get(field, "")).lower()
                    if search_term in value:
                        filtered_materials.append(material)
                        break

            # Populate treeview with filtered materials
            for material in filtered_materials:
                self.tree.insert("", tk.END, values=(
                    material.get("id", ""),
                    material.get("name", ""),
                    material.get("leather_type", ""),
                    material.get("quality_grade", ""),
                    f"{material.get('area', 0):.2f}",
                    f"{material.get('thickness', 0):.1f}",
                    material.get("color", ""),
                    material.get("supplier_name", ""),
                    f"${material.get('price_per_unit', 0):.2f}",
                    material.get("storage_location", "")
                ))

            # Update status
            self.status_var.set(f"Found {len(filtered_materials)} leather materials matching '{search_term}'")

        except Exception as e:
            error_message = f"Error searching leather materials: {str(e)}"
            self.show_error("Search Error", error_message)
            logger.error(error_message, exc_info=True)
            self.status_var.set("Error during search")

    def _on_select(self, event=None) -> None:
        """
        Handle selection of an item in the treeview.

        Args:
            event: Selection event
        """
        selected_items = self.tree.selection()
        if not selected_items:
            self._selected_material_id = None
            return

        # Get the first selected item
        item = selected_items[0]
        values = self.tree.item(item, "values")

        if values:
            self._selected_material_id = values[0]  # ID is the first column

    def _on_double_click(self, event=None) -> None:
        """
        Handle double-click on a treeview item.

        Args:
            event: Double-click event
        """
        self._edit_selected()

    def _add_leather(self) -> None:
        """
        Show dialog to add a new leather material.
        """
        dialog = LeatherDetailsDialog(
            self,
            "Add New Leather Material",
            None  # No existing data for a new entry
        )

        if dialog.result:
            try:
                # Add new leather through service
                result = self.material_service.add_material(
                    material_type=MaterialType.LEATHER,
                    **dialog.result
                )

                if result and isinstance(result, dict) and "id" in result:
                    self.show_info("Success", "Leather material added successfully!")
                    self._load_data()  # Refresh the view
                else:
                    self.show_error("Error", "Failed to add leather material.")

            except Exception as e:
                error_message = f"Error adding leather material: {str(e)}"
                self.show_error("Add Error", error_message)
                logger.error(error_message, exc_info=True)

    def _edit_selected(self) -> None:
        """
        Show dialog to edit the selected leather material.
        """
        if not self._selected_material_id:
            self.show_warning("Warning", "Please select a leather material to edit.")
            return

        try:
            # Get details of the selected material
            material = self.material_service.get_material(self._selected_material_id)

            if not material:
                self.show_error("Error", "Selected material not found.")
                self._load_data()  # Refresh to ensure view is up-to-date
                return

            # Open dialog with existing data
            dialog = LeatherDetailsDialog(
                self,
                f"Edit Leather Material: {material.get('name', '')}",
                material
            )

            if dialog.result:
                # Update material through service
                result = self.material_service.update_material(
                    material_id=self._selected_material_id,
                    **dialog.result
                )

                if result:
                    self.show_info("Success", "Leather material updated successfully!")
                    self._load_data()  # Refresh the view
                else:
                    self.show_error("Error", "Failed to update leather material.")

        except Exception as e:
            error_message = f"Error editing leather material: {str(e)}"
            self.show_error("Edit Error", error_message)
            logger.error(error_message, exc_info=True)

    def _delete_selected(self) -> None:
        """
        Delete the selected leather material after confirmation.
        """
        if not self._selected_material_id:
            self.show_warning("Warning", "Please select a leather material to delete.")
            return

        # Confirm deletion
        if not messagebox.askyesno("Confirm Deletion",
                                   "Are you sure you want to delete this leather material?\n"
                                   "This action cannot be undone."):
            return

        try:
            # Check if material is used in any projects
            # This would ideally be handled by the service with a method like:
            # is_material_in_use = self.project_service.is_material_used(self._selected_material_id)

            # Delete material through service
            result = self.material_service.delete_material(self._selected_material_id)

            if result:
                self.show_info("Success", "Leather material deleted successfully!")
                self._selected_material_id = None
                self._load_data()  # Refresh the view
            else:
                self.show_error("Error", "Failed to delete leather material.")

        except Exception as e:
            error_message = f"Error deleting leather material: {str(e)}"
            self.show_error("Delete Error", error_message)
            logger.error(error_message, exc_info=True)