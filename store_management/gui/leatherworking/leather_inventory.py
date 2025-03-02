# gui/leatherworking/leather_inventory.py
"""
Advanced leather inventory view with comprehensive management features.
"""
import logging
from typing import Any, Dict, List, Optional, Tuple, Union
from functools import lru_cache

import tkinter as tk
import tkinter.messagebox as messagebox
from tkinter import ttk, simpledialog, filedialog

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from gui.base_view import BaseView
from gui.leatherworking.leather_dialog import LeatherDetailsDialog
from services.interfaces.material_service import IMaterialService, MaterialType
from services.interfaces.project_service import IProjectService

# Additional imports for advanced features
from utils.validators import DataSanitizer
from utils.notifications import StatusNotification
from utils.performance_tracker import PERFORMANCE_TRACKER
from utils.exporters import OrderExporter
from config.pattern_config import PATTERN_CONFIG


class LeatherInventoryView(BaseView):
    """Advanced view for managing leather inventory with comprehensive features."""

    def __init__(self, parent: tk.Widget, app: Any):
        super().__init__(parent, app)

        # Store the container reference from the app
        if hasattr(app, 'container'):
            self.container = app.container
        else:
            # If app doesn't have container, assume it is the container
            self.container = app

        # Try to get the material service with proper error handling
        try:
            from services.interfaces.material_service import IMaterialService
            self.material_service = self.get_service(IMaterialService)
        except ValueError as e:
            logging.error(f"Failed to retrieve MaterialService: {e}")
            # Fallback to creating the service directly
            try:
                from services.implementations.material_service import MaterialService
                self.material_service = MaterialService()
                logging.info("Created MaterialService directly as fallback")
            except Exception as e:
                logging.error(f"Failed to create MaterialService directly: {e}")
                self.material_service = None

        # Continue with the rest of your initialization
        self._setup_ui()

    def _setup_ui(self):
        """Set up the advanced UI components."""
        # Main layout
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=0)  # Toolbar
        self.rowconfigure(1, weight=1)  # Content
        self.rowconfigure(2, weight=0)  # Additional controls

        # Create toolbar
        toolbar = ttk.Frame(self, padding=(5, 5, 5, 5))
        toolbar.grid(row=0, column=0, sticky="ew")

        # Toolbar buttons
        ttk.Button(toolbar, text="New", command=self.on_new).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="Edit", command=self.on_edit).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Delete", command=self.on_delete).pack(side=tk.LEFT, padx=5)
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=10, fill=tk.Y)
        ttk.Button(toolbar, text="Refresh", command=self.on_refresh).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Export", command=self.export_inventory).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Visualize", command=self.visualize_inventory_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Batch Update", command=self.batch_update_materials).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Batch Delete", command=self.batch_delete_materials).pack(side=tk.LEFT, padx=5)

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
            selectmode="extended"  # Changed to support multiple selections
        )

        # Configure column headings with sorting
        columns_config = [
            ("id", "ID", 50, "center"),
            ("name", "Name", 150, "w"),
            ("type", "Type", 100, "center"),
            ("quantity", "Quantity", 80, "center"),
            ("price", "Price", 80, "e"),
            ("grade", "Grade", 80, "center"),
            ("thickness", "Thickness", 80, "center")
        ]

        for col, heading, width, anchor in columns_config:
            self.tree.heading(col, text=heading, command=lambda c=col: self._sort_column(c, False))
            self.tree.column(col, width=width, anchor=anchor)

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

        # Advanced filter and action buttons
        action_frame = ttk.Frame(self)
        action_frame.grid(row=2, column=0, sticky="ew", pady=5)

        ttk.Button(action_frame, text="Advanced Filter", command=self._show_advanced_filter).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Reset Filter", command=self._reset_filter).pack(side=tk.LEFT, padx=5)

    @PERFORMANCE_TRACKER.track_performance(cache_enabled=True)
    def _load_data(self, reset_filter: bool = False):
        """Load leather inventory data with advanced filtering and sorting.

        Args:
            reset_filter (bool): Reset filter criteria if True
        """
        try:
            # Reset filter if requested
            if reset_filter:
                self._reset_filter()

            # Prepare filter parameters
            filter_params = {
                "material_type": MaterialType.LEATHER
            }

            # Apply specific filters
            if self.filter_criteria["type"] != "All":
                filter_params["type"] = self.filter_criteria["type"]

            if self.filter_criteria["grade"] != "All":
                filter_params["quality_grade"] = self.filter_criteria["grade"]

            # Price range filter
            if self.filter_criteria["min_price"] is not None:
                filter_params["min_price"] = self.filter_criteria["min_price"]
            if self.filter_criteria["max_price"] is not None:
                filter_params["max_price"] = self.filter_criteria["max_price"]

            # Quantity range filter
            if self.filter_criteria["min_quantity"] is not None:
                filter_params["min_quantity"] = self.filter_criteria["min_quantity"]
            if self.filter_criteria["max_quantity"] is not None:
                filter_params["max_quantity"] = self.filter_criteria["max_quantity"]

            # Retrieve materials
            materials = self.cached_get_materials(**filter_params)

            # Sort if a sort column is defined
            if self.current_sort["column"]:
                materials = self._sort_materials(
                    materials,
                    self.current_sort["column"],
                    self.current_sort["reverse"]
                )

            # Clear existing items
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Add materials to the treeview
            for material in materials:
                sanitized_material = DataSanitizer.sanitize_dict(material)
                self.tree.insert(
                    "",
                    "end",
                    values=(
                        sanitized_material.get("id", ""),
                        sanitized_material.get("name", ""),
                        sanitized_material.get("type", "LEATHER"),
                        sanitized_material.get("quantity", 0),
                        f"${sanitized_material.get('unit_price', 0):.2f}",
                        sanitized_material.get("quality_grade", ""),
                        sanitized_material.get("thickness", "")
                    )
                )

            # Update status
            self.notification_manager.show_info(
                f"Loaded {len(materials)} leather materials with current filters"
            )
            self.logger.info(f"Loaded {len(materials)} leather materials")

        except Exception as e:
            self.logger.error(f"Error loading leather inventory: {str(e)}")
            self.show_error("Data Load Error", f"Failed to load leather inventory: {str(e)}")

    @lru_cache(maxsize=10)
    def cached_get_materials(self, **kwargs):
        """Cached method for retrieving materials.

        Args:
            **kwargs: Filter parameters for material retrieval

        Returns:
            List of materials
        """
        return self.material_service.get_materials(**kwargs)

    def _sort_column(self, col: str, reverse: bool):
        """Sort treeview column.

        Args:
            col (str): Column to sort
            reverse (bool): Reverse sorting order
        """
        # Update sorting state
        self.current_sort = {"column": col, "reverse": not reverse}

        # Reload data with sorting
        self._load_data()

    def _sort_materials(self, materials: List[Dict], col: str, reverse: bool) -> List[Dict]:
        """Sort materials based on a specific column.

        Args:
            materials (List[Dict]): List of materials to sort
            col (str): Column to sort by
            reverse (bool): Reverse sorting order

        Returns:
            List[Dict]: Sorted materials
        """
        # Column mapping for sorting
        sort_key_map = {
            "id": lambda x: x.get("id", 0),
            "name": lambda x: x.get("name", "").lower(),
            "type": lambda x: x.get("type", "").lower(),
            "quantity": lambda x: float(x.get("quantity", 0)),
            "price": lambda x: float(x.get("unit_price", 0)),
            "grade": lambda x: x.get("quality_grade", "").lower(),
            "thickness": lambda x: float(x.get("thickness", 0))
        }

        return sorted(materials, key=sort_key_map.get(col, lambda x: x), reverse=reverse)

    def _show_advanced_filter(self):
        """Show advanced filter dialog."""
        filter_dialog = tk.Toplevel(self)
        filter_dialog.title("Advanced Leather Inventory Filter")
        filter_dialog.geometry("400x500")

        # Type filter
        ttk.Label(filter_dialog, text="Leather Type:").pack(pady=(10, 0))
        type_var = tk.StringVar(value=self.filter_criteria["type"])
        type_dropdown = ttk.Combobox(
            filter_dialog,
            textvariable=type_var,
            values=["All", "Full Grain", "Top Grain", "Split", "Other"],
            state="readonly"
        )
        type_dropdown.pack(pady=(0, 10))

        # Grade filter
        ttk.Label(filter_dialog, text="Quality Grade:").pack(pady=(10, 0))
        grade_var = tk.StringVar(value=self.filter_criteria["grade"])
        grade_dropdown = ttk.Combobox(
            filter_dialog,
            textvariable=grade_var,
            values=["All", "Premium", "Standard", "Economy"],
            state="readonly"
        )
        grade_dropdown.pack(pady=(0, 10))

        # Price range
        ttk.Label(filter_dialog, text="Price Range:").pack(pady=(10, 0))
        price_frame = ttk.Frame(filter_dialog)
        price_frame.pack(pady=(0, 10))

        min_price_var = tk.StringVar(value=str(self.filter_criteria["min_price"] or ""))
        max_price_var = tk.StringVar(value=str(self.filter_criteria["max_price"] or ""))

        ttk.Label(price_frame, text="Min $").pack(side=tk.LEFT)
        min_price_entry = ttk.Entry(price_frame, textvariable=min_price_var, width=10)
        min_price_entry.pack(side=tk.LEFT, padx=5)

        ttk.Label(price_frame, text="Max $").pack(side=tk.LEFT)
        max_price_entry = ttk.Entry(price_frame, textvariable=max_price_var, width=10)
        max_price_entry.pack(side=tk.LEFT, padx=5)

        # Quantity range
        ttk.Label(filter_dialog, text="Quantity Range:").pack(pady=(10, 0))
        qty_frame = ttk.Frame(filter_dialog)
        qty_frame.pack(pady=(0, 10))

        min_qty_var = tk.StringVar(value=str(self.filter_criteria["min_quantity"] or ""))
        max_qty_var = tk.StringVar(value=str(self.filter_criteria["max_quantity"] or ""))

        ttk.Label(qty_frame, text="Min Qty").pack(side=tk.LEFT)
        min_qty_entry = ttk.Entry(qty_frame, textvariable=min_qty_var, width=10)
        min_qty_entry.pack(side=tk.LEFT, padx=5)

        ttk.Label(qty_frame, text="Max Qty").pack(side=tk.LEFT)
        max_qty_entry = ttk.Entry(qty_frame, textvariable=max_qty_var, width=10)
        max_qty_entry.pack(side=tk.LEFT, padx=5)

        # Apply and Reset buttons
        button_frame = ttk.Frame(filter_dialog)
        button_frame.pack(pady=20)

        def apply_filter():
            try:
                # Parse and validate inputs
                self.filter_criteria = {
                    "type": type_var.get(),
                    "grade": grade_var.get(),
                    "min_price": float(min_price_var.get()) if min_price_var.get() else None,
                    "max_price": float(max_price_var.get()) if max_price_var.get() else None,
                    "min_quantity": float(min_qty_var.get()) if min_qty_var.get() else None,
                    "max_quantity": float(max_qty_var.get()) if max_qty_var.get() else None
                }

                # Reload data with new filters
                self._load_data()
                filter_dialog.destroy()
            except ValueError:
                self.show_error("Invalid Input", "Please enter valid numeric values for price and quantity.")

        def reset_filter():
            # Reset all filter criteria
            self._load_data(reset_filter=True)
            filter_dialog.destroy()

        ttk.Button(button_frame, text="Apply", command=apply_filter).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Reset", command=reset_filter).pack(side=tk.LEFT, padx=5)

    def _reset_filter(self):
        """Reset all filter criteria to default state."""
        self.filter_criteria = {
            "type": "All",
            "min_price": None,
            "max_price": None,
            "min_quantity": None,
            "max_quantity": None,
            "grade": "All"
        }
        self.current_sort = {"column": None, "reverse": False}
        self._load_data()
        self.notification_manager.show_info("Filters and sorting reset")

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
            # Search leather materials
            materials = self.material_service.search_materials(
                search_text,
                material_type=MaterialType.LEATHER
            )

            # Clear existing items
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Add materials to the treeview
            for material in materials:
                sanitized_material = DataSanitizer.sanitize_dict(material)
                self.tree.insert(
                    "",
                    "end",
                    values=(
                        sanitized_material.get("id", ""),
                        sanitized_material.get("name", ""),
                        sanitized_material.get("type", "LEATHER"),
                        sanitized_material.get("quantity", 0),
                        f"${sanitized_material.get('unit_price', 0):.2f}",
                        sanitized_material.get("quality_grade", ""),
                        sanitized_material.get("thickness", "")
                    )
                )

            self.notification_manager.show_info(f"Found {len(materials)} matching leather materials")
            self.logger.info(f"Search found {len(materials)} materials")

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
                material = self.material_service.create(dialog.result)

                # Refresh view
                self._load_data()

                # Select the new material
                for item in self.tree.get_children():
                    if self.tree.item(item, "values")[0] == str(material.get("id")):
                        self.tree.selection_set(item)
                        self.tree.see(item)
                        break

                self.notification_manager.show_success(f"Created new leather material: {material.get('name')}")
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
            material = self.material_service.get_by_id(int(item_id))

            if not material:
                self.show_error("Not Found", f"Leather material with ID {item_id} not found.")
                return

            # Open dialog with existing data
            dialog = LeatherDetailsDialog(self, "Edit Leather Material", material)

            if dialog.result:
                # Update material
                updated_material = self.material_service.update(int(item_id), dialog.result)

                # Refresh view
                self._load_data()

                # Re-select the edited material
                for item in self.tree.get_children():
                    if self.tree.item(item, "values")[0] == str(updated_material.get("id")):
                        self.tree.selection_set(item)
                        self.tree.see(item)
                        break

                self.notification_manager.show_success(f"Updated leather material: {updated_material.get('name')}")
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

        # Get selected item ID and name
        item_id = self.tree.item(selection[0], "values")[0]
        item_name = self.tree.item(selection[0], "values")[1]

        # Confirm deletion
        if not self.confirm("Confirm Delete",
                            f"Are you sure you want to delete the leather material '{item_name}'?"):
            return

        try:
            # Delete material
            success = self.material_service.delete(int(item_id))

            if success:
                # Refresh view
                self._load_data()

                self.notification_manager.show_success(f"Deleted leather material: {item_name}")
                self.logger.info(f"Deleted leather material: {item_name}")
            else:
                self.show_error("Delete Failed", f"Failed to delete leather material '{item_name}'.")

        except Exception as e:
            self.logger.error(f"Error deleting leather material: {str(e)}")
            self.show_error("Delete Error", f"Failed to delete leather material: {str(e)}")

    def on_refresh(self):
        """Refresh the inventory view."""
        self._load_data()
        self.notification_manager.show_info("Inventory refreshed")

    def export_inventory(self):
        """Export current leather inventory to CSV or Excel."""
        try:
            # Retrieve current filtered materials
            filter_params = {
                "material_type": MaterialType.LEATHER
            }

            # Apply existing filters
            if self.filter_criteria["type"] != "All":
                filter_params["type"] = self.filter_criteria["type"]

            if self.filter_criteria["grade"] != "All":
                filter_params["quality_grade"] = self.filter_criteria["grade"]

            if self.filter_criteria["min_price"] is not None:
                filter_params["min_price"] = self.filter_criteria["min_price"]
            if self.filter_criteria["max_price"] is not None:
                filter_params["max_price"] = self.filter_criteria["max_price"]

            if self.filter_criteria["min_quantity"] is not None:
                filter_params["min_quantity"] = self.filter_criteria["min_quantity"]
            if self.filter_criteria["max_quantity"] is not None:
                filter_params["max_quantity"] = self.filter_criteria["max_quantity"]

            # Retrieve materials
            materials = self.material_service.get_materials(**filter_params)

            # Prepare data for export
            export_data = [
                {
                    "ID": m.get("id", ""),
                    "Name": m.get("name", ""),
                    "Type": m.get("type", ""),
                    "Quantity": m.get("quantity", 0),
                    "Unit Price": m.get("unit_price", 0),
                    "Quality Grade": m.get("quality_grade", ""),
                    "Thickness": m.get("thickness", "")
                } for m in materials
            ]

            # Open file dialog to choose export location
            export_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx")]
            )

            if export_path:
                # Use OrderExporter to export data
                if export_path.endswith('.csv'):
                    OrderExporter.export_to_csv(export_data, export_path)
                else:
                    OrderExporter.export_to_excel(export_data, export_path)

                self.notification_manager.show_success(f"Inventory exported to {export_path}")
                self.logger.info(f"Exported leather inventory to {export_path}")

        except Exception as e:
            self.logger.error(f"Export failed: {str(e)}")
            self.show_error("Export Error", f"Failed to export inventory: {str(e)}")

    def visualize_inventory_data(self):
        """Create advanced visualizations of leather inventory data."""
        try:
            # Retrieve all leather materials
            materials = self.material_service.get_materials(material_type=MaterialType.LEATHER)

            # Create visualization window
            viz_window = tk.Toplevel(self)
            viz_window.title("Leather Inventory Visualization")
            viz_window.geometry("800x600")

            # Create notebook for multiple visualization tabs
            notebook = ttk.Notebook(viz_window)
            notebook.pack(expand=True, fill='both', padx=10, pady=10)

            # 1. Quantity Distribution Pie Chart
            def create_quantity_distribution_tab():
                frame = ttk.Frame(notebook)
                notebook.add(frame, text="Quantity Distribution")

                # Prepare data
                types = {}
                for material in materials:
                    mat_type = material.get('type', 'Unknown')
                    quantity = material.get('quantity', 0)
                    types[mat_type] = types.get(mat_type, 0) + quantity

                # Create pie chart
                fig, ax = plt.subplots(figsize=(8, 6))
                ax.pie(
                    list(types.values()),
                    labels=list(types.keys()),
                    autopct='%1.1f%%',
                    startangle=90
                )
                ax.axis('equal')
                plt.title('Leather Inventory Quantity by Type')

                # Embed in Tkinter
                canvas = FigureCanvasTkAgg(fig, master=frame)
                canvas_widget = canvas.get_tk_widget()
                canvas_widget.pack(expand=True, fill='both')

                return frame

            # 2. Price Histogram
            def create_price_histogram_tab():
                frame = ttk.Frame(notebook)
                notebook.add(frame, text="Price Distribution")

                # Prepare data
                prices = [material.get('unit_price', 0) for material in materials]

                # Create histogram
                fig, ax = plt.subplots(figsize=(8, 6))
                ax.hist(prices, bins=10, edgecolor='black')
                plt.title('Distribution of Leather Material Prices')
                plt.xlabel('Price')
                plt.ylabel('Frequency')

                # Embed in Tkinter
                canvas = FigureCanvasTkAgg(fig, master=frame)
                canvas_widget = canvas.get_tk_widget()
                canvas_widget.pack(expand=True, fill='both')

                return frame

            # 3. Quality Grade Breakdown Bar Chart
            def create_grade_breakdown_tab():
                frame = ttk.Frame(notebook)
                notebook.add(frame, text="Quality Grade Breakdown")

                # Prepare data
                grades = {}
                for material in materials:
                    grade = material.get('quality_grade', 'Unknown')
                    grades[grade] = grades.get(grade, 0) + 1

                # Create bar chart
                fig, ax = plt.subplots(figsize=(8, 6))
                ax.bar(list(grades.keys()), list(grades.values()))
                plt.title('Leather Materials by Quality Grade')
                plt.xlabel('Quality Grade')
                plt.ylabel('Number of Materials')
                plt.xticks(rotation=45)

                # Embed in Tkinter
                canvas = FigureCanvasTkAgg(fig, master=frame)
                canvas_widget = canvas.get_tk_widget()
                canvas_widget.pack(expand=True, fill='both')

                return frame

            # Create tabs
            create_quantity_distribution_tab()
            create_price_histogram_tab()
            create_grade_breakdown_tab()

            self.logger.info("Inventory visualization created")
            self.notification_manager.show_info("Inventory visualization generated")

        except Exception as e:
            self.logger.error(f"Visualization error: {str(e)}")
            self.show_error("Visualization Error", f"Failed to create inventory visualization: {str(e)}")

    def batch_update_materials(self):
        """Implement batch update for selected materials."""
        # Get selected materials
        selected_items = self.tree.selection()

        if not selected_items:
            self.show_info("No Selection", "Please select materials to update.")
            return

        # Create batch update dialog
        batch_dialog = tk.Toplevel(self)
        batch_dialog.title("Batch Update Leather Materials")
        batch_dialog.geometry("400x500")

        # Update fields
        ttk.Label(batch_dialog, text="Fields to Update:").pack(pady=(10, 0))

        # Checkboxes for updateable fields
        update_fields = {
            "price": tk.BooleanVar(),
            "quantity": tk.BooleanVar(),
            "grade": tk.BooleanVar(),
            "thickness": tk.BooleanVar()
        }

        field_frames = {}
        for field, var in update_fields.items():
            frame = ttk.Frame(batch_dialog)
            frame.pack(fill='x', padx=20, pady=5)

            cb = ttk.Checkbutton(frame, text=field.capitalize(), variable=var)
            cb.pack(side=tk.LEFT)

            # Entry for new value
            entry = ttk.Entry(frame, state='disabled', width=20)
            entry.pack(side=tk.RIGHT, padx=10)

            # Enable/disable entry when checkbox is checked
            def create_toggle_callback(entry_widget, var):
                def callback():
                    entry_widget.config(state='normal' if var.get() else 'disabled')

                return callback

                var.trace_add('write', create_toggle_callback(entry, var))

                field_frames[field] = {
                    'var': var,
                    'entry': entry
                }

                # Batch update confirmation

            def perform_batch_update():
                try:
                    # Collect update parameters
                    update_params = {}
                    for field, info in field_frames.items():
                        if info['var'].get():
                            # Validate and parse input
                            value = info['entry'].get().strip()
                            if not value:
                                raise ValueError(f"{field.capitalize()} cannot be empty")

                            # Convert to appropriate type
                            if field == 'price':
                                update_params[field] = float(value)
                            elif field == 'quantity':
                                update_params[field] = int(value)
                            else:
                                update_params[field] = value

                    # Confirm batch update
                    confirm = messagebox.askyesno(
                        "Confirm Batch Update",
                        f"Update {len(selected_items)} materials with:\n" +
                        "\n".join(f"{k}: {v}" for k, v in update_params.items())
                    )

                    if not confirm:
                        return

                    # Perform batch update
                    updated_count = 0
                    failed_materials = []
                    for item in selected_items:
                        material_id = int(self.tree.item(item, "values")[0])
                        try:
                            self.material_service.update(material_id, update_params)
                            updated_count += 1
                        except Exception as e:
                            self.logger.warning(f"Failed to update material {material_id}: {str(e)}")
                            failed_materials.append(material_id)

                    # Refresh view
                    self._load_data()

                    # Show results
                    if failed_materials:
                        self.notification_manager.show_warning(
                            f"Successfully updated {updated_count} materials. "
                            f"Failed to update {len(failed_materials)} materials (IDs: {failed_materials})"
                        )
                    else:
                        self.notification_manager.show_success(
                            f"Successfully updated {updated_count} materials"
                        )

                    self.logger.info(f"Batch updated {updated_count} materials")

                    # Close dialog
                    batch_dialog.destroy()

                except ValueError as ve:
                    self.show_error("Validation Error", str(ve))
                except Exception as e:
                    self.show_error("Batch Update Error", f"Failed to perform batch update: {str(e)}")

                # Batch update and cancel buttons

            button_frame = ttk.Frame(batch_dialog)
            button_frame.pack(pady=20)

            ttk.Button(button_frame, text="Update", command=perform_batch_update).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Cancel", command=batch_dialog.destroy).pack(side=tk.LEFT, padx=5)

    def batch_delete_materials(self):
        """Implement batch delete for selected materials."""
        # Get selected materials
        selected_items = self.tree.selection()

        if not selected_items:
            self.show_info("No Selection", "Please select materials to delete.")
            return

        # Confirm batch deletion
        confirm = messagebox.askyesno(
            "Confirm Batch Delete",
            f"Are you sure you want to delete {len(selected_items)} materials?"
        )

        if not confirm:
            return

        try:
            # Perform batch delete
            deleted_count = 0
            failed_materials = []

            for item in selected_items:
                material_id = int(self.tree.item(item, "values")[0])
                material_name = self.tree.item(item, "values")[1]
                try:
                    success = self.material_service.delete(material_id)
                    if success:
                        deleted_count += 1
                    else:
                        failed_materials.append({
                            'id': material_id,
                            'name': material_name
                        })
                except Exception as e:
                    self.logger.warning(f"Failed to delete material {material_id}: {str(e)}")
                    failed_materials.append({
                        'id': material_id,
                        'name': material_name
                    })

            # Refresh view
            self._load_data()

            # Show results
            if failed_materials:
                failed_details = "\n".join([f"ID: {m['id']}, Name: {m['name']}" for m in failed_materials])
                self.notification_manager.show_warning(
                    f"Deleted {deleted_count} materials. "
                    f"Failed to delete {len(failed_materials)} materials:\n{failed_details}"
                )
            else:
                self.notification_manager.show_success(
                    f"Successfully deleted {deleted_count} materials"
                )

            self.logger.info(f"Batch deleted {deleted_count} materials")

        except Exception as e:
            self.show_error("Batch Delete Error", f"Failed to perform batch delete: {str(e)}")

    def cleanup(self):
        """Cleanup method to clear caches and reset tracking."""
        # Clear LRU cache
        self.cached_get_materials.cache_clear()

        # Reset performance tracker
        PERFORMANCE_TRACKER.reset_metrics()

        # Close any open matplotlib figures
        plt.close('all')

        self.logger.info("Leather Inventory View cleanup completed")

# Optional: instantiation and running code for standalone testing
def main():
    """Standalone testing of the Leather Inventory View."""
    root = tk.Tk()
    root.title("Leather Inventory")
    root.geometry("1200x800")

    # Set up dependency injection container
    try:
        from di.container import DependencyContainer
        from di.setup import setup_dependency_injection
        container = setup_dependency_injection()
    except ImportError:
        # Create a simple mock container
        class MockContainer:
            def get(self, service_type):
                if hasattr(service_type, '__name__') and service_type.__name__ == 'IMaterialService':
                    from services.implementations.material_service import MaterialService
                    return MaterialService()
                return None

        container = MockContainer()

    inventory_view = LeatherInventoryView(root, container)
    inventory_view.pack(fill=tk.BOTH, expand=True)

    # Handle window close
    def on_close():
        try:
            inventory_view.cleanup()
        except:
            pass
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()

if __name__ == "__main__":
    main()