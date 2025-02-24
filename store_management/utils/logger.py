from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
logger = logging.getLogger(__name__)


def setup_logging(log_level: int=logging.INFO, log_dir: Optional[str]=None,
    log_filename: str='app.log'):
    """
    Set up logging configuration for the application.

    Args:
        log_level (int, optional): Logging level. Defaults to logging.INFO.
        log_dir (Optional[str], optional): Directory to store log files. Defaults to None.
        log_filename (str, optional): Name of the log file. Defaults to 'app.log'.
    """
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, log_filename)
    else:
        log_path = log_filename
    logging.basicConfig(level=log_level, format=
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s', handlers=[
        logging.FileHandler(log_path), logging.StreamHandler()])
    global logger
    logger = logging.getLogger(__name__)
    logger.setLevel(log_level)


def get_logger(name: str) ->logging.Logger:
    """
    Get a logger with the specified name.

    Args:
        name (str): Name of the logger.

    Returns:
        logging.Logger: Configured logger instance.
    """
    return logging.getLogger(name)


def log_error(error: Exception, context: Optional[str]=None, logger_name:
    str='root'):
    """
    Log an error with optional context.

    Args:
        error (Exception): The error to log.
        context (Optional[str], optional): Additional context for the error. Defaults to None.
        logger_name (str, optional): Name of the logger. Defaults to 'root'.
    """
    log_logger = get_logger(logger_name)
    error_message = str(error)
    if context:
        error_message = f'{context}: {error_message}'
    log_logger.error(error_message, exc_info=True)


def log_info(message: str, logger_name: str='root'):
    """
    Log an informational message.

    Args:
        message (str): The message to log.
        logger_name (str, optional): Name of the logger. Defaults to 'root'.
    """
    log_logger = get_logger(logger_name)
    log_logger.info(message)


def log_debug(message: str, logger_name: str='root'):
    """
    Log a debug message.

    Args:
        message (str): The message to log.
        logger_name (str, optional): Name of the logger. Defaults to 'root'.
    """
    log_logger = get_logger(logger_name)
    log_logger.debug(message)


setup_logging()
