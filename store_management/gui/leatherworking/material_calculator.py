# Path: gui/leatherworking/material_calculator.py
"""
Material Calculator for precise material estimation in leatherworking projects.
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from typing import Dict, List, Optional


class MaterialCalculator(tk.Frame):
    """
    A comprehensive material calculation and estimation tool for leatherworking.
    """

    def __init__(self, parent, controller=None):
        """
        Initialize the material calculator.

        Args:
            parent (tk.Tk or tk.Frame): Parent widget
            controller (object, optional): Application controller for navigation
        """
        super().__init__(parent)
        self.controller = controller

        # Styling
        self.style = ttk.Style()
        self.style.theme_use('clam')

        # Material data storage
        self.materials: List[Dict[str, Any]] = []

        # Setup UI components
        self._setup_layout()
        self._create_material_input()
        self._create_material_list()
        self._create_calculation_summary()

        # Load initial data
        self.load_initial_materials()

    def _setup_layout(self):
        """
        Configure grid layout for material calculator.
        """
        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=1)

        # Create main sections
        self.input_frame = ttk.LabelFrame(self, text="Material Input", padding=(10, 10))
        self.input_frame.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)

        self.summary_frame = ttk.LabelFrame(self, text="Calculation Summary", padding=(10, 10))
        self.summary_frame.grid(row=0, column=1, sticky='nsew', padx=5, pady=5)

        self.list_frame = ttk.LabelFrame(self, text="Material List", padding=(10, 10))
        self.list_frame.grid(row=1, column=0, columnspan=2, sticky='nsew', padx=5, pady=5)

    def _create_material_input(self):
        """
        Create input fields for material calculations.
        """
        # Material Type Dropdown
        ttk.Label(self.input_frame, text="Material Type:").grid(row=0, column=0, sticky='w', pady=5)
        self.material_type_var = tk.StringVar()
        material_types = [
            "Full Grain Leather",
            "Top Grain Leather",
            "Suede",
            "Hardware",
            "Thread",
            "Lining"
        ]
        material_type_dropdown = ttk.Combobox(
            self.input_frame,
            textvariable=self.material_type_var,
            values=material_types,
            state="readonly"
        )
        material_type_dropdown.grid(row=0, column=1, sticky='ew', pady=5)

        # Dimensions
        input_fields = [
            ("Width (cm)", "width_var"),
            ("Length (cm)", "length_var"),
            ("Quantity", "quantity_var"),
            ("Cost per Unit", "cost_var")
        ]

        for idx, (label, var_name) in enumerate(input_fields, start=1):
            ttk.Label(self.input_frame, text=f"{label}:").grid(row=idx, column=0, sticky='w', pady=5)
            var = tk.StringVar()
            setattr(self, var_name, var)
            entry = ttk.Entry(self.input_frame, textvariable=var)
            entry.grid(row=idx, column=1, sticky='ew', pady=5)

        # Add Material Button
        add_btn = ttk.Button(
            self.input_frame,
            text="Add Material",
            command=self.add_material
        )
        add_btn.grid(row=len(input_fields) + 1, column=0, columnspan=2, sticky='ew', pady=10)

    def _create_material_list(self):
        """
        Create a treeview to display added materials.
        """
        columns = ('Type', 'Width', 'Length', 'Qty', 'Unit Cost', 'Total Cost')
        self.material_tree = ttk.Treeview(
            self.list_frame,
            columns=columns,
            show='headings'
        )

        # Configure columns
        for col in columns:
            self.material_tree.heading(col, text=col)
            self.material_tree.column(col, width=100, anchor='center')

        self.material_tree.pack(fill='both', expand=True)

        # Scrollbar
        scrollbar = ttk.Scrollbar(
            self.list_frame,
            orient='vertical',
            command=self.material_tree.yview
        )
        self.material_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side='right', fill='y')

        # Context menu for deletion
        self.material_tree_context_menu = tk.Menu(self, tearoff=0)
        self.material_tree_context_menu.add_command(
            label="Delete",
            command=self.delete_selected_material
        )
        self.material_tree.bind('<Button-3>', self.show_context_menu)

    def _create_calculation_summary(self):
        """
        Create summary section for material calculations.
        """
        summary_metrics = [
            ("Total Materials", "total_materials"),
            ("Total Area (sq cm)", "total_area"),
            ("Total Cost", "total_cost"),
            ("Estimated Wastage (%)", "wastage_percentage")
        ]

        for idx, (label, attr_name) in enumerate(summary_metrics):
            frame = ttk.Frame(self.summary_frame)
            frame.pack(fill='x', pady=5)

            ttk.Label(frame, text=label, width=20).pack(side='left')
            value_label = ttk.Label(frame, text="0", width=10)
            value_label.pack(side='right')
            setattr(self, f"{attr_name}_label", value_label)

        # Calculate Buttons
        btn_frame = ttk.Frame(self.summary_frame)
        btn_frame.pack(fill='x', pady=10)

        calculate_btn = ttk.Button(
            btn_frame,
            text="Recalculate",
            command=self.recalculate_summary
        )
        calculate_btn.pack(side='left', expand=True, fill='x', padx=5)

        export_btn = ttk.Button(
            btn_frame,
            text="Export Report",
            command=self.export_material_report
        )
        export_btn.pack(side='right', expand=True, fill='x', padx=5)

    def add_material(self):
        """
        Add a new material to the list.
        """
        try:
            # Validate inputs
            material_type = self.material_type_var.get()
            width = float(self.width_var.get())
            length = float(self.length_var.get())
            quantity = int(self.quantity_var.get())
            cost_per_unit = float(self.cost_var.get())

            # Calculate total cost
            total_cost = width * length * quantity * cost_per_unit

            # Create material entry
            material = {
                'type': material_type,
                'width': width,
                'length': length,
                'quantity': quantity,
                'unit_cost': cost_per_unit,
                'total_cost': total_cost
            }

            # Add to materials list
            self.materials.append(material)

            # Add to treeview
            self.material_tree.insert('', 'end', values=(
                material['type'],
                f"{width:.2f}",
                f"{length:.2f}",
                quantity,
                f"${cost_per_unit:.2f}",
                f"${total_cost:.2f}"
            ))

            # Recalculate summary
            self.recalculate_summary()

            # Clear input fields
            self.material_type_var.set('')
            for var in [self.width_var, self.length_var, self.quantity_var, self.cost_var]:
                var.set('')

        except ValueError as e:
            messagebox.showerror("Input Error", f"Invalid input: {str(e)}")

    def delete_selected_material(self):
        """
        Delete the selected material from the list.
        """
        selected_item = self.material_tree.selection()
        if not selected_item:
            messagebox.showwarning("Selection", "Please select a material to delete.")
            return

        # Remove from treeview
        self.material_tree.delete(selected_item[0])

        # Remove from materials list
        del self.materials[self.material_tree.index(selected_item[0])]

        # Recalculate summary
        self.recalculate_summary()

    def show_context_menu(self, event):
        """
        Show context menu for material list.
        """
        # Select the row under the cursor
        iid = self.material_tree.identify_row(event.y)
        if iid:
            self.material_tree.selection_set(iid)
            self.material_tree_context_menu.post(event.x_root, event.y_root)

    def recalculate_summary(self):
        """
        Recalculate and update summary metrics.
        """
        # Total materials
        total_materials = len(self.materials)
        self.total_materials_label.config(text=str(total_materials))

        # Total area
        total_area = sum(m['width'] * m['length'] * m['quantity'] for m in self.materials)
        self.total_area_label.config(text=f"{total_area:.2f}")

        # Total cost
        total_cost = sum(m['total_cost'] for m in self.materials)
        self.total_cost_label.config(text=f"${total_cost:.2f}")

        # Estimated wastage (mock calculation)
        wastage_percentage = min(15, total_materials * 2)  # Simple mock calculation
        self.wastage_percentage_label.config(text=f"{wastage_percentage:.2f}%")

    def export_material_report(self):
        """
        Export material calculation report.
        """
        try:
            filename = simpledialog.askstring(
                "Export Report",
                "Enter filename for report:",
                initialvalue="material_report.csv"
            )

            if not filename:
                return

            # Mock export functionality
            with open(filename, 'w') as f:
                # Write CSV headers
                f.write("Material Type,Width,Length,Quantity,Unit Cost,Total Cost\n")

                # Write material data
                for m in self.materials:
                    f.write(
                        f"{m['type']},"
                        f"{m['width']},"
                        f"{m['length']},"
                        f"{m['quantity']},"
                        f"{m['unit_cost']},"
                        f"{m['total_cost']}\n"
                    )

            messagebox.showinfo("Export Successful", f"Report exported to {filename}")

        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    def load_initial_materials(self):
        """
        Load some initial materials for demonstration.
        """
        initial_materials = [
            {
                'type': 'Full Grain Leather',
                'width': 50,
                'length': 100,
                'quantity': 2,
                'unit_cost': 15.50,
                'total_cost': 1550
            }
        ]

        for material in initial_materials:
            self.materials.append(material)
            self.material_tree.insert('', 'end', values=(
                material['type'],
                f"{material['width']:.2f}",
                f"{material['length']:.2f}",
                material['quantity'],
                f"${material['unit_cost']:.2f}",
                f"${material['total_cost']:.2f}"
            ))

        self.recalculate_summary()


def main():
    """
    Standalone testing of the MaterialCalculator.
    """
    root = tk.Tk()
    root.title("Leatherworking Material Calculator")
    root.geometry("800x600")

    calculator = MaterialCalculator(root)
    calculator.pack(fill='both', expand=True)

    root.mainloop()


if __name__ == '__main__':
    main()