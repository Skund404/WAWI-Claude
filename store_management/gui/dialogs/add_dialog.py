import tkinter as tk
from tkinter import ttk
from typing import Dict, Callable


class AddDialog(tk.Toplevel):
    def __init__(self, parent, fields: list, callback: Callable):
        super().__init__(parent)
        self.title("Add New Item")
        self.callback = callback

        # Make dialog modal
        self.transient(parent)
        self.grab_set()

        # Create main frame
        main_frame = ttk.Frame(self, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Create entry fields
        self.entries = {}
        for i, field in enumerate(fields):
            ttk.Label(main_frame, text=field.replace('_', ' ').title()).grid(
                row=i, column=0, sticky=tk.W, padx=5, pady=2
            )

            self.entries[field] = ttk.Entry(main_frame)
            self.entries[field].grid(
                row=i, column=1, sticky=(tk.W, tk.E), padx=5, pady=2
            )

        # Create buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=len(fields), column=0, columnspan=2, pady=10)

        ttk.Button(button_frame, text="Continue", command=self.save).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.destroy).pack(side=tk.LEFT, padx=5)

        # Configure grid
        main_frame.columnconfigure(1, weight=1)

        # Set focus to first entry
        first_entry = next(iter(self.entries.values()), None)
        if first_entry:
            first_entry.focus_set()

    def save(self):
        """Collect data and call callback"""
        data = {field: entry.get() for field, entry in self.entries.items()}

        # Validate required fields
        if not all(data.values()):
            tk.messagebox.showerror("Error", "All fields are required")
            return

        if self.callback(data):
            self.destroy()