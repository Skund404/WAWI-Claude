

from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
class SearchDialog(tk.Toplevel):

        @inject(MaterialService)
        def __init__(self, parent, columns: List[str], search_callback:
        Callable[[Dict], None]):
        """
        Initialize search dialog

        Args:
            parent: Parent window
            columns: List of column names to search in
            search_callback: Function to call with search parameters
        """
        super().__init__(parent)
        self.title('Search Items')
        self.geometry('400x200')
        self.transient(parent)
        self.grab_set()
        self.columns = ['All'] + columns
        self.search_callback = search_callback
        self.setup_ui()

        @inject(MaterialService)
        def setup_ui(self):
        """Setup the dialog UI components"""
        main_frame = ttk.Frame(self, padding='10')
        main_frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(main_frame, text='Search in:').grid(row=0, column=0,
            sticky='w', padx=5, pady=2)
        self.column_var = tk.StringVar(value='All')
        column_combo = ttk.Combobox(main_frame, textvariable=self.column_var)
        column_combo['values'] = [col.replace('_', ' ').title() for col in
            self.columns]
        column_combo.grid(row=0, column=1, sticky='ew', padx=5, pady=2)
        column_combo.state(['readonly'])
        ttk.Label(main_frame, text='Search for:').grid(row=1, column=0,
            sticky='w', padx=5, pady=2)
        self.search_entry = ttk.Entry(main_frame)
        self.search_entry.grid(row=1, column=1, sticky='ew', padx=5, pady=2)
        self.match_case_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(main_frame, text='Match case', variable=self.
            match_case_var).grid(row=2, column=1, sticky='w', padx=5, pady=2)
        main_frame.columnconfigure(1, weight=1)
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=10)
        ttk.Button(button_frame, text='Search', command=self.search).pack(side
            =tk.LEFT, padx=5)
        ttk.Button(button_frame, text='Cancel', command=self.destroy).pack(side
            =tk.LEFT, padx=5)
        self.search_entry.focus_set()
        self.search_entry.bind('<Return>', lambda e: self.search())

        @inject(MaterialService)
        def search(self):
        """Execute the search"""
        column_display = self.column_var.get()
        column = self.columns[0] if column_display == 'All' else '_'.join(
            column_display.lower().split())
        search_params = {'column': column, 'text': self.search_entry.get(),
            'match_case': self.match_case_var.get()}
        self.search_callback(search_params)
        self.destroy()
