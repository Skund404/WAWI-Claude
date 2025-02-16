import tkinter as tk
from tkinter import ttk
from typing import List, Callable


class FilterDialog(tk.Toplevel):
    def __init__(self, parent, columns: List[str], callback: Callable):
        super().__init__(parent)
        self.title("Filter")
        self.callback = callback
        self.columns = columns
        self.filter_rows = []

        # Make dialog modal
        self.transient(parent)
        self.grab_set()

        # Create main frame
        self.main_frame = ttk.Frame(self, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Create filter frame
        self.filter_frame = ttk.Frame(self.main_frame)
        self.filter_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Add initial filter row
        self.add_filter_row()

        # Buttons
        button_frame = ttk.Frame(self.main_frame)
        button_frame.grid(row=1, column=0, pady=10)

        ttk.Button(button_frame, text="Add Filter",
                   command=self.add_filter_row).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Apply",
                   command=self.apply_filters).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel",
                   command=self.destroy).pack(side=tk.LEFT, padx=5)

        # Configure grid
        self.main_frame.columnconfigure(0, weight=1)

    def add_filter_row(self):
        """Add a new filter condition row"""
        row_frame = ttk.Frame(self.filter_frame)
        row_frame.pack(fill=tk.X, pady=2)

        # Column selection
        column_var = tk.StringVar()
        column_combo = ttk.Combobox(row_frame, textvariable=column_var,
                                    values=self.columns)
        column_combo.pack(side=tk.LEFT, padx=2)

        # Operator selection
        operator_var = tk.StringVar()
        operator_combo = ttk.Combobox(row_frame, textvariable=operator_var,
                                      values=['equals', 'contains',
                                              'greater than', 'less than'])
        operator_combo.pack(side=tk.LEFT, padx=2)

        # Value entry
        value_var = tk.StringVar()
        value_entry = ttk.Entry(row_frame, textvariable=value_var)
        value_entry.pack(side=tk.LEFT, padx=2)

        # Remove button
        if self.filter_rows:  # Only add remove button if not the first row
            ttk.Button(row_frame, text="✕",
                       command=lambda: self.remove_filter_row(row_frame)).pack(
                side=tk.LEFT, padx=2)

        # Store references
        self.filter_rows.append({
            'frame': row_frame,
            'column': column_var,
            'operator': operator_var,
            'value': value_var
        })

    def remove_filter_row(self, row_frame):
        """Remove a filter row"""
        # Find and remove row from filter_rows
        self.filter_rows = [row for row in self.filter_rows
                            if row['frame'] != row_frame]
        row_frame.destroy()

    def apply_filters(self):
        """Collect filter conditions and call callback"""
        filters = []
        for row in self.filter_rows:
            if all([row['column'].get(), row['operator'].get(), row['value'].get()]):
                filters.append({
                    'column': row['column'].get(),
                    'operator': row['operator'].get(),
                    'value': row['value'].get()
                })

        if not filters:
            tk.messagebox.showwarning("Warning", "No valid filters specified")
            return

        self.callback(filters)
        self.destroy()