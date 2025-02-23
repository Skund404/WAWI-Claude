# Path: gui/leatherworking/cost_estimator.py
"""
Cost Estimator for calculating and tracking expenses in leatherworking projects.
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from typing import List, Dict, Any, Optional


class CostEstimator(tk.Frame):
    """
    A comprehensive cost estimation and tracking tool for leatherworking projects.
    """

    def __init__(self, parent, controller=None):
        """
        Initialize the cost estimator.

        Args:
            parent (tk.Tk or tk.Frame): Parent widget
            controller (object, optional): Application controller for navigation
        """
        super().__init__(parent)
        self.controller = controller

        # Styling
        self.style = ttk.Style()
        self.style.theme_use('clam')

        # Cost tracking data
        self.cost_items: List[Dict[str, Any]] = []

        # Setup UI components
        self._setup_layout()
        self._create_cost_input()
        self._create_cost_breakdown()
        self._create_cost_visualization()
        self._create_cost_summary()

        # Load initial data
        self.load_initial_costs()

    def _setup_layout(self):
        """
        Configure grid layout for cost estimator.
        """
        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=1)

        # Create main sections
        self.input_frame = ttk.LabelFrame(self, text="Cost Input", padding=(10, 10))
        self.input_frame.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)

        self.visualization_frame = ttk.LabelFrame(self, text="Cost Breakdown", padding=(10, 10))
        self.visualization_frame.grid(row=0, column=1, sticky='nsew', padx=5, pady=5)

        self.summary_frame = ttk.LabelFrame(self, text="Cost Summary", padding=(10, 10))
        self.summary_frame.grid(row=1, column=0, columnspan=2, sticky='nsew', padx=5, pady=5)

    def _create_cost_input(self):
        """
        Create input fields for adding cost items.
        """
        # Cost Category
        ttk.Label(self.input_frame, text="Cost Category:").grid(row=0, column=0, sticky='w', pady=5)
        self.category_var = tk.StringVar()
        cost_categories = [
            "Leather",
            "Hardware",
            "Thread",
            "Tools",
            "Adhesive",
            "Lining",
            "Labor",
            "Miscellaneous"
        ]
        category_dropdown = ttk.Combobox(
            self.input_frame,
            textvariable=self.category_var,
            values=cost_categories,
            state="readonly",
            width=27
        )
        category_dropdown.grid(row=0, column=1, sticky='ew', pady=5)

        # Item Name
        ttk.Label(self.input_frame, text="Item Name:").grid(row=1, column=0, sticky='w', pady=5)
        self.item_name_var = tk.StringVar()
        item_name_entry = ttk.Entry(
            self.input_frame,
            textvariable=self.item_name_var,
            width=30
        )
        item_name_entry.grid(row=1, column=1, sticky='ew', pady=5)

        # Quantity
        ttk.Label(self.input_frame, text="Quantity:").grid(row=2, column=0, sticky='w', pady=5)
        self.quantity_var = tk.StringVar(value="1")
        quantity_entry = ttk.Entry(
            self.input_frame,
            textvariable=self.quantity_var,
            width=30
        )
        quantity_entry.grid(row=2, column=1, sticky='ew', pady=5)

        # Unit Price
        ttk.Label(self.input_frame, text="Unit Price ($):").grid(row=3, column=0, sticky='w', pady=5)
        self.unit_price_var = tk.StringVar()
        unit_price_entry = ttk.Entry(
            self.input_frame,
            textvariable=self.unit_price_var,
            width=30
        )
        unit_price_entry.grid(row=3, column=1, sticky='ew', pady=5)

        # Total Hours (for Labor)
        ttk.Label(self.input_frame, text="Hours (Labor):").grid(row=4, column=0, sticky='w', pady=5)
        self.hours_var = tk.StringVar(value="0")
        hours_entry = ttk.Entry(
            self.input_frame,
            textvariable=self.hours_var,
            width=30
        )
        hours_entry.grid(row=4, column=1, sticky='ew', pady=5)

        # Hourly Rate (for Labor)
        ttk.Label(self.input_frame, text="Hourly Rate ($):").grid(row=5, column=0, sticky='w', pady=5)
        self.hourly_rate_var = tk.StringVar(value="25")
        hourly_rate_entry = ttk.Entry(
            self.input_frame,
            textvariable=self.hourly_rate_var,
            width=30
        )
        hourly_rate_entry.grid(row=5, column=1, sticky='ew', pady=5)

        # Add Cost Item Button
        add_btn = ttk.Button(
            self.input_frame,
            text="Add Cost Item",
            command=self.add_cost_item
        )
        add_btn.grid(row=6, column=0, columnspan=2, sticky='ew', pady=10)

    def _create_cost_breakdown(self):
        """
        Create a treeview to display cost breakdown.
        """
        columns = ('Category', 'Item', 'Quantity', 'Unit Price', 'Total Cost')
        self.cost_tree = ttk.Treeview(
            self.visualization_frame,
            columns=columns,
            show='headings'
        )

        # Configure columns
        for col in columns:
            self.cost_tree.heading(col, text=col)
            self.cost_tree.column(col, width=100, anchor='center')

        self.cost_tree.pack(fill='both', expand=True)

        # Scrollbar
        scrollbar = ttk.Scrollbar(
            self.visualization_frame,
            orient='vertical',
            command=self.cost_tree.yview
        )
        self.cost_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side='right', fill='y')

        # Context menu
        self.cost_tree_context_menu = tk.Menu(self, tearoff=0)
        self.cost_tree_context_menu.add_command(
            label="Delete",
            command=self.delete_selected_cost_item
        )
        self.cost_tree.bind('<Button-3>', self.show_context_menu)

    def _create_cost_visualization(self):
        """
        Create pie chart for cost distribution.
        """
        # Create matplotlib figure
        self.figure, self.ax = plt.subplots(figsize=(5, 4), dpi=100)
        self.ax.set_title("Cost Distribution")

        # Embed matplotlib figure in Tkinter
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.visualization_frame)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill='both', expand=True)

    def _create_cost_summary(self):
        """
        Create summary section for cost tracking.
        """
        summary_metrics = [
            ("Total Materials Cost", "materials_cost"),
            ("Labor Cost", "labor_cost"),
            ("Total Project Cost", "total_cost"),
            ("Estimated Profit Margin (%)", "profit_margin")
        ]

        for idx, (label, attr_name) in enumerate(summary_metrics):
            frame = ttk.Frame(self.summary_frame)
            frame.pack(fill='x', pady=5)

            ttk.Label(frame, text=label, width=25).pack(side='left')
            value_label = ttk.Label(frame, text="$0.00", width=15)
            value_label.pack(side='right')
            setattr(self, f"{attr_name}_label", value_label)

        # Buttons
        btn_frame = ttk.Frame(self.summary_frame)
        btn_frame.pack(fill='x', pady=10)

        calculate_btn = ttk.Button(
            btn_frame,
            text="Recalculate",
            command=self.recalculate_costs
        )
        calculate_btn.pack(side='left', expand=True, fill='x', padx=5)

        export_btn = ttk.Button(
            btn_frame,
            text="Export Report",
            command=self.export_cost_report
        )
        export_btn.pack(side='right', expand=True, fill='x', padx=5)

    def add_cost_item(self):
        """
        Add a new cost item to the breakdown.
        """
        try:
            # Validate inputs
            category = self.category_var.get()
            if not category:
                raise ValueError("Please select a cost category")

            item_name = self.item_name_var.get().strip()
            if not item_name:
                raise ValueError("Item name cannot be empty")

            quantity = float(self.quantity_var.get())
            if quantity <= 0:
                raise ValueError("Quantity must be a positive number")

            # Handle special case for labor
            if category == "Labor":
                hours = float(self.hours_var.get())
                hourly_rate = float(self.hourly_rate_var.get())
                unit_price = hourly_rate
                total_cost = hours * hourly_rate
            else:
                unit_price = float(self.unit_price_var.get())
                total_cost = quantity * unit_price

            # Create cost item
            cost_item = {
                'category': category,
                'item_name': item_name,
                'quantity': quantity,
                'unit_price': unit_price,
                'total_cost': total_cost
            }

            # Add to cost items list
            self.cost_items.append(cost_item)

            # Add to treeview
            self.cost_tree.insert('', 'end', values=(
                category,
                item_name,
                f"{quantity}",
                f"${unit_price:.2f}",
                f"${total_cost:.2f}"
            ))

            # Recalculate costs
            self.recalculate_costs()

            # Clear input fields
            self.category_var.set('')
            self.item_name_var.set('')
            self.quantity_var.set('1')
            self.unit_price_var.set('')
            self.hours_var.set('0')
            self.hourly_rate_var.set('25')

        except ValueError as e:
            messagebox.showerror("Input Error", str(e))

    def recalculate_costs(self):
        """
        Recalculate and update cost summary.
        """
        # Calculate material costs
        materials_cost = sum(
            item['total_cost'] for item in self.cost_items
            if item['category'] != 'Labor'
        )
        self.materials_cost_label.config(text=f"${materials_cost:.2f}")

        # Calculate labor costs
        labor_cost = sum(
            item['total_cost'] for item in self.cost_items
            if item['category'] == 'Labor'
        )
        self.labor_cost_label.config(text=f"${labor_cost:.2f}")

        # Total project cost
        total_cost = materials_cost + labor_cost
        self.total_cost_label.config(text=f"${total_cost:.2f}")

        # Estimated selling price (markup of 2x)
        estimated_selling_price = total_cost * 2
        estimated_profit = estimated_selling_price - total_cost

        # Profit margin calculation
        profit_margin = (estimated_profit / estimated_selling_price) * 100 if estimated_selling_price > 0 else 0
        self.profit_margin_label.config(text=f"{profit_margin:.2f}%")

        # Update cost distribution pie chart
        self._update_cost_distribution_chart()

    def _update_cost_distribution_chart(self):
        """
        Update pie chart showing cost distribution.
        """
        # Clear previous plot
        self.ax.clear()
        self.ax.set_title("Cost Distribution")

        # Prepare data for pie chart
        categories = {}
        for item in self.cost_items:
            categories[item['category']] = categories.get(
                item['category'], 0
            ) + item['total_cost']

        # Create pie chart
        if categories:
            self.ax.pie(
                list(categories.values()),
                labels=list(categories.keys()),
                autopct='%1.1f%%'
            )
        else:
            self.ax.text(0.5, 0.5, "No Cost Data", ha='center', va='center')

        # Redraw canvas
        self.canvas.draw()

    def delete_selected_cost_item(self):
        """
        Delete the selected cost item from the breakdown.
        """
        selected_item = self.cost_tree.selection()
        if not selected_item:
            messagebox.showwarning("Selection", "Please select a cost item to delete.")
            return

        # Remove from treeview
        self.cost_tree.delete(selected_item[0])

        # Remove from cost items list
        del self.cost_items[self.cost_tree.index(selected_item[0])]

        # Recalculate costs
        self.recalculate_costs()

    def show_context_menu(self, event):
        """
        Show context menu for cost items list.
        """
        # Select the row under the cursor
        iid = self.cost_tree.identify_row(event.y)
        if iid:
            self.cost_tree.selection_set(iid)
            self.cost_tree_context_menu.post(event.x_root, event.y_root)

    def export_cost_report(self):
        """
        Export cost report to a CSV file.
        """
        try:
            filename = simpledialog.askstring(
                "Export Report",
                "Enter filename for cost report:",
                initialvalue="cost_report.csv"
            )

            if not filename:
                return

            # Write CSV file
            with open(filename, 'w') as f:
                # Write headers
                f.write("Category,Item,Quantity,Unit Price,Total Cost\n")

                # Write cost items
                for item in self.cost_items:
                    f.write(
                        f"{item['category']},"
                        f"{item['item_name']},"
                        f"{item['quantity']},"
                        f"{item['unit_price']},"
                        f"{item['total_cost']}\n"
                    )

            # Add summary information
            f.write("\nSummary,,,\n")
            f.write(f"Materials Cost,,,{self.materials_cost_label.cget('text')}\n")
            f.write(f"Labor Cost,,,{self.labor_cost_label.cget('text')}\n")
            f.write(f"Total Project Cost,,,{self.total_cost_label.cget('text')}\n")
            f.write(f"Estimated Profit Margin,,,{self.profit_margin_label.cget('text')}\n")

            messagebox.showinfo("Export Successful", f"Cost report exported to {filename}")

        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    def load_initial_costs(self):
        """
        Load some initial cost items for demonstration.
        """
        initial_costs = [
            {
                'category': 'Leather',
                'item_name': 'Full Grain Leather',
                'quantity': 2,
                'unit_price': 50.00,
                'total_cost': 100.00
            },
            {
                'category': 'Hardware',
                'item_name': 'Metal Buckles',
                'quantity': 4,
                'unit_price': 5.50,
                'total_cost': 22.00
            },
            {
                'category': 'Labor',
                'item_name': 'Design and Cutting',
                'quantity': 3,
                'unit_price': 25.00,
                'total_cost': 75.00
            }
        ]

        for cost_item in initial_costs:
            self.cost_items.append(cost_item)
            self.cost_tree.insert('', 'end', values=(
                cost_item['category'],
                cost_item['item_name'],
                f"{cost_item['quantity']}",
                f"${cost_item['unit_price']:.2f}",
                f"${cost_item['total_cost']:.2f}"
            ))

        # Recalculate costs
        self.recalculate_costs()

def main():
    """
    Standalone testing of the CostEstimator.
    """
    root = tk.Tk()
    root.title("Leatherworking Cost Estimator")
    root.geometry("1000x700")

    cost_estimator = CostEstimator(root)
    cost_estimator.pack(fill='both', expand=True)

    root.mainloop()

if __name__ == '__main__':
    main()