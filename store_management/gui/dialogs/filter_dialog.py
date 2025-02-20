import tkinter as tk
from tkinter import ttk
from typing import List, Callable, Dict


class FilterDialog(tk.Toplevel):
    def __init__(self, parent, columns: List[str], filter_callback: Callable[[List[Dict]], None]):
        """
        Initialize filter dialog

        Args:
            parent: Parent window
            columns: List of column names to filter on
            filter_callback: Function to call with filter conditions
        """
        super().__init__(parent)
        self.title("Filter Items")
        self.geometry("500x400")
        self.transient(parent)
        self.grab_set()

        self.columns = columns
        self.filter_callback = filter_callback
        self.filter_frames = []  # Keep track of filter frames

        self.setup_ui()

    def setup_ui(self):
        """Setup the dialog UI components"""
        # Main frame
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Filters container with scrollbar
        container_frame = ttk.Frame(main_frame)
        container_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Canvas for scrolling
        canvas = tk.Canvas(container_frame)
        scrollbar = ttk.Scrollbar(container_frame, orient="vertical", command=canvas.yview)
        self.filters_frame = ttk.Frame(canvas)

        # Configure scrolling
        self.filters_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.filters_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Pack scrollable components
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Add initial filter
        self.add_filter()

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)

        ttk.Button(
            button_frame,
            text="Add Filter",
            command=self.add_filter
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            button_frame,
            text="Apply Filters",
            command=self.apply_filters
        ).pack(side=tk.RIGHT, padx=5)

        ttk.Button(
            button_frame,
            text="Cancel",
            command=self.destroy
        ).pack(side=tk.RIGHT, padx=5)

    def add_filter(self):
        """Add a new filter row"""
        filter_frame = ttk.Frame(self.filters_frame)
        filter_frame.pack(fill=tk.X, pady=2)

        # Column selection
        column_var = tk.StringVar()
        column_combo = ttk.Combobox(filter_frame, textvariable=column_var)
        column_combo['values'] = [col.replace('_', ' ').title() for col in self.columns]
        column_combo.pack(side=tk.LEFT, padx=2)
        column_combo.state(['readonly'])

        # Operator selection
        operator_var = tk.StringVar()
        operator_combo = ttk.Combobox(filter_frame, textvariable=operator_var, width=15)
        operator_combo['values'] = ['equals', 'contains', 'greater than', 'less than']
        operator_combo.pack(side=tk.LEFT, padx=2)
        operator_combo.state(['readonly'])

        # Value entry
        value_entry = ttk.Entry(filter_frame)
        value_entry.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)

        # Remove button
        ttk.Button(
            filter_frame,
            text="✕",
            width=3,
            command=lambda: self.remove_filter(filter_frame)
        ).pack(side=tk.LEFT, padx=2)

        # Store filter components
        self.filter_frames.append({
            'frame': filter_frame,
            'column': column_var,
            'operator': operator_var,
            'value': value_entry
        })

        # Set initial values
        if self.columns:
            column_combo.set(self.columns[0].replace('_', ' ').title())
        operator_combo.set('equals')

    def remove_filter(self, filter_frame):
        """Remove a filter row"""
        # Find and remove the filter components
        self.filter_frames = [f for f in self.filter_frames if f['frame'] != filter_frame]
        filter_frame.destroy()

    def get_filter_conditions(self) -> List[Dict]:
        """Get all filter conditions"""
        conditions = []

        for filter_comp in self.filter_frames:
            column_display = filter_comp['column'].get()
            column = '_'.join(column_display.lower().split())

            operator = filter_comp['operator'].get()
            value = filter_comp['value'].get().strip()

            if column and operator and value:
                conditions.append({
                    'column': column,
                    'operator': operator,
                    'value': value
                })

        return conditions

    def apply_filters(self):
        """Apply all filter conditions"""
        conditions = self.get_filter_conditions()

        if not conditions:
            if not tk.messagebox.askyesno(
                    "Warning",
                    "No filter conditions specified. This will show all items. Continue?"
            ):
                return

        self.filter_callback(conditions)
        self.destroy()

    def validate_numeric_filter(self, value: str, column: str) -> bool:
        """Validate numeric filters"""
        numeric_columns = ['thickness', 'size_ft', 'area_sqft']
        if column in numeric_columns:
            try:
                float(value)
                return True
            except ValueError:
                tk.messagebox.showerror(
                    "Error",
                    f"{column.replace('_', ' ').title()} must be a number"
                )
                return False
        return True

    def clear_filters(self):
        """Clear all filter conditions"""
        for filter_frame in self.filter_frames:
            filter_frame['frame'].destroy()
        self.filter_frames.clear()
        self.add_filter()  # Add one empty filter