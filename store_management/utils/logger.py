# Path: utils/logger.py
import os
import logging
from typing import Optional, Union


def setup_logging(
        log_level: Union[str, int] = logging.INFO,
        log_dir: Optional[str] = None,
        log_filename: str = 'app.log'
) -> None:
    """
    Configure logging for the application.

    Args:
        log_level (Union[str, int]): Logging level. Defaults to logging.INFO.
        log_dir (Optional[str]): Directory to store log files. If None, uses a default location.
        log_filename (str): Name of the log file. Defaults to 'app.log'.
    """
    # Normalize log level
    if isinstance(log_level, str):
        log_level = getattr(logging, log_level.upper(), logging.INFO)

    # Determine log directory
    if log_dir is None:
        # Default to a 'logs' directory in the project root
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        log_dir = os.path.join(project_root, 'logs')

    # Create logs directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)

    # Full path for log file
    log_path = os.path.join(log_dir, log_filename)

    # Configure logging
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            # Console handler
            logging.StreamHandler(),
            # File handler
            logging.FileHandler(log_path, encoding='utf-8')
        ]
    )


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger with the specified name.

    Args:
        name (Optional[str]): Name of the logger. If None, uses the root logger.

    Returns:
        logging.Logger: Configured logger instance
    """
    return logging.getLogger(name)


def log_error(error: Exception, context: Optional[str] = None) -> None:
    """
    Log an error with optional context.

    Args:
        error (Exception): The exception to log
        context (Optional[str]): Additional context for the error
    """
    logger = get_logger()
    if context:
        logger.error(f"{context}: {str(error)}", exc_info=True)
    else:
        logger.error(str(error), exc_info=True)


def log_info(message: str) -> None:
    """
    Log an informational message.

    Args:
        message (str): Message to log
    """
    logger = get_logger()
    logger.info(message)


def log_debug(message: str) -> None:
    """
    Log a debug message.

    Args:
        message (str): Message to log
    """
    logger = get_logger()
    logger.debug(message)