from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
"""
Shopping list view implementation that displays shopping lists.
"""
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ShoppingListView(BaseView):
    """
    View for displaying and managing shopping lists.
    """

    @inject(MaterialService)
        def __init__(self, parent, app):
        """
        Initialize the shopping list view.

        Args:
            parent: Parent widget
            app: Application instance
        """
        super().__init__(parent, app)
        self.db_path = self._find_database_file()
        logger.debug(
            f'ShoppingListView initialized with database: {self.db_path}')
        self.setup_ui()
        self.load_data()

        @inject(MaterialService)
            def _find_database_file(self):
        """Find the SQLite database file."""
        possible_locations = ['store_management.db',
                              'data/store_management.db', 'database/store_management.db',
                              'config/database/store_management.db']
        for location in possible_locations:
            if os.path.exists(location):
                return location
        logger.info('Searching for database file...')
        for root, _, files in os.walk(''):
            for file in files:
                if file.endswith('.db'):
                    path = os.path.join(root, file)
                    logger.info(f'Found database file: {path}')
                    return path
        return None

        @inject(MaterialService)
            def setup_ui(self):
        """Set up the user interface components."""
        self.create_toolbar()
        self.create_treeview()

        @inject(MaterialService)
            def create_toolbar(self):
        """Create the toolbar with buttons."""
        toolbar = ttk.Frame(self)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        ttk.Button(toolbar, text='Add List', command=self.show_add_dialog
                   ).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text='Delete Selected', command=lambda e=None:
                   self.delete_selected(e)).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text='Search', command=self.show_search_dialog
                   ).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text='Refresh', command=self.load_data).pack(
            side=tk.LEFT, padx=2)
        logger.debug('Toolbar created')

        @inject(MaterialService)
            def create_treeview(self):
        """Create the treeview for displaying shopping lists."""
        frame = ttk.Frame(self)
        frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        columns = 'id', 'name', 'date', 'status', 'priority', 'items', 'total'
        self.tree = ttk.Treeview(frame, columns=columns, show='headings')
        self.tree.heading('id', text='ID')
        self.tree.heading('name', text='Name')
        self.tree.heading('date', text='Date')
        self.tree.heading('status', text='Status')
        self.tree.heading('priority', text='Priority')
        self.tree.heading('items', text='Items')
        self.tree.heading('total', text='Total')
        self.tree.column('id', width=50)
        self.tree.column('name', width=200)
        self.tree.column('date', width=100)
        self.tree.column('status', width=100)
        self.tree.column('priority', width=80)
        self.tree.column('items', width=80)
        self.tree.column('total', width=100)
        vsb = ttk.Scrollbar(frame, orient='vertical', command=self.tree.yview)
        hsb = ttk.Scrollbar(frame, orient='horizontal', command=self.tree.xview
                            )
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.tree.bind('<Double-1>', self.on_double_click)
        logger.debug('Treeview created')

        @inject(MaterialService)
            def load_data(self):
        """Load shopping lists from the database and display them."""
        try:
            logger.info('Loading shopping list data')
            for item in self.tree.get_children():
                self.tree.delete(item)
            if not self.db_path:
                logger.error('Database file not found')
                self.set_status('Error: Database file not found')
                return
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='shopping_list';
            """
            )
            if not cursor.fetchone():
                logger.info(
                    "Shopping list table doesn't exist. Creating sample data.")
                self.set_status(
                    "Shopping list table doesn't exist - showing sample data")
                today = datetime.now().strftime('%Y-%m-%d')
                sample_data = [(1, 'Weekly Groceries', today, 'Active',
                                'High', 15, '$125.50'), (2, 'Office Supplies', today,
                                                         'Pending', 'Medium', 8, '$45.75'), (3, 'Party Supplies',
                                                                                             today, 'Complete', 'Low', 12, '$78.25'), (4,
                                                                                                                                       'Emergency Items', today, 'Active', 'Urgent', 5,
                                                                                                                                       '$32.99'), (5, 'Home Improvement', today, 'Draft',
                                                                                                                                                   'Low', 3, '$215.00')]
                for shopping_list in sample_data:
                    self.tree.insert('', tk.END, values=shopping_list)
                return
            cursor.execute(
                'SELECT id, name, date, status, priority, items, total FROM shopping_list;'
            )
            rows = cursor.fetchall()
            for row in rows:
                self.tree.insert('', tk.END, values=row)
            self.set_status(f'Loaded {len(rows)} shopping lists')
            logger.info(f'Loaded {len(rows)} shopping lists')
        except Exception as e:
            logger.error(f'Error loading shopping list data: {str(e)}',
                         exc_info=True)
            self.show_error('Data Load Error',
                            f'Failed to load shopping list data: {str(e)}')
        finally:
            if 'conn' in locals():
                conn.close()

        @inject(MaterialService)
            def show_add_dialog(self):
        """Show dialog to add a new shopping list."""
        logger.debug('Add dialog requested but not implemented')
        self.show_info('Not Implemented',
                       'Add shopping list functionality is not yet implemented.')

        @inject(MaterialService)
            def on_double_click(self, event):
        """Handle double-click on a shopping list item."""
        logger.debug('Double-click event received but not implemented')
        self.show_info('Not Implemented',
                       'Edit shopping list functionality is not yet implemented.')

        @inject(MaterialService)
            def delete_selected(self, event):
        """Delete the selected shopping list."""
        logger.debug('Delete requested but not implemented')
        self.show_info('Not Implemented',
                       'Delete shopping list functionality is not yet implemented.')

        @inject(MaterialService)
            def show_search_dialog(self):
        """Show search dialog."""
        logger.debug('Search requested but not implemented')
        self.show_info('Not Implemented',
                       'Search functionality is not yet implemented.')
