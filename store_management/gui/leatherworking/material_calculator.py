# gui/leatherworking/material_calculator.py
import logging
import tkinter as tk
from tkinter import messagebox, ttk, filedialog
from typing import Any, Dict, List, Optional

from gui.base_view import BaseView
from services.interfaces.material_service import IMaterialService
from services.interfaces.project_service import IProjectService


class MaterialCalculator(BaseView):
    """
    Calculator for estimating material requirements for leatherworking projects.

    This view allows users to:
    - Input dimensions and parameters for leather pieces
    - Calculate total area, weight, and cost
    - Save and export material calculations
    - Plan material usage efficiently
    """

    def __init__(self, parent: tk.Widget, app: Any):
        """
        Initialize the material calculator.

        Args:
            parent: Parent widget
            app: Application instance with service access
        """
        super().__init__(parent, app)
        self.materials = []
        self.current_id = 0
        self._setup_layout()
        self.load_initial_materials()

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

    def _setup_layout(self):
        """Configure the material calculator layout."""
        # Main container with vertical layout
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Title and description
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(title_frame, text="Material Calculator",
                  font=("TkDefaultFont", 14, "bold")).pack(side=tk.LEFT)

        # Split the view: left for input/list, right for summary
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Left panel
        left_panel = ttk.Frame(content_frame)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        # Input panel
        input_frame = ttk.LabelFrame(left_panel, text="Material Dimensions")
        input_frame.pack(fill=tk.X, pady=(0, 10))
        self._create_material_input(input_frame)

        # Material list
        list_frame = ttk.LabelFrame(left_panel, text="Material List")
        list_frame.pack(fill=tk.BOTH, expand=True)
        self._create_material_list(list_frame)

        # Right panel - Summary and stats
        right_panel = ttk.Frame(content_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        summary_frame = ttk.LabelFrame(right_panel, text="Calculation Summary")
        summary_frame.pack(fill=tk.BOTH, expand=True)
        self._create_calculation_summary(summary_frame)

        # Bottom action buttons
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(action_frame, text="Export Report", command=self.export_material_report).pack(side=tk.LEFT)
        ttk.Button(action_frame, text="Reset All", command=self._reset_all).pack(side=tk.LEFT, padx=5)

    def _create_material_input(self, parent):
        """
        Create input fields for material calculations.

        Args:
            parent: Parent widget for material input fields
        """
        # Grid for input fields
        grid_frame = ttk.Frame(parent)
        grid_frame.pack(fill=tk.X, padx=10, pady=10)

        # Row 1: Material name and type
        ttk.Label(grid_frame, text="Name:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.name_var = tk.StringVar()
        ttk.Entry(grid_frame, textvariable=self.name_var, width=20).grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)

        ttk.Label(grid_frame, text="Type:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.type_var = tk.StringVar()
        self.type_combo = ttk.Combobox(grid_frame, textvariable=self.type_var, width=15)
        self.type_combo['values'] = ('Vegetable Tan', 'Chrome Tan', 'Oil Tan', 'Latigo', 'Suede', 'Lining', 'Other')
        self.type_combo.grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)

        # Row 2: Dimensions
        ttk.Label(grid_frame, text="Length:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.length_var = tk.DoubleVar(value=0.0)
        ttk.Spinbox(grid_frame, from_=0, to=1000, increment=0.1, textvariable=self.length_var, width=10).grid(
            row=1, column=1, sticky=tk.W, padx=5, pady=5)

        ttk.Label(grid_frame, text="Width:").grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)
        self.width_var = tk.DoubleVar(value=0.0)
        ttk.Spinbox(grid_frame, from_=0, to=1000, increment=0.1, textvariable=self.width_var, width=10).grid(
            row=1, column=3, sticky=tk.W, padx=5, pady=5)

        # Units
        ttk.Label(grid_frame, text="Units:").grid(row=1, column=4, sticky=tk.W, padx=5, pady=5)
        self.units_var = tk.StringVar(value="cm")
        units_combo = ttk.Combobox(grid_frame, textvariable=self.units_var, width=5)
        units_combo['values'] = ('mm', 'cm', 'in')
        units_combo.grid(row=1, column=5, sticky=tk.W, padx=5, pady=5)
        units_combo.current(1)  # Default to cm

        # Row 3: Thickness and quantity
        ttk.Label(grid_frame, text="Thickness:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.thickness_var = tk.DoubleVar(value=2.0)  # Default 2mm
        ttk.Spinbox(grid_frame, from_=0, to=20, increment=0.1, textvariable=self.thickness_var, width=10).grid(
            row=2, column=1, sticky=tk.W, padx=5, pady=5)

        ttk.Label(grid_frame, text="Quantity:").grid(row=2, column=2, sticky=tk.W, padx=5, pady=5)
        self.quantity_var = tk.IntVar(value=1)
        ttk.Spinbox(grid_frame, from_=1, to=1000, textvariable=self.quantity_var, width=10).grid(
            row=2, column=3, sticky=tk.W, padx=5, pady=5)

        # Row 4: Price info
        ttk.Label(grid_frame, text="Price per unit:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.price_var = tk.DoubleVar(value=0.0)
        ttk.Spinbox(grid_frame, from_=0, to=10000, increment=0.1, textvariable=self.price_var, width=10).grid(
            row=3, column=1, sticky=tk.W, padx=5, pady=5)

        ttk.Label(grid_frame, text="Price unit:").grid(row=3, column=2, sticky=tk.W, padx=5, pady=5)
        self.price_unit_var = tk.StringVar(value="sq ft")
        price_unit_combo = ttk.Combobox(grid_frame, textvariable=self.price_unit_var, width=10)
        price_unit_combo['values'] = ('sq ft', 'sq m', 'piece')
        price_unit_combo.grid(row=3, column=3, sticky=tk.W, padx=5, pady=5)

        # Add button
        ttk.Button(grid_frame, text="Add Material", command=self.add_material).grid(
            row=4, column=0, columnspan=6, pady=10)

        # Configure grid columns to expand
        for i in range(6):
            grid_frame.columnconfigure(i, weight=1)

    def _create_material_list(self, parent):
        """
        Create a treeview to display added materials.

        Args:
            parent: Parent widget for material list
        """
        # Frame with treeview and scrollbar
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create the treeview
        columns = ("id", "name", "type", "dimensions", "area", "quantity", "cost")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings")

        # Define headings
        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="Name")
        self.tree.heading("type", text="Type")
        self.tree.heading("dimensions", text="Dimensions")
        self.tree.heading("area", text="Area")
        self.tree.heading("quantity", text="Qty")
        self.tree.heading("cost", text="Est. Cost")

        # Define columns
        self.tree.column("id", width=30, anchor=tk.CENTER)
        self.tree.column("name", width=100, anchor=tk.W)
        self.tree.column("type", width=80, anchor=tk.W)
        self.tree.column("dimensions", width=100, anchor=tk.CENTER)
        self.tree.column("area", width=80, anchor=tk.CENTER)
        self.tree.column("quantity", width=40, anchor=tk.CENTER)
        self.tree.column("cost", width=80, anchor=tk.E)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Pack elements
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind events
        self.tree.bind("<Double-1>", lambda e: self.delete_selected_material())
        self.tree.bind("<Button-3>", self.show_context_menu)

        # Context menu
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Delete", command=self.delete_selected_material)

    def _create_calculation_summary(self, parent):
        """
        Create summary section for material calculations.

        Args:
            parent: Parent widget for calculation summary
        """
        # Frame for summary content
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Total area
        ttk.Label(frame, text="Total Material Area:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.total_area_var = tk.StringVar(value="0.0 sq ft")
        ttk.Label(frame, textvariable=self.total_area_var, font=("TkDefaultFont", 10, "bold")).grid(
            row=0, column=1, sticky=tk.E, padx=5, pady=5)

        # Total cost
        ttk.Label(frame, text="Estimated Total Cost:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.total_cost_var = tk.StringVar(value="$0.00")
        ttk.Label(frame, textvariable=self.total_cost_var, font=("TkDefaultFont", 10, "bold")).grid(
            row=1, column=1, sticky=tk.E, padx=5, pady=5)

        # Total weight (estimated)
        ttk.Label(frame, text="Estimated Weight:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.total_weight_var = tk.StringVar(value="0.0 oz")
        ttk.Label(frame, textvariable=self.total_weight_var, font=("TkDefaultFont", 10, "bold")).grid(
            row=2, column=1, sticky=tk.E, padx=5, pady=5)

        # Number of pieces
        ttk.Label(frame, text="Total Pieces:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.total_pieces_var = tk.StringVar(value="0")
        ttk.Label(frame, textvariable=self.total_pieces_var, font=("TkDefaultFont", 10, "bold")).grid(
            row=3, column=1, sticky=tk.E, padx=5, pady=5)

        # Separator
        ttk.Separator(frame, orient=tk.HORIZONTAL).grid(row=4, column=0, columnspan=2, sticky=tk.EW, pady=10)

        # Waste factor
        ttk.Label(frame, text="Waste Factor (%):").grid(row=5, column=0, sticky=tk.W, padx=5, pady=5)
        self.waste_factor_var = tk.IntVar(value=15)  # Default 15% waste
        waste_spinbox = ttk.Spinbox(frame, from_=0, to=100, textvariable=self.waste_factor_var, width=10)
        waste_spinbox.grid(row=5, column=1, sticky=tk.E, padx=5, pady=5)
        waste_spinbox.bind("<KeyRelease>", lambda e: self.recalculate_summary())

        # Notes
        ttk.Label(frame, text="Notes:").grid(row=6, column=0, sticky=tk.NW, padx=5, pady=5)
        self.notes_text = tk.Text(frame, height=4, width=30)
        self.notes_text.grid(row=6, column=1, sticky=tk.EW, padx=5, pady=5)

        # Configure grid
        frame.columnconfigure(1, weight=1)

    def add_material(self):
        """Add a new material to the list based on current input values."""
        try:
            # Validate inputs
            name = self.name_var.get()
            if not name:
                messagebox.showwarning("Input Error", "Please enter a material name.")
                return

            length = self.length_var.get()
            width = self.width_var.get()
            if length <= 0 or width <= 0:
                messagebox.showwarning("Input Error", "Length and width must be greater than zero.")
                return

            material_type = self.type_var.get()
            thickness = self.thickness_var.get()
            quantity = self.quantity_var.get()
            price = self.price_var.get()
            units = self.units_var.get()
            price_unit = self.price_unit_var.get()

            # Convert dimensions to standard units (sq ft)
            length_ft = length
            width_ft = width

            # Convert to feet based on input units
            if units == "cm":
                length_ft = length / 30.48  # cm to ft
                width_ft = width / 30.48
            elif units == "mm":
                length_ft = length / 304.8  # mm to ft
                width_ft = width / 304.8
            elif units == "in":
                length_ft = length / 12  # in to ft
                width_ft = width / 12

            # Calculate area
            area_sq_ft = length_ft * width_ft

            # Calculate cost based on price unit
            cost = 0
            if price_unit == "sq ft":
                cost = area_sq_ft * price * quantity
            elif price_unit == "sq m":
                # Convert sq ft to sq m for pricing
                area_sq_m = area_sq_ft * 0.092903
                cost = area_sq_m * price * quantity
            elif price_unit == "piece":
                cost = price * quantity

            # Format for display
            area_display = f"{area_sq_ft:.2f} sq ft"
            dimensions = f"{length:.1f}x{width:.1f} {units}"
            cost_display = f"${cost:.2f}"

            # Get next ID
            self.current_id += 1

            # Add to tree
            self.tree.insert("", tk.END, values=(
                self.current_id,
                name,
                material_type,
                dimensions,
                area_display,
                quantity,
                cost_display
            ))

            # Add to materials list
            self.materials.append({
                "id": self.current_id,
                "name": name,
                "type": material_type,
                "length": length,
                "width": width,
                "units": units,
                "thickness": thickness,
                "quantity": quantity,
                "area_sq_ft": area_sq_ft,
                "price": price,
                "price_unit": price_unit,
                "cost": cost
            })

            # Update summary
            self.recalculate_summary()

            # Clear input fields
            self.name_var.set("")
            self.length_var.set(0.0)
            self.width_var.set(0.0)
            self.price_var.set(0.0)

            # Show confirmation
            self.set_status(f"Added material: {name} - {area_display}")

        except Exception as e:
            logging.error(f"Error adding material: {str(e)}")
            messagebox.showerror("Error", f"Failed to add material: {str(e)}")

    def delete_selected_material(self):
        """Delete the selected material from the list."""
        selected = self.tree.selection()
        if not selected:
            return

        item_id = self.tree.item(selected[0], "values")[0]

        # Remove from tree
        self.tree.delete(selected[0])

        # Remove from materials list
        self.materials = [m for m in self.materials if m["id"] != int(item_id)]

        # Update summary
        self.recalculate_summary()

        self.set_status("Material removed")

    def show_context_menu(self, event):
        """
        Show context menu for material list.

        Args:
            event: Event that triggered the context menu
        """
        # Select the item under cursor
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def recalculate_summary(self):
        """Recalculate and update summary metrics."""
        try:
            # Calculate totals
            total_area = sum(m["area_sq_ft"] * m["quantity"] for m in self.materials)
            total_cost = sum(m["cost"] for m in self.materials)
            total_pieces = sum(m["quantity"] for m in self.materials)

            # Apply waste factor
            waste_factor = self.waste_factor_var.get() / 100.0
            adjusted_area = total_area * (1 + waste_factor)
            adjusted_cost = total_cost * (1 + waste_factor)

            # Estimate weight (rough calculation based on leather thickness)
            # Assumption: 1 sq ft of 1mm thick leather weighs approximately 2 oz
            total_weight = 0
            for m in self.materials:
                thickness_mm = m["thickness"]
                if m["type"] in ["Vegetable Tan", "Chrome Tan", "Oil Tan", "Latigo"]:
                    # For leather types
                    weight_per_sqft = thickness_mm * 2  # 2 oz per sq ft per mm
                    material_weight = m["area_sq_ft"] * m["quantity"] * weight_per_sqft
                    total_weight += material_weight

            # Update display
            self.total_area_var.set(f"{adjusted_area:.2f} sq ft")
            self.total_cost_var.set(f"${adjusted_cost:.2f}")
            self.total_weight_var.set(f"{total_weight:.1f} oz")
            self.total_pieces_var.set(f"{total_pieces}")

        except Exception as e:
            logging.error(f"Error calculating summary: {str(e)}")

    def export_material_report(self):
        """Export material calculation report."""
        try:
            if not self.materials:
                messagebox.showinfo("Export", "No materials to export.")
                return

            # Get file path
            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("CSV files", "*.csv"), ("All files", "*.*")],
                title="Export Material Report"
            )

            if not file_path:
                return

            # Create report content
            lines = ["Material Calculation Report", "=" * 30, ""]

            # Add summary
            lines.append(f"Total Area: {self.total_area_var.get()}")
            lines.append(f"Total Cost: {self.total_cost_var.get()}")
            lines.append(f"Est. Weight: {self.total_weight_var.get()}")
            lines.append(f"Total Pieces: {self.total_pieces_var.get()}")
            lines.append(f"Waste Factor: {self.waste_factor_var.get()}%")
            lines.append("")

            # Add notes if present
            notes = self.notes_text.get("1.0", tk.END).strip()
            if notes:
                lines.append("Notes:")
                lines.append(notes)
                lines.append("")

            # Add materials
            lines.append("Material Details:")
            lines.append("-" * 30)

            for m in self.materials:
                lines.append(f"Name: {m['name']} ({m['type']})")
                lines.append(f"Dimensions: {m['length']}x{m['width']} {m['units']}, Thickness: {m['thickness']}mm")
                lines.append(f"Area: {m['area_sq_ft']:.2f} sq ft, Quantity: {m['quantity']}")
                lines.append(f"Cost: ${m['cost']:.2f}")
                lines.append("-" * 30)

            # Write to file
            with open(file_path, 'w') as f:
                f.write("\n".join(lines))

            self.set_status(f"Report exported to {file_path}")
            messagebox.showinfo("Export Successful", f"Report exported to {file_path}")

        except Exception as e:
            logging.error(f"Error exporting report: {str(e)}")
            messagebox.showerror("Export Error", f"Failed to export report: {str(e)}")

    def _reset_all(self):
        """Reset all inputs and calculations."""
        confirm = messagebox.askyesno("Confirm Reset",
                                      "Are you sure you want to clear all materials and reset the calculator?")
        if not confirm:
            return

        # Clear materials
        self.materials = []
        self.current_id = 0

        # Clear tree
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Reset summary
        self.total_area_var.set("0.0 sq ft")
        self.total_cost_var.set("$0.00")
        self.total_weight_var.set("0.0 oz")
        self.total_pieces_var.set("0")

        # Clear notes
        self.notes_text.delete("1.0", tk.END)

        self.set_status("Calculator reset")

    def load_initial_materials(self):
        """Load some initial materials for demonstration."""
        # Only load example data if no materials exist
        if self.materials:
            return

        # Example leather materials
        examples = [
            {
                "name": "Main Body",
                "type": "Vegetable Tan",
                "length": 30,
                "width": 15,
                "units": "cm",
                "thickness": 2.0,
                "quantity": 1,
                "price": 12.99,
                "price_unit": "sq ft"
            },
            {
                "name": "Pocket",
                "type": "Vegetable Tan",
                "length": 12,
                "width": 8,
                "units": "cm",
                "thickness": 1.2,
                "quantity": 2,
                "price": 12.99,
                "price_unit": "sq ft"
            },
            {
                "name": "Lining",
                "type": "Lining",
                "length": 28,
                "width": 13,
                "units": "cm",
                "thickness": 0.8,
                "quantity": 1,
                "price": 6.99,
                "price_unit": "sq ft"
            }
        ]

        # Add each example
        for example in examples:
            # Set form values
            self.name_var.set(example["name"])
            self.type_var.set(example["type"])
            self.length_var.set(example["length"])
            self.width_var.set(example["width"])
            self.units_var.set(example["units"])
            self.thickness_var.set(example["thickness"])
            self.quantity_var.set(example["quantity"])
            self.price_var.set(example["price"])
            self.price_unit_var.set(example["price_unit"])

            # Add to list
            self.add_material()

    def set_status(self, message: str):
        """Set the status message in the application."""
        # Assuming you have a status label in your UI to display messages
        if hasattr(self, 'status_label'):
            self.status_label.config(text=message)
        else:
            logging.info(message)  # Fallback to logging if no status label exists


class MockApp:
    """Mock application for standalone testing."""

    def get_service(self, service_type):
        """
        Mock service getter.

        Args:
            service_type: The service interface to get

        Returns:
            None
        """
        return None


def main():
    """Main function for standalone testing."""
    root = tk.Tk()
    root.title("Material Calculator")
    root.geometry("800x600")

    app = MockApp()
    calculator_view = MaterialCalculator(root, app)
    calculator_view.pack(fill=tk.BOTH, expand=True)

    root.mainloop()


if __name__ == "__main__":
    main()
