from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
import logging
from typing import Any, Dict, List, Optional
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from decimal import Decimal

logger = logging.getLogger(__name__)


class AdvancedPatternLibrary(BaseView):
    """
    Advanced Pattern Library UI for managing leatherworking patterns.

    This class provides a comprehensive interface for viewing, adding, editing,
    and deleting patterns, as well as running tests for the ProjectWorkflowManager.
    """

    @inject(MaterialService)
    def __init__(self, parent: tk.Widget, app: Any):
        """
        Initialize the AdvancedPatternLibrary.

        Args:
            parent (tk.Widget): The parent widget.
            app (Any): The main application instance.
        """
        super().__init__(parent, app)
        self.project_service: ProjectService = self.get_service(ProjectService)
        self.patterns: Dict[str, Any] = {}
        self.current_pattern: Optional[str] = None
        self.logger = logging.getLogger(__name__)
        self.labor_rate = Decimal('25.00')
        self.setup_ui()

    @inject(MaterialService)
    def setup_ui(self) -> None:
        """Set up the main user interface components."""
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        self.pattern_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.pattern_frame, text='Pattern Library')
        self.test_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.test_frame, text='Tests')
        self.setup_pattern_library()
        self.setup_test_suite()

    @inject(MaterialService)
    def setup_pattern_library(self) -> None:
        """Set up the pattern library interface."""
        self.pattern_frame.columnconfigure(1, weight=1)
        self.pattern_frame.rowconfigure(0, weight=1)
        self.pattern_list_frame = ttk.Frame(self.pattern_frame)
        self.pattern_list_frame.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)
        self.setup_pattern_list()
        self.pattern_details_frame = ttk.Frame(self.pattern_frame)
        self.pattern_details_frame.grid(row=0, column=1, sticky='nsew', padx=5, pady=5)
        self.setup_pattern_details()
        self.toolbar = ttk.Frame(self.pattern_frame)
        self.toolbar.grid(row=1, column=0, columnspan=2, sticky='ew', padx=5, pady=5)
        self.setup_toolbar()

    @inject(MaterialService)
    def setup_pattern_list(self) -> None:
        """Set up the pattern list treeview."""
        self.pattern_tree = ttk.Treeview(self.pattern_list_frame, columns=('name', 'type'), show='headings')
        self.pattern_tree.heading('name', text='Pattern Name')
        self.pattern_tree.heading('type', text='Type')
        self.pattern_tree.column('name', width=150)
        self.pattern_tree.column('type', width=100)
        self.pattern_tree.pack(fill=tk.BOTH, expand=True)
        self.pattern_tree.bind('<<TreeviewSelect>>', self.on_pattern_select)

    @inject(MaterialService)
    def setup_pattern_details(self) -> None:
        """Set up the pattern details display area."""
        self.details_canvas = tk.Canvas(self.pattern_details_frame, bg='white')
        self.details_canvas.pack(fill=tk.BOTH, expand=True)
        self.pattern_name_var = tk.StringVar()
        self.pattern_type_var = tk.StringVar()
        self.pattern_desc_var = tk.StringVar()
        ttk.Label(self.details_canvas, text='Name:').pack(anchor='w')
        ttk.Entry(self.details_canvas, textvariable=self.pattern_name_var, state='readonly').pack(fill='x')
        ttk.Label(self.details_canvas, text='Type:').pack(anchor='w')
        ttk.Entry(self.details_canvas, textvariable=self.pattern_type_var, state='readonly').pack(fill='x')
        ttk.Label(self.details_canvas, text='Description:').pack(anchor='w')
        ttk.Entry(self.details_canvas, textvariable=self.pattern_desc_var, state='readonly').pack(fill='x')
        self.image_label = ttk.Label(self.details_canvas)
        self.image_label.pack(pady=10)
        self.materials_tree = ttk.Treeview(self.details_canvas, columns=('material', 'quantity'), show='headings')
        self.materials_tree.heading('material', text='Material')
        self.materials_tree.heading('quantity', text='Quantity')
        self.materials_tree.pack(fill='x', pady=10)

    @inject(MaterialService)
    def setup_toolbar(self) -> None:
        """Set up the toolbar with action buttons."""
        ttk.Button(self.toolbar, text='Add Pattern', command=self.add_pattern).pack(side='left', padx=5)
        ttk.Button(self.toolbar, text='Edit Pattern', command=self.edit_pattern).pack(side='left', padx=5)
        ttk.Button(self.toolbar, text='Delete Pattern', command=self.delete_pattern).pack(side='left', padx=5)
        ttk.Button(self.toolbar, text='Import Patterns', command=self.import_patterns).pack(side='left', padx=5)
        ttk.Button(self.toolbar, text='Export Patterns', command=self.export_patterns).pack(side='left', padx=5)

    @inject(MaterialService)
    def setup_test_suite(self) -> None:
        """Set up the test suite interface."""
        self.test_output = tk.Text(self.test_frame, wrap=tk.WORD)
        self.test_output.pack(fill=tk.BOTH, expand=True)
        self.run_tests_button = ttk.Button(self.test_frame, text='Run Tests', command=self.run_tests)
        self.run_tests_button.pack(pady=10)

    @inject(MaterialService)
    def load_data(self) -> None:
        """Load pattern data from the project service."""
        try:
            self.patterns = self.project_service.get_all_patterns()
            self.update_pattern_list()
        except Exception as e:
            self.logger.error(f'Error loading pattern data: {str(e)}')
            messagebox.showerror('Error', f'Failed to load pattern data: {str(e)}')

    @inject(MaterialService)
    def update_pattern_list(self) -> None:
        """Update the pattern list in the treeview."""
        self.pattern_tree.delete(*self.pattern_tree.get_children())
        for pattern_id, pattern in self.patterns.items():
            self.pattern_tree.insert('', 'end', pattern_id, values=(pattern['name'], pattern['type']))

    @inject(MaterialService)
    def on_pattern_select(self, event: tk.Event) -> None:
        """Handle pattern selection in the treeview."""
        selected_items = self.pattern_tree.selection()
        if selected_items:
            self.current_pattern = selected_items[0]
            self.display_pattern_details(self.current_pattern)

    @inject(MaterialService)
    def display_pattern_details(self, pattern_id: str) -> None:
        """Display details of the selected pattern."""
        pattern = self.patterns[pattern_id]
        self.pattern_name_var.set(pattern['name'])
        self.pattern_type_var.set(pattern['type'])
        self.pattern_desc_var.set(pattern['description'])
        if 'image' in pattern:
            image = Image.open(io.BytesIO(pattern['image']))
            image.thumbnail((300, 300))
            photo = ImageTk.PhotoImage(image)
            self.image_label.config(image=photo)
            self.image_label.image = photo
        else:
            self.image_label.config(image='')
        self.materials_tree.delete(*self.materials_tree.get_children())
        for material, quantity in pattern.get('materials', {}).items():
            self.materials_tree.insert('', 'end', values=(material, quantity))

    @inject(MaterialService)
    def add_pattern(self) -> None:
        """Open dialog to add a new pattern."""
        dialog = PatternDialog(self, 'Add Pattern')
        if dialog.result:
            try:
                new_pattern = dialog.result
                pattern_id = self.project_service.add_pattern(new_pattern)
                self.patterns[pattern_id] = new_pattern
                self.update_pattern_list()
                self.logger.info(f"Added new pattern: {new_pattern['name']}")
            except Exception as e:
                self.logger.error(f'Error adding pattern: {str(e)}')
                messagebox.showerror('Error', f'Failed to add pattern: {str(e)}')

    @inject(MaterialService)
    def edit_pattern(self) -> None:
        """Open dialog to edit the selected pattern."""
        if not self.current_pattern:
            messagebox.showwarning('Warning', 'Please select a pattern to edit.')
            return
        dialog = PatternDialog(self, 'Edit Pattern', self.patterns[self.current_pattern])
        if dialog.result:
            try:
                updated_pattern = dialog.result
                self.project_service.update_pattern(self.current_pattern, updated_pattern)
                self.patterns[self.current_pattern] = updated_pattern
                self.update_pattern_list()
                self.display_pattern_details(self.current_pattern)
                self.logger.info(f"Updated pattern: {updated_pattern['name']}")
            except Exception as e:
                self.logger.error(f'Error updating pattern: {str(e)}')
                messagebox.showerror('Error', f'Failed to update pattern: {str(e)}')

    @inject(MaterialService)
    def delete_pattern(self) -> None:
        """Delete the selected pattern."""
        if not self.current_pattern:
            messagebox.showwarning('Warning', 'Please select a pattern to delete.')
            return
        if messagebox.askyesno('Confirm Delete', 'Are you sure you want to delete this pattern?'):
            try:
                self.project_service.delete_pattern(self.current_pattern)
                del self.patterns[self.current_pattern]
                self.update_pattern_list()
                self.current_pattern = None
                self.clear_pattern_details()
                self.logger.info(f'Deleted pattern: {self.current_pattern}')
            except Exception as e:
                self.logger.error(f'Error deleting pattern: {str(e)}')
                messagebox.showerror('Error', f'Failed to delete pattern: {str(e)}')

    @inject(MaterialService)
    def clear_pattern_details(self) -> None:
        """Clear the pattern details display."""
        self.pattern_name_var.set('')
        self.pattern_type_var.set('')
        self.pattern_desc_var.set('')
        self.image_label.config(image='')
        self.materials_tree.delete(*self.materials_tree.get_children())

    @inject(MaterialService)
    def import_patterns(self) -> None:
        """Import patterns from a JSON file."""
        file_path = filedialog.askopenfilename(filetypes=[('JSON Files', '*.json')])
        if file_path:
            try:
                with open(file_path, 'r') as file:
                    imported_patterns = json.load(file)
                for pattern in imported_patterns:
                    pattern_id = self.project_service.add_pattern(pattern)
                    self.patterns[pattern_id] = pattern
                self.update_pattern_list()
                self.logger.info(f'Imported {len(imported_patterns)} patterns.')
                messagebox.showinfo('Import Successful', f'Imported {len(imported_patterns)} patterns.')
            except Exception as e:
                self.logger.error(f'Error importing patterns: {str(e)}')
                messagebox.showerror('Error', f'Failed to import patterns: {str(e)}')

    @inject(MaterialService)
    def export_patterns(self) -> None:
        """Export patterns to a JSON file."""
        file_path = filedialog.asksaveasfilename(defaultextension='.json',
                                                   filetypes=[('JSON Files', '*.json')])
        if file_path:
            try:
                with open(file_path, 'w') as file:
                    json.dump(list(self.patterns.values()), file, indent=2)
                self.logger.info(f'Exported {len(self.patterns)} patterns.')
                messagebox.showinfo('Export Successful', f'Exported {len(self.patterns)} patterns.')
            except Exception as e:
                self.logger.error(f'Error exporting patterns: {str(e)}')
                messagebox.showerror('Error', f'Failed to export patterns: {str(e)}')

    @inject(MaterialService)
    def run_tests(self) -> None:
        """Run the test suite for ProjectWorkflowManager."""
        self.test_output.delete('1.0', tk.END)
        suite = unittest.TestLoader().loadTestsFromTestCase(TestProjectWorkflowManager)
        stream = StringIO()
        runner = unittest.TextTestRunner(stream=stream, verbosity=2)
        result = runner.run(suite)
        self.test_output.insert(tk.END, stream.getvalue())
        summary = f'\n\nTest Summary:\n'
        summary += f'Ran {result.testsRun} tests\n'
        summary += (f'Successes: {result.testsRun - len(result.failures) - len(result.errors)}\n')
        summary += f'Failures: {len(result.failures)}\n'
        summary += f'Errors: {len(result.errors)}\n'
        self.test_output.insert(tk.END, summary)
        self.logger.info(f'Ran test suite: {result.testsRun} tests, {len(result.failures)} failures, {len(result.errors)} errors')


class PatternDialog(tk.Toplevel):
    """Dialog for adding or editing a pattern."""

    @inject(MaterialService)
    def __init__(self, parent: tk.Widget, title: str, pattern: Optional[Dict[str, Any]] = None):
        """
        Initialize the PatternDialog.

        Args:
            parent (tk.Widget): The parent widget.
            title (str): The dialog title.
            pattern (Optional[Dict[str, Any]]): Existing pattern data for editing.
        """
        super().__init__(parent)
        self.title(title)
        self.pattern = pattern or {}
        self.result: Optional[Dict[str, Any]] = None
        self.setup_ui()

    @inject(MaterialService)
    def setup_ui(self) -> None:
        """Set up the user interface for the dialog."""
        self.columnconfigure(1, weight=1)
        ttk.Label(self, text='Name:').grid(row=0, column=0, sticky='e', padx=5, pady=5)
        self.name_entry = ttk.Entry(self)
        self.name_entry.grid(row=0, column=1, sticky='ew', padx=5, pady=5)
        self.name_entry.insert(0, self.pattern.get('name', ''))
        ttk.Label(self, text='Type:').grid(row=1, column=0, sticky='e', padx=5, pady=5)
        self.type_entry = ttk.Entry(self)
        self.type_entry.grid(row=1, column=1, sticky='ew', padx=5, pady=5)
        self.type_entry.insert(0, self.pattern.get('type', ''))
        ttk.Label(self, text='Description:').grid(row=2, column=0, sticky='e', padx=5, pady=5)
        self.desc_entry = ttk.Entry(self)
        self.desc_entry.grid(row=2, column=1, sticky='ew', padx=5, pady=5)
        self.desc_entry.insert(0, self.pattern.get('description', ''))
        ttk.Button(self, text='Select Image', command=self.select_image).grid(row=3, column=0, columnspan=2, pady=10)
        self.materials_frame = ttk.LabelFrame(self, text='Materials')
        self.materials_frame.grid(row=4, column=0, columnspan=2, sticky='nsew', padx=5, pady=5)
        self.setup_materials_ui()
        ttk.Button(self, text='Save', command=self.save).grid(row=5, column=0, pady=10)
        ttk.Button(self, text='Cancel', command=self.cancel).grid(row=5, column=1, pady=10)

    @inject(MaterialService)
    def setup_materials_ui(self) -> None:
        """Set up the materials UI within the dialog."""
        self.materials: List[Dict[str, Any]] = self.pattern.get('materials', [])
        self.materials_tree = ttk.Treeview(self.materials_frame, columns=('material', 'quantity'), show='headings')
        self.materials_tree.heading('material', text='Material')
        self.materials_tree.heading('quantity', text='Quantity')
        self.materials_tree.pack(fill='x', expand=True)
        for material in self.materials:
            self.materials_tree.insert('', 'end', values=(material['name'], material['quantity']))
        ttk.Button(self.materials_frame, text='Add Material', command=self.add_material).pack(side='left', padx=5)
        ttk.Button(self.materials_frame, text='Remove Material', command=self.remove_material).pack(side='left', padx=5)

    @inject(MaterialService)
    def add_material(self) -> None:
        """Open a dialog to add a new material to the pattern."""
        dialog = MaterialDialog(self)
        if dialog.result:
            self.materials.append(dialog.result)
            self.materials_tree.insert('', 'end', values=(dialog.result['name'], dialog.result['quantity']))

    @inject(MaterialService)
    def remove_material(self) -> None:
        """Remove the selected material from the pattern."""
        selected_item = self.materials_tree.selection()
        if selected_item:
            index = self.materials_tree.index(selected_item)
            del self.materials[index]
            self.materials_tree.delete(selected_item)

    @inject(MaterialService)
    def select_image(self) -> None:
        """Open a file dialog to select an image for the pattern."""
        file_path = filedialog.askopenfilename(filetypes=[('Image Files', '*.png *.jpg *.jpeg *.gif')])
        if file_path:
            with open(file_path, 'rb') as file:
                self.pattern['image'] = file.read()

    @inject(MaterialService)
    def save(self) -> None:
        """Save the pattern data and close the dialog."""
        self.result = {
            'name': self.name_entry.get(),
            'type': self.type_entry.get(),
            'description': self.desc_entry.get(),
            'materials': self.materials
        }
        if 'image' in self.pattern:
            self.result['image'] = self.pattern['image']
        self.destroy()

    @inject(MaterialService)
    def cancel(self) -> None:
        """Cancel the dialog without saving."""
        self.destroy()


class MaterialDialog(tk.Toplevel):
    """Dialog for adding a material to a pattern."""

    @inject(MaterialService)
    def __init__(self, parent: tk.Widget):
        """
        Initialize the MaterialDialog.

        Args:
            parent (tk.Widget): The parent widget.
        """
        super().__init__(parent)
        self.title('Add Material')
        self.result: Optional[Dict[str, Any]] = None
        self.setup_ui()

    @inject(MaterialService)
    def setup_ui(self) -> None:
        """Set up the user interface for the material dialog."""
        ttk.Label(self, text='Material Name:').grid(row=0, column=0, sticky='e', padx=5, pady=5)
        self.name_entry = ttk.Entry(self)
        self.name_entry.grid(row=0, column=1, sticky='ew', padx=5, pady=5)
        ttk.Label(self, text='Quantity:').grid(row=1, column=0, sticky='e', padx=5, pady=5)
        self.quantity_entry = ttk.Entry(self)
        self.quantity_entry.grid(row=1, column=1, sticky='ew', padx=5, pady=5)
        ttk.Button(self, text='Save', command=self.save).grid(row=2, column=0, pady=10)
        ttk.Button(self, text='Cancel', command=self.cancel).grid(row=2, column=1, pady=10)

    @inject(MaterialService)
    def save(self) -> None:
        """Save the material data and close the dialog."""
        try:
            self.result = {
                'name': self.name_entry.get(),
                'quantity': float(self.quantity_entry.get())
            }
            self.destroy()
        except ValueError:
            messagebox.showerror('Error', 'Quantity must be a number.')

    @inject(MaterialService)
    def cancel(self) -> None:
        """Cancel the dialog without saving."""
        self.destroy()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    root = tk.Tk()
    app = AdvancedPatternLibrary(root, None)
    app.pack(fill='both', expand=True)
    root.mainloop()
