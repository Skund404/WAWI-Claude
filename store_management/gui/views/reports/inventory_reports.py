# gui/views/reports/inventory_reports.py
"""
Inventory reports module for the leatherworking ERP system.

This module provides various inventory-related reports, including
inventory stock levels, valuation, and material usage analytics.
"""

import logging
import tkinter as tk
from tkinter import ttk
import sqlite3
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum

from gui.views.reports.base_report_view import BaseReportView
from gui.views.reports.export_utils import ReportExporter, get_default_report_filename
from gui.widgets.enhanced_treeview import EnhancedTreeview
from gui.widgets.enum_combobox import EnumCombobox
from gui.theme import COLORS
from gui.config import DEFAULT_PADDING

from database.models.enums import (
    MaterialType, InventoryStatus, QualityGrade
)

from di import resolve
from utils.service_access import with_service

logger = logging.getLogger(__name__)


class StockLevelReport(BaseReportView):
    """
    Inventory Stock Level Report.

    Shows current inventory levels for materials, highlighting items
    that are low in stock or out of stock.
    """

    REPORT_TITLE = "Inventory Stock Level Report"
    REPORT_DESCRIPTION = "Overview of current inventory levels by material type"

    def __init__(self, parent):
        """
        Initialize the stock level report view.

        Args:
            parent: The parent widget
        """
        self.material_type_filter = tk.StringVar()
        self.status_filter = tk.StringVar()
        self.include_zero_stock = tk.BooleanVar(value=False)

        # Initialize the columns for the report
        self.columns = [
            {"name": "Material ID", "key": "id", "width": 80},
            {"name": "Material Name", "key": "name", "width": 200},
            {"name": "Type", "key": "material_type", "width": 100},
            {"name": "Quantity", "key": "quantity", "width": 80},
            {"name": "Unit", "key": "unit", "width": 80},
            {"name": "Status", "key": "status", "width": 100},
            {"name": "Quality", "key": "quality", "width": 80},
            {"name": "Location", "key": "location", "width": 120},
            {"name": "Last Update", "key": "updated_at", "width": 150}
        ]

        # Call the parent constructor
        super().__init__(parent)

    def create_filters(self, parent):
        """
        Create custom filters for the stock level report.

        Args:
            parent: The parent widget
        """
        # Create a frame for the custom filters
        filter_container = ttk.Frame(parent)
        filter_container.pack(fill=tk.X, padx=DEFAULT_PADDING, pady=(5, 0))

        # Material Type Filter
        type_frame = ttk.Frame(filter_container)
        type_frame.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(type_frame, text="Material Type:").pack(side=tk.LEFT, padx=(0, 5))

        # Create a list of material types from the enum
        material_types = ["All"] + [t.value for t in MaterialType]
        type_combo = ttk.Combobox(type_frame, textvariable=self.material_type_filter,
                                  values=material_types, state="readonly", width=15)
        type_combo.pack(side=tk.LEFT)
        self.material_type_filter.set("All")  # Default value

        # Inventory Status Filter
        status_frame = ttk.Frame(filter_container)
        status_frame.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(status_frame, text="Status:").pack(side=tk.LEFT, padx=(0, 5))

        # Create a list of inventory statuses from the enum
        statuses = ["All"] + [s.value for s in InventoryStatus]
        status_combo = ttk.Combobox(status_frame, textvariable=self.status_filter,
                                    values=statuses, state="readonly", width=15)
        status_combo.pack(side=tk.LEFT)
        self.status_filter.set("All")  # Default value

        # Include Zero Stock Checkbox
        zero_stock_frame = ttk.Frame(filter_container)
        zero_stock_frame.pack(side=tk.LEFT)

        ttk.Checkbutton(zero_stock_frame, text="Include Zero Stock",
                        variable=self.include_zero_stock).pack(side=tk.LEFT)

    def reset_custom_filters(self):
        """Reset custom filters to their default values."""
        self.material_type_filter.set("All")
        self.status_filter.set("All")
        self.include_zero_stock.set(False)

    def create_report_content(self, parent):
        """
        Create the main content area for the stock level report.

        Args:
            parent: The parent widget
        """
        # Create a frame for the treeview with scrollbars
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=5)

        # Create column configuration
        columns = [col["name"] for col in self.columns[1:]]  # Skip ID column

        # Create the treeview
        self.tree = EnhancedTreeview(
            tree_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )

        # Configure the treeview and scrollbars
        for i, col in enumerate(self.columns[1:], 0):
            self.tree.heading(i, text=col["name"])
            self.tree.column(i, width=col["width"], stretch=tk.NO)

        # Enable sorting
        for i in range(len(columns)):
            self.tree.heading(i, command=lambda c=i: self._sort_by_column(c))

        # Pack the treeview
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Create a summary frame below the treeview
        summary_frame = ttk.LabelFrame(parent, text="Summary")
        summary_frame.pack(fill=tk.X, padx=0, pady=(5, 0))

        # Create summary labels
        summary_grid = ttk.Frame(summary_frame)
        summary_grid.pack(fill=tk.X, padx=DEFAULT_PADDING, pady=DEFAULT_PADDING)

        # Row 1
        ttk.Label(summary_grid, text="Total Items:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.total_items_label = ttk.Label(summary_grid, text="0")
        self.total_items_label.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))

        ttk.Label(summary_grid, text="Total Value:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.total_value_label = ttk.Label(summary_grid, text="$0.00")
        self.total_value_label.grid(row=0, column=3, sticky=tk.W, padx=(0, 20))

        ttk.Label(summary_grid, text="Low Stock Items:").grid(row=0, column=4, sticky=tk.W, padx=(0, 5))
        self.low_stock_label = ttk.Label(summary_grid, text="0")
        self.low_stock_label.grid(row=0, column=5, sticky=tk.W)

        # Row 2
        ttk.Label(summary_grid, text="Total Types:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5))
        self.total_types_label = ttk.Label(summary_grid, text="0")
        self.total_types_label.grid(row=1, column=1, sticky=tk.W)

        ttk.Label(summary_grid, text="Avg Value/Item:").grid(row=1, column=2, sticky=tk.W, padx=(0, 5))
        self.avg_value_label = ttk.Label(summary_grid, text="$0.00")
        self.avg_value_label.grid(row=1, column=3, sticky=tk.W)

        ttk.Label(summary_grid, text="Out of Stock:").grid(row=1, column=4, sticky=tk.W, padx=(0, 5))
        self.out_of_stock_label = ttk.Label(summary_grid, text="0")
        self.out_of_stock_label.grid(row=1, column=5, sticky=tk.W)

    def load_report_data(self):
        """Load inventory data for the report."""
        self.update_status("Loading inventory data...")
        self.is_loading = True

        try:
            # Get date range
            start_date, end_date = self.date_selector.get_date_range()

            # Get filter values
            material_type = self.material_type_filter.get()
            status = self.status_filter.get()
            include_zero = self.include_zero_stock.get()

            # Build filter criteria
            criteria = {}

            if material_type != "All":
                criteria["material_type"] = material_type

            if status != "All":
                criteria["status"] = status

            if not include_zero:
                criteria["quantity_gt"] = 0

            # In a real implementation, we would use the inventory service to get data
            # For demonstration, we'll generate some sample data
            self.report_data = self._get_sample_data(criteria)

            # Update the display
            self.update_report_display()

            # Update status
            self.update_status(f"Loaded {len(self.report_data)} inventory items")

        except Exception as e:
            logger.error(f"Error loading inventory data: {str(e)}", exc_info=True)
            self.update_status(f"Error: {str(e)}")

        finally:
            self.is_loading = False

    def update_report_display(self):
        """Update the report display with current data."""
        # Clear existing data
        self.tree.clear()

        if not self.report_data:
            return

        # Calculate summary metrics
        total_items = len(self.report_data)
        total_value = sum(item.get("value", 0) for item in self.report_data)
        total_types = len(set(item.get("material_type") for item in self.report_data))
        low_stock = sum(1 for item in self.report_data if item.get("status") == "low_stock")
        out_of_stock = sum(1 for item in self.report_data if item.get("status") == "out_of_stock")

        avg_value = total_value / total_items if total_items > 0 else 0

        # Update summary labels
        self.total_items_label.config(text=str(total_items))
        self.total_value_label.config(text=f"${total_value:.2f}")
        self.total_types_label.config(text=str(total_types))
        self.avg_value_label.config(text=f"${avg_value:.2f}")
        self.low_stock_label.config(text=str(low_stock))
        self.out_of_stock_label.config(text=str(out_of_stock))

        # Add data to treeview
        for item in self.report_data:
            values = [item.get(col["key"], "") for col in self.columns[1:]]

            # Format the date
            if item.get("updated_at"):
                date_str = item["updated_at"].strftime("%Y-%m-%d %H:%M")
                values[-1] = date_str

            # Insert with tag based on status
            status = item.get("status", "")
            tag = status if status in ["low_stock", "out_of_stock"] else "normal"

            self.tree.insert("", tk.END, values=values, tags=(tag,))

        # Configure tag colors
        self.tree.tag_configure("low_stock", background="#FFF9C4")  # Light yellow
        self.tree.tag_configure("out_of_stock", background="#FFCDD2")  # Light red

    def export_pdf(self):
        """Export the report to PDF."""
        self.update_status("Exporting to PDF...")

        try:
            # Generate default filename
            filename = get_default_report_filename(self.REPORT_TITLE)

            # Use the ReportExporter to create the PDF
            success = ReportExporter.export_to_pdf(
                self.REPORT_TITLE,
                self.report_data,
                self.columns,
                filename=None  # Let the user choose the filename
            )

            if success:
                self.update_status("Report exported to PDF successfully")
            else:
                self.update_status("PDF export cancelled")

        except Exception as e:
            logger.error(f"Error exporting to PDF: {str(e)}", exc_info=True)
            self.update_status(f"Error: {str(e)}")

    def print_report(self):
        """Print the report."""
        self.update_status("Preparing to print...")

        try:
            # Use the ReportExporter to print
            success = ReportExporter.print_report(
                self.REPORT_TITLE,
                self.report_data,
                self.columns
            )

            if success:
                self.update_status("Report sent to printer")
            else:
                self.update_status("Print cancelled")

        except Exception as e:
            logger.error(f"Error printing report: {str(e)}", exc_info=True)
            self.update_status(f"Error: {str(e)}")

    def _sort_by_column(self, column_index):
        """
        Sort treeview data by column.

        Args:
            column_index: Index of the column to sort by
        """
        # This would normally sort the data in the treeview
        # For now, we'll just log it
        column_name = self.columns[column_index + 1]["name"]  # +1 to skip ID column
        logger.info(f"Sorting by column: {column_name}")

    def _get_sample_data(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate sample data for demonstration purposes.

        In a real implementation, this would fetch data from the database.

        Args:
            criteria: Filter criteria

        Returns:
            List of inventory items
        """
        sample_data = []

        # Generate sample data for different material types
        material_types = [MaterialType.LEATHER, MaterialType.HARDWARE,
                          MaterialType.THREAD, MaterialType.ADHESIVE]

        if criteria.get("material_type"):
            # Filter to specific type if requested
            filtered_types = [t for t in material_types
                              if t.value == criteria["material_type"]]
            if filtered_types:
                material_types = filtered_types

        # Status options
        statuses = [
            InventoryStatus.IN_STOCK,
            InventoryStatus.LOW_STOCK,
            InventoryStatus.OUT_OF_STOCK
        ]

        if criteria.get("status"):
            # Filter to specific status if requested
            filtered_statuses = [s for s in statuses
                                 if s.value == criteria["status"]]
            if filtered_statuses:
                statuses = filtered_statuses

        # Sample materials for each type
        type_materials = {
            MaterialType.LEATHER: [
                "Full Grain Cowhide", "Top Grain Goatskin", "Suede Split",
                "Veg-Tan Shoulder", "Chrome-Tanned Calfskin"
            ],
            MaterialType.HARDWARE: [
                "Brass Buckles", "Stainless D-Rings", "Copper Rivets",
                "Magnetic Snaps", "Steel Chicago Screws"
            ],
            MaterialType.THREAD: [
                "Waxed Linen Thread", "Polyester Thread", "Nylon Thread",
                "Bonded Nylon", "Tiger Thread"
            ],
            MaterialType.ADHESIVE: [
                "Contact Cement", "Edge Kote", "Leather Glue",
                "Fabric Adhesive", "Epoxy"
            ]
        }

        # Sample units by type
        type_units = {
            MaterialType.LEATHER: "sq.ft",
            MaterialType.HARDWARE: "piece",
            MaterialType.THREAD: "spool",
            MaterialType.ADHESIVE: "bottle"
        }

        # Generate items
        item_id = 1
        for material_type in material_types:
            for item_name in type_materials.get(material_type, []):
                for status in statuses:
                    # Determine quantity based on status
                    if status == InventoryStatus.OUT_OF_STOCK:
                        quantity = 0
                    elif status == InventoryStatus.LOW_STOCK:
                        quantity = 2
                    else:
                        quantity = 10 + (item_id % 20)  # Random-ish quantity

                    # Skip if we're excluding zero quantity
                    if criteria.get("quantity_gt", 0) > quantity:
                        continue

                    # Create the item
                    item = {
                        "id": item_id,
                        "name": item_name,
                        "material_type": material_type.value,
                        "quantity": quantity,
                        "unit": type_units.get(material_type, "piece"),
                        "status": status.value,
                        "quality": QualityGrade.STANDARD.value,
                        "location": f"Rack {(item_id % 5) + 1}, Bin {(item_id % 10) + 1}",
                        "updated_at": datetime.now() - timedelta(days=item_id % 30),
                        "value": quantity * (10 + (item_id % 15))  # Random-ish value
                    }

                    sample_data.append(item)
                    item_id += 1

        return sample_data