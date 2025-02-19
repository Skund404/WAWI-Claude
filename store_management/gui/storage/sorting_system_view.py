import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Dict, List, Optional
import uuid
import csv
import traceback
import random
import string

from store_management.database.db_manager import DatabaseManager
from store_management.config import TABLES, COLORS
from store_management.gui.dialogs.add_dialog import AddDialog
from store_management.gui.dialogs.search_dialog import SearchDialog
from store_management.gui.dialogs.filter_dialog import FilterDialog
from store_management.config import get_database_path



def evaluate_math_expression(current_value, expression):
    """
    Evaluate a mathematical expression relative to the current value.

    Args:
        current_value (int): Current storage value
        expression (str): Mathematical expression to evaluate

    Returns:
        int: Calculated new value

    Raises:
        ValueError: If expression is invalid or results in negative value
    """
    import math

    try:
        # Replace 'x' or '*' with multiplication operator
        expression = expression.replace('x', '*')

        # Strip any whitespace from the expression
        expression = expression.strip()

        # If the expression starts with an operator, prepend the current value
        if expression[0] in ['+', '-', '*', '/']:
            full_expression = f"{current_value}{expression}"
        else:
            full_expression = expression

        # Safely evaluate the expression
        # We use a restricted eval with only basic math operations
        allowed_names = {
            'abs': abs,
            'int': int,
            'round': round,
            'min': min,
            'max': max
        }
        allowed_names.update(vars(math))

        # Evaluate the expression
        result = eval(full_expression, {"__builtins__": None}, allowed_names)

        # Ensure result is a non-negative integer
        result = int(result)
        if result < 0:
            raise ValueError("Result cannot be negative")

        return result

    except Exception as e:
        raise ValueError(f"Invalid mathematical expression: {str(e)}")

class SortingSystemView(ttk.Frame):

    def generate_part_id(self, name, bin_location):
        """
        Generate a unique Part ID
        - Always starts with 'P'
        - Followed by first letters of first two words of name
        - Ensures uniqueness with a random suffix
        """
        import random
        import string

        # Sanitize name input
        name = name.strip()

        # Split name into words and get first two word initials
        words = name.split()

        # Determine first letters
        if len(words) >= 2:
            # Use first letters of first two words
            first_letters = words[0][0].upper() + words[1][0].upper()
        elif len(words) == 1:
            # If only one word, use its first letter twice
            first_letters = words[0][0].upper() * 2
        else:
            # Fallback for empty name
            first_letters = 'XX'

        # Check for existing IDs
        existing_ids = []
        try:
            self.db.connect()
            results = self.db.execute_query("SELECT unique_id_parts FROM sorting_system")
            existing_ids = [row[0] for row in results] if results else []
        except Exception as e:
            print(f"Error checking existing IDs: {e}")
        finally:
            self.db.disconnect()

        # Generate unique ID
        while True:
            # Generate random alphanumeric suffix
            suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))

            # Construct Part ID: P + first letters of first two words + random suffix
            part_id = f"P{first_letters}{suffix}"

            # Check if ID is unique
            if part_id not in existing_ids:
                return part_id

    def save_part(self, entries, dialog):
        """Save the new part to the database"""
        try:
            # Collect input data
            data = {}
            required_fields = [
                ('name', 'Part Name'),
                ('bin', 'Bin Location'),
                ('in_storage', 'Initial Stock'),
                ('warning_threshold', 'Warning Threshold')
            ]

            for field, label in required_fields:
                value = entries[field].get().strip()
                if not value:
                    messagebox.showerror("Error", f"{label} is required")
                    return
                data[field] = value

            # Collect optional fields
            data['color'] = entries['color'].get().strip() or None
            data['notes'] = entries['notes'].get().strip() or None

            # Validate numeric inputs
            try:
                data['in_storage'] = int(data['in_storage'])
                data['warning_threshold'] = int(data['warning_threshold'])

                if data['in_storage'] < 0:
                    raise ValueError("Stock cannot be negative")
                if data['warning_threshold'] < 0:
                    raise ValueError("Warning threshold cannot be negative")
            except ValueError as e:
                messagebox.showerror("Error", str(e))
                return

            # Generate Part ID
            part_id = self.generate_part_id(data['name'], data['bin'])

            # Prepare data for database insertion
            insert_data = {
                'unique_id_parts': part_id,
                'name': data['name'],
                'color': data['color'],
                'in_storage': data['in_storage'],
                'warning_threshold': data['warning_threshold'],
                'bin': data['bin'],
                'notes': data['notes']
            }

            # Attempt to insert record
            self.db.connect()
            try:
                success = self.db.insert_record('sorting_system', insert_data)

                if success:
                    # Add to undo stack
                    self.undo_stack.append(('add', insert_data))
                    self.redo_stack.clear()

                    # Refresh the view
                    self.load_data()

                    messagebox.showinfo(
                        "Success",
                        f"Part added successfully\nPart ID: {part_id}"
                    )
                    dialog.destroy()
                else:
                    messagebox.showerror(
                        "Error",
                        "Failed to add part. Please check your database connection."
                    )

            except Exception as e:
                print(f"Error Details: {str(e)}")
                traceback.print_exc()
                messagebox.showerror(
                    "Database Error",
                    f"An error occurred while adding the part:\n{str(e)}"
                )
            finally:
                self.db.disconnect()

        except Exception as e:
            print("Unexpected Error:")
            traceback.print_exc()
            messagebox.showerror(
                "Unexpected Error",
                f"An unexpected error occurred:\n{str(e)}"
            )

    def show_add_part_dialog(self):
        """Show dialog for adding a new part to the sorting system"""
        dialog = tk.Toplevel(self)
        dialog.title("Add New Part")
        dialog.geometry("600x400")
        dialog.transient(self)
        dialog.grab_set()

        # Main frame
        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Entry fields dictionary
        entries = {}
        fields = [
            ('name', 'Part Name', True),
            ('color', 'Color', False),  # Optional
            ('in_storage', 'Initial Stock', True),
            ('warning_threshold', 'Warning Threshold', True),
            ('bin', 'Bin Location', True),
            ('notes', 'Notes', False)
        ]

        for i, (field, label, required) in enumerate(fields):
            ttk.Label(main_frame, text=f"{label}:").grid(row=i, column=0, sticky='w', padx=5, pady=2)

            if field in ['in_storage', 'warning_threshold']:
                entries[field] = ttk.Spinbox(main_frame, from_=0, to=1000, width=20)
                if field == 'warning_threshold':
                    entries[field].insert(0, "5")  # Default warning threshold
            else:
                entries[field] = ttk.Entry(main_frame, width=40)

            entries[field].grid(row=i, column=1, sticky='ew', padx=5, pady=2)

            if required:
                ttk.Label(main_frame, text="*", foreground="red").grid(row=i, column=2, sticky='w')

        # Configure grid
        main_frame.columnconfigure(1, weight=1)

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=len(fields), column=0, columnspan=3, pady=10)

        ttk.Button(
            button_frame,
            text="Save",
            command=lambda: self.save_part(entries, dialog)
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            button_frame,
            text="Cancel",
            command=dialog.destroy
        ).pack(side=tk.LEFT, padx=5)

        # Add required fields note
        ttk.Label(
            main_frame,
            text="* Required fields",
            foreground="red"
        ).grid(row=len(fields) + 1, column=0, columnspan=3, sticky='w', pady=(5, 0))

        # Set focus
        entries['name'].focus_set()

    def show_add_dialog(self):
        """Wrapper method for backward compatibility"""
        self.show_add_part_dialog()





    def show_batch_threshold_dialog(self):
        """Show dialog for batch updating warning thresholds"""
        dialog = tk.Toplevel(self)
        dialog.title("Update Warning Thresholds")
        dialog.geometry("400x200")
        dialog.transient(self)
        dialog.grab_set()

        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Value entry
        ttk.Label(main_frame, text="New Warning Threshold:").pack(pady=5)
        threshold_entry = ttk.Spinbox(main_frame, from_=0, to=1000, width=20)
        threshold_entry.pack(pady=5)
        threshold_entry.insert(0, "5")

        # Apply method choice
        method_var = tk.StringVar(value="absolute")
        ttk.Radiobutton(
            main_frame,
            text="Absolute Value",
            variable=method_var,
            value="absolute"
        ).pack(pady=2)
        ttk.Radiobutton(
            main_frame,
            text="Percentage of Current Stock",
            variable=method_var,
            value="percentage"
        ).pack(pady=2)

        def apply_update():
            try:
                new_value = threshold_entry.get().strip()
                if not new_value:
                    messagebox.showerror("Error", "Please enter a value")
                    return

                value = float(new_value)
                if value < 0:
                    messagebox.showerror("Error", "Value must be non-negative")
                    return

                selected = self.tree.selection()
                if not selected:
                    messagebox.showinfo("Info", "Please select items to update")
                    return

                self.db.connect()
                try:
                    updated_items = []
                    for item in selected:
                        old_values = {col: self.tree.set(item, col) for col in self.columns}

                        if method_var.get() == "percentage":
                            current_stock = int(self.tree.set(item, 'in_storage'))
                            new_threshold = int(current_stock * (value / 100))
                        else:
                            new_threshold = int(value)

                        # Update database
                        unique_id = self.tree.set(item, 'unique_id_parts')
                        self.update_record(unique_id, 'warning_threshold', str(new_threshold))

                        # Update treeview
                        self.tree.set(item, 'warning_threshold', str(new_threshold))

                        # Update warning status
                        in_storage = int(self.tree.set(item, 'in_storage'))
                        warning_tag = self.get_warning_tag(in_storage, new_threshold)
                        self.tree.item(item, tags=(warning_tag,))

                        updated_items.append((item, old_values))

                    # Add to undo stack
                    if updated_items:
                        self.undo_stack.append(('batch_edit', updated_items))
                        self.redo_stack.clear()

                    messagebox.showinfo(
                        "Success",
                        f"Updated warning thresholds for {len(updated_items)} items"
                    )
                    dialog.destroy()

                finally:
                    self.db.disconnect()

            except ValueError as e:
                messagebox.showerror("Error", f"Invalid value: {str(e)}")
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred: {str(e)}")

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text="Apply", command=apply_update).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    def show_add_dialog(self):
        """Wrapper method for backward compatibility"""
        self.show_add_part_dialog()

    def handle_return(self, event=None):
        """Handle Return key press - typically used for editing or confirming selection"""
        selected = self.tree.selection()
        if selected:
            # Start editing the second column of the first selected item
            self.start_cell_edit(selected[0], '#2')

    def handle_escape(self, event=None):
        """Handle Escape key press - typically used to clear selection"""
        self.tree.selection_remove(self.tree.selection())

    def __init__(self, parent):
        super().__init__(parent)
        self.db = DatabaseManager(get_database_path())

        # Initialize undo/redo stacks
        self.undo_stack = []
        self.redo_stack = []

        # Setup UI components
        self.setup_toolbar()
        self.setup_table()
        self.load_data()

    def setup_toolbar(self):
        """Create the toolbar with all buttons"""
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, padx=5, pady=5)

        # Left side buttons
        ttk.Button(toolbar, text="ADD", command=self.show_add_part_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Search", command=self.show_search_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Filter", command=self.show_filter_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Batch Update", command=self.show_batch_threshold_dialog).pack(side=tk.LEFT, padx=2)

        # Right side buttons
        ttk.Button(toolbar, text="Undo", command=self.undo).pack(side=tk.RIGHT, padx=2)
        ttk.Button(toolbar, text="Redo", command=self.redo).pack(side=tk.RIGHT, padx=2)
        ttk.Button(toolbar, text="Save", command=self.save_table).pack(side=tk.RIGHT, padx=2)
        ttk.Button(toolbar, text="Load", command=self.load_table).pack(side=tk.RIGHT, padx=2)
        ttk.Button(toolbar, text="Reset View", command=self.reset_view).pack(side=tk.RIGHT, padx=2)

    def setup_table(self):
        """Create the main table view"""
        # Create table frame
        self.tree_frame = ttk.Frame(self)
        self.tree_frame.pack(expand=True, fill='both', padx=5, pady=5)

        # Define columns
        self.columns = [
            'unique_id_parts', 'name', 'color', 'in_storage', 'warning_threshold', 'bin', 'notes'
        ]

        # Create scrollbars
        vsb = ttk.Scrollbar(self.tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(self.tree_frame, orient="horizontal")

        # Create treeview
        self.tree = ttk.Treeview(
            self.tree_frame,
            columns=self.columns,
            show='headings',
            selectmode='extended',
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set
        )

        # Configure scrollbars
        vsb.configure(command=self.tree.yview)
        hsb.configure(command=self.tree.xview)

        # Setup headers and columns
        for col in self.columns:
            self.tree.heading(col, text=col.replace('_', ' ').title(),
                              command=lambda c=col: self.sort_column(c))
            self.tree.column(col, width=100, minwidth=50)

        # Grid layout
        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

        # Configure grid weights
        self.tree_frame.grid_columnconfigure(0, weight=1)
        self.tree_frame.grid_rowconfigure(0, weight=1)

        # Configure warning levels
        self.tree.tag_configure('critical_stock', background='#ff8080')  # Dark red
        self.tree.tag_configure('low_stock', background='#ffcccc')  # Light red
        self.tree.tag_configure('warning_stock', background='#ffe6cc')  # Orange

        # Bind events
        self.tree.bind('<Double-1>', self.on_double_click)
        self.tree.bind('<Delete>', self.delete_selected)
        self.tree.bind('<Return>', self.handle_return)
        self.tree.bind('<Escape>', self.handle_escape)



    def get_warning_tag(self, in_storage: int, warning_threshold: int) -> str:
        """
        Determine the warning level tag based on stock level

        Args:
            in_storage (int): Current stock level
            warning_threshold (int): Warning threshold level

        Returns:
            str: Warning tag level or empty string if no warning
        """
        try:
            in_storage = int(in_storage)
            warning_threshold = int(warning_threshold)

            if in_storage <= warning_threshold * 0.5:  # Below 50% of threshold
                return 'critical_stock'
            elif in_storage <= warning_threshold * 0.75:  # Below 75% of threshold
                return 'low_stock'
            elif in_storage <= warning_threshold:  # At or below threshold
                return 'warning_stock'
            return ''
        except (ValueError, TypeError):
            # If either value can't be converted to int, return no warning
            return ''

    def load_data(self):
        """Load data from database into table"""
        self.db.connect()
        try:
            query = "SELECT * FROM sorting_system ORDER BY bin"
            results = self.db.execute_query(query)

            # Clear existing items
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Insert new data
            for row in results:
                item = self.tree.insert('', 'end', values=row[:-2])  # Exclude timestamps

                try:
                    # Check against warning threshold
                    in_storage = row[3]  # in_storage column
                    warning_threshold = row[4]  # warning_threshold column

                    if in_storage is not None and warning_threshold is not None:
                        warning_tag = self.get_warning_tag(in_storage, warning_threshold)
                        if warning_tag:
                            self.tree.item(item, tags=(warning_tag,))
                except (IndexError, ValueError, TypeError) as e:
                    print(f"Warning: Could not process warning threshold for row: {row}. Error: {e}")
                    continue

        finally:
            self.db.disconnect()

    def sort_column(self, col):
        """Sort table by column"""
        # Get all items
        l = [(self.tree.set(k, col), k) for k in self.tree.get_children('')]

        # Determine sort direction
        reverse = False
        if hasattr(self, '_last_sort') and self._last_sort == (col, False):
            reverse = True

        # Store sort state
        self._last_sort = (col, reverse)

        # Sort items
        try:
            # Try numeric sort for in_storage column
            if col == 'in_storage':
                l.sort(key=lambda x: float(x[0]) if x[0] else 0, reverse=reverse)
            else:
                l.sort(reverse=reverse)
        except ValueError:
            l.sort(reverse=reverse)

        # Rearrange items
        for index, (_, k) in enumerate(l):
            self.tree.move(k, '', index)

        # Update header arrow
        for column in self.columns:
            if column != col:
                self.tree.heading(column, text=column.replace('_', ' ').title())
        arrow = "▼" if reverse else "▲"
        self.tree.heading(col, text=f"{col.replace('_', ' ').title()} {arrow}")

    def on_double_click(self, event):
        """
        Handle double-click event on treeview cells
        Enables cell editing when a cell is double-clicked
        """
        # Print debug information
        print("Double-click event triggered")

        # Identify the region, column, and row of the click
        region = self.tree.identify("region", event.x, event.y)
        print(f"Clicked region: {region}")

        # Only proceed if clicked on a cell
        if region == "cell":
            # Identify the column and row
            column = self.tree.identify_column(event.x)
            item = self.tree.identify_row(event.y)

            print(f"Column: {column}")
            print(f"Item: {item}")

            # Get the column index (remove the '#' and convert to zero-based index)
            col_index = int(column[1:]) - 1

            # Get the column name
            col_name = self.columns[col_index]
            print(f"Column Name: {col_name}")

            # Skip editing for certain columns (like unique ID)
            if col_name == 'unique_id_parts':
                print("Skipping edit for unique_id_parts")
                return

            # Start cell editing
            self.start_cell_edit(item, column)

    def start_cell_edit(self, item, column):
        """Start cell editing with support for warning threshold"""
        try:
            print(f"Starting cell edit for item: {item}, column: {column}")

            # Get column index and name
            try:
                col_num = int(column[1:]) - 1
                col_name = self.columns[col_num]
            except (IndexError, ValueError) as e:
                print(f"Error parsing column: {e}")
                messagebox.showerror("Edit Error", f"Invalid column: {column}")
                return

            # Skip editing for certain columns
            if col_name == 'unique_id_parts':
                return

            # Get current value
            current_value = self.tree.set(item, col_name)

            # Create edit frame
            frame = ttk.Frame(self.tree)

            # Create appropriate entry widget
            if col_name in ['in_storage', 'warning_threshold']:
                entry = ttk.Entry(frame)
            else:
                entry = ttk.Entry(frame)

            entry.insert(0, current_value)
            entry.select_range(0, tk.END)
            entry.pack(fill=tk.BOTH, expand=True)

            # Position the edit frame
            bbox = self.tree.bbox(item, column)
            if bbox:
                frame.place(x=bbox[0], y=bbox[1], width=bbox[2], height=bbox[3])
            else:
                frame.destroy()
                return

            def save_edit(event=None):
                try:
                    new_value = entry.get().strip()

                    # Validate and process the new value
                    if col_name in ['in_storage', 'warning_threshold']:
                        if any(op in new_value for op in ['-', '+', '*', '/', '(', ')']):
                            try:
                                current_int = int(current_value)
                                new_value_int = evaluate_math_expression(current_int, new_value)
                                new_value = str(new_value_int)
                            except ValueError as e:
                                messagebox.showerror("Error", str(e))
                                frame.destroy()
                                return
                        else:
                            try:
                                new_value_int = int(new_value)
                                if new_value_int < 0:
                                    messagebox.showerror("Error", "Value must be non-negative")
                                    frame.destroy()
                                    return
                            except ValueError:
                                messagebox.showerror("Error", "Must be a valid number")
                                frame.destroy()
                                return

                    # Only update if value has changed
                    if new_value != current_value:
                        old_values = {col: self.tree.set(item, col) for col in self.columns}
                        self.undo_stack.append(('edit', item, old_values))
                        self.redo_stack.clear()

                        # Update database and treeview
                        unique_id = self.tree.set(item, 'unique_id_parts')
                        self.update_record(unique_id, col_name, new_value)
                        self.tree.set(item, col_name, new_value)

                        # Update low stock warning
                        in_storage = int(self.tree.set(item, 'in_storage'))
                        warning_threshold = int(self.tree.set(item, 'warning_threshold'))

                        if in_storage <= warning_threshold:
                            self.tree.item(item, tags=('low_stock',))
                        else:
                            self.tree.item(item, tags=())

                    frame.destroy()

                except Exception as e:
                    print(f"Save error: {e}")
                    messagebox.showerror("Error", str(e))
                    frame.destroy()

            def cancel_edit(event=None):
                frame.destroy()

            # Bind events
            entry.bind('<Return>', save_edit)
            entry.bind('<Escape>', cancel_edit)
            entry.bind('<FocusOut>', save_edit)
            entry.focus_set()

        except Exception as e:
            print(f"Cell edit error: {e}")
            messagebox.showerror("Error", str(e))

    def update_record(self, unique_id: str, column: str, value: str):
        """Update record in database"""
        self.db.connect()
        try:
            success = self.db.update_record(
                TABLES['SORTING_SYSTEM'],
                {column: value},
                "unique_id_parts = ?",
                (unique_id,)
            )
            if not success:
                messagebox.showerror("Error", "Failed to update database")
        finally:
            self.db.disconnect()

    def delete_selected(self, event=None):
        """Delete selected items"""
        selected = self.tree.selection()
        if not selected:
            return

        if messagebox.askyesno("Confirm Delete",
                               "Are you sure you want to delete the selected items?"):
            self.db.connect()
            try:
                # Check if parts are used in any recipes
                used_parts = []
                for item in selected:
                    unique_id = self.tree.set(item, 'unique_id_parts')
                    result = self.db.execute_query(
                        "SELECT recipe_id FROM recipe_details WHERE unique_id_parts = ?",
                        (unique_id,)
                    )
                    if result:
                        used_parts.append(unique_id)

                if used_parts:
                    messagebox.showerror(
                        "Error",
                        f"Cannot delete parts that are used in recipes: {', '.join(used_parts)}"
                    )
                    return

                # Store for undo
                deleted_items = []
                for item in selected:
                    values = {col: self.tree.set(item, col) for col in self.columns}
                    deleted_items.append((item, values))

                    # Delete from database
                    unique_id = values['unique_id_parts']
                    self.db.delete_record(
                        TABLES['SORTING_SYSTEM'],
                        "unique_id_parts = ?",
                        (unique_id,)
                    )

                    # Delete from tree
                    self.tree.delete(item)

                self.undo_stack.append(('delete', deleted_items))
                self.redo_stack.clear()

            finally:
                self.db.disconnect()

    def undo(self, event=None):
        """Undo last action"""
        if not self.undo_stack:
            return

        action = self.undo_stack.pop()
        action_type = action[0]

        if action_type == 'edit':
            item, old_values = action[1:]
            # Store current values for redo
            current_values = {col: self.tree.set(item, col) for col in self.columns}
            self.redo_stack.append(('edit', item, current_values))

            # Restore old values
            for col, value in old_values.items():
                self.tree.set(item, col, value)
                self.update_record(old_values['unique_id_parts'], col, value)

            # Update low stock warning
            in_storage = int(old_values['in_storage'])
            if in_storage <= 5:
                self.tree.item(item, tags=('low_stock',))
            else:
                self.tree.item(item, tags=())

        elif action_type == 'add':
            data = action[1]
            # Delete added record
            self.db.connect()
            try:
                self.db.delete_record(
                    TABLES['SORTING_SYSTEM'],
                    "unique_id_parts = ?",
                    (data['unique_id_parts'],)
                )

                # Find and delete tree item
                for item in self.tree.get_children():
                    if self.tree.set(item, 'unique_id_parts') == data['unique_id_parts']:
                        self.tree.delete(item)
                        break

                self.redo_stack.append(('readd', data))

            finally:
                self.db.disconnect()

        elif action_type == 'delete':
            deleted_items = action[1]
            restored_items = []

            self.db.connect()
            try:
                for item_id, values in deleted_items:
                    # Restore to database
                    self.db.insert_record(TABLES['SORTING_SYSTEM'], values)

                    # Restore to tree
                    new_item = self.tree.insert('', 'end', values=list(values.values()))

                    # Restore low stock warning
                    in_storage = int(values['in_storage'])
                    if in_storage <= 5:
                        self.tree.item(new_item, tags=('low_stock',))

                    restored_items.append((new_item, values))

                self.redo_stack.append(('undelete', restored_items))

            finally:
                self.db.disconnect()

    def redo(self, event=None):
        """Redo last undone action"""
        if not self.redo_stack:
            return

        action = self.redo_stack.pop()
        action_type = action[0]

        if action_type == 'edit':
            item, new_values = action[1:]
            # Store current values for undo
            current_values = {col: self.tree.set(item, col) for col in self.columns}
            self.undo_stack.append(('edit', item, current_values))

            # Restore new values
            for col, value in new_values.items():
                self.tree.set(item, col, value)
                self.update_record(new_values['unique_id_parts'], col, value)

            # Update low stock warning
            in_storage = int(new_values['in_storage'])
            if in_storage <= 5:
                self.tree.item(item, tags=('low_stock',))
            else:
                self.tree.item(item, tags=())

        elif action_type == 'readd':
            data = action[1]
            # Re-add the record
            self.db.connect()
            try:
                if self.db.insert_record(TABLES['SORTING_SYSTEM'], data):
                    # Add to tree
                    item = self.tree.insert('', 'end', values=list(data.values()))

                    # Add low stock warning if needed
                    if int(data['in_storage']) <= 5:
                        self.tree.item(item, tags=('low_stock',))

                    self.undo_stack.append(('add', data))

            finally:
                self.db.disconnect()

        elif action_type == 'undelete':
            restored_items = action[1]
            deleted_items = []

            self.db.connect()
            try:
                for item, values in restored_items:
                    # Delete from database
                    self.db.delete_record(
                        TABLES['SORTING_SYSTEM'],
                        "unique_id_parts = ?",
                        (values['unique_id_parts'],)
                    )

                    # Delete from tree
                    self.tree.delete(item)
                    deleted_items.append((item, values))

                self.undo_stack.append(('delete', deleted_items))

            finally:
                self.db.disconnect()

    def save_table(self):
        """Save current table state to file"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )

        if not file_path:
            return

        try:
            with open(file_path, 'w', newline='') as file:
                writer = csv.writer(file)
                # Write headers
                writer.writerow(self.columns)

                # Write data
                for item in self.tree.get_children():
                    row = [self.tree.set(item, col) for col in self.columns]
                    writer.writerow(row)

            messagebox.showinfo("Success", "Table saved successfully")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save table: {str(e)}")

    def load_table(self):
        """Load table state from file"""
        file_path = filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )

        if not file_path:
            return

        try:
            self.db.connect()

            # Clear existing data
            self.db.execute_query("DELETE FROM sorting_system")

            # Read and insert new data
            with open(file_path, 'r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    self.db.insert_record(TABLES['SORTING_SYSTEM'], row)

            # Reload table
            self.load_data()
            messagebox.showinfo("Success", "Table loaded successfully")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load table: {str(e)}")

        finally:
            self.db.disconnect()

    def show_search_dialog(self):
        """Show search dialog"""
        dialog = SearchDialog(self, self.columns, self.search_items)
        self.wait_window(dialog)

    def search_items(self, search_params: Dict):
        """Search items based on search parameters"""
        column = search_params['column']
        search_text = search_params['text']
        match_case = search_params['match_case']

        # Clear current selection
        self.tree.selection_remove(*self.tree.selection())

        for item in self.tree.get_children():
            values = self.tree.item(item)['values']

            # Get the value to search in
            if column == 'All':
                search_in = ' '.join(str(v) for v in values)
            else:
                col_idx = self.columns.index(column)
                search_in = str(values[col_idx])

            # Perform search
            if not match_case:
                search_in = search_in.lower()
                search_text = search_text.lower()

            if search_text in search_in:
                self.tree.selection_add(item)
                self.tree.see(item)

    def show_filter_dialog(self):
        """Show filter dialog"""
        dialog = FilterDialog(self, self.columns, self.apply_filters)
        self.wait_window(dialog)

    def apply_filters(self, filters: List[Dict]):
        """Apply filters to the table view"""
        query = "SELECT * FROM sorting_system WHERE "
        conditions = []
        params = []

        for filter_condition in filters:
            column = filter_condition['column']
            operator = filter_condition['operator']
            value = filter_condition['value']

            if operator == 'equals':
                conditions.append(f"{column} = ?")
                params.append(value)
            elif operator == 'contains':
                conditions.append(f"{column} LIKE ?")
                params.append(f"%{value}%")
            elif operator == 'greater than':
                conditions.append(f"{column} > ?")
                params.append(value)
            elif operator == 'less than':
                conditions.append(f"{column} < ?")
                params.append(value)

        query += " AND ".join(conditions)
        query += " ORDER BY bin"

        self.db.connect()
        try:
            results = self.db.execute_query(query, tuple(params))

            # Update table
            for item in self.tree.get_children():
                self.tree.delete(item)

            for row in results:
                item = self.tree.insert('', 'end', values=row[:-2])
                if int(row[3]) <= 5:  # Check in_storage
                    self.tree.item(item, tags=('low_stock',))

        finally:
            self.db.disconnect()

    def reset_view(self):
        """Reset table to default view"""
        self.load_data()
