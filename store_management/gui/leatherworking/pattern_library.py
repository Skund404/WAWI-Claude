# Path: gui/leatherworking/pattern_library.py
"""
Pattern Library View for Leatherworking Project Management

This module provides a comprehensive UI for managing leatherworking patterns,
including creation, editing, searching, and categorization of patterns.
"""

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Dict, Any, Optional, List


class PatternLibrary(tk.Frame):
    """
    A comprehensive pattern management view for leatherworking projects.

    Provides functionality for:
    - Browsing existing patterns
    - Adding new patterns
    - Editing pattern details
    - Searching and filtering patterns
    - Managing pattern metadata
    """

    def __init__(self, parent, controller):
        """
        Initialize the Pattern Library view.

        Args:
            parent (tk.Widget): Parent widget
            controller (object): Application controller for managing interactions
        """
        super().__init__(parent)
        self.controller = controller

        # Pattern storage
        self.patterns: List[Dict[str, Any]] = []

        # UI Setup
        self._setup_layout()
        self._create_pattern_input()
        self._create_pattern_list()
        self._create_pattern_details()

        # Load initial patterns
        self.load_initial_patterns()

    def _setup_layout(self):
        """
        Set up the overall layout of the Pattern Library view.
        """
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)

        # Main frame sections
        self.pattern_input_frame = ttk.LabelFrame(self, text="Pattern Input")
        self.pattern_input_frame.grid(row=0, column=0, padx=10, pady=10, sticky='nsew')

        self.pattern_list_frame = ttk.LabelFrame(self, text="Pattern List")
        self.pattern_list_frame.grid(row=0, column=1, padx=10, pady=10, sticky='nsew')

        self.pattern_details_frame = ttk.LabelFrame(self, text="Pattern Details")
        self.pattern_details_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky='nsew')

    def _create_pattern_input(self):
        """
        Create input fields for adding new patterns.
        """
        # Pattern Name
        ttk.Label(self.pattern_input_frame, text="Pattern Name:").grid(row=0, column=0, sticky='w')
        self.pattern_name_entry = ttk.Entry(self.pattern_input_frame, width=30)
        self.pattern_name_entry.grid(row=0, column=1, padx=5, pady=5)

        # Pattern Type
        ttk.Label(self.pattern_input_frame, text="Pattern Type:").grid(row=1, column=0, sticky='w')
        self.pattern_type_var = tk.StringVar()
        pattern_types = ['Bag', 'Wallet', 'Belt', 'Accessory', 'Other']
        self.pattern_type_combo = ttk.Combobox(self.pattern_input_frame,
                                               textvariable=self.pattern_type_var,
                                               values=pattern_types)
        self.pattern_type_combo.grid(row=1, column=1, padx=5, pady=5)

        # Image Upload
        self.pattern_image_path = tk.StringVar()
        ttk.Button(self.pattern_input_frame, text="Upload Image",
                   command=self.browse_image).grid(row=2, column=0, columnspan=2, pady=5)

        # Add Pattern Button
        ttk.Button(self.pattern_input_frame, text="Add Pattern",
                   command=self.add_pattern).grid(row=3, column=0, columnspan=2, pady=10)

    def browse_image(self):
        """
        Open file dialog to browse and select pattern image.
        """
        filename = filedialog.askopenfilename(
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp")]
        )
        if filename:
            self.pattern_image_path.set(filename)
            # Optional: Show thumbnail or preview

    def _create_pattern_list(self):
        """
        Create a treeview to display existing patterns.
        """
        columns = ('Name', 'Type', 'Created')
        self.pattern_tree = ttk.Treeview(self.pattern_list_frame,
                                         columns=columns, show='headings')

        for col in columns:
            self.pattern_tree.heading(col, text=col)
            self.pattern_tree.column(col, width=100)

        self.pattern_tree.pack(expand=True, fill='both')

        # Bind events
        self.pattern_tree.bind('<Double-1>', self.show_pattern_details)

        # Context menu
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Edit", command=self.edit_pattern)
        self.context_menu.add_command(label="Delete", command=self.delete_pattern)

        self.pattern_tree.bind('<Button-3>', self.show_context_menu)

    def _create_pattern_details(self):
        """
        Create a detailed view for selected pattern.
        """
        # Detailed information display
        self.details_text = tk.Text(self.pattern_details_frame,
                                    height=10, width=70, wrap=tk.WORD)
        self.details_text.pack(expand=True, fill='both', padx=10, pady=10)

    def add_pattern(self):
        """
        Add a new pattern to the library.
        """
        name = self.pattern_name_entry.get()
        pattern_type = self.pattern_type_var.get()
        image_path = self.pattern_image_path.get()

        if not name or not pattern_type:
            messagebox.showwarning("Incomplete Information",
                                   "Please fill in Pattern Name and Type")
            return

        pattern = {
            'name': name,
            'type': pattern_type,
            'image_path': image_path,
            'created': tk.datetime.now().strftime("%Y-%m-%d")
        }

        self.patterns.append(pattern)
        self._update_pattern_tree()

        # Clear input fields
        self.pattern_name_entry.delete(0, tk.END)
        self.pattern_type_var.set('')
        self.pattern_image_path.set('')

    def _update_pattern_tree(self):
        """
        Update the pattern treeview with current patterns.
        """
        # Clear existing items
        for i in self.pattern_tree.get_children():
            self.pattern_tree.delete(i)

        # Add patterns
        for pattern in self.patterns:
            self.pattern_tree.insert('', 'end',
                                     values=(pattern['name'],
                                             pattern['type'],
                                             pattern['created']))

    def show_pattern_details(self, event):
        """
        Display details of selected pattern.

        Args:
            event (tk.Event): Treeview selection event
        """
        selected_item = self.pattern_tree.selection()
        if not selected_item:
            return

        # Get pattern details
        values = self.pattern_tree.item(selected_item[0])['values']
        pattern = next((p for p in self.patterns
                        if p['name'] == values[0] and p['type'] == values[1]), None)

        if pattern:
            details = f"""
Pattern Name: {pattern['name']}
Pattern Type: {pattern['type']}
Created: {pattern['created']}
Image Path: {pattern['image_path']}
            """

            self.details_text.delete(1.0, tk.END)
            self.details_text.insert(tk.END, details)

    def show_context_menu(self, event):
        """
        Show context menu for pattern selection.

        Args:
            event (tk.Event): Right-click event
        """
        # Select the row under the cursor
        iid = self.pattern_tree.identify_row(event.y)
        if iid:
            self.pattern_tree.selection_set(iid)
            self.context_menu.post(event.x_root, event.y_root)

    def edit_pattern(self):
        """
        Edit the selected pattern.
        """
        selected_item = self.pattern_tree.selection()
        if not selected_item:
            messagebox.showwarning("No Selection", "Please select a pattern to edit")
            return

        # Placeholder for edit dialog
        messagebox.showinfo("Edit Pattern", "Edit functionality to be implemented")

    def delete_pattern(self):
        """
        Delete the selected pattern.
        """
        selected_item = self.pattern_tree.selection()
        if not selected_item:
            messagebox.showwarning("No Selection", "Please select a pattern to delete")
            return

        # Confirm deletion
        if messagebox.askyesno("Confirm Deletion",
                               "Are you sure you want to delete this pattern?"):
            values = self.pattern_tree.item(selected_item[0])['values']
            self.patterns = [p for p in self.patterns
                             if not (p['name'] == values[0] and p['type'] == values[1])]
            self._update_pattern_tree()

    def load_initial_patterns(self):
        """
        Load initial patterns (can be replaced with database/file loading in future).
        """
        initial_patterns = [
            {
                'name': 'Classic Leather Bag',
                'type': 'Bag',
                'image_path': '',
                'created': '2024-02-23'
            },
            {
                'name': 'Minimalist Wallet',
                'type': 'Wallet',
                'image_path': '',
                'created': '2024-02-23'
            }
        ]
        self.patterns.extend(initial_patterns)
        self._update_pattern_tree()


def main():
    """
    Standalone test for PatternLibrary.
    """
    root = tk.Tk()
    root.title("Pattern Library")
    root.geometry("800x600")

    # Create a dummy controller
    class DummyController:
        pass

    pattern_library = PatternLibrary(root, DummyController())
    pattern_library.pack(fill='both', expand=True)

    root.mainloop()


if __name__ == "__main__":
    main()