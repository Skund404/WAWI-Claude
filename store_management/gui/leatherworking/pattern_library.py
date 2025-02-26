# gui/leatherworking/pattern_library.py
"""
View for managing pattern library in a leatherworking store management system.
Provides functionality to view, add, edit, and delete patterns for leather projects.
"""

import logging
import tkinter as tk
from tkinter import filedialog
import tkinter.ttk as ttk
from typing import Any, Dict, List, Optional, Type

from gui.base_view import BaseView
from services.interfaces.material_service import IMaterialService
from services.interfaces.project_service import IProjectService

# Configure logger
logger = logging.getLogger(__name__)


class PatternLibrary(BaseView):
    """
    View for displaying and managing pattern library.

    Provides a tabular interface for viewing leatherworking patterns, with functionality
    to add, edit, and delete entries. Includes import/export capabilities.
    """

    def __init__(self, parent: tk.Widget, app: Any):
        """
        Initialize the Pattern Library view.

        Args:
            parent (tk.Widget): Parent widget
            app (Any): Application controller for managing interactions
        """
        super().__init__(parent, app)

        self._material_service = None
        self._project_service = None
        self._selected_pattern_id = None

        # Initialize UI components
        self._create_ui()
        self._load_data()

        logger.info("Pattern library view initialized")

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
        # Set up container frame
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # Create toolbar
        toolbar_frame = ttk.Frame(self, padding=5)
        toolbar_frame.grid(row=0, column=0, sticky="ew")

        # Add toolbar buttons
        ttk.Button(toolbar_frame, text="Add Pattern", command=self._add_pattern).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar_frame, text="Edit Pattern", command=self._edit_pattern).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar_frame, text="Delete Pattern", command=self._delete_pattern).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar_frame, text="View Details", command=self._view_pattern_details).pack(side=tk.LEFT, padx=2)
        ttk.Separator(toolbar_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)
        ttk.Button(toolbar_frame, text="Import Pattern", command=self._import_pattern).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar_frame, text="Export Pattern", command=self._export_pattern).pack(side=tk.LEFT, padx=2)

        # Add search bar
        ttk.Label(toolbar_frame, text="Search:").pack(side=tk.LEFT, padx=(10, 2))
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(toolbar_frame, textvariable=self.search_var, width=20)
        search_entry.pack(side=tk.LEFT, padx=2)
        search_entry.bind("<Return>", self._search_patterns)
        ttk.Button(toolbar_frame, text="Search", command=self._search_patterns).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar_frame, text="Reset", command=self._reset_search).pack(side=tk.LEFT, padx=2)

        # Create pattern categories sidebar
        left_panel = ttk.Frame(self, padding=5, relief="groove", borderwidth=1)
        left_panel.grid(row=1, column=0, sticky="nsw", padx=(0, 5))

        ttk.Label(left_panel, text="Pattern Categories", font=("", 10, "bold")).pack(anchor="w", pady=(0, 5))

        self.category_tree = ttk.Treeview(left_panel, columns=("category",), show="tree", height=15)
        self.category_tree.pack(fill=tk.Y, expand=True)

        # Add default categories
        self.category_tree.insert("", "end", "wallets", text="Wallets")
        self.category_tree.insert("", "end", "bags", text="Bags")
        self.category_tree.insert("", "end", "belts", text="Belts")
        self.category_tree.insert("", "end", "cases", text="Cases")
        self.category_tree.insert("", "end", "accessories", text="Accessories")
        self.category_tree.insert("", "end", "templates", text="Templates")

        # Add subcategories
        self.category_tree.insert("wallets", "end", "bifold", text="Bifold Wallets")
        self.category_tree.insert("wallets", "end", "trifold", text="Trifold Wallets")
        self.category_tree.insert("wallets", "end", "card", text="Card Holders")

        self.category_tree.insert("bags", "end", "tote", text="Tote Bags")
        self.category_tree.insert("bags", "end", "messenger", text="Messenger Bags")

        self.category_tree.insert("belts", "end", "standard", text="Standard Belts")
        self.category_tree.insert("belts", "end", "dress", text="Dress Belts")

        # Bind selection event
        self.category_tree.bind("<<TreeviewSelect>>", self._on_category_select)

        # Create pattern list (main content)
        main_content = ttk.Frame(self)
        main_content.grid(row=1, column=1, sticky="nsew")
        main_content.columnconfigure(0, weight=1)
        main_content.rowconfigure(0, weight=1)

        # Set up treeview for patterns
        columns = ("id", "name", "category", "skill_level", "dimensions", "pieces", "description", "created_date")
        self.pattern_tree = ttk.Treeview(main_content, columns=columns, show="headings", selectmode="browse")

        # Configure headings
        self.pattern_tree.heading("id", text="ID")
        self.pattern_tree.heading("name", text="Pattern Name")
        self.pattern_tree.heading("category", text="Category")
        self.pattern_tree.heading("skill_level", text="Skill Level")
        self.pattern_tree.heading("dimensions", text="Dimensions")
        self.pattern_tree.heading("pieces", text="Pieces")
        self.pattern_tree.heading("description", text="Description")
        self.pattern_tree.heading("created_date", text="Created")

        # Configure columns
        self.pattern_tree.column("id", width=50, stretch=False)
        self.pattern_tree.column("name", width=150)
        self.pattern_tree.column("category", width=100)
        self.pattern_tree.column("skill_level", width=80)
        self.pattern_tree.column("dimensions", width=100)
        self.pattern_tree.column("pieces", width=60, anchor="e")
        self.pattern_tree.column("description", width=200)
        self.pattern_tree.column("created_date", width=100)

        # Add scrollbars
        y_scrollbar = ttk.Scrollbar(main_content, orient=tk.VERTICAL, command=self.pattern_tree.yview)
        x_scrollbar = ttk.Scrollbar(main_content, orient=tk.HORIZONTAL, command=self.pattern_tree.xview)
        self.pattern_tree.configure(yscroll=y_scrollbar.set, xscroll=x_scrollbar.set)

        # Grid layout for treeview and scrollbars
        self.pattern_tree.grid(row=0, column=0, sticky="nsew")
        y_scrollbar.grid(row=0, column=1, sticky="ns")
        x_scrollbar.grid(row=1, column=0, sticky="ew")

        # Bind events
        self.pattern_tree.bind("<<TreeviewSelect>>", self._on_pattern_select)
        self.pattern_tree.bind("<Double-1>", self._on_pattern_double_click)

        # Status bar
        self.status_var = tk.StringVar()
        status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=2, column=0, columnspan=2, sticky="ew")

        self.status_var.set("Ready")

    def _load_data(self) -> None:
        """
        Load pattern data and populate the treeview.
        """
        # Clear existing items
        for item in self.pattern_tree.get_children():
            self.pattern_tree.delete(item)

        try:
            # Get patterns from service
            # This would be something like: patterns = self.project_service.get_patterns()
            # For now, using mock data
            patterns = self._get_mock_patterns()

            if not patterns:
                self.status_var.set("No patterns found")
                logger.info("No patterns found")
                return

            # Populate treeview
            for pattern in patterns:
                self.pattern_tree.insert("", tk.END, values=(
                    pattern.get("id", ""),
                    pattern.get("name", ""),
                    pattern.get("category", ""),
                    pattern.get("skill_level", ""),
                    pattern.get("dimensions", ""),
                    pattern.get("pieces", ""),
                    pattern.get("description", ""),
                    pattern.get("created_date", "")
                ))

            # Update status
            self.status_var.set(f"Loaded {len(patterns)} patterns")
            logger.info(f"Loaded {len(patterns)} patterns")

        except Exception as e:
            error_message = f"Error loading patterns: {str(e)}"
            self.show_error("Data Loading Error", error_message)
            logger.error(error_message, exc_info=True)
            self.status_var.set("Error loading data")

    def _get_mock_patterns(self) -> List[Dict[str, Any]]:
        """
        Generate mock pattern data for testing.

        Returns:
            List[Dict[str, Any]]: List of pattern dictionaries
        """
        return [
            {
                "id": 1,
                "name": "Classic Bifold Wallet",
                "category": "Wallets",
                "skill_level": "Beginner",
                "dimensions": "9cm x 11cm",
                "pieces": 6,
                "description": "Simple bifold wallet with card slots",
                "created_date": "2025-01-15"
            },
            {
                "id": 2,
                "name": "Leather Tote Bag",
                "category": "Bags",
                "skill_level": "Intermediate",
                "dimensions": "35cm x 40cm x 12cm",
                "pieces": 12,
                "description": "Large tote bag with inside pocket",
                "created_date": "2025-01-22"
            },
            {
                "id": 3,
                "name": "Classic Belt",
                "category": "Belts",
                "skill_level": "Beginner",
                "dimensions": "3.5cm x 120cm",
                "pieces": 2,
                "description": "Simple belt with buckle attachment",
                "created_date": "2025-01-10"
            },
            {
                "id": 4,
                "name": "Pen Case",
                "category": "Cases",
                "skill_level": "Beginner",
                "dimensions": "18cm x 6cm",
                "pieces": 3,
                "description": "Simple pen case with stitching",
                "created_date": "2025-02-05"
            },
            {
                "id": 5,
                "name": "Laptop Messenger Bag",
                "category": "Bags",
                "skill_level": "Advanced",
                "dimensions": "40cm x 30cm x 10cm",
                "pieces": 18,
                "description": "Professional messenger bag with padding",
                "created_date": "2025-02-12"
            }
        ]

    def _on_category_select(self, event=None) -> None:
        """
        Handle selection of a category in the category tree.

        Args:
            event: Selection event
        """
        selected_items = self.category_tree.selection()
        if not selected_items:
            return

        # Get the selected category
        category_id = selected_items[0]
        category_name = self.category_tree.item(category_id, "text")

        self.status_var.set(f"Selected category: {category_name}")

        # Apply category filter
        self._filter_by_category(category_name)

    def _filter_by_category(self, category: str) -> None:
        """
        Filter patterns by category.

        Args:
            category: Category name to filter by
        """
        # Clear existing items
        for item in self.pattern_tree.get_children():
            self.pattern_tree.delete(item)

        try:
            # Get all patterns
            patterns = self._get_mock_patterns()

            # Filter patterns by category (case-insensitive)
            filtered_patterns = []
            for pattern in patterns:
                pattern_category = pattern.get("category", "").lower()
                if category.lower() in pattern_category:
                    filtered_patterns.append(pattern)

            # Populate treeview with filtered patterns
            for pattern in filtered_patterns:
                self.pattern_tree.insert("", tk.END, values=(
                    pattern.get("id", ""),
                    pattern.get("name", ""),
                    pattern.get("category", ""),
                    pattern.get("skill_level", ""),
                    pattern.get("dimensions", ""),
                    pattern.get("pieces", ""),
                    pattern.get("description", ""),
                    pattern.get("created_date", "")
                ))

            # Update status
            self.status_var.set(f"Found {len(filtered_patterns)} patterns in category '{category}'")

        except Exception as e:
            error_message = f"Error filtering patterns: {str(e)}"
            self.show_error("Filter Error", error_message)
            logger.error(error_message, exc_info=True)

    def _search_patterns(self, event=None) -> None:
        """
        Search patterns by name or description.

        Args:
            event: Event that triggered the search
        """
        search_term = self.search_var.get().strip().lower()

        if not search_term:
            self._load_data()  # Reset to show all patterns
            return

        # Clear existing items
        for item in self.pattern_tree.get_children():
            self.pattern_tree.delete(item)

        try:
            # Get all patterns
            patterns = self._get_mock_patterns()

            # Filter patterns by search term
            filtered_patterns = []
            for pattern in patterns:
                pattern_name = pattern.get("name", "").lower()
                pattern_desc = pattern.get("description", "").lower()

                if search_term in pattern_name or search_term in pattern_desc:
                    filtered_patterns.append(pattern)

            # Populate treeview with filtered patterns
            for pattern in filtered_patterns:
                self.pattern_tree.insert("", tk.END, values=(
                    pattern.get("id", ""),
                    pattern.get("name", ""),
                    pattern.get("category", ""),
                    pattern.get("skill_level", ""),
                    pattern.get("dimensions", ""),
                    pattern.get("pieces", ""),
                    pattern.get("description", ""),
                    pattern.get("created_date", "")
                ))

            # Update status
            self.status_var.set(f"Found {len(filtered_patterns)} patterns matching '{search_term}'")

        except Exception as e:
            error_message = f"Error searching patterns: {str(e)}"
            self.show_error("Search Error", error_message)
            logger.error(error_message, exc_info=True)

    def _reset_search(self) -> None:
        """Reset search field and reload all data."""
        self.search_var.set("")
        self._load_data()

    def _on_pattern_select(self, event=None) -> None:
        """
        Handle selection of a pattern in the treeview.

        Args:
            event: Selection event
        """
        selected_items = self.pattern_tree.selection()
        if not selected_items:
            self._selected_pattern_id = None
            return

        # Get the first selected item
        item = selected_items[0]
        values = self.pattern_tree.item(item, "values")

        if values:
            self._selected_pattern_id = values[0]  # ID is the first column

    def _on_pattern_double_click(self, event=None) -> None:
        """
        Handle double-click on a pattern in the treeview.

        Args:
            event: Double-click event
        """
        self._view_pattern_details()

    def _add_pattern(self) -> None:
        """Show dialog to add a new pattern."""
        # Placeholder - in a real app, this would open a dialog
        self.show_info("Add Pattern", "Pattern creation dialog would open here.")
        logger.info("Add pattern functionality called")

    def _edit_pattern(self) -> None:
        """Show dialog to edit the selected pattern."""
        if not self._selected_pattern_id:
            self.show_warning("Warning", "Please select a pattern to edit.")
            return

        # Placeholder - in a real app, this would open a dialog with the selected pattern
        self.show_info("Edit Pattern",
                       f"Pattern editing dialog would open here for pattern ID {self._selected_pattern_id}.")
        logger.info(f"Edit pattern called for ID: {self._selected_pattern_id}")

    def _delete_pattern(self) -> None:
        """Delete the selected pattern after confirmation."""
        if not self._selected_pattern_id:
            self.show_warning("Warning", "Please select a pattern to delete.")
            return

        # Ask for confirmation
        if not tk.messagebox.askyesno("Confirm Deletion",
                                      "Are you sure you want to delete this pattern?\n"
                                      "This action cannot be undone."):
            return

        # Placeholder - in a real app, this would call a service to delete the pattern
        self.show_info("Delete Pattern", f"Pattern with ID {self._selected_pattern_id} would be deleted.")
        logger.info(f"Delete pattern called for ID: {self._selected_pattern_id}")

        # Simulate deletion and refresh
        self._selected_pattern_id = None
        self._load_data()

    def _view_pattern_details(self) -> None:
        """Show detailed view of the selected pattern."""
        if not self._selected_pattern_id:
            self.show_warning("Warning", "Please select a pattern to view details.")
            return

        # Placeholder - in a real app, this would open a detailed view dialog
        patterns = self._get_mock_patterns()
        for pattern in patterns:
            if str(pattern.get("id")) == str(self._selected_pattern_id):
                details = (
                    f"Pattern: {pattern.get('name')}\n"
                    f"Category: {pattern.get('category')}\n"
                    f"Skill Level: {pattern.get('skill_level')}\n"
                    f"Dimensions: {pattern.get('dimensions')}\n"
                    f"Pieces: {pattern.get('pieces')}\n"
                    f"Description: {pattern.get('description')}\n"
                    f"Created: {pattern.get('created_date')}"
                )
                self.show_info("Pattern Details", details)
                break

        logger.info(f"View pattern details called for ID: {self._selected_pattern_id}")

    def _import_pattern(self) -> None:
        """Import a pattern from a file."""
        # Open file dialog
        file_path = filedialog.askopenfilename(
            title="Import Pattern",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
        )

        if not file_path:
            return  # User cancelled

        # Placeholder - in a real app, this would process the selected file
        self.show_info("Import Pattern", f"Pattern would be imported from {file_path}")
        logger.info(f"Import pattern called with file: {file_path}")

    def _export_pattern(self) -> None:
        """Export the selected pattern to a file."""
        if not self._selected_pattern_id:
            self.show_warning("Warning", "Please select a pattern to export.")
            return

        # Open file dialog
        file_path = filedialog.asksaveasfilename(
            title="Export Pattern",
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
        )

        if not file_path:
            return  # User cancelled

        # Placeholder - in a real app, this would export the pattern to the selected file
        self.show_info("Export Pattern",
                       f"Pattern with ID {self._selected_pattern_id} would be exported to {file_path}")
        logger.info(f"Export pattern called for ID: {self._selected_pattern_id} to file: {file_path}")