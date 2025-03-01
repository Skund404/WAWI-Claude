# gui/leatherworking/cost_estimator.py
# deprecated, replace by cost
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from typing import Any, Dict, List


class CostEstimator(tk.Frame):
    """Cost estimator for leatherworking projects.

    Allows users to estimate and track costs for leatherworking projects.
    """

    def __init__(self, parent, controller=None):
        """Initialize the cost estimator.

        Args:
            parent (tk.Tk or tk.Frame): Parent widget
            controller (object, optional): Application controller for navigation
        """
        super().__init__(parent)
        self.parent = parent
        self.controller = controller
        self.cost_items = []

        # Create the layout
        self._setup_layout()
        self._create_cost_input()
        self._create_cost_breakdown()
        self._create_cost_visualization()
        self._create_cost_summary()

        # Load some sample data
        self.load_initial_costs()

    def _setup_layout(self):
        """Configure grid layout for cost estimator."""
        # Configure grid
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=2)
        self.rowconfigure(0, weight=0)  # Input area
        self.rowconfigure(1, weight=1)  # Breakdown and visualization
        self.rowconfigure(2, weight=0)  # Summary

        # Create frames
        self.input_frame = ttk.LabelFrame(self, text="Add Cost Item")
        self.input_frame.grid(row=0, column=0, columnspan=2, padx=10, pady=5, sticky="ew")

        self.breakdown_frame = ttk.LabelFrame(self, text="Cost Breakdown")
        self.breakdown_frame.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")

        self.visualization_frame = ttk.LabelFrame(self, text="Cost Distribution")
        self.visualization_frame.grid(row=1, column=1, padx=10, pady=5, sticky="nsew")

        self.summary_frame = ttk.LabelFrame(self, text="Cost Summary")
        self.summary_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=5, sticky="ew")

    def _create_cost_input(self):
        """Create input fields for adding cost items."""
        # Configure grid
        self.input_frame.columnconfigure(1, weight=1)

        # Item description
        ttk.Label(self.input_frame, text="Description:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.description_var = tk.StringVar()
        ttk.Entry(self.input_frame, textvariable=self.description_var).grid(row=0, column=1, padx=5, pady=5,
                                                                            sticky="ew")

        # Item category
        ttk.Label(self.input_frame, text="Category:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.category_var = tk.StringVar()
        categories = ["Leather", "Hardware", "Thread", "Tools", "Labor", "Other"]
        ttk.Combobox(self.input_frame, textvariable=self.category_var, values=categories).grid(row=0, column=3, padx=5,
                                                                                               pady=5, sticky="ew")

        # Item cost
        ttk.Label(self.input_frame, text="Cost ($):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.cost_var = tk.StringVar()
        ttk.Entry(self.input_frame, textvariable=self.cost_var).grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        # Item quantity
        ttk.Label(self.input_frame, text="Quantity:").grid(row=1, column=2, padx=5, pady=5, sticky="w")
        self.quantity_var = tk.StringVar(value="1")
        ttk.Entry(self.input_frame, textvariable=self.quantity_var).grid(row=1, column=3, padx=5, pady=5, sticky="ew")

        # Add button
        add_button = ttk.Button(self.input_frame, text="Add Cost Item", command=self.add_cost_item)
        add_button.grid(row=1, column=4, padx=5, pady=5, sticky="e")

    def _create_cost_breakdown(self):
        """Create a treeview to display cost breakdown."""
        # Create treeview
        columns = ("description", "category", "cost", "quantity", "total")
        self.cost_tree = ttk.Treeview(self.breakdown_frame, columns=columns, show="headings")

        # Configure columns
        self.cost_tree.heading("description", text="Description")
        self.cost_tree.heading("category", text="Category")
        self.cost_tree.heading("cost", text="Cost ($)")
        self.cost_tree.heading("quantity", text="Qty")
        self.cost_tree.heading("total", text="Total ($)")

        self.cost_tree.column("description", width=150)
        self.cost_tree.column("category", width=80)
        self.cost_tree.column("cost", width=60)
        self.cost_tree.column("quantity", width=40)
        self.cost_tree.column("total", width=60)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.breakdown_frame, orient=tk.VERTICAL, command=self.cost_tree.yview)
        self.cost_tree.configure(yscroll=scrollbar.set)

        # Pack elements
        self.cost_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind right-click for context menu
        self.cost_tree.bind("<Button-3>", self.show_context_menu)

        # Create context menu
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Delete Item", command=self.delete_selected_cost_item)

    def _create_cost_visualization(self):
        """Create pie chart for cost distribution."""
        # Create figure and axis
        self.figure, self.ax = plt.subplots(figsize=(5, 4), dpi=100)

        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.visualization_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Initial empty plot
        self.ax.set_title("Cost Distribution by Category")
        self.ax.text(0.5, 0.5, "Add cost items to see distribution",
                     horizontalalignment='center', verticalalignment='center', transform=self.ax.transAxes)
        self.canvas.draw()

    def _create_cost_summary(self):
        """Create summary section for cost tracking."""
        # Configure grid
        self.summary_frame.columnconfigure(1, weight=1)
        self.summary_frame.columnconfigure(3, weight=1)

        # Total cost
        ttk.Label(self.summary_frame, text="Total Cost:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.total_cost_var = tk.StringVar(value="$0.00")
        ttk.Label(self.summary_frame, textvariable=self.total_cost_var, font=("Helvetica", 12, "bold")).grid(row=0,
                                                                                                             column=1,
                                                                                                             padx=5,
                                                                                                             pady=5,
                                                                                                             sticky="w")

        # Item count
        ttk.Label(self.summary_frame, text="Number of Items:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.item_count_var = tk.StringVar(value="0")
        ttk.Label(self.summary_frame, textvariable=self.item_count_var).grid(row=0, column=3, padx=5, pady=5,
                                                                             sticky="w")

        # Action buttons
        button_frame = ttk.Frame(self.summary_frame)
        button_frame.grid(row=1, column=0, columnspan=4, padx=5, pady=5, sticky="ew")

        export_button = ttk.Button(button_frame, text="Export Cost Report", command=self.export_cost_report)
        export_button.pack(side=tk.LEFT, padx=5)

        clear_button = ttk.Button(button_frame, text="Clear All",
                                  command=lambda: self.cost_tree.delete(*self.cost_tree.get_children()))
        clear_button.pack(side=tk.LEFT, padx=5)

    def add_cost_item(self):
        """Add a new cost item to the breakdown."""
        # Get values
        description = self.description_var.get().strip()
        category = self.category_var.get().strip()

        # Validate inputs
        try:
            cost = float(self.cost_var.get())
            quantity = int(self.quantity_var.get())
        except ValueError:
            messagebox.showerror("Input Error", "Cost must be a number and quantity must be an integer.")
            return

        if not description:
            messagebox.showerror("Input Error", "Please enter a description.")
            return

        if not category:
            messagebox.showerror("Input Error", "Please select a category.")
            return

        # Calculate total
        total = cost * quantity

        # Add to treeview
        item_id = self.cost_tree.insert("", tk.END, values=(
            description,
            category,
            f"{cost:.2f}",
            quantity,
            f"{total:.2f}"
        ))

        # Add to data
        self.cost_items.append({
            "id": item_id,
            "description": description,
            "category": category,
            "cost": cost,
            "quantity": quantity,
            "total": total
        })

        # Clear inputs
        self.description_var.set("")
        self.cost_var.set("")
        self.quantity_var.set("1")

        # Update summary and visualization
        self.recalculate_costs()

    def recalculate_costs(self):
        """Recalculate and update cost summary."""
        # Calculate totals
        total_cost = sum(item["total"] for item in self.cost_items)

        # Update variables
        self.total_cost_var.set(f"${total_cost:.2f}")
        self.item_count_var.set(str(len(self.cost_items)))

        # Update visualization
        self._update_cost_distribution_chart()

    def _update_cost_distribution_chart(self):
        """Update pie chart showing cost distribution."""
        # Clear previous plot
        self.ax.clear()

        # Skip if no items
        if not self.cost_items:
            self.ax.set_title("Cost Distribution by Category")
            self.ax.text(0.5, 0.5, "Add cost items to see distribution",
                         horizontalalignment='center', verticalalignment='center', transform=self.ax.transAxes)
            self.canvas.draw()
            return

        # Group by category
        category_totals = {}
        for item in self.cost_items:
            category = item["category"]
            if category in category_totals:
                category_totals[category] += item["total"]
            else:
                category_totals[category] = item["total"]

        # Create pie chart
        labels = list(category_totals.keys())
        values = list(category_totals.values())

        # Use custom colors for categories
        colors = {'Leather': '#8B4513', 'Hardware': '#A9A9A9', 'Thread': '#4682B4',
                  'Tools': '#556B2F', 'Labor': '#CD5C5C', 'Other': '#9932CC'}

        plot_colors = [colors.get(category, '#1f77b4') for category in labels]

        self.ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=90, colors=plot_colors)
        self.ax.set_title("Cost Distribution by Category")
        self.ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle

        # Draw the plot
        self.canvas.draw()

    def delete_selected_cost_item(self):
        """Delete the selected cost item from the breakdown."""
        selected_items = self.cost_tree.selection()
        if not selected_items:
            return

        # Remove from treeview
        for item_id in selected_items:
            self.cost_tree.delete(item_id)

            # Remove from data
            self.cost_items = [item for item in self.cost_items if item["id"] != item_id]

        # Update summary and visualization
        self.recalculate_costs()

    def show_context_menu(self, event):
        """Show context menu for cost items list.

        Args:
            event: The event that triggered the context menu
        """
        # Select the item under cursor
        item = self.cost_tree.identify_row(event.y)
        if item:
            self.cost_tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def export_cost_report(self):
        """Export cost report to a CSV file."""
        messagebox.showinfo("Export", "Export functionality not implemented yet.")

    def load_initial_costs(self):
        """Load some initial cost items for demonstration."""
        sample_items = [
            {"description": "Veg-Tan Leather (2-3 oz)", "category": "Leather", "cost": 25.99, "quantity": 1},
            {"description": "Solid Brass Buckle", "category": "Hardware", "cost": 4.50, "quantity": 2},
            {"description": "Waxed Thread (25 yards)", "category": "Thread", "cost": 8.75, "quantity": 1},
            {"description": "Edge Beveler Tool", "category": "Tools", "cost": 15.00, "quantity": 1},
            {"description": "Construction Time (2 hours)", "category": "Labor", "cost": 30.00, "quantity": 2}
        ]

        for item in sample_items:
            self.description_var.set(item["description"])
            self.category_var.set(item["category"])
            self.cost_var.set(str(item["cost"]))
            self.quantity_var.set(str(item["quantity"]))
            self.add_cost_item()


def main():
    """Standalone testing of the CostEstimator."""
    root = tk.Tk()
    root.title("Cost Estimator")
    root.geometry("800x600")

    app = CostEstimator(root)
    app.pack(fill=tk.BOTH, expand=True)

    # Ensure proper cleanup on exit
    def on_close():
        plt.close('all')
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)

    root.mainloop()


if __name__ == "__main__":
    main()