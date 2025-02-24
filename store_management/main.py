from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)


def setup_exception_handler(root: Optional[tk.Tk]=None):
    """
    Set up a global exception handler to log and display unhandled exceptions.

    Args:
        root (Optional[tk.Tk]): The root Tkinter window to display error messages.
    """

    def handle_exception(exc_type, exc_value, exc_traceback):
        logging.error('Uncaught exception', exc_info=(exc_type, exc_value,
            exc_traceback))
        error_msg = ''.join(traceback.format_exception(exc_type, exc_value,
            exc_traceback))
        if root:
            from tkinter import messagebox
            messagebox.showerror('Unhandled Exception', error_msg)
        print(error_msg)
        sys.exit(1)
    sys.excepthook = handle_exception


def initialize_app() ->Application:
    """
    Initialize the application services and create the application instance.

    Returns:
        Application: Configured application instance
    """
    try:
        configure_application_services()
        return Application()
    except Exception as e:
        logging.error(f'Failed to initialize application: {e}')
        raise


def main():
    """
    Main entry point for the application.
    Sets up logging, exception handling, and launches the GUI.
    """
    try:
        log_path = get_log_path()
        setup_logging(log_level=logging.INFO, log_dir=os.path.dirname(log_path)
            )
        db_path = get_database_path()
        logging.info(f'Using database at: {db_path}')
        root = tk.Tk()
        root.title('Store Management System')
        root.geometry('1200x800')
        setup_exception_handler(root)
        app = initialize_app()
        main_window = MainWindow(root, app)
        main_window.pack(fill=tk.BOTH, expand=True)
        root.mainloop()
    except Exception as e:
        logging.error(f'Application startup failed: {e}')
        logging.error(traceback.format_exc())
        import tkinter.messagebox as messagebox
        messagebox.showerror('Startup Error', str(e))


if __name__ == '__main__':
    main()
