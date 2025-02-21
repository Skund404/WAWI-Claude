# store_management/gui/storage/storage_view.py

import tkinter as tk
from tkinter import ttk, messagebox
from ...application import Application


class StorageView(ttk.Frame):
    """Storage view for managing storage locations"""

    def __init__(self, parent, app: Application):
        super().__init__(parent)
        self.parent = parent
        self.app = app

        # Get service from application
        self.storage_service = app.storage_service

        # Set up UI
        self.setup_ui()

        # Load initial data
        self.load_data()

    def setup_ui(self):
        """Set up the UI components"""

        # Create toolbar
        self.toolbar = ttk.Frame(self)
        self.toolbar.pack(side=tk.TOP, fill=tk.X)

        # Add toolbar buttons
        self.add_btn = ttk.Button(self.toolbar, text="Add Storage", command=self.show_add_dialog)
        self.add_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.refresh_btn = ttk.Button(self.toolbar, text="Refresh", command=self.load_data)
        self.refresh_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.search_btn = ttk.Button(self.toolbar, text="Search", command=self.show_search_dialog)
        self.search_btn.pack(side=tk.LEFT, padx=5, pady=5)

        # Create treeview
        self.tree_frame = ttk.Frame(self)
        self.tree_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Add scrollbar
        self.scrollbar = ttk.Scrollbar(self.tree_frame)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Configure treeview
        self.tree = ttk.Treeview(
            self.tree_frame,
            columns=("id", "location", "capacity", "status", "utilization"),
            show="headings",
            yscrollcommand=self.scrollbar.set
        )

        # Set column headings
        self.tree.heading("id", text="ID")
        self.tree.heading("location", text="Location")
        self.tree.heading("capacity", text="Capacity")
        self.tree.heading("status", text="Status")
        self.tree.heading("utilization", text="Utilization")

        # Set column widths
        self.tree.column("id", width=50)
        self.tree.column("location", width=150)
        self.tree.column("capacity", width=100)
        self.tree.column("status", width=100)
        self.tree.column("utilization", width=100)

        # Pack treeview
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Configure scrollbar
        self.scrollbar.config(command=self.tree.yview)

        # Bind events
        self.tree.bind("<Double-1>", self.on_double_click)
        self.tree.bind("<Delete>", self.delete_selected)

    def load_data(self):
        """Load storage data from service"""
        try:
            # Clear existing items
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Get storage utilization data
            storage_utilization = self.storage_service.get_storage_utilization()

            # Add storage locations to treeview
            for storage in storage_utilization:
                self.tree.insert("", "end", values=(
                    storage["id"],
                    storage["location"],
                    storage["capacity"],
                    "Available",  # Assuming status is not in utilization data
                    f"{storage['utilization_percent']:.1f}%"
                ))

            # Update status if main window available
            if hasattr(self.app, "main_window"):
                self.app.main_window.set_status(f"Loaded {len(storage_utilization)} storage locations")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load storage data: {str(e)}")

    def show_add_dialog(self):
        """Show dialog for adding a new storage location"""
        # Create a toplevel window
        dialog = tk.Toplevel(self)
        dialog.title("Add Storage Location")
        dialog.geometry("400x250")
        dialog.transient(self)  # Make dialog modal
        dialog.grab_set()

        # Create form fields
        ttk.Label(dialog, text="Location:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        location_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=location_var, width=30).grid(row=0, column=1, padx=10, pady=10)

        ttk.Label(dialog, text="Capacity:").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        capacity_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=capacity_var, width=30).grid(row=1, column=1, padx=10, pady=10)

        ttk.Label(dialog, text="Status:").grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
        status_var = tk.StringVar(value="available")
        status_combo = ttk.Combobox(dialog, textvariable=status_var, values=["available", "maintenance", "full"])
        status_combo.grid(row=2, column=1, padx=10, pady=10)

        # Create buttons
        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=3, column=0, columnspan=2, pady=20)

        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).grid(row=0, column=0, padx=10)

        def save_storage():
            """Save the new storage location"""
            try:
                # Validate inputs
                location = location_var.get().strip()
                if not location:
                    messagebox.showerror("Error", "Location is required")
                    return

                try:
                    capacity = float(capacity_var.get())
                    if capacity <= 0:
                        messagebox.showerror("Error", "Capacity must be greater than zero")
                        return
                except ValueError:
                    messagebox.showerror("Error", "Capacity must be a number")
                    return

                status = status_var.get()

                # Create storage location
                result = self.storage_service.create_storage_location({
                    "location": location,
                    "capacity": capacity,
                    "status": status
                })

                if result:
                    messagebox.showinfo("Success", "Storage location created successfully")
                    dialog.destroy()
                    self.load_data()  # Refresh data
                else:
                    messagebox.showerror("Error", "Failed to create storage location")
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred: {str(e)}")

        ttk.Button(button_frame, text="Save", command=save_storage).grid(row=0, column=1, padx=10)

    def on_double_click(self, event):
        """Handle double-click event"""
        item = self.tree.selection()[0]
        column = self.tree.identify_column(event.x)
        column_id = int(column.replace('#', ''))

        # Only allow editing for location, capacity, and status
        if column_id in [2, 3, 4]:  # location, capacity, status
            self.start_cell_edit(item, column_id)

    def start_cell_edit(self, item, column):
        """Start editing a cell"""
        # This would be implemented to allow inline editing
        # For simplicity, we'll show an edit dialog instead
        values = self.tree.item(item, "values")
        storage_id = values[0]

        # Create edit dialog
        dialog = tk.Toplevel(self)
        dialog.title("Edit Storage Location")
        dialog.geometry("400x250")
        dialog.transient(self)
        dialog.grab_set()

        # Create form fields with current values
        ttk.Label(dialog, text="Location:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        location_var = tk.StringVar(value=values[1])
        ttk.Entry(dialog, textvariable=location_var, width=30).grid(row=0, column=1, padx=10, pady=10)

        ttk.Label(dialog, text="Capacity:").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        capacity_var = tk.StringVar(value=values[2])
        ttk.Entry(dialog, textvariable=capacity_var, width=30).grid(row=1, column=1, padx=10, pady=10)

        ttk.Label(dialog, text="Status:").grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
        status_var = tk.StringVar(value=values[3])
        status_combo = ttk.Combobox(dialog, textvariable=status_var, values=["available", "maintenance", "full"])
        status_combo.grid(row=2, column=1, padx=10, pady=10)

        # Create buttons
        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=3, column=0, columnspan=2, pady=20)

        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).grid(row=0, column=0, padx=10)

        def update_storage():
            """Update the storage location"""
            try:
                # Validate inputs
                location = location_var.get().strip()
                if not location:
                    messagebox.showerror("Error", "Location is required")
                    return

                try:
                    capacity = float(capacity_var.get())
                    if capacity <= 0:
                        messagebox.showerror("Error", "Capacity must be greater than zero")
                        return
                except ValueError:
                    messagebox.showerror("Error", "Capacity must be a number")
                    return

                status = status_var.get()

                # Update storage location
                storage_repo = self.storage_service.storage_repo
                storage = storage_repo.get(storage_id)
                if storage:
                    storage.location = location
                    storage.capacity = capacity
                    storage.status = status

                    # Commit changes
                    self.storage_service.session.commit()

                    messagebox.showinfo("Success", "Storage location updated successfully")
                    dialog.destroy()
                    self.load_data()  # Refresh data
                else:
                    messagebox.showerror("Error", "Storage location not found")
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred: {str(e)}")

        ttk.Button(button_frame, text="Save", command=update_storage).grid(row=0, column=1, padx=10)

    def delete_selected(self, event=None):
        """Delete selected storage locations"""
        selected_items = self.tree.selection()
        if not selected_items:
            return

        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete the selected storage locations?"):
            for item in selected_items:
                values = self.tree.item(item, "values")
                storage_id = values[0]

                # Delete storage
                storage_repo = self.storage_service.storage_repo
                if storage_repo.delete(storage_id):
                    self.storage_service.session.commit()

            # Refresh data
            self.load_data()

    def show_search_dialog(self):
        """Show search dialog"""
        # Implementation would go here
        pass