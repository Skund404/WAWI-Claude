# gui/leatherworking/material_calculator.py
"""
Material calculator module for leatherworking projects.
Helps calculate material requirements based on project specifications.
"""

import logging
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any, Dict, List, Optional

from gui.base_view import BaseView
from services.interfaces.material_service import IMaterialService
from services.interfaces.project_service import IProjectService

# Configure logger
logger = logging.getLogger(__name__)


class MaterialCalculator(BaseView):
    """Tool for calculating material requirements for leatherworking projects."""

    def __init__(self, parent: tk.Widget, app: Any):
        """Initialize the material calculator.

        Args:
            parent: Parent widget
            app: Application instance with service access
        """
        super().__init__(parent, app)
        logger.info("Initializing Material Calculator")

        # Material data
        self.materials = []

        # Set up UI
        self._setup_layout()

        # Load initial sample data
        self.load_initial_materials()

        logger.info("Material Calculator initialized")

    def _setup_layout(self):
        """Configure the material calculator layout."""
        # Main container with padding
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(main_frame, text="Material Calculator", font=("Helvetica", 16, "bold"))
        title_label.pack(pady=(0, 10))

        # Split into left and right panels
        panel_frame = ttk.Frame(main_frame)
        panel_frame.pack(fill=tk.BOTH, expand=True)

        # Left panel - inputs
        left_frame = ttk.LabelFrame(panel_frame, text="Project Specifications")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        # Material input fields
        self._create_material_input(left_frame)

        # Right panel - results & list
        right_frame = ttk.Frame(panel_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        # Material list
        list_frame = ttk.LabelFrame(right_frame, text="Materials List")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))

        self._create_material_list(list_frame)

        # Calculation summary
        summary_frame = ttk.LabelFrame(right_frame, text="Calculation Summary")
        summary_frame.pack(fill=tk.X, pady=(5, 0))

        self._create_calculation_summary(summary_frame)

        # Bottom buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(button_frame, text="Export Material Report", command=self.export_material_report).pack(side=tk.RIGHT)
        ttk.Button(button_frame, text="Reset All", command=self._reset_all).pack(side=tk.RIGHT, padx=5)

    def _create_material_input(self, parent):
        """Create input fields for material calculations.

        Args:
            parent: Parent widget for material input fields
        """
        # Project type selection
        ttk.Label(parent, text="Project Type:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.project_type_var = tk.StringVar(value="Wallet")
        project_types = ["Wallet", "Bag", "Belt", "Notebook Cover", "Custom"]
        ttk.Combobox(parent, textvariable=self.project_type_var, values=project_types, state="readonly").grid(
            row=0, column=1, sticky=tk.EW, pady=5
        )

        # Size inputs
        ttk.Label(parent, text="Dimensions:").grid(row=1, column=0, sticky=tk.W, pady=5)
        size_frame = ttk.Frame(parent)
        size_frame.grid(row=1, column=1, sticky=tk.EW, pady=5)

        ttk.Label(size_frame, text="Width:").pack(side=tk.LEFT)
        self.width_var = tk.DoubleVar(value=10.0)
        ttk.Spinbox(size_frame, from_=1, to=100, increment=0.5, textvariable=self.width_var, width=5).pack(side=tk.LEFT,
                                                                                                           padx=2)
        ttk.Label(size_frame, text="cm").pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(size_frame, text="Height:").pack(side=tk.LEFT)
        self.height_var = tk.DoubleVar(value=8.0)
        ttk.Spinbox(size_frame, from_=1, to=100, increment=0.5, textvariable=self.height_var, width=5).pack(
            side=tk.LEFT, padx=2)
        ttk.Label(size_frame, text="cm").pack(side=tk.LEFT)

        # Material thickness
        ttk.Label(parent, text="Leather Thickness:").grid(row=2, column=0, sticky=tk.W, pady=5)
        thickness_frame = ttk.Frame(parent)
        thickness_frame.grid(row=2, column=1, sticky=tk.EW, pady=5)

        self.thickness_var = tk.DoubleVar(value=2.0)
        ttk.Spinbox(thickness_frame, from_=0.5, to=10, increment=0.1, textvariable=self.thickness_var, width=5).pack(
            side=tk.LEFT, padx=2)
        ttk.Label(thickness_frame, text="mm").pack(side=tk.LEFT)

        # Leather type
        ttk.Label(parent, text="Leather Type:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.leather_type_var = tk.StringVar(value="Vegetable Tanned")
        leather_types = ["Vegetable Tanned", "Chrome Tanned", "Oil Tanned", "Latigo", "Suede", "Exotic"]
        ttk.Combobox(parent, textvariable=self.leather_type_var, values=leather_types, state="readonly").grid(
            row=3, column=1, sticky=tk.EW, pady=5
        )

        # Number of layers
        ttk.Label(parent, text="Number of Layers:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.layers_var = tk.IntVar(value=2)
        ttk.Spinbox(parent, from_=1, to=10, textvariable=self.layers_var, width=5).grid(
            row=4, column=1, sticky=tk.W, pady=5
        )

        # Waste factor
        ttk.Label(parent, text="Waste Factor (%):").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.waste_var = tk.DoubleVar(value=15.0)
        ttk.Spinbox(parent, from_=0, to=50, increment=1, textvariable=self.waste_var, width=5).grid(
            row=5, column=1, sticky=tk.W, pady=5
        )

        # Add material button
        ttk.Button(parent, text="Calculate & Add to List", command=self.add_material).grid(
            row=6, column=0, columnspan=2, pady=10
        )

        # Explanation text
        explanation = ttk.Label(parent,
                                text="This calculator estimates the amount of leather needed based on dimensions and waste factor. Adjust values as needed for your specific project.",
                                wraplength=300, justify=tk.LEFT)
        explanation.grid(row=7, column=0, columnspan=2, sticky=tk.W, pady=10)

        # Configure grid
        parent.columnconfigure(1, weight=1)

    def _create_material_list(self, parent):
        """Create a treeview to display added materials.

        Args:
            parent: Parent widget for material list
        """
        # Create treeview with scrollbar
        columns = ("material", "dimensions", "area", "thickness", "layers", "total_area", "waste")
        self.tree = ttk.Treeview(parent, columns=columns, show="headings", selectmode="browse")

        # Configure columns
        self.tree.heading("material", text="Material Type")
        self.tree.heading("dimensions", text="Dimensions")
        self.tree.heading("area", text="Area")
        self.tree.heading("thickness", text="Thickness")
        self.tree.heading("layers", text="Layers")
        self.tree.heading("total_area", text="Total Area")
        self.tree.heading("waste", text="With Waste")

        self.tree.column("material", width=120)
        self.tree.column("dimensions", width=100, anchor=tk.CENTER)
        self.tree.column("area", width=80, anchor=tk.CENTER)
        self.tree.column("thickness", width=80, anchor=tk.CENTER)
        self.tree.column("layers", width=60, anchor=tk.CENTER)
        self.tree.column("total_area", width=80, anchor=tk.CENTER)
        self.tree.column("waste", width=80, anchor=tk.CENTER)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Pack widgets
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind events
        self.tree.bind("<Button-3>", self.show_context_menu)  # Right-click
        self.tree.bind("<Delete>", lambda e: self.delete_selected_material())

    def _create_calculation_summary(self, parent):
        """Create summary section for material calculations.

        Args:
            parent: Parent widget for calculation summary
        """
        # Summary grid
        summary_frame = ttk.Frame(parent, padding=10)
        summary_frame.pack(fill=tk.BOTH)

        # Total leather area
        ttk.Label(summary_frame, text="Total Leather Area:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.total_area_var = tk.StringVar(value="0.0 cm²")
        ttk.Label(summary_frame, textvariable=self.total_area_var).grid(row=0, column=1, sticky=tk.E, padx=5, pady=2)

        # With waste factor
        ttk.Label(summary_frame, text="With Waste Factor:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.total_with_waste_var = tk.StringVar(value="0.0 cm²")
        ttk.Label(summary_frame, textvariable=self.total_with_waste_var).grid(row=1, column=1, sticky=tk.E, padx=5,
                                                                              pady=2)

        # In square feet
        ttk.Label(summary_frame, text="Square Feet Needed:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.total_sqft_var = tk.StringVar(value="0.0 ft²")
        ttk.Label(summary_frame, textvariable=self.total_sqft_var).grid(row=2, column=1, sticky=tk.E, padx=5, pady=2)

        # Configure grid
        summary_frame.columnconfigure(1, weight=1)

    def add_material(self):
        """Add a new material to the list based on current input values."""
        try:
            # Get values from input fields
            leather_type = self.leather_type_var.get()
            width = self.width_var.get()
            height = self.height_var.get()
            thickness = self.thickness_var.get()
            layers = self.layers_var.get()
            waste_factor = self.waste_var.get() / 100.0

            # Calculate area
            area = width * height
            total_area = area * layers
            with_waste = total_area * (1 + waste_factor)

            # Format for display
            dimensions = f"{width:.1f} × {height:.1f} cm"
            area_str = f"{area:.1f} cm²"
            thickness_str = f"{thickness:.1f} mm"
            total_area_str = f"{total_area:.1f} cm²"
            with_waste_str = f"{with_waste:.1f} cm²"

            # Add to tree
            self.tree.insert("", "end", values=(
                leather_type, dimensions, area_str, thickness_str,
                layers, total_area_str, with_waste_str
            ))

            # Add to materials list
            self.materials.append({
                'type': leather_type,
                'width': width,
                'height': height,
                'area': area,
                'thickness': thickness,
                'layers': layers,
                'total_area': total_area,
                'with_waste': with_waste
            })

            # Update summary
            self.recalculate_summary()

            # Log
            logger.info(f"Added material: {leather_type}, {dimensions}, {layers} layers")

        except Exception as e:
            logger.error(f"Error adding material: {str(e)}", exc_info=True)
            self.show_error("Input Error", f"Failed to add material: {str(e)}")

    def delete_selected_material(self):
        """Delete the selected material from the list."""
        selected = self.tree.selection()
        if not selected:
            return

        try:
            # Get selected index
            index = self.tree.index(selected[0])

            # Remove from tree and materials list
            self.tree.delete(selected[0])
            if 0 <= index < len(self.materials):
                del self.materials[index]

            # Update summary
            self.recalculate_summary()

            logger.info("Deleted selected material")

        except Exception as e:
            logger.error(f"Error deleting material: {str(e)}", exc_info=True)
            self.show_error("Error", f"Failed to delete material: {str(e)}")

    def show_context_menu(self, event):
        """Show context menu for material list.

        Args:
            event: Event that triggered the context menu
        """
        # Select row under mouse
        item_id = self.tree.identify_row(event.y)
        if item_id:
            self.tree.selection_set(item_id)

            # Create popup menu
            menu = tk.Menu(self, tearoff=0)
            menu.add_command(label="Delete", command=self.delete_selected_material)
            menu.post(event.x_root, event.y_root)

    def recalculate_summary(self):
        """Recalculate and update summary metrics."""
        total_area = sum(item['total_area'] for item in self.materials)
        total_with_waste = sum(item['with_waste'] for item in self.materials)

        # Convert to square feet (1 sq cm = 0.00107639 sq ft)
        total_sqft = total_with_waste * 0.00107639

        # Update displays
        self.total_area_var.set(f"{total_area:.1f} cm²")
        self.total_with_waste_var.set(f"{total_with_waste:.1f} cm²")
        self.total_sqft_var.set(f"{total_sqft:.2f} ft²")

    def export_material_report(self):
        """Export material calculation report."""
        # This would normally save to a CSV or similar
        messagebox.showinfo("Export", "Material report export would be implemented here.")
        logger.info("Material report export requested")

    def _reset_all(self):
        """Reset all inputs and calculations."""
        # Clear treeview
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Clear materials list
        self.materials.clear()

        # Reset summary
        self.recalculate_summary()

        # Reset inputs to defaults
        self.project_type_var.set("Wallet")
        self.width_var.set(10.0)
        self.height_var.set(8.0)
        self.thickness_var.set(2.0)
        self.leather_type_var.set("Vegetable Tanned")
        self.layers_var.set(2)
        self.waste_var.set(15.0)

        logger.info("Reset all fields and calculations")

    def load_initial_materials(self):
        """Load some initial materials for demonstration."""
        # Example materials
        example_materials = [
            {
                'type': 'Vegetable Tanned',
                'width': 20.0,
                'height': 10.0,
                'thickness': 2.0,
                'layers': 2
            },
            {
                'type': 'Chrome Tanned',
                'width': 15.0,
                'height': 12.0,
                'thickness': 1.2,
                'layers': 1
            }
        ]

        # Add each example material
        for material in example_materials:
            self.leather_type_var.set(material['type'])
            self.width_var.set(material['width'])
            self.height_var.set(material['height'])
            self.thickness_var.set(material['thickness'])
            self.layers_var.set(material['layers'])
            self.add_material()

        logger.info("Loaded initial material examples")