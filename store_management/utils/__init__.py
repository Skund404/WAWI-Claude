# utils/__init__.py
"""
Initialization module for utils package in the leatherworking store management application.
"""

import logging
from typing import Optional, Union

from .circular_import_resolver import CircularImportResolver, get_module




def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Create and configure a logger for the given name.

    Args:
        name (str): Name of the logger
        level (int, optional): Logging level. Defaults to logging.INFO.

    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Only add handler if no existing handlers to prevent duplicate logs
    if not logger.handlers:
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)

        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)

        # Add handler to logger
        logger.addHandler(console_handler)

    return logger


def configure_logging(
        log_level: int = logging.INFO,
        log_file: Optional[str] = None
) -> None:
    """
    Configure global logging settings.

    Args:
        log_level (int, optional): Logging level. Defaults to logging.INFO.
        log_file (Optional[str], optional): Path to log file. Defaults to None.
    """
    # Basic configuration
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # If log file is provided, add file handler
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)

        # Add file handler to root logger
        logging.getLogger().addHandler(file_handler)


# Initialize the CircularImportResolver when the package is imported
CircularImportResolver()


# Import and re-export the CircularImportResolver
try:
    from .circular_import_resolver import CircularImportResolver, get_module, get_class, lazy_import
    __all__ = ['CircularImportResolver', 'get_module', 'get_class', 'lazy_import']
except ImportError as e:
    logging.warning(f"Could not import CircularImportResolver: {e}")