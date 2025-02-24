

from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
class LoggerConfig:
    """
    Comprehensive logging configuration with multiple handlers
    and advanced formatting
    """

        @staticmethod
    def create_logger(name: str='store_management', log_level: str='INFO',
        log_dir: Optional[str]=None) ->logging.Logger:
        """
        Create a configured logger with file and console handlers

        Args:
            name (str): Logger name
            log_level (str): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_dir (Optional[str]): Directory for log files

        Returns:
            Configured logging.Logger instance
        """
        if not log_dir:
            log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.
                abspath(__file__))), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, log_level.upper()))
        logger.handlers.clear()
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)8s | %(name)s | %(filename)s:%(lineno)d | %(message)s'
            , datefmt='%Y-%m-%d %H:%M:%S')
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        log_file_path = os.path.join(log_dir, f'{name}.log')
        file_handler = RotatingFileHandler(log_file_path, maxBytes=10 * 
            1024 * 1024, backupCount=5)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        return logger


class ErrorTracker:
    """
    Advanced error tracking and logging utility
    """

        @inject(MaterialService)
        def __init__(self, logger: Optional[logging.Logger]=None):
        """
        Initialize ErrorTracker

        Args:
            logger (Optional[logging.Logger]): Logger instance
        """
        self.logger = logger or LoggerConfig.create_logger()

        @inject(MaterialService)
        def log_error(self, error: Exception, context: Optional[Dict[str, Any]]
        =None, additional_info: Optional[str]=None):
        """
        Comprehensive error logging with context and stack trace

        Args:
            error (Exception): The exception to log
            context (Optional[Dict]): Additional context information
            additional_info (Optional[str]): Extra descriptive information
        """
        error_details = {'error_type': type(error).__name__,
            'error_message': str(error), 'stack_trace': traceback.format_exc()}
        if context:
            error_details['context'] = context
        log_message = f"Error Occurred: {error_details['error_type']}"
        if additional_info:
            log_message += f' | {additional_info}'
        self.logger.error(log_message, extra=error_details)

        @inject(MaterialService)
        def trace_method(self, method_name: str):
        """
        Method decorator for tracing method calls and errors

        Args:
            method_name (str): Name of the method being traced
        """

        def decorator(func):

            def wrapper(*args, **kwargs):
                try:
                    self.logger.debug(f'Entering method: {method_name}')
                    result = func(*args, **kwargs)
                    self.logger.debug(f'Exiting method: {method_name}')
                    return result
                except Exception as e:
                    context = {'method': method_name, 'args': args,
                        'kwargs': kwargs}
                    self.log_error(e, context)
                    raise
            return wrapper
        return decorator


logger = LoggerConfig.create_logger()
error_tracker = ErrorTracker(logger)
