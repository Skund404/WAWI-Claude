import tkinter as tk
from tkinter import ttk


class SearchDialog(tk.Toplevel):
    def __init__(self, parent, callback):
        super().__init__(parent)
        self.title("Search")
        self.callback = callback

        # Make dialog modal
        self.transient(parent)
        self.grab_set()

        # Create UI
        self.create_ui()

    def create_ui(self):
        # Basic search UI
        frame = ttk.Frame(self, padding="10")
        frame.pack(fill='both', expand=True)

        ttk.Label(frame, text="Search:").pack()
        self.search_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.search_var).pack(pady=5)

        ttk.Button(frame, text="Search",
                   command=self.search).pack(pady=5)
        ttk.Button(frame, text="Cancel",
                   command=self.destroy).pack(pady=5)

    def search(self):
        if self.callback:
            self.callback(self.search_var.get())
        self.destroy()


class FilterDialog(tk.Toplevel):
    def __init__(self, parent, callback):
        super().__init__(parent)
        self.title("Filter")
        self.callback = callback

        # Make dialog modal
        self.transient(parent)
        self.grab_set()

        # Create UI
        self.create_ui()

    def create_ui(self):
        # Basic filter UI
        frame = ttk.Frame(self, padding="10")
        frame.pack(fill='both', expand=True)

        ttk.Label(frame, text="Filter by:").pack()
        self.filter_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.filter_var).pack(pady=5)

        ttk.Button(frame, text="Apply",
                   command=self.apply_filter).pack(pady=5)
        ttk.Button(frame, text="Cancel",
                   command=self.destroy).pack(pady=5)

    def apply_filter(self):
        if self.callback:
            self.callback(self.filter_var.get())
        self.destroy()