# Path: gui/leatherworking/leather_inventory.py
"""
Leather Inventory Management View for Leatherworking Project

This module provides a comprehensive UI for managing leather inventory,
including tracking, analysis, and detailed reporting of leather materials.
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from typing import Dict, List, Any
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class LeatherInventoryView(tk.Frame):
    """
    A comprehensive leather inventory management view.

    Features:
    - Inventory tracking
    - Detailed leather item management
    - Usage analytics
    - Quality tracking
    """

    def __init__(self, parent, app):
        """
        Initialize the Leather Inventory View.

        Args:
            parent (tk.Widget): Parent widget
            app (object): Application context
        """
        super().__init__(parent)
        self.app = app

        # Leather inventory data structure
        self.leather_inventory: List[Dict[str, Any]] = []

        # Setup UI components
        self._setup_layout()
        self._create_inventory_list()
        self._create_analytics_section()
        self._create_action_buttons()

        # Load initial data
        self._load_initial_leather_data()

    def _setup_layout(self):
        """
        Configure the overall layout of the view.
        """
        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=1)

        # Frames
        self.inventory_frame = ttk.LabelFrame(self, text="Leather Inventory")
        self.inventory_frame.grid(row=0, column=0, padx=10, pady=10, sticky='nsew')

        self.analytics_frame = ttk.LabelFrame(self, text="Inventory Analytics")
        self.analytics_frame.grid(row=0, column=1, padx=10, pady=10, sticky='nsew')

        self.action_frame = ttk.Frame(self)
        self.action_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky='ew')

    def _create_inventory_list(self):
        """
        Create a treeview to display leather inventory.
        """
        columns = ('ID', 'Type', 'Color', 'Area', 'Quality', 'Status')
        self.inventory_tree = ttk.Treeview(self.inventory_frame,
                                           columns=columns, show='headings')

        # Configure columns
        for col in columns:
            self.inventory_tree.heading(col, text=col)
            self.inventory_tree.column(col, width=100, anchor='center')

        self.inventory_tree.pack(expand=True, fill='both')

        # Bind events
        self.inventory_tree.bind('<Double-1>', self._show_leather_details)
        self.inventory_tree.bind('<Button-3>', self._show_context_menu)

    def _create_analytics_section(self):
        """
        Create a section for inventory analytics and visualization.
        """
        # Matplotlib figure for analytics
        self.fig, self.ax = plt.subplots(figsize=(5, 4), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.analytics_frame)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(expand=True, fill='both')

    def _create_action_buttons(self):
        """
        Create action buttons for leather inventory management.
        """
        # Add Leather Button
        add_btn = ttk.Button(self.action_frame, text="Add Leather",
                             command=self._add_leather_dialog)
        add_btn.pack(side=tk.LEFT, padx=5)

        # Update Leather Button
        update_btn = ttk.Button(self.action_frame, text="Update Leather",
                                command=self._update_leather_dialog)
        update_btn.pack(side=tk.LEFT, padx=5)

        # Delete Leather Button
        delete_btn = ttk.Button(self.action_frame, text="Delete Leather",
                                command=self._delete_leather)
        delete_btn.pack(side=tk.LEFT, padx=5)

        # Generate Report Button
        report_btn = ttk.Button(self.action_frame, text="Generate Report",
                                command=self._generate_leather_report)
        report_btn.pack(side=tk.LEFT, padx=5)

    def _add_leather_dialog(self):
        """
        Open a dialog to add new leather to the inventory.
        """
        from gui.leatherworking.leather_dialog import LeatherDetailsDialog

        # Create dialog with callback to add leather
        dialog = LeatherDetailsDialog(
            self,
            callback=self._add_leather,
            initial_data=None
        )

    def _add_leather(self, leather_data):
        """
        Add a new leather item to the inventory.

        Args:
            leather_data (dict): Leather details to add
        """
        # Generate unique ID (in real implementation, this would be database-driven)
        leather_data['id'] = f"LTH-{len(self.leather_inventory) + 1:03d}"

        # Validate leather data
        if not self._validate_leather_data(leather_data):
            messagebox.showerror("Invalid Data", "Please fill in all required fields")
            return

        # Add to inventory
        self.leather_inventory.append(leather_data)

        # Update UI
        self._update_inventory_tree()
        self._update_analytics()

    def _update_leather_dialog(self):
        """
        Open a dialog to update selected leather item.
        """
        # Get selected item
        selected_item = self.inventory_tree.selection()
        if not selected_item:
            messagebox.showwarning("No Selection", "Please select a leather item to update")
            return

        # Get current leather data
        values = self.inventory_tree.item(selected_item[0])['values']
        current_leather = next((l for l in self.leather_inventory if l['id'] == values[0]), None)

        if current_leather:
            from gui.leatherworking.leather_dialog import LeatherDetailsDialog
            dialog = LeatherDetailsDialog(
                self,
                callback=self._update_leather,
                initial_data=current_leather
            )

    def _update_leather(self, updated_data):
        """
        Update an existing leather item in the inventory.

        Args:
            updated_data (dict): Updated leather details
        """
        # Find and update the leather item
        for i, leather in enumerate(self.leather_inventory):
            if leather['id'] == updated_data['id']:
                self.leather_inventory[i] = updated_data
                break

        # Refresh UI
        self._update_inventory_tree()
        self._update_analytics()

    def _delete_leather(self):
        """
        Delete selected leather item from inventory.
        """
        # Get selected item
        selected_item = self.inventory_tree.selection()
        if not selected_item:
            messagebox.showwarning("No Selection", "Please select a leather item to delete")
            return

        # Confirm deletion
        if not messagebox.askyesno("Confirm Deletion",
                                   "Are you sure you want to delete this leather item?"):
            return

        # Get leather ID
        values = self.inventory_tree.item(selected_item[0])['values']
        leather_id = values[0]

        # Remove from inventory
        self.leather_inventory = [l for l in self.leather_inventory if l['id'] != leather_id]

        # Update UI
        self._update_inventory_tree()
        self._update_analytics()

    def _validate_leather_data(self, leather_data):
        """
        Validate leather data before adding/updating.

        Args:
            leather_data (dict): Leather details to validate

        Returns:
            bool: True if data is valid, False otherwise
        """
        required_fields = ['type', 'color', 'area', 'quality']
        return all(leather_data.get(field) for field in required_fields)

    def _update_inventory_tree(self):
        """
        Update the inventory treeview with current leather items.
        """
        # Clear existing items
        for item in self.inventory_tree.get_children():
            self.inventory_tree.delete(item)

        # Add current inventory
        for leather in self.leather_inventory:
            self.inventory_tree.insert('', 'end',
                                       values=(
                                           leather.get('id', ''),
                                           leather.get('type', ''),
                                           leather.get('color', ''),
                                           leather.get('area', ''),
                                           leather.get('quality', ''),
                                           leather.get('status', 'Available')
                                       ))

    def _update_analytics(self):
        """
        Update analytics visualization based on current inventory.
        """
        # Clear previous plot
        self.ax.clear()

        # Analyze leather types
        type_distribution = {}
        for leather in self.leather_inventory:
            leather_type = leather.get('type', 'Unknown')
            type_distribution[leather_type] = type_distribution.get(leather_type, 0) + 1

        # Pie chart of leather types
        self.ax.pie(
            list(type_distribution.values()),
            labels=list(type_distribution.keys()),
            autopct='%1.1f%%'
        )
        self.ax.set_title('Leather Inventory by Type')

        # Refresh canvas
        self.canvas.draw()

    def _show_leather_details(self, event):
        """
        Display detailed information for selected leather item.

        Args:
            event (tk.Event): Double-click event
        """
        selected_item = self.inventory_tree.selection()
        if not selected_item:
            return

        # Get leather details
        values = self.inventory_tree.item(selected_item[0])['values']
        leather = next((l for l in self.leather_inventory if l['id'] == values[0]), None)

        if leather:
            details = "\n".join(f"{key.capitalize()}: {value}" for key, value in leather.items())
            messagebox.showinfo("Leather Details", details)

    def _show_context_menu(self, event):
        """
        Show context menu for leather inventory.

        Args:
            event (tk.Event): Right-click event
        """
        # Select the row under the cursor
        iid = self.inventory_tree.identify_row(event.y)
        if iid:
            self.inventory_tree.selection_set(iid)

            # Create context menu
            context_menu = tk.Menu(self, tearoff=0)
            context_menu.add_command(label="View Details",
                                     command=lambda: self._show_leather_details(event))
            context_menu.add_command(label="Update",
                                     command=self._update_leather_dialog)
            context_menu.add_command(label="Delete",
                                     command=self._delete_leather)

            # Post menu
            context_menu.post(event.x_root, event.y_root)

    def _generate_leather_report(self):
        """
        Generate a comprehensive report of leather inventory.
        """
        # Basic report generation
        report = "Leather Inventory Report\n"
        report += "=" * 30 + "\n\n"

        # Inventory summary
        report += f"Total Leather Items: {len(self.leather_inventory)}\n"

        # Type distribution
        type_distribution = {}
        total_area = 0
        for leather in self.leather_inventory:
            leather_type = leather.get('type', 'Unknown')
            type_distribution[leather_type] = type_distribution.get(leather_type, 0) + 1
            total_area += float(leather.get('area', 0))

        report += "\nType Distribution:\n"
        for leather_type, count in type_distribution.items():
            report += f"{leather_type}: {count} items\n"

        report += f"\nTotal Leather Area: {total_area:.2f} sq units\n"

        # Prompt to save report
        filename = tk.filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )

        if filename:
            try:
                with open(filename, 'w') as f:
                    f.write(report)
                messagebox.showinfo("Report Generated",
                                    f"Leather inventory report saved to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Could not save report: {str(e)}")

    def _load_initial_leather_data(self):
        """
        Load initial leather inventory data (mock data for demonstration).
        """
        initial_data = [
            {
                'id': 'LTH-001',
                'type': 'Full Grain',
                'color': 'Brown',
                'area': '5.5',
                'quality': 'Premium',
                'status': 'Available'
            },
            {
                'id': 'LTH-002',
                'type': 'Top Grain',
                'color': 'Black',
                'area': '3.2',
                'quality': 'Standard',
                'status': 'Available'
            },
            {
                'id': 'LTH-003',
                'type': 'Suede',
                'color': 'Tan',
                'area': '4.1',
                'quality': 'Good',
                'status': 'Reserved'
            }
        ]

        self.leather_inventory.extend(initial_data)
        self._update_inventory_tree()
        self._update_analytics()


def main():
    """
    Standalone test for LeatherInventoryView.
    """
    root = tk.Tk()
    root.title("Leather Inventory")
    root.geometry("1000x700")

    # Create a dummy app context
    class DummyApp:
        pass

    leather_inventory = LeatherInventoryView(root, DummyApp())
    leather_inventory.pack(fill='both', expand=True)

    root.mainloop()


if __name__ == "__main__":
    main()