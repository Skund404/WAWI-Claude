import logging
import json
from typing import Any, Dict, List, Optional
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from gui.base_view import BaseView


logger = logging.getLogger(__name__)


class AdvancedPatternLibrary(BaseView):
    """
    Advanced Pattern Library UI for managing leatherworking patterns.

    This class provides a comprehensive interface for viewing, adding, editing,
    and deleting patterns.
    """

    def __init__(self, parent: tk.Widget, app: Any):
        """
        Initialize the AdvancedPatternLibrary.

        Args:
            parent (tk.Widget): The parent widget.
            app (Any): The main application instance.
        """
        super().__init__(parent, app)

        # Dependency injection for services
        # Access them via the property getter, not direct assignment.
        # self.material_service: IMaterialService = self._get_service(IMaterialService)
        # self.inventory_service: IInventoryService = self._get_service(IInventoryService)
        # self.order_service: IOrderService = self._get_service(IOrderService)

        # Logger
        self.logger = logging.getLogger(__name__)

        # Pattern data
        self.patterns: Dict[str, Dict[str, Any]] = {}
        self.current_pattern: Optional[str] = None

        # Setup UI
        self._setup_ui()

    def _setup_ui(self):
        """
        Set up the user interface for the advanced pattern library.
        """
        # Main frame
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(
            main_frame,
            text="Advanced Pattern Library",
            font=("Helvetica", 16, "bold")
        )
        title_label.pack(pady=(0, 10))

        # Pattern list area
        list_frame = ttk.LabelFrame(main_frame, text="Patterns")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Toolbar
        toolbar_frame = ttk.Frame(main_frame)
        toolbar_frame.pack(fill=tk.X, padx=5, pady=5)

        # Add buttons to toolbar
        add_pattern_btn = ttk.Button(
            toolbar_frame,
            text="Add Pattern",
            command=self.add_pattern
        )
        add_pattern_btn.pack(side=tk.LEFT, padx=2)

        edit_pattern_btn = ttk.Button(
            toolbar_frame,
            text="Edit Pattern",
            command=self.edit_pattern
        )
        edit_pattern_btn.pack(side=tk.LEFT, padx=2)

        delete_pattern_btn = ttk.Button(
            toolbar_frame,
            text="Delete Pattern",
            command=self.delete_pattern
        )
        delete_pattern_btn.pack(side=tk.LEFT, padx=2)

        export_btn = ttk.Button(
            toolbar_frame,
            text="Export Library",
            command=self.export_patterns
        )
        export_btn.pack(side=tk.LEFT, padx=2)

        import_btn = ttk.Button(
            toolbar_frame,
            text="Import Library",
            command=self.import_patterns
        )
        import_btn.pack(side=tk.LEFT, padx=2)

        # Pattern treeview
        columns = ("name", "type", "complexity", "materials_used", "created_date")
        self.pattern_tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="headings"
        )

        # Configure column headings
        for col in columns:
            self.pattern_tree.heading(col, text=col.replace("_", " ").title())
            self.pattern_tree.column(col, width=100, anchor=tk.CENTER)

        self.pattern_tree.pack(fill=tk.BOTH, expand=True)

        # Bind events
        self.pattern_tree.bind("<<TreeviewSelect>>", self.on_pattern_select)

    def load_data(self) -> None:
        """Load pattern data from the project service."""
        try:
            self.patterns = self.project_service.get_all_patterns()
            self.update_pattern_list()
        except Exception as e:
            self.logger.error(f"Error loading pattern data: {str(e)}")
            messagebox.showerror("Error", f"Failed to load pattern data: {str(e)}")

    def update_pattern_list(self) -> None:
        """Update the pattern list in the treeview."""
        self.pattern_tree.delete(*self.pattern_tree.get_children())
        for pattern_id, pattern in self.patterns.items():
            self.pattern_tree.insert(
                "", "end", pattern_id, values=(
                    pattern["name"],
                    pattern["type"],
                    pattern.get("complexity", "N/A"),
                    len(pattern.get("materials", [])),
                    pattern.get("created_date", "N/A")
                )
            )

    def on_pattern_select(self, event: tk.Event) -> None:
        """Handle pattern selection in the treeview."""
        selected_items = self.pattern_tree.selection()
        if selected_items:
            self.current_pattern = selected_items[0]
            self.display_pattern_details(self.current_pattern)

    def display_pattern_details(self, pattern_id: str) -> None:
        """Display details of the selected pattern."""
        pattern = self.patterns[pattern_id]
        # Display pattern details in a new dialog or a dedicated section
        messagebox.showinfo("Pattern Details", f"Name: {pattern['name']}\nType: {pattern['type']}")

    def add_pattern(self) -> None:
        """Open dialog to add a new pattern."""
        dialog = PatternDialog(self, "Add Pattern")
        if dialog.result:
            try:
                new_pattern = dialog.result
                pattern_id = self.project_service.add_pattern(new_pattern)
                self.patterns[pattern_id] = new_pattern
                self.update_pattern_list()
                self.logger.info(f"Added new pattern: {new_pattern['name']}")
            except Exception as e:
                self.logger.error(f"Error adding pattern: {str(e)}")
                messagebox.showerror("Error", f"Failed to add pattern: {str(e)}")

    def edit_pattern(self) -> None:
        """Open dialog to edit the selected pattern."""
        if not self.current_pattern:
            messagebox.showwarning("Warning", "Please select a pattern to edit.")
            return
        dialog = PatternDialog(self, "Edit Pattern", self.patterns[self.current_pattern])
        if dialog.result:
            try:
                updated_pattern = dialog.result
                self.project_service.update_pattern(self.current_pattern, updated_pattern)
                self.patterns[self.current_pattern] = updated_pattern
                self.update_pattern_list()
                self.logger.info(f"Updated pattern: {updated_pattern['name']}")
            except Exception as e:
                self.logger.error(f"Error updating pattern: {str(e)}")
                messagebox.showerror("Error", f"Failed to update pattern: {str(e)}")

    def delete_pattern(self) -> None:
        """Delete the selected pattern."""
        if not self.current_pattern:
            messagebox.showwarning("Warning", "Please select a pattern to delete.")
            return
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this pattern?"):
            try:
                self.project_service.delete_pattern(self.current_pattern)
                del self.patterns[self.current_pattern]
                self.update_pattern_list()
                self.current_pattern = None
                self.logger.info("Deleted pattern.")
            except Exception as e:
                self.logger.error(f"Error deleting pattern: {str(e)}")
                messagebox.showerror("Error", f"Failed to delete pattern: {str(e)}")

    def import_patterns(self) -> None:
        """Import patterns from a JSON file."""
        file_path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if file_path:
            try:
                with open(file_path, "r") as file:
                    imported_patterns = json.load(file)
                for pattern in imported_patterns:
                    pattern_id = self.project_service.add_pattern(pattern)
                    self.patterns[pattern_id] = pattern
                self.update_pattern_list()
                self.logger.info(f"Imported {len(imported_patterns)} patterns.")
                messagebox.showinfo("Import Successful", f"Imported {len(imported_patterns)} patterns.")
            except Exception as e:
                self.logger.error(f"Error importing patterns: {str(e)}")
                messagebox.showerror("Error", f"Failed to import patterns: {str(e)}")

    def export_patterns(self) -> None:
        """Export patterns to a JSON file."""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json")]
        )
        if file_path:
            try:
                with open(file_path, "w") as file:
                    json.dump(list(self.patterns.values()), file, indent=2)
                self.logger.info(f"Exported {len(self.patterns)} patterns.")
                messagebox.showinfo("Export Successful", f"Exported {len(self.patterns)} patterns.")
            except Exception as e:
                self.logger.error(f"Error exporting patterns: {str(e)}")
                messagebox.showerror("Error", f"Failed to export patterns: {str(e)}")


class PatternDialog(tk.Toplevel):
    """Dialog for adding or editing a pattern."""

    def __init__(self, parent: tk.Widget, title: str, pattern: Optional[Dict[str, Any]] = None):
        super().__init__(parent)
        self.title(title)
        self.pattern = pattern or {}
        self.result: Optional[Dict[str, Any]] = None
        self._setup_ui()

    def _setup_ui(self):
        """Set up the user interface for the dialog."""
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="Pattern Name:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.name_var = tk.StringVar(value=self.pattern.get("name", ""))
        ttk.Entry(main_frame, textvariable=self.name_var).grid(row=0, column=1, sticky=tk.EW, pady=2)

        ttk.Label(main_frame, text="Pattern Type:").grid(row=1, column=0, sticky=tk.W, pady=2)
        pattern_types = ["Wallet", "Bag", "Belt", "Accessory", "Custom"]
        self.type_var = tk.StringVar(value=self.pattern.get("type", pattern_types[0]))
        ttk.Combobox(
            main_frame,
            textvariable=self.type_var,
            values=pattern_types,
            state="readonly"
        ).grid(row=1, column=1, sticky=tk.EW, pady=2)

        ttk.Button(main_frame, text="Save", command=self._save).grid(row=2, column=0, columnspan=2, pady=10)

        main_frame.columnconfigure(1, weight=1)

    def _save(self):
        """Save the pattern data and close the dialog."""
        self.result = {
            "name": self.name_var.get().strip(),
            "type": self.type_var.get().strip()
        }
        self.destroy()


def main():
    """Standalone testing of the AdvancedPatternLibrary."""
    root = tk.Tk()
    root.title("Advanced Pattern Library Test")
    root.geometry("800x600")

    class DummyController:
        def get_service(self, service_type):
            return None

    library = AdvancedPatternLibrary(root, DummyController())
    library.pack(fill=tk.BOTH, expand=True)

    root.mainloop()


if __name__ == "__main__":
    main()
