import tkinter as tk
from tkinter import ttk
from typing import List, Callable


class SearchDialog(tk.Toplevel):
    def __init__(self, parent, columns: List[str], callback: Callable):
        super().__init__(parent)
        self.title("Search")
        self.callback = callback

        # Make dialog modal
        self.transient(parent)
        self.grab_set()

        # Create main frame
        main_frame = ttk.Frame(self, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Create search widgets
        ttk.Label(main_frame, text="Search in:").grid(row=0, column=0, sticky=tk.W)

        self.column_var = tk.StringVar(value="All")
        column_choices = ["All"] + columns
        self.column_combo = ttk.Combobox(main_frame, textvariable=self.column_var,
                                         values=column_choices)
        self.column_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)

        ttk.Label(main_frame, text="Search for:").grid(row=1, column=0, sticky=tk.W)
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(main_frame, textvariable=self.search_var)
        self.search_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)

        # Options
        self.match_case = tk.BooleanVar()
        ttk.Checkbutton(main_frame, text="Match case",
                        variable=self.match_case).grid(row=2, column=0, columnspan=2)

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=10)

        ttk.Button(button_frame, text="Search",
                   command=self.search).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel",
                   command=self.destroy).pack(side=tk.LEFT, padx=5)

        # Configure grid
        main_frame.columnconfigure(1, weight=1)

        # Set focus to search entry
        self.search_entry.focus_set()

        # Bind enter key
        self.bind('<Return>', lambda e: self.search())

    def search(self):
        """Collect search parameters and call callback"""
        search_params = {
            "column": self.column_var.get(),
            "text": self.search_var.get(),
            "match_case": self.match_case.get()
        }

        if not search_params["text"]:
            tk.messagebox.showwarning("Warning", "Please enter search text")
            return

        self.callback(search_params)
        self.destroy()