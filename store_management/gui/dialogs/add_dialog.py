

from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService


class AddDialog(tk.Toplevel):
    """
    A flexible dialog for adding new entries with dynamic field generation.

    Supports different field types and provides validation mechanisms.

    Attributes:
        _parent: Parent window
        _save_callback: Function to call when save is triggered
        _fields: List of field configurations
        _entries: Dictionary to store entry widgets
    """

    @inject(MaterialService)
        def __init__(self, parent: tk.Tk, save_callback: Callable[[Dict[str,
                                                                    Any]], None], fields: List[Tuple[str, str, bool, str]] = [], title:
                 str = 'Add Entry'):
        """
        Initialize the add dialog.

        Args:
            parent: Parent window
            save_callback: Function called with form data on save
            fields: List of field tuples (field_name, display_name, required, field_type)
            title: Dialog title

        Field Types:
            - 'string': Text entry
            - 'text': Multiline text entry
            - 'float': Numeric entry (floating-point)
            - 'int': Integer entry
            - 'boolean': Checkbox
        """
        super().__init__(parent)
        self._parent = parent
        self._save_callback = save_callback
        self._fields = fields
        self._entries: Dict[str, Union[tk.Entry, tk.Text, ttk.Checkbutton]] = {
        }
        self.title(title)
        self.geometry('400x500')
        self.resizable(False, False)
        self._create_ui()

        @inject(MaterialService)
            def _create_ui(self) -> None:
        """
        Create dialog user interface with dynamic fields.
        """
        main_frame = ttk.Frame(self, padding='10 10 10 10')
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.columnconfigure(1, weight=1)
        for i, (field_name, display_name, required, field_type) in enumerate(
                self._fields):
            label = ttk.Label(main_frame, text=f'{display_name}:')
            label.grid(row=i, column=0, sticky=tk.W, padx=5, pady=5)
            if field_type == 'string':
                entry = ttk.Entry(main_frame, width=40)
                entry.grid(row=i, column=1, sticky=tk.EW, padx=5, pady=5)
                self._entries[field_name] = entry
            elif field_type == 'text':
                entry = tk.Text(main_frame, height=4, width=40)
                entry.grid(row=i, column=1, sticky=tk.EW, padx=5, pady=5)
                self._entries[field_name] = entry
            elif field_type == 'float':
                entry = ttk.Entry(main_frame, width=40)
                entry.grid(row=i, column=1, sticky=tk.EW, padx=5, pady=5)
                self._entries[field_name] = entry
            elif field_type == 'int':
                entry = ttk.Entry(main_frame, width=40)
                entry.grid(row=i, column=1, sticky=tk.EW, padx=5, pady=5)
                self._entries[field_name] = entry
            elif field_type == 'boolean':
                var = tk.BooleanVar()
                entry = ttk.Checkbutton(main_frame, variable=var)
                entry.grid(row=i, column=1, sticky=tk.W, padx=5, pady=5)
                self._entries[field_name] = var
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=len(self._fields), column=0, columnspan=2,
                           sticky=tk.EW, pady=10)
        save_btn = ttk.Button(buttons_frame, text='Save', command=self._on_save
                              )
        save_btn.pack(side=tk.RIGHT, padx=5)
        cancel_btn = ttk.Button(buttons_frame, text='Cancel', command=self.
                                destroy)
        cancel_btn.pack(side=tk.RIGHT)

        @inject(MaterialService)
            def _on_save(self) -> None:
        """
        Handle save action, validate and process form data.
        """
        form_data = {}
        for field_name, _, required, field_type in self._fields:
            entry = self._entries[field_name]
            if field_type == 'string':
                value = entry.get()
            elif field_type == 'text':
                value = entry.get('1.0', tk.END).strip()
            elif field_type == 'float':
                try:
                    value = float(entry.get())
                except ValueError:
                    messagebox.showerror('Invalid Input',
                                         f'Invalid float value for {field_name}')
                    return
            elif field_type == 'int':
                try:
                    value = int(entry.get())
                except ValueError:
                    messagebox.showerror('Invalid Input',
                                         f'Invalid integer value for {field_name}')
                    return
            elif field_type == 'boolean':
                value = entry.get()
            if required and not value:
                messagebox.showerror('Missing Input',
                                     f'{field_name} is required')
                return
            form_data[field_name] = value
        if 'id' not in form_data:
            form_data['id'] = str(uuid.uuid4())
        try:
            self._save_callback(form_data)
            self.destroy()
        except Exception as e:
            messagebox.showerror('Save Error', str(e))
