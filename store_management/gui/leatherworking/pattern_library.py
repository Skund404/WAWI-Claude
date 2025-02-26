# Path: gui/leatherworking/pattern_library.py
"""Pattern Library view for leatherworking store management application."""

import tkinter as tk
import tkinter.ttk as ttk
from typing import Any, Optional

from di.core import inject
from services.interfaces.material_service import IMaterialService
from services.interfaces.project_service import IProjectService


class PatternLibrary(ttk.Frame):
    """
    Pattern Library view for managing and displaying leatherworking patterns.

    This view provides functionality to browse, add, edit, and delete patterns.
    """

    def __init__(self, parent: tk.Widget, controller: Any):
        """
        Initialize the Pattern Library view.

        Args:
            parent (tk.Widget): Parent widget
            controller (Any): Application controller for managing interactions
        """
        super().__init__(parent)
        self.controller = controller

        # Dependency Injection for services
        self.material_service: IMaterialService = inject(IMaterialService)
        self.project_service: IProjectService = inject(IProjectService)

        self._setup_layout()
        self._create_pattern_input()
        self._create_pattern_list()
        self._create_pattern_details()

        # Load initial patterns
        self.load_initial_patterns()

    def _setup_layout(self) -> None:
        """Set up the overall layout of the Pattern Library view."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

    def _create_pattern_input(self) -> None:
        """Create input fields for adding new patterns."""
        input_frame = ttk.LabelFrame(self, text="Add New Pattern")
        input_frame.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

        # Pattern name
        ttk.Label(input_frame, text="Pattern Name:").grid(row=0, column=0, padx=5, pady=5)
        self.pattern_name_entry = ttk.Entry(input_frame)
        self.pattern_name_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        # Pattern type
        ttk.Label(input_frame, text="Pattern Type:").grid(row=1, column=0, padx=5, pady=5)
        pattern_types = ["Wallet", "Bag", "Belt", "Accessory", "Custom"]
        self.pattern_type_var = tk.StringVar(value=pattern_types[0])
        pattern_type_dropdown = ttk.Combobox(input_frame, textvariable=self.pattern_type_var, values=pattern_types)
        pattern_type_dropdown.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        # Add pattern button
        add_pattern_btn = ttk.Button(input_frame, text="Add Pattern", command=self.add_pattern)
        add_pattern_btn.grid(row=2, column=0, columnspan=2, padx=5, pady=5)

    def _create_pattern_list(self) -> None:
        """Create a treeview to display existing patterns."""
        list_frame = ttk.LabelFrame(self, text="Pattern List")
        list_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")

        columns = ("Name", "Type", "Created Date")
        self.pattern_tree = ttk.Treeview(list_frame, columns=columns, show="headings")

        for col in columns:
            self.pattern_tree.heading(col, text=col)
            self.pattern_tree.column(col, width=100)

        self.pattern_tree.pack(expand=True, fill="both")

        # Bind events
        self.pattern_tree.bind("<Double-1>", self.show_pattern_details)
        self.pattern_tree.bind("<Button-3>", self.show_context_menu)

    def _create_pattern_details(self) -> None:
        """Create a detailed view for selected pattern."""
        details_frame = ttk.LabelFrame(self, text="Pattern Details")
        details_frame.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")

        # Placeholder for pattern details
        self.details_text = tk.Text(details_frame, wrap=tk.WORD, height=10)
        self.details_text.pack(expand=True, fill="both", padx=5, pady=5)

    def browse_image(self) -> None:
        """Open file dialog to browse and select pattern image."""
        import tkinter.filedialog as filedialog
        filename = filedialog.askopenfilename(
            title="Select Pattern Image",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif")]
        )
        if filename:
            # TODO: Implement image handling logic
            print(f"Selected image: {filename}")

    def add_pattern(self) -> None:
        """Add a new pattern to the library."""
        name = self.pattern_name_entry.get().strip()
        pattern_type = self.pattern_type_var.get()

        if not name:
            tk.messagebox.showerror("Error", "Pattern name cannot be empty")
            return

        try:
            # TODO: Implement actual pattern creation in service
            pattern_data = {
                "name": name,
                "type": pattern_type,
                "created_date": tk.datetime.now()
            }

            # Call project service to create pattern
            new_pattern = self.project_service.create_pattern(pattern_data)

            # Update treeview
            self.pattern_tree.insert("", "end", values=(
                new_pattern.name,
                new_pattern.type,
                new_pattern.created_date
            ))

            # Clear input
            self.pattern_name_entry.delete(0, tk.END)

            tk.messagebox.showinfo("Success", "Pattern added successfully")

        except Exception as e:
            tk.messagebox.showerror("Error", f"Failed to add pattern: {str(e)}")

    def show_pattern_details(self, event: Optional[tk.Event] = None) -> None:
        """
        Display details of selected pattern.

        Args:
            event (Optional[tk.Event]): Treeview selection event
        """
        selected_item = self.pattern_tree.selection()
        if not selected_item:
            return

        # Retrieve pattern details
        pattern_data = self.pattern_tree.item(selected_item)['values']

        # Update details text
        self.details_text.delete(1.0, tk.END)
        self.details_text.insert(tk.END, f"Name: {pattern_data[0]}\n")
        self.details_text.insert(tk.END, f"Type: {pattern_data[1]}\n")
        self.details_text.insert(tk.END, f"Created: {pattern_data[2]}\n")

    def show_context_menu(self, event: tk.Event) -> None:
        """
        Show context menu for pattern selection.

        Args:
            event (tk.Event): Right-click event
        """
        # Create context menu
        context_menu = tk.Menu(self, tearoff=0)
        context_menu.add_command(label="Edit", command=self.edit_pattern)
        context_menu.add_command(label="Delete", command=self.delete_pattern)

        # Display menu
        context_menu.post(event.x_root, event.y_root)

    def edit_pattern(self) -> None:
        """Edit the selected pattern."""
        selected_item = self.pattern_tree.selection()
        if not selected_item:
            tk.messagebox.showwarning("Warning", "Please select a pattern to edit")
            return

        # TODO: Implement edit pattern dialog/logic

    def delete_pattern(self) -> None:
        """Delete the selected pattern."""
        selected_item = self.pattern_tree.selection()
        if not selected_item:
            tk.messagebox.showwarning("Warning", "Please select a pattern to delete")
            return

        # Confirm deletion
        if tk.messagebox.askyesno("Confirm", "Are you sure you want to delete this pattern?"):
            try:
                # TODO: Implement actual pattern deletion in service
                self.pattern_tree.delete(selected_item)
                tk.messagebox.showinfo("Success", "Pattern deleted successfully")
            except Exception as e:
                tk.messagebox.showerror("Error", f"Failed to delete pattern: {str(e)}")

    def load_initial_patterns(self) -> None:
        """
        Load initial patterns (can be replaced with database/file loading in future).

        This method provides sample data for demonstration purposes.
        """
        initial_patterns = [
            ("Classic Wallet", "Wallet", "2025-02-01"),
            ("Leather Messenger Bag", "Bag", "2025-02-10"),
            ("Handcrafted Belt", "Belt", "2025-02-15")
        ]

        for pattern in initial_patterns:
            self.pattern_tree.insert("", "end", values=pattern)


def main() -> None:
    """Standalone test for PatternLibrary."""
    root = tk.Tk()
    root.title("Pattern Library Test")

    class DummyController:
        """Dummy controller for testing."""
        pass

    pattern_library = PatternLibrary(root, DummyController())
    pattern_library.pack(fill="both", expand=True)

    root.mainloop()


if __name__ == "__main__":
    main()