# utils/logger.py
import logging
import os
from typing import Optional
from config.settings import get_log_path


# Configure the root logger
def configure_logging():
    """
    Configure the root logger with basic settings.

    This function sets up the basic configuration for logging,
    including format, level, and file handler if a log path is available.
    """
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    log_level = logging.INFO

    # Configure basic logging to console
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[logging.StreamHandler()]
    )

    # Add file handler if log path is available
    try:
        log_path = get_log_path()
        if log_path:
            log_dir = os.path.dirname(log_path)
            os.makedirs(log_dir, exist_ok=True)

            file_handler = logging.FileHandler(log_path)
            file_handler.setFormatter(logging.Formatter(log_format))

            # Add file handler to root logger
            logging.getLogger().addHandler(file_handler)
    except Exception as e:
        logging.error(f"Failed to configure file logging: {e}")


# Initialize logging
configure_logging()


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance with the given name.

    Args:
        name: The name for the logger. If None, the root logger is returned.

    Returns:
        A logger instance
    """
    return logging.getLogger(name)