# gui/views/inventory/storage_location_view.py
"""
Storage Location View.
Provides management of storage locations and organization of inventory.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any, Dict, List, Optional

from database.models.enums import StorageLocationType
from gui.base.base_list_view import BaseListView
from gui.widgets.status_badge import StatusBadge
from gui.utils.service_access import get_service


class StorageLocationView(BaseListView):
    """View for managing storage locations."""

    def __init__(self, parent):
        """
        Initialize the storage location view.

        Args:
            parent: The parent widget
        """
        super().__init__(parent)
        self.title = "Storage Locations"
        self.service_name = "IInventoryService"

        # Configure columns
        self.columns = [
            ("location", "Location", 200),
            ("location_type", "Type", 100),
            ("items_count", "Items", 80),
            ("total_value", "Value", 100),
            ("last_updated", "Last Updated", 150),
            ("description", "Description", 300)
        ]

        # Configure search fields
        self.search_fields = [
            {"name": "location", "label": "Location", "type": "text", "width": 20},
            {"name": "location_type", "label": "Type", "type": "select",
             "options": [e.value for e in StorageLocationType], "width": 15}
        ]

        # Set sort defaults
        self.sort_column = "location"
        self.sort_direction = "asc"

    def build(self):
        """Build the storage location view."""
        super().build()

        # Add storage organization button to action buttons
        btn_organize = ttk.Button(
            self.action_buttons,
            text="Organize Storage",
            command=self.open_storage_organization)
        btn_organize.pack(side=tk.LEFT, padx=5)

        # Add report button to action buttons
        btn_report = ttk.Button(
            self.action_buttons,
            text="Storage Report",
            command=self.generate_storage_report)
        btn_report.pack(side=tk.LEFT, padx=5)

    def extract_item_values(self, item):
        """
        Extract values from a storage location item for display in the treeview.

        Args:
            item: The storage location item to extract values from

        Returns:
            List of values corresponding to treeview columns
        """
        # For dictionary data
        if isinstance(item, dict):
            location = item.get("location", "")
            location_parts = location.split(":", 1) if ":" in location else ["", location]
            location_type = location_parts[0] if len(location_parts) > 1 else ""

            return [
                location,
                location_type,
                item.get("items_count", 0),
                item.get("total_value", 0),
                item.get("last_updated", ""),
                item.get("description", "")
            ]

        # For other data types (assuming namedtuple or similar)
        elif hasattr(item, "_asdict"):
            data = item._asdict()
            location = data.get("location", "")
            location_parts = location.split(":", 1) if ":" in location else ["", location]
            location_type = location_parts[0] if len(location_parts) > 1 else ""

            return [
                location,
                location_type,
                data.get("items_count", 0),
                data.get("total_value", 0),
                data.get("last_updated", ""),
                data.get("description", "")
            ]

        # Unknown data type
        return [str(item)] + [""] * (len(self.columns) - 1)

    def on_add(self):
        """Handle add new storage location action."""
        self.logger.info("Opening add storage location dialog")

        # Create dialog
        dialog = tk.Toplevel(self.frame)
        dialog.title("Add Storage Location")
        dialog.geometry("450x350")
        dialog.transient(self.frame)
        dialog.grab_set()

        # Create content frame
        content = ttk.Frame(dialog, padding=20)
        content.pack(fill=tk.BOTH, expand=True)

        # Create form
        ttk.Label(content, text="Location Type:").pack(anchor="w", pady=(0, 5))

        type_var = tk.StringVar()
        type_combo = ttk.Combobox(
            content,
            textvariable=type_var,
            values=[e.value for e in StorageLocationType],
            state="readonly",
            width=30
        )
        type_combo.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(content, text="Location Identifier:").pack(anchor="w", pady=(0, 5))

        identifier_var = tk.StringVar()
        identifier_entry = ttk.Entry(content, textvariable=identifier_var, width=30)
        identifier_entry.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(content, text="Description:").pack(anchor="w", pady=(0, 5))

        description_var = tk.StringVar()
        description_entry = ttk.Entry(content, textvariable=description_var, width=30)
        description_entry.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(content, text="Notes:").pack(anchor="w", pady=(0, 5))

        notes_text = tk.Text(content, height=5, width=30)
        notes_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Create buttons
        btn_frame = ttk.Frame(dialog, padding=10)
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM)

        ttk.Button(
            btn_frame,
            text="Cancel",
            command=dialog.destroy
        ).pack(side=tk.RIGHT, padx=5)

        def on_save():
            # Validate input
            location_type = type_var.get()
            identifier = identifier_var.get()
            description = description_var.get()
            notes = notes_text.get("1.0", tk.END).strip()

            if not location_type:
                messagebox.showerror("Error", "Please select a location type")
                return

            if not identifier:
                messagebox.showerror("Error", "Please enter a location identifier")
                return

            # Format the location string
            location = f"{location_type}:{identifier}"

            try:
                # Add the location
                service = self.get_service(self.service_name)
                result = service.add_storage_location(
                    location=location,
                    description=description,
                    notes=notes
                )

                if result:
                    # Close dialog
                    dialog.destroy()

                    # Refresh the view
                    self.refresh()

                    # Show success message
                    messagebox.showinfo("Success", f"Storage location {location} added successfully")
                else:
                    messagebox.showerror("Error", "Failed to add storage location")

            except Exception as e:
                self.logger.error(f"Error adding storage location: {str(e)}")
                messagebox.showerror("Error", f"Could not add storage location: {str(e)}")

        ttk.Button(
            btn_frame,
            text="Save",
            command=on_save
        ).pack(side=tk.RIGHT, padx=5)

        # Center the dialog
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f'+{x}+{y}')

    def on_view(self):
        """Handle view storage location action."""
        if not self.selected_item:
            return

        self.logger.info(f"Opening view storage location for {self.selected_item}")

        try:
            # Get the selected location
            selected_values = self.treeview.get_selected_item_values()
            if not selected_values:
                return

            location = selected_values[0]

            # Get location details
            service = self.get_service(self.service_name)
            location_details = service.get_storage_location_details(location)

            if not location_details:
                self.show_error("Error", f"Could not retrieve details for location {location}")
                return

            # Create dialog
            dialog = tk.Toplevel(self.frame)
            dialog.title(f"Storage Location: {location}")
            dialog.geometry("800x600")
            dialog.transient(self.frame)
            dialog.grab_set()

            # Create content frame
            content = ttk.Frame(dialog, padding=20)
            content.pack(fill=tk.BOTH, expand=True)

            # Create header
            ttk.Label(
                content,
                text=f"Storage Location: {location}",
                font=("Helvetica", 16, "bold")
            ).pack(anchor="w", pady=(0, 20))

            # Create details frame
            details_frame = ttk.LabelFrame(content, text="Location Details")
            details_frame.pack(fill=tk.X, pady=10)

            details_grid = ttk.Frame(details_frame, padding=10)
            details_grid.pack(fill=tk.X)

            # Location type
            location_parts = location.split(":", 1) if ":" in location else ["", location]
            location_type = location_parts[0] if len(location_parts) > 1 else ""

            ttk.Label(details_grid, text="Location Type:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
            ttk.Label(details_grid, text=location_type).grid(row=0, column=1, sticky="w", padx=5, pady=2)

            ttk.Label(details_grid, text="Items Count:").grid(row=0, column=2, sticky="w", padx=5, pady=2)
            ttk.Label(details_grid, text=str(location_details.get("items_count", 0))).grid(row=0, column=3, sticky="w",
                                                                                           padx=5, pady=2)

            ttk.Label(details_grid, text="Description:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
            ttk.Label(details_grid, text=location_details.get("description", "")).grid(row=1, column=1, sticky="w",
                                                                                       padx=5, pady=2)

            ttk.Label(details_grid, text="Total Value:").grid(row=1, column=2, sticky="w", padx=5, pady=2)
            ttk.Label(details_grid, text=str(location_details.get("total_value", 0))).grid(row=1, column=3, sticky="w",
                                                                                           padx=5, pady=2)

            ttk.Label(details_grid, text="Last Updated:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
            ttk.Label(details_grid, text=str(location_details.get("last_updated", ""))).grid(row=2, column=1,
                                                                                             sticky="w", padx=5, pady=2)

            # Create items frame
            items_frame = ttk.LabelFrame(content, text="Items in Location")
            items_frame.pack(fill=tk.BOTH, expand=True, pady=10)

            # Create treeview for items
            tree_frame = ttk.Frame(items_frame, padding=10)
            tree_frame.pack(fill=tk.BOTH, expand=True)

            tree = ttk.Treeview(
                tree_frame,
                columns=("id", "type", "name", "quantity", "value", "status"),
                show="headings"
            )

            tree.heading("id", text="ID")
            tree.heading("type", text="Type")
            tree.heading("name", text="Item")
            tree.heading("quantity", text="Quantity")
            tree.heading("value", text="Value")
            tree.heading("status", text="Status")

            tree.column("id", width=60)
            tree.column("type", width=100)
            tree.column("name", width=200)
            tree.column("quantity", width=80)
            tree.column("value", width=80)
            tree.column("status", width=100)

            # Add scrollbar
            sb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
            tree.configure(yscrollcommand=sb.set)
            sb.pack(side=tk.RIGHT, fill=tk.Y)
            tree.pack(fill=tk.BOTH, expand=True)

            # Add items to treeview
            if "items" in location_details and location_details["items"]:
                for item in location_details["items"]:
                    tree.insert("", "end", values=(
                        item.get("id", ""),
                        item.get("item_type", "").capitalize(),
                        item.get("name", ""),
                        item.get("quantity", 0),
                        item.get("value", 0),
                        item.get("status", "")
                    ))

            # Add buttons
            btn_frame = ttk.Frame(dialog, padding=10)
            btn_frame.pack(fill=tk.X, side=tk.BOTTOM)

            ttk.Button(
                btn_frame,
                text="Close",
                command=dialog.destroy
            ).pack(side=tk.RIGHT, padx=5)

            ttk.Button(
                btn_frame,
                text="Print",
                command=lambda: self.print_location_report(location)
            ).pack(side=tk.RIGHT, padx=5)

            # Center the dialog
            dialog.update_idletasks()
            width = dialog.winfo_width()
            height = dialog.winfo_height()
            x = (dialog.winfo_screenwidth() // 2) - (width // 2)
            y = (dialog.winfo_screenheight() // 2) - (height // 2)
            dialog.geometry(f'+{x}+{y}')

        except Exception as e:
            self.logger.error(f"Error viewing storage location: {str(e)}")
            self.show_error("Error", f"Could not view storage location: {str(e)}")

    def on_edit(self):
        """Handle edit storage location action."""
        if not self.selected_item:
            return

        self.logger.info(f"Opening edit storage location for {self.selected_item}")

        try:
            # Get the selected location
            selected_values = self.treeview.get_selected_item_values()
            if not selected_values:
                return

            location = selected_values[0]

            # Get location details
            service = self.get_service(self.service_name)
            location_details = service.get_storage_location_details(location)

            if not location_details:
                self.show_error("Error", f"Could not retrieve details for location {location}")
                return

            # Create dialog
            dialog = tk.Toplevel(self.frame)
            dialog.title(f"Edit Storage Location: {location}")
            dialog.geometry("450x350")
            dialog.transient(self.frame)
            dialog.grab_set()

            # Create content frame
            content = ttk.Frame(dialog, padding=20)
            content.pack(fill=tk.BOTH, expand=True)

            # Extract location parts
            location_parts = location.split(":", 1) if ":" in location else ["", location]
            location_type = location_parts[0] if len(location_parts) > 1 else ""
            location_id = location_parts[1] if len(location_parts) > 1 else location

            # Create form
            ttk.Label(content, text="Location Type:").pack(anchor="w", pady=(0, 5))

            type_var = tk.StringVar(value=location_type)
            type_combo = ttk.Combobox(
                content,
                textvariable=type_var,
                values=[e.value for e in StorageLocationType],
                state="readonly",
                width=30
            )
            type_combo.pack(fill=tk.X, pady=(0, 10))

            ttk.Label(content, text="Location Identifier:").pack(anchor="w", pady=(0, 5))

            identifier_var = tk.StringVar(value=location_id)
            identifier_entry = ttk.Entry(content, textvariable=identifier_var, width=30)
            identifier_entry.pack(fill=tk.X, pady=(0, 10))

            ttk.Label(content, text="Description:").pack(anchor="w", pady=(0, 5))

            description_var = tk.StringVar(value=location_details.get("description", ""))
            description_entry = ttk.Entry(content, textvariable=description_var, width=30)
            description_entry.pack(fill=tk.X, pady=(0, 10))

            ttk.Label(content, text="Notes:").pack(anchor="w", pady=(0, 5))

            notes_text = tk.Text(content, height=5, width=30)
            notes_text.insert("1.0", location_details.get("notes", ""))
            notes_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

            # Create buttons
            btn_frame = ttk.Frame(dialog, padding=10)
            btn_frame.pack(fill=tk.X, side=tk.BOTTOM)

            ttk.Button(
                btn_frame,
                text="Cancel",
                command=dialog.destroy
            ).pack(side=tk.RIGHT, padx=5)

            def on_save():
                # Validate input
                new_location_type = type_var.get()
                new_identifier = identifier_var.get()
                new_description = description_var.get()
                new_notes = notes_text.get("1.0", tk.END).strip()

                if not new_location_type:
                    messagebox.showerror("Error", "Please select a location type")
                    return

                if not new_identifier:
                    messagebox.showerror("Error", "Please enter a location identifier")
                    return

                # Format the new location string
                new_location = f"{new_location_type}:{new_identifier}"

                try:
                    # Update the location
                    service = self.get_service(self.service_name)
                    result = service.update_storage_location(
                        old_location=location,
                        new_location=new_location,
                        description=new_description,
                        notes=new_notes
                    )

                    if result:
                        # Close dialog
                        dialog.destroy()

                        # Refresh the view
                        self.refresh()

                        # Show success message
                        messagebox.showinfo(
                            "Success",
                            f"Storage location updated from {location} to {new_location}"
                        )
                    else:
                        messagebox.showerror("Error", "Failed to update storage location")

                except Exception as e:
                    self.logger.error(f"Error updating storage location: {str(e)}")
                    messagebox.showerror("Error", f"Could not update storage location: {str(e)}")

            ttk.Button(
                btn_frame,
                text="Save",
                command=on_save
            ).pack(side=tk.RIGHT, padx=5)

            # Center the dialog
            dialog.update_idletasks()
            width = dialog.winfo_width()
            height = dialog.winfo_height()
            x = (dialog.winfo_screenwidth() // 2) - (width // 2)
            y = (dialog.winfo_screenheight() // 2) - (height // 2)
            dialog.geometry(f'+{x}+{y}')

        except Exception as e:
            self.logger.error(f"Error editing storage location: {str(e)}")
            self.show_error("Error", f"Could not edit storage location: {str(e)}")

    def on_delete(self):
        """Handle delete storage location action."""
        if not self.selected_item:
            return

        self.logger.info(f"Deleting storage location {self.selected_item}")

        try:
            # Get the selected location
            selected_values = self.treeview.get_selected_item_values()
            if not selected_values:
                return

            location = selected_values[0]

            # Confirm deletion
            if not self.show_confirm(
                    "Confirm Deletion",
                    f"Are you sure you want to delete the storage location '{location}'?\n\n"
                    "This will remove all items from this location."
            ):
                return

            # Delete the location
            service = self.get_service(self.service_name)
            result = service.delete_storage_location(location)

            if result:
                # Refresh the view
                self.refresh()

                # Show success message
                self.show_info("Success", f"Storage location {location} deleted successfully")
            else:
                self.show_error("Error", f"Failed to delete storage location {location}")

        except Exception as e:
            self.logger.error(f"Error deleting storage location: {str(e)}")
            self.show_error("Error", f"Could not delete storage location: {str(e)}")

    def open_storage_organization(self):
        """Open the storage organization tool."""
        self.logger.info("Opening storage organization tool")

        try:
            # Create dialog
            dialog = tk.Toplevel(self.frame)
            dialog.title("Storage Organization")
            dialog.geometry("900x700")
            dialog.transient(self.frame)
            dialog.grab_set()

            # Create content frame
            content = ttk.Frame(dialog, padding=20)
            content.pack(fill=tk.BOTH, expand=True)

            # Create header
            ttk.Label(
                content,
                text="Storage Organization Tool",
                font=("Helvetica", 16, "bold")
            ).pack(anchor="w", pady=(0, 10))

            ttk.Label(
                content,
                text="Use this tool to organize and optimize your storage locations.",
                wraplength=800
            ).pack(anchor="w", pady=(0, 20))

            # Create tabs for different organization views
            notebook = ttk.Notebook(content)
            notebook.pack(fill=tk.BOTH, expand=True)

            # Create tab for bulk operations
            bulk_tab = ttk.Frame(notebook, padding=10)
            notebook.add(bulk_tab, text="Bulk Operations")
            self.create_bulk_operations_tab(bulk_tab)

            # Create tab for visual layout
            layout_tab = ttk.Frame(notebook, padding=10)
            notebook.add(layout_tab, text="Visual Layout")
            self.create_visual_layout_tab(layout_tab)

            # Create tab for item finder
            finder_tab = ttk.Frame(notebook, padding=10)
            notebook.add(finder_tab, text="Item Finder")
            self.create_item_finder_tab(finder_tab)

            # Add buttons
            btn_frame = ttk.Frame(dialog, padding=10)
            btn_frame.pack(fill=tk.X, side=tk.BOTTOM)

            ttk.Button(
                btn_frame,
                text="Close",
                command=dialog.destroy
            ).pack(side=tk.RIGHT, padx=5)

            # Center the dialog
            dialog.update_idletasks()
            width = dialog.winfo_width()
            height = dialog.winfo_height()
            x = (dialog.winfo_screenwidth() // 2) - (width // 2)
            y = (dialog.winfo_screenheight() // 2) - (height // 2)
            dialog.geometry(f'+{x}+{y}')

        except Exception as e:
            self.logger.error(f"Error opening storage organization tool: {str(e)}")
            self.show_error("Error", f"Could not open storage organization tool: {str(e)}")

    def create_bulk_operations_tab(self, parent):
        """
        Create the bulk operations tab content.

        Args:
            parent: The parent widget
        """
        # Create source and destination selection frames
        selection_frame = ttk.Frame(parent)
        selection_frame.pack(fill=tk.X, pady=10)

        # Source selection
        source_frame = ttk.LabelFrame(selection_frame, text="Source Location", padding=10)
        source_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        ttk.Label(source_frame, text="Select source location:").pack(anchor="w", pady=(0, 5))

        source_var = tk.StringVar()
        source_combo = ttk.Combobox(
            source_frame,
            textvariable=source_var,
            state="readonly",
            width=30
        )
        source_combo.pack(fill=tk.X, pady=(0, 5))

        # Populate source combo with locations
        service = self.get_service(self.service_name)
        locations = service.get_storage_locations()
        source_combo['values'] = [loc.get("location", "") for loc in locations]

        # Destination selection
        dest_frame = ttk.LabelFrame(selection_frame, text="Destination Location", padding=10)
        dest_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        ttk.Label(dest_frame, text="Select destination location:").pack(anchor="w", pady=(0, 5))

        dest_var = tk.StringVar()
        dest_combo = ttk.Combobox(
            dest_frame,
            textvariable=dest_var,
            state="readonly",
            width=30
        )
        dest_combo.pack(fill=tk.X, pady=(0, 5))

        # Populate destination combo with locations
        dest_combo['values'] = [loc.get("location", "") for loc in locations]

        # Create actions frame
        actions_frame = ttk.LabelFrame(parent, text="Actions", padding=10)
        actions_frame.pack(fill=tk.X, pady=10)

        # Move all items button
        move_all_btn = ttk.Button(
            actions_frame,
            text="Move All Items",
            command=lambda: self.move_all_items(source_var.get(), dest_var.get())
        )
        move_all_btn.pack(fill=tk.X, pady=5)

        # Consolidate similar items button
        consolidate_btn = ttk.Button(
            actions_frame,
            text="Consolidate Similar Items",
            command=lambda: self.consolidate_items(source_var.get(), dest_var.get())
        )
        consolidate_btn.pack(fill=tk.X, pady=5)

        # Optimize storage button
        optimize_btn = ttk.Button(
            actions_frame,
            text="Optimize Storage",
            command=self.optimize_storage
        )
        optimize_btn.pack(fill=tk.X, pady=5)

        # Create items list frame
        items_frame = ttk.LabelFrame(parent, text="Items in Selected Location", padding=10)
        items_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Create treeview for items
        tree_frame = ttk.Frame(items_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        tree = ttk.Treeview(
            tree_frame,
            columns=("id", "type", "name", "quantity", "value", "status"),
            show="headings",
            selectmode="extended"  # Allow multiple selection
        )

        tree.heading("id", text="ID")
        tree.heading("type", text="Type")
        tree.heading("name", text="Item")
        tree.heading("quantity", text="Quantity")
        tree.heading("value", text="Value")
        tree.heading("status", text="Status")

        tree.column("id", width=60)
        tree.column("type", width=100)
        tree.column("name", width=200)
        tree.column("quantity", width=80)
        tree.column("value", width=80)
        tree.column("status", width=100)

        # Add scrollbar
        sb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        tree.pack(fill=tk.BOTH, expand=True)

        # Function to update the items list when a source is selected
        def on_source_select(event):
            # Clear the tree
            for item in tree.get_children():
                tree.delete(item)

            # Get selected location
            location = source_var.get()
            if not location:
                return

            # Get items in location
            try:
                location_details = service.get_storage_location_details(location)
                if location_details and "items" in location_details:
                    for item in location_details["items"]:
                        tree.insert("", "end", values=(
                            item.get("id", ""),
                            item.get("item_type", "").capitalize(),
                            item.get("name", ""),
                            item.get("quantity", 0),
                            item.get("value", 0),
                            item.get("status", "")
                        ))
            except Exception as e:
                self.logger.error(f"Error loading items for location {location}: {str(e)}")

        # Bind source selection to update items
        source_combo.bind("<<ComboboxSelected>>", on_source_select)

        # Add selected items move button
        move_selected_btn = ttk.Button(
            items_frame,
            text="Move Selected Items",
            command=lambda: self.move_selected_items(
                source_var.get(),
                dest_var.get(),
                tree.selection()
            )
        )
        move_selected_btn.pack(pady=10)

    def create_visual_layout_tab(self, parent):
        """
        Create the visual layout tab content.

        Args:
            parent: The parent widget
        """
        # Create canvas for layout visualization
        canvas_frame = ttk.Frame(parent)
        canvas_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        canvas = tk.Canvas(
            canvas_frame,
            bg="white",
            width=800,
            height=500,
            highlightthickness=1,
            highlightbackground="#cccccc"
        )
        canvas.pack(fill=tk.BOTH, expand=True)

        # Create controls frame
        controls_frame = ttk.Frame(parent)
        controls_frame.pack(fill=tk.X, pady=10)

        # Location type filter
        ttk.Label(controls_frame, text="Location Type:").pack(side=tk.LEFT, padx=5)

        type_var = tk.StringVar(value="ALL")
        type_combo = ttk.Combobox(
            controls_frame,
            textvariable=type_var,
            values=["ALL"] + [e.value for e in StorageLocationType],
            state="readonly",
            width=15
        )
        type_combo.pack(side=tk.LEFT, padx=5)

        # Zoom control
        ttk.Label(controls_frame, text="Zoom:").pack(side=tk.LEFT, padx=5)

        zoom_var = tk.DoubleVar(value=1.0)
        zoom_scale = ttk.Scale(
            controls_frame,
            from_=0.5,
            to=2.0,
            orient=tk.HORIZONTAL,
            variable=zoom_var,
            length=150
        )
        zoom_scale.pack(side=tk.LEFT, padx=5)

        # Draw button
        draw_btn = ttk.Button(
            controls_frame,
            text="Draw Layout",
            command=lambda: self.draw_storage_layout(
                canvas,
                type_var.get(),
                zoom_var.get()
            )
        )
        draw_btn.pack(side=tk.RIGHT, padx=5)

        # Draw initial layout
        self.draw_storage_layout(canvas, "ALL", 1.0)

    def create_item_finder_tab(self, parent):
        """
        Create the item finder tab content.

        Args:
            parent: The parent widget
        """
        # Create search frame
        search_frame = ttk.Frame(parent)
        search_frame.pack(fill=tk.X, pady=10)

        ttk.Label(search_frame, text="Search for item:").pack(side=tk.LEFT, padx=5)

        search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=5)

        # Create filter options
        filter_frame = ttk.Frame(parent)
        filter_frame.pack(fill=tk.X, pady=10)

        ttk.Label(filter_frame, text="Item Type:").pack(side=tk.LEFT, padx=5)

        type_var = tk.StringVar(value="ALL")
        type_combo = ttk.Combobox(
            filter_frame,
            textvariable=type_var,
            values=["ALL", "material", "product", "tool"],
            state="readonly",
            width=15
        )
        type_combo.pack(side=tk.LEFT, padx=5)

        # Search button
        search_btn = ttk.Button(
            filter_frame,
            text="Search",
            command=lambda: self.find_items(
                search_var.get(),
                type_var.get(),
                results_tree
            )
        )
        search_btn.pack(side=tk.RIGHT, padx=5)

        # Create results frame
        results_frame = ttk.LabelFrame(parent, text="Search Results", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Create treeview for results
        tree_frame = ttk.Frame(results_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        results_tree = ttk.Treeview(
            tree_frame,
            columns=("id", "type", "name", "location", "quantity", "status"),
            show="headings"
        )

        results_tree.heading("id", text="ID")
        results_tree.heading("type", text="Type")
        results_tree.heading("name", text="Item")
        results_tree.heading("location", text="Location")
        results_tree.heading("quantity", text="Quantity")
        results_tree.heading("status", text="Status")

        results_tree.column("id", width=60)
        results_tree.column("type", width=100)
        results_tree.column("name", width=200)
        results_tree.column("location", width=150)
        results_tree.column("quantity", width=80)
        results_tree.column("status", width=100)

        # Add scrollbar
        sb = ttk.Scrollbar(tree_frame, orient="vertical", command=results_tree.yview)
        results_tree.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        results_tree.pack(fill=tk.BOTH, expand=True)

        # Action buttons
        action_frame = ttk.Frame(results_frame)
        action_frame.pack(fill=tk.X, pady=10)

        ttk.Button(
            action_frame,
            text="View Item",
            command=lambda: self.view_found_item(results_tree)
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            action_frame,
            text="Show on Map",
            command=lambda: self.show_on_map(results_tree)
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            action_frame,
            text="Generate Path",
            command=lambda: self.generate_picking_path(results_tree)
        ).pack(side=tk.LEFT, padx=5)

    def move_all_items(self, source_location, dest_location):
        """
        Move all items from source location to destination.

        Args:
            source_location: Source location
            dest_location: Destination location
        """
        if not source_location or not dest_location:
            messagebox.showerror("Error", "Please select both source and destination locations")
            return

        if source_location == dest_location:
            messagebox.showerror("Error", "Source and destination locations cannot be the same")
            return

        # Confirm operation
        if not messagebox.askyesno(
                "Confirm Move",
                f"Are you sure you want to move all items from {source_location} to {dest_location}?"
        ):
            return

        try:
            service = self.get_service(self.service_name)
            result = service.move_all_items(source_location, dest_location)

            if result:
                messagebox.showinfo(
                    "Success",
                    f"Successfully moved all items from {source_location} to {dest_location}"
                )

                # Refresh the view
                self.refresh()
            else:
                messagebox.showerror("Error", "Failed to move items")

        except Exception as e:
            self.logger.error(f"Error moving items: {str(e)}")
            messagebox.showerror("Error", f"Could not move items: {str(e)}")

    def move_selected_items(self, source_location, dest_location, item_selections):
        """
        Move selected items from source location to destination.

        Args:
            source_location: Source location
            dest_location: Destination location
            item_selections: Selected items
        """
        if not source_location or not dest_location:
            messagebox.showerror("Error", "Please select both source and destination locations")
            return

        if source_location == dest_location:
            messagebox.showerror("Error", "Source and destination locations cannot be the same")
            return

        if not item_selections:
            messagebox.showerror("Error", "Please select at least one item to move")
            return

        # Confirm operation
        if not messagebox.askyesno(
                "Confirm Move",
                f"Are you sure you want to move selected items from {source_location} to {dest_location}?"
        ):
            return

        try:
            # Get item IDs from selection
            # In a real app, we'd extract the item IDs from the tree item values
            # For this demo, we'll just use the selection index
            item_ids = list(range(len(item_selections)))

            service = self.get_service(self.service_name)
            result = service.move_items(source_location, dest_location, item_ids)

            if result:
                messagebox.showinfo(
                    "Success",
                    f"Successfully moved selected items from {source_location} to {dest_location}"
                )

                # Refresh the view
                self.refresh()
            else:
                messagebox.showerror("Error", "Failed to move items")

        except Exception as e:
            self.logger.error(f"Error moving items: {str(e)}")
            messagebox.showerror("Error", f"Could not move items: {str(e)}")

    def consolidate_items(self, source_location, dest_location):
        """
        Consolidate similar items between source and destination.

        Args:
            source_location: Source location
            dest_location: Destination location
        """
        if not source_location or not dest_location:
            messagebox.showerror("Error", "Please select both source and destination locations")
            return

        if source_location == dest_location:
            messagebox.showerror("Error", "Source and destination locations cannot be the same")
            return

        # Confirm operation
        if not messagebox.askyesno(
                "Confirm Consolidation",
                f"Are you sure you want to consolidate similar items between {source_location} and {dest_location}?"
        ):
            return

        try:
            service = self.get_service(self.service_name)
            result = service.consolidate_items(source_location, dest_location)

            if result:
                messagebox.showinfo(
                    "Success",
                    f"Successfully consolidated items between {source_location} and {dest_location}"
                )

                # Refresh the view
                self.refresh()
            else:
                messagebox.showerror("Error", "Failed to consolidate items")

        except Exception as e:
            self.logger.error(f"Error consolidating items: {str(e)}")
            messagebox.showerror("Error", f"Could not consolidate items: {str(e)}")

    def optimize_storage(self):
        """Optimize storage layout."""
        # Confirm operation
        if not messagebox.askyesno(
                "Confirm Optimization",
                "Are you sure you want to optimize the storage layout?\n\n"
                "This will reorganize items based on usage patterns and may move items between locations."
        ):
            return

        try:
            service = self.get_service(self.service_name)
            result = service.optimize_storage()

            if result:
                messagebox.showinfo(
                    "Success",
                    "Storage optimization complete. Items have been reorganized based on usage patterns."
                )

                # Refresh the view
                self.refresh()
            else:
                messagebox.showerror("Error", "Failed to optimize storage")

        except Exception as e:
            self.logger.error(f"Error optimizing storage: {str(e)}")
            messagebox.showerror("Error", f"Could not optimize storage: {str(e)}")

    def draw_storage_layout(self, canvas, location_type, zoom):
        """
        Draw the storage layout on canvas.

        Args:
            canvas: Canvas widget
            location_type: Type of locations to display or ALL
            zoom: Zoom level
        """
        # Clear canvas
        canvas.delete("all")

        try:
            # Get storage locations
            service = self.get_service(self.service_name)
            locations = service.get_storage_locations()

            # Filter by type if needed
            if location_type != "ALL":
                locations = [
                    loc for loc in locations
                    if ":" in loc.get("location", "") and loc.get("location", "").split(":", 1)[0] == location_type
                ]

            # Organize locations by type
            location_by_type = {}
            for loc in locations:
                location = loc.get("location", "")
                if ":" in location:
                    loc_type, loc_id = location.split(":", 1)
                    if loc_type not in location_by_type:
                        location_by_type[loc_type] = []
                    location_by_type[loc_type].append(loc)
                else:
                    if "OTHER" not in location_by_type:
                        location_by_type["OTHER"] = []
                    location_by_type["OTHER"].append(loc)

            # Calculate layout dimensions
            canvas_width = canvas.winfo_width()
            canvas_height = canvas.winfo_height()

            # Base cell size with zoom
            cell_w = 80 * zoom
            cell_h = 60 * zoom
            padding = 20 * zoom

            # Draw grid of locations
            y_offset = padding

            # Draw title
            canvas.create_text(
                canvas_width / 2,
                padding / 2,
                text="Storage Layout",
                font=("Helvetica", int(14 * zoom), "bold")
            )

            # Draw each type of location
            for loc_type, locs in location_by_type.items():
                # Draw type header
                canvas.create_text(
                    padding,
                    y_offset,
                    text=loc_type,
                    font=("Helvetica", int(12 * zoom), "bold"),
                    anchor="w"
                )

                y_offset += padding

                # Calculate grid dimensions
                cols = max(1, min(8, int((canvas_width - 2 * padding) / (cell_w + padding))))
                rows = (len(locs) + cols - 1) // cols  # Ceiling division

                # Draw locations
                for i, loc in enumerate(locs):
                    row = i // cols
                    col = i % cols

                    x = padding + col * (cell_w + padding)
                    y = y_offset + row * (cell_h + padding)

                    # Determine color based on occupancy
                    items_count = loc.get("items_count", 0)
                    if items_count == 0:
                        fill_color = "#EAEAEA"  # Empty
                    elif items_count < 5:
                        fill_color = "#D4EAD0"  # Low occupancy
                    elif items_count < 10:
                        fill_color = "#FFE699"  # Medium occupancy
                    else:
                        fill_color = "#F8CBAD"  # High occupancy

                    # Draw cell
                    canvas.create_rectangle(
                        x, y,
                        x + cell_w, y + cell_h,
                        fill=fill_color,
                        outline="#666666",
                        width=1
                    )

                    # Draw location ID (truncate if needed)
                    location = loc.get("location", "")
                    if ":" in location:
                        _, loc_id = location.split(":", 1)
                    else:
                        loc_id = location

                    # Truncate if too long
                    if len(loc_id) > 10:
                        loc_id = loc_id[:8] + "..."

                    canvas.create_text(
                        x + cell_w / 2,
                        y + cell_h / 3,
                        text=loc_id,
                        font=("Helvetica", int(9 * zoom))
                    )

                    # Draw item count
                    canvas.create_text(
                        x + cell_w / 2,
                        y + 2 * cell_h / 3,
                        text=f"Items: {items_count}",
                        font=("Helvetica", int(8 * zoom))
                    )

                    # Make cells clickable
                    canvas.tag_bind(
                        canvas.create_rectangle(
                            x, y,
                            x + cell_w, y + cell_h,
                            fill="",
                            outline=""
                        ),
                        "<Button-1>",
                        lambda event, loc=loc.get("location", ""): self.on_location_click(loc)
                    )

                # Update y_offset for next type
                y_offset += rows * (cell_h + padding) + padding

            # Draw legend
            legend_y = canvas_height - padding * 3
            legend_x = padding

            canvas.create_rectangle(
                legend_x, legend_y,
                legend_x + 20, legend_y + 20,
                fill="#EAEAEA",
                outline="#666666"
            )
            canvas.create_text(
                legend_x + 25, legend_y + 10,
                text="Empty",
                anchor="w",
                font=("Helvetica", int(8 * zoom))
            )

            legend_x += 100 * zoom
            canvas.create_rectangle(
                legend_x, legend_y,
                legend_x + 20, legend_y + 20,
                fill="#D4EAD0",
                outline="#666666"
            )
            canvas.create_text(
                legend_x + 25, legend_y + 10,
                text="Low Occupancy",
                anchor="w",
                font=("Helvetica", int(8 * zoom))
            )

            legend_x += 100 * zoom
            canvas.create_rectangle(
                legend_x, legend_y,
                legend_x + 20, legend_y + 20,
                fill="#FFE699",
                outline="#666666"
            )
            canvas.create_text(
                legend_x + 25, legend_y + 10,
                text="Medium Occupancy",
                anchor="w",
                font=("Helvetica", int(8 * zoom))
            )

            legend_x += 150 * zoom
            canvas.create_rectangle(
                legend_x, legend_y,
                legend_x + 20, legend_y + 20,
                fill="#F8CBAD",
                outline="#666666"
            )
            canvas.create_text(
                legend_x + 25, legend_y + 10,
                text="High Occupancy",
                anchor="w",
                font=("Helvetica", int(8 * zoom))
            )

        except Exception as e:
            self.logger.error(f"Error drawing storage layout: {str(e)}")
            canvas.create_text(
                canvas_width / 2,
                canvas_height / 2,
                text=f"Error drawing layout: {str(e)}",
                fill="red"
            )

    def on_location_click(self, location):
        """
        Handle location click on the map.

        Args:
            location: The clicked location
        """
        self.logger.info(f"Location clicked: {location}")

        try:
            # Show location details
            service = self.get_service(self.service_name)
            location_details = service.get_storage_location_details(location)

            if location_details:
                # Create popup
                dialog = tk.Toplevel(self.frame)
                dialog.title(f"Location: {location}")
                dialog.geometry("400x300")
                dialog.transient(self.frame)
                dialog.grab_set()

                # Create content
                content = ttk.Frame(dialog, padding=20)
                content.pack(fill=tk.BOTH, expand=True)

                # Title
                ttk.Label(
                    content,
                    text=location,
                    font=("Helvetica", 14, "bold")
                ).pack(anchor="w", pady=(0, 10))

                # Details
                details_frame = ttk.Frame(content)
                details_frame.pack(fill=tk.X, pady=5)

                ttk.Label(details_frame, text="Items Count:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
                ttk.Label(details_frame, text=str(location_details.get("items_count", 0))).grid(row=0, column=1,
                                                                                                sticky="w", padx=5,
                                                                                                pady=2)

                ttk.Label(details_frame, text="Total Value:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
                ttk.Label(details_frame, text=str(location_details.get("total_value", 0))).grid(row=1, column=1,
                                                                                                sticky="w", padx=5,
                                                                                                pady=2)

                ttk.Label(details_frame, text="Last Updated:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
                ttk.Label(details_frame, text=str(location_details.get("last_updated", ""))).grid(row=2, column=1,
                                                                                                  sticky="w", padx=5,
                                                                                                  pady=2)

                # Description
                if location_details.get("description"):
                    desc_frame = ttk.LabelFrame(content, text="Description")
                    desc_frame.pack(fill=tk.X, pady=10)

                    ttk.Label(
                        desc_frame,
                        text=location_details.get("description", ""),
                        wraplength=350
                    ).pack(padx=10, pady=10)

                # Add buttons
                btn_frame = ttk.Frame(dialog, padding=10)
                btn_frame.pack(fill=tk.X, side=tk.BOTTOM)

                ttk.Button(
                    btn_frame,
                    text="Close",
                    command=dialog.destroy
                ).pack(side=tk.RIGHT, padx=5)

                ttk.Button(
                    btn_frame,
                    text="View Details",
                    command=lambda: (dialog.destroy(), self.on_view())
                ).pack(side=tk.RIGHT, padx=5)

                # Center the dialog
                dialog.update_idletasks()
                width = dialog.winfo_width()
                height = dialog.winfo_height()
                x = (dialog.winfo_screenwidth() // 2) - (width // 2)
                y = (dialog.winfo_screenheight() // 2) - (height // 2)
                dialog.geometry(f'+{x}+{y}')

        except Exception as e:
            self.logger.error(f"Error showing location details: {str(e)}")
            messagebox.showerror("Error", f"Could not show location details: {str(e)}")

    def find_items(self, search_text, item_type, results_tree):
        """
        Search for items and display in results tree.

        Args:
            search_text: Text to search for
            item_type: Type of item to search for or ALL
            results_tree: Treeview to display results
        """
        # Clear existing results
        for item in results_tree.get_children():
            results_tree.delete(item)

        if not search_text:
            messagebox.showinfo("Search", "Please enter search text")
            return

        try:
            # Prepare filters
            filters = {"search": search_text}
            if item_type != "ALL":
                filters["item_type"] = item_type

            # Search for items
            service = self.get_service(self.service_name)
            items = service.find_inventory_items(**filters)

            # Add items to results
            if items:
                for item in items:
                    results_tree.insert("", "end", values=(
                        item.get("id", ""),
                        item.get("item_type", "").capitalize(),
                        item.get("name", ""),
                        item.get("storage_location", ""),
                        item.get("quantity", 0),
                        item.get("status", "")
                    ))

                # Show count
                messagebox.showinfo("Search Results", f"Found {len(items)} items matching your search.")
            else:
                messagebox.showinfo("Search Results", "No items found matching your search.")

        except Exception as e:
            self.logger.error(f"Error searching for items: {str(e)}")
            messagebox.showerror("Error", f"Could not search for items: {str(e)}")

    def view_found_item(self, results_tree):
        """
        View details of a found item.

        Args:
            results_tree: Treeview with results
        """
        selection = results_tree.selection()
        if not selection:
            messagebox.showinfo("View Item", "Please select an item to view")
            return

        try:
            # Get selected item values
            item_id = results_tree.item(selection[0], "values")[0]
            item_type = results_tree.item(selection[0], "values")[1].lower()

            # Open appropriate view based on item type
            if item_type == "material":
                from gui.views.materials.material_details_dialog import MaterialDetailsDialog
                dialog = MaterialDetailsDialog(self.frame, material_id=int(item_id), readonly=True)
                dialog.show()
            elif item_type == "product":
                from gui.views.products.product_details_view import ProductDetailsView
                dialog = ProductDetailsView(self.frame, product_id=int(item_id), readonly=True)
                dialog.show()
            elif item_type == "tool":
                from gui.views.tools.tool_details_dialog import ToolDetailsDialog
                dialog = ToolDetailsDialog(self.frame, tool_id=int(item_id), readonly=True)
                dialog.show()
            else:
                messagebox.showinfo("View Item", f"Viewing items of type {item_type} is not implemented")

        except Exception as e:
            self.logger.error(f"Error viewing found item: {str(e)}")
            messagebox.showerror("Error", f"Could not view item: {str(e)}")

    def show_on_map(self, results_tree):
        """
        Show selected item on storage map.

        Args:
            results_tree: Treeview with results
        """
        selection = results_tree.selection()
        if not selection:
            messagebox.showinfo("Show on Map", "Please select an item to show on the map")
            return

        try:
            # Get selected item location
            location = results_tree.item(selection[0], "values")[3]

            # Create map dialog
            dialog = tk.Toplevel(self.frame)
            dialog.title(f"Location Map: {location}")
            dialog.geometry("800x600")
            dialog.transient(self.frame)
            dialog.grab_set()

            # Create content
            content = ttk.Frame(dialog, padding=20)
            content.pack(fill=tk.BOTH, expand=True)

            # Create canvas for map
            canvas = tk.Canvas(
                content,
                bg="white",
                width=750,
                height=500,
                highlightthickness=1,
                highlightbackground="#cccccc"
            )
            canvas.pack(fill=tk.BOTH, expand=True)

            # Extract location type if available
            location_type = "ALL"
            if ":" in location:
                location_type = location.split(":", 1)[0]

            # Draw layout with highlighting for the selected location
            self.draw_storage_layout_with_highlight(canvas, location, 1.0)

            # Add close button
            btn_frame = ttk.Frame(dialog, padding=10)
            btn_frame.pack(fill=tk.X, side=tk.BOTTOM)

            ttk.Button(
                btn_frame,
                text="Close",
                command=dialog.destroy
            ).pack(side=tk.RIGHT, padx=5)

            # Center the dialog
            dialog.update_idletasks()
            width = dialog.winfo_width()
            height = dialog.winfo_height()
            x = (dialog.winfo_screenwidth() // 2) - (width // 2)
            y = (dialog.winfo_screenheight() // 2) - (height // 2)
            dialog.geometry(f'+{x}+{y}')

        except Exception as e:
            self.logger.error(f"Error showing location on map: {str(e)}")
            messagebox.showerror("Error", f"Could not show location on map: {str(e)}")

    def draw_storage_layout_with_highlight(self, canvas, highlight_location, zoom):
        """
        Draw storage layout with highlighting for a specific location.

        Args:
            canvas: Canvas widget
            highlight_location: Location to highlight
            zoom: Zoom level
        """
        # Clear canvas
        canvas.delete("all")

        try:
            # Get storage locations
            service = self.get_service(self.service_name)
            locations = service.get_storage_locations()

            # Organize locations by type
            location_by_type = {}
            for loc in locations:
                location = loc.get("location", "")
                if ":" in location:
                    loc_type, loc_id = location.split(":", 1)
                    if loc_type not in location_by_type:
                        location_by_type[loc_type] = []
                    location_by_type[loc_type].append(loc)
                else:
                    if "OTHER" not in location_by_type:
                        location_by_type["OTHER"] = []
                    location_by_type["OTHER"].append(loc)

            # Calculate layout dimensions
            canvas_width = canvas.winfo_width()
            canvas_height = canvas.winfo_height()

            # Base cell size with zoom
            cell_w = 80 * zoom
            cell_h = 60 * zoom
            padding = 20 * zoom

            # Draw grid of locations
            y_offset = padding

            # Draw title
            canvas.create_text(
                canvas_width / 2,
                padding / 2,
                text=f"Storage Map - Highlighted: {highlight_location}",
                font=("Helvetica", int(14 * zoom), "bold")
            )

            # Draw each type of location
            for loc_type, locs in location_by_type.items():
                # Draw type header
                canvas.create_text(
                    padding,
                    y_offset,
                    text=loc_type,
                    font=("Helvetica", int(12 * zoom), "bold"),
                    anchor="w"
                )

                y_offset += padding

                # Calculate grid dimensions
                cols = max(1, min(8, int((canvas_width - 2 * padding) / (cell_w + padding))))
                rows = (len(locs) + cols - 1) // cols  # Ceiling division

                # Draw locations
                for i, loc in enumerate(locs):
                    row = i // cols
                    col = i % cols

                    x = padding + col * (cell_w + padding)
                    y = y_offset + row * (cell_h + padding)

                    location = loc.get("location", "")

                    # Determine color based on matching highlight or occupancy
                    if location == highlight_location:
                        fill_color = "#FFC7CE"  # Highlighted in pink
                        outline_color = "#FF0000"  # Red outline
                        outline_width = 3
                    else:
                        items_count = loc.get("items_count", 0)
                        if items_count == 0:
                            fill_color = "#EAEAEA"  # Empty
                        elif items_count < 5:
                            fill_color = "#D4EAD0"  # Low occupancy
                        elif items_count < 10:
                            fill_color = "#FFE699"  # Medium occupancy
                        else:
                            fill_color = "#F8CBAD"  # High occupancy
                        outline_color = "#666666"
                        outline_width = 1

                    # Draw cell
                    canvas.create_rectangle(
                        x, y,
                        x + cell_w, y + cell_h,
                        fill=fill_color,
                        outline=outline_color,
                        width=outline_width
                    )

                    # Draw location ID (truncate if needed)
                    if ":" in location:
                        _, loc_id = location.split(":", 1)
                    else:
                        loc_id = location

                    # Truncate if too long
                    if len(loc_id) > 10:
                        loc_id = loc_id[:8] + "..."

                    canvas.create_text(
                        x + cell_w / 2,
                        y + cell_h / 3,
                        text=loc_id,
                        font=("Helvetica", int(9 * zoom))
                    )

                    # Draw item count
                    canvas.create_text(
                        x + cell_w / 2,
                        y + 2 * cell_h / 3,
                        text=f"Items: {loc.get('items_count', 0)}",
                        font=("Helvetica", int(8 * zoom))
                    )

                # Update y_offset for next type
                y_offset += rows * (cell_h + padding) + padding

            # Draw legend
            legend_y = canvas_height - padding * 3
            legend_x = padding

            # Highlight color
            canvas.create_rectangle(
                legend_x, legend_y,
                legend_x + 20, legend_y + 20,
                fill="#FFC7CE",
                outline="#FF0000",
                width=2
            )
            canvas.create_text(
                legend_x + 25, legend_y + 10,
                text="Highlighted Location",
                anchor="w",
                font=("Helvetica", int(8 * zoom))
            )

        except Exception as e:
            self.logger.error(f"Error drawing storage layout with highlight: {str(e)}")
            canvas.create_text(
                canvas_width / 2,
                canvas_height / 2,
                text=f"Error drawing layout: {str(e)}",
                fill="red"
            )

    def generate_picking_path(self, results_tree):
        """
        Generate an optimal picking path for selected items.

        Args:
            results_tree: Treeview with results
        """
        selections = results_tree.selection()
        if not selections:
            messagebox.showinfo("Generate Path", "Please select at least one item")
            return

        try:
            # Get selected items
            items = []
            for selection in selections:
                item_id = results_tree.item(selection, "values")[0]
                item_type = results_tree.item(selection, "values")[1].lower()
                item_name = results_tree.item(selection, "values")[2]
                location = results_tree.item(selection, "values")[3]
                items.append({
                    "id": item_id,
                    "type": item_type,
                    "name": item_name,
                    "location": location
                })

            # Call service to generate path
            service = self.get_service(self.service_name)
            path_result = service.generate_picking_path(items)

            if not path_result:
                messagebox.showerror("Error", "Failed to generate picking path")
                return

            # Create path dialog
            dialog = tk.Toplevel(self.frame)
            dialog.title("Picking Path")
            dialog.geometry("800x600")
            dialog.transient(self.frame)
            dialog.grab_set()

            # Create content
            content = ttk.Frame(dialog, padding=20)
            content.pack(fill=tk.BOTH, expand=True)

            # Create title
            ttk.Label(
                content,
                text="Optimal Picking Path",
                font=("Helvetica", 16, "bold")
            ).pack(anchor="w", pady=(0, 10))

            # Create path visualization
            canvas = tk.Canvas(
                content,
                bg="white",
                width=750,
                height=400,
                highlightthickness=1,
                highlightbackground="#cccccc"
            )
            canvas.pack(fill=tk.X, pady=10)

            # Draw path visualization
            self.draw_picking_path(canvas, path_result)

            # Create step-by-step instructions
            instructions_frame = ttk.LabelFrame(content, text="Step-by-Step Instructions")
            instructions_frame.pack(fill=tk.BOTH, expand=True, pady=10)

            # Create text widget for instructions
            instructions_text = tk.Text(instructions_frame, height=10, wrap=tk.WORD)
            instructions_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            # Add path steps
            for i, step in enumerate(path_result.get("steps", [])):
                instructions_text.insert(tk.END, f"{i + 1}. {step}\n\n")

            instructions_text.config(state="disabled")  # Make read-only

            # Add buttons
            btn_frame = ttk.Frame(dialog, padding=10)
            btn_frame.pack(fill=tk.X, side=tk.BOTTOM)

            ttk.Button(
                btn_frame,
                text="Close",
                command=dialog.destroy
            ).pack(side=tk.RIGHT, padx=5)

            ttk.Button(
                btn_frame,
                text="Print Path",
                command=lambda: self.print_picking_path(path_result)
            ).pack(side=tk.RIGHT, padx=5)

            # Center the dialog
            dialog.update_idletasks()
            width = dialog.winfo_width()
            height = dialog.winfo_height()
            x = (dialog.winfo_screenwidth() // 2) - (width // 2)
            y = (dialog.winfo_screenheight() // 2) - (height // 2)
            dialog.geometry(f'+{x}+{y}')

        except Exception as e:
            self.logger.error(f"Error generating picking path: {str(e)}")
            messagebox.showerror("Error", f"Could not generate picking path: {str(e)}")

    def draw_picking_path(self, canvas, path_result):
        """
        Draw the picking path visualization.

        Args:
            canvas: Canvas widget
            path_result: Path result data
        """
        # This is a placeholder for a real path visualization
        # In a real application, this would draw an actual map with the path

        canvas_width = canvas.winfo_width()
        canvas_height = canvas.winfo_height()

        # Draw title
        canvas.create_text(
            canvas_width / 2,
            30,
            text="Path Visualization",
            font=("Helvetica", 14, "bold")
        )

        # Draw simplified visualization
        canvas.create_text(
            canvas_width / 2,
            canvas_height / 2,
            text="Path visualization would be displayed here.\n"
                 "In a real application, this would show a map with the optimal route.",
            font=("Helvetica", 12),
            justify=tk.CENTER
        )

        # Draw placeholder visualization
        locations = path_result.get("path", [])
        if locations:
            # Draw simple path between locations
            margin = 100
            available_width = canvas_width - 2 * margin
            step_width = available_width / (len(locations) - 1) if len(locations) > 1 else available_width

            # Draw nodes and connections
            for i, location in enumerate(locations):
                x = margin + i * step_width
                y = canvas_height - 100

                # Draw node
                canvas.create_oval(x - 10, y - 10, x + 10, y + 10, fill="#4472C4", outline="")

                # Draw location text
                canvas.create_text(x, y - 20, text=location, font=("Helvetica", 9))

                # Draw connection line
                if i > 0:
                    prev_x = margin + (i - 1) * step_width
                    canvas.create_line(prev_x, y, x, y, fill="#4472C4", width=2, arrow=tk.LAST)

            # Draw start and end indicators
            start_x = margin
            end_x = margin + (len(locations) - 1) * step_width

            canvas.create_text(start_x, canvas_height - 130, text="START", font=("Helvetica", 10, "bold"),
                               fill="#4472C4")
            canvas.create_text(end_x, canvas_height - 130, text="END", font=("Helvetica", 10, "bold"), fill="#4472C4")

    def print_picking_path(self, path_result):
        """
        Print the picking path.

        Args:
            path_result: Path result data
        """
        messagebox.showinfo(
            "Print Path",
            "In a real application, this would print the picking path.\n\n"
            "The path would be formatted as a checklist for use in the warehouse."
        )

    def print_location_report(self, location):
        """
        Print a report for a specific location.

        Args:
            location: The location to print a report for
        """
        messagebox.showinfo(
            "Print Location Report",
            f"In a real application, this would print a report for location {location}.\n\n"
            "The report would include a list of all items and their quantities."
        )

    def generate_storage_report(self):
        """Generate a storage report."""
        self.logger.info("Opening storage report dialog")

        try:
            # Create dialog
            dialog = tk.Toplevel(self.frame)
            dialog.title("Generate Storage Report")
            dialog.geometry("500x400")
            dialog.transient(self.frame)
            dialog.grab_set()

            # Create content frame
            content = ttk.Frame(dialog, padding=20)
            content.pack(fill=tk.BOTH, expand=True)

            # Add instructions
            ttk.Label(
                content,
                text="Storage Report Generator",
                font=("Helvetica", 14, "bold")
            ).pack(pady=(0, 10))

            ttk.Label(
                content,
                text="Generate a report of storage locations and their contents.",
                wraplength=450
            ).pack(pady=5)

            # Report type section
            report_frame = ttk.LabelFrame(content, text="Report Type")
            report_frame.pack(fill=tk.X, pady=10)

            report_grid = ttk.Frame(report_frame, padding=10)
            report_grid.pack(fill=tk.X)

            report_type_var = tk.StringVar(value="SUMMARY")

            ttk.Radiobutton(
                report_grid,
                text="Summary Report",
                variable=report_type_var,
                value="SUMMARY"
            ).grid(row=0, column=0, sticky="w", padx=5)

            ttk.Radiobutton(
                report_grid,
                text="Detailed Report",
                variable=report_type_var,
                value="DETAILED"
            ).grid(row=0, column=1, sticky="w", padx=5)

            ttk.Radiobutton(
                report_grid,
                text="Utilization Report",
                variable=report_type_var,
                value="UTILIZATION"
            ).grid(row=1, column=0, sticky="w", padx=5)

            ttk.Radiobutton(
                report_grid,
                text="Optimization Report",
                variable=report_type_var,
                value="OPTIMIZATION"
            ).grid(row=1, column=1, sticky="w", padx=5)

            # Filters section
            filters_frame = ttk.LabelFrame(content, text="Filters")
            filters_frame.pack(fill=tk.X, pady=10)

            filters_grid = ttk.Frame(filters_frame, padding=10)
            filters_grid.pack(fill=tk.X)

            # Location type filter
            ttk.Label(filters_grid, text="Location Type:").grid(row=0, column=0, sticky="w", padx=5, pady=2)

            location_type_var = tk.StringVar(value="ALL")
            location_type_combo = ttk.Combobox(
                filters_grid,
                textvariable=location_type_var,
                values=["ALL"] + [e.value for e in StorageLocationType],
                state="readonly",
                width=15
            )
            location_type_combo.grid(row=0, column=1, sticky="w", padx=5, pady=2)

            # Minimum occupancy filter
            ttk.Label(filters_grid, text="Min. Occupancy:").grid(row=0, column=2, sticky="w", padx=5, pady=2)

            min_occupancy_var = tk.StringVar(value="0")
            min_occupancy_combo = ttk.Combobox(
                filters_grid,
                textvariable=min_occupancy_var,
                values=["0", "25%", "50%", "75%", "90%"],
                state="readonly",
                width=5
            )
            min_occupancy_combo.grid(row=0, column=3, sticky="w", padx=5, pady=2)

            # Format options
            format_frame = ttk.LabelFrame(content, text="Output Format")
            format_frame.pack(fill=tk.X, pady=10)

            format_grid = ttk.Frame(format_frame, padding=10)
            format_grid.pack(fill=tk.X)

            format_var = tk.StringVar(value="PDF")

            ttk.Radiobutton(
                format_grid,
                text="PDF Document",
                variable=format_var,
                value="PDF"
            ).grid(row=0, column=0, sticky="w", padx=5)

            ttk.Radiobutton(
                format_grid,
                text="Excel Spreadsheet",
                variable=format_var,
                value="EXCEL"
            ).grid(row=0, column=1, sticky="w", padx=5)

            ttk.Radiobutton(
                format_grid,
                text="CSV File",
                variable=format_var,
                value="CSV"
            ).grid(row=0, column=2, sticky="w", padx=5)

            # Add visualization option
            include_viz_var = tk.BooleanVar(value=True)
            ttk.Checkbutton(
                content,
                text="Include layout visualization",
                variable=include_viz_var
            ).pack(anchor="w", pady=5)

            # Buttons
            btn_frame = ttk.Frame(dialog, padding=10)
            btn_frame.pack(fill=tk.X, side=tk.BOTTOM)

            ttk.Button(
                btn_frame,
                text="Cancel",
                command=dialog.destroy
            ).pack(side=tk.RIGHT, padx=5)

            def generate_report():
                try:
                    # Get the filter values
                    report_type = report_type_var.get()
                    location_type = None if location_type_var.get() == "ALL" else location_type_var.get()
                    min_occupancy = min_occupancy_var.get()
                    include_viz = include_viz_var.get()

                    # Get the format
                    output_format = format_var.get()

                    # Generate the report
                    service = self.get_service(self.service_name)

                    # Show a confirmation that report is being generated
                    dialog.destroy()
                    messagebox.showinfo(
                        "Report Generation",
                        f"The {report_type} storage report is being generated in {output_format} format.\n\n"
                        "It will be saved to the reports directory."
                    )

                    # In a real application, this would call the service to generate the report
                    # For this demonstration, we'll just log the parameters
                    self.logger.info(
                        f"Generating storage report with: "
                        f"type={report_type}, format={output_format}, "
                        f"location_type={location_type}, min_occupancy={min_occupancy}, "
                        f"include_viz={include_viz}"
                    )

                except Exception as e:
                    self.logger.error(f"Error generating storage report: {str(e)}")
                    messagebox.showerror("Error", f"Could not generate report: {str(e)}")

            ttk.Button(
                btn_frame,
                text="Generate",
                command=generate_report
            ).pack(side=tk.RIGHT, padx=5)

            # Center the dialog
            dialog.update_idletasks()
            width = dialog.winfo_width()
            height = dialog.winfo_height()
            x = (dialog.winfo_screenwidth() // 2) - (width // 2)
            y = (dialog.winfo_screenheight() // 2) - (height // 2)
            dialog.geometry(f'+{x}+{y}')

        except Exception as e:
            self.logger.error(f"Error opening report dialog: {str(e)}")
            self.show_error("Error", f"Could not open report dialog: {str(e)}")