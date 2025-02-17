def __init__(self, parent):
    try:
        super().__init__(parent)

        # Initialize database connection
        self.db = DatabaseManager(DATABASE_PATH)

        # Verify database connection
        if not self.db:
            raise DatabaseError("Failed to establish database connection")

        # Initialize undo/redo stacks
        self.undo_stack = []
        self.redo_stack = []

        # Setup UI components
        self.setup_toolbar()
        self.setup_table()

        # Load data with error handling
        try:
            self.load_data()
        except Exception as load_error:
            logger.error(f"Failed to load data: {load_error}")
            messagebox.showerror("Data Load Error", str(load_error))

    except Exception as init_error:
        logger.error(f"Supplier View Initialization Error: {init_error}")
        ErrorHandler.show_error("Initialization Error",
                                "Failed to initialize Supplier View",
                                init_error)
        raise