# gui\storage\shelf_view.py

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List
from datetime import datetime

from store_management.database.sqlalchemy.managers.shelf_manager import ShelfManager
from store_management.database.sqlalchemy.session import get_session
from store_management.gui.dialogs.add_dialog import AddDialog
from store_management.gui.dialogs.search_dialog import SearchDialog
from store_management.gui.dialogs.filter_dialog import FilterDialog
from store_management.utils.logger import get_logger

logger = get_logger(__name__)


class ShelfView(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.shelf_manager = ShelfManager(get_session)
        self.tree = None
        self._search_after_id = None
        self.setup_ui()

    def setup_ui(self):
        self.setup_toolbar()
        self.setup_table()
        self.load_data()

    def setup_toolbar(self):
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(toolbar, text="ADD", command=self.show_add_shelf_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Search", command=self.show_search_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Filter", command=self.show_filter_dialog).pack(side=tk.LEFT, padx=2)

    def setup_table(self):
        columns = ['id', 'name', 'location', 'description']

        self.tree = ttk.Treeview(self, columns=columns, show='headings')
        self.tree.pack(fill=tk.BOTH, expand=True)

        for col in columns:
            self.tree.heading(col, text=col.title(), command=lambda c=col: self.sort_column(c))
            self.tree.column(col, width=100)

        self.tree.bind('<Double-1>', self.on_double_click)

    def load_data(self):
        self.tree.delete(*self.tree.get_children())
        shelves = self.shelf_manager.get_all()
        for shelf in shelves:
            values = [getattr(shelf, col) for col in self.tree['columns']]
            self.tree.insert('', tk.END, values=values)

    def show_add_shelf_dialog(self):
        fields = [
            ('name', 'Shelf Name', True),
            ('location', 'Location', True),
            ('description', 'Description', False)
        ]
        dialog = AddDialog(self, self.add_shelf, fields)
        self.wait_window(dialog)

    def add_shelf(self, data: Dict[str, str]) -> None:
        try:
            shelf = self.shelf_manager.add_shelf(data)
            if shelf:
                values = [getattr(shelf, col) for col in self.tree['columns']]
                self.tree.insert('', tk.END, values=values)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add shelf: {str(e)}")

    def search_shelves(self, term: str) -> None:
        self.tree.selection_remove(*self.tree.selection())
        shelves = self.shelf_manager.search_shelves(term)
        for shelf in shelves:
            values = [getattr(shelf, col) for col in self.tree['columns']]
            item = self.tree.insert('', tk.END, values=values)
            self.tree.selection_add(item)

    def on_double_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region == "cell":
            column = self.tree.identify_column(event.x)
            item = self.tree.identify_row(event.y)

            if column == "#1":  # ID column
                return

            col_index = int(column[1:]) - 1
            col_name = self.tree['columns'][col_index]
            self.edit_cell(item, col_name)

    def edit_cell(self, item, column):
        old_value = self.tree.set(item, column)

        entry = ttk.Entry(self.tree)
        entry.place(x=self.tree.bbox(item, column)[0], y=self.tree.bbox(item, column)[1],
                    width=self.tree.column(column, 'width'), height=self.tree.bbox(item, column)[3])

        def save_edit(event):
            new_value = entry.get()
            if new_value != old_value:
                shelf_id = self.tree.set(item, 'id')
                if self.shelf_manager.update(shelf_id, {column: new_value}):
                    self.tree.set(item, column, new_value)
            entry.destroy()

        def cancel_edit(event):
            entry.destroy()

        entry.insert(0, old_value)
        entry.select_range(0, tk.END)
        entry.focus_set()

        entry.bind("<Return>", save_edit)
        entry.bind("<Escape>", cancel_edit)
        entry.bind("<FocusOut>", save_edit)

    def show_search_dialog(self):
        dialog = SearchDialog(self, self.tree['columns'], self.search_shelves)
        self.wait_window(dialog)

    def show_filter_dialog(self):
        dialog = FilterDialog(self, self.tree['columns'], self.apply_filters)
        self.wait_window(dialog)

    def apply_filters(self, filters: List[Dict[str, str]]):
        self.tree.delete(*self.tree.get_children())
        shelves = self.shelf_manager.filter(filters)
        for shelf in shelves:
            values = [getattr(shelf, col) for col in self.tree['columns']]
            self.tree.insert('', tk.END, values=values)

    def sort_column(self, column):
        if self.tree.heading(column, 'text').endswith('▲'):
            self.tree.heading(column, text=column.title() + ' ▼')
            reverse = True
        else:
            self.tree.heading(column, text=column.title() + ' ▲')
            reverse = False

        data = [(self.tree.set(child, column), child) for child in self.tree.get_children('')]
        data.sort(reverse=reverse)

        for index, (_, child) in enumerate(data):
            self.tree.move(child, '', index)