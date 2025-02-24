# Relative path: store_management/utils/logger.py

"""
Logging Utility Module

Provides centralized logging configuration and utility functions.
"""

import logging
import os
from typing import Optional

from config.settings import get_log_path


def setup_logging(
    log_level: int = logging.INFO,
    log_dir: Optional[str] = None,
    log_filename: str = 'application.log'
) -> None:
    """
    Configure logging for the application.

    Args:
        log_level (int, optional): Logging level. Defaults to logging.INFO.
        log_dir (Optional[str], optional): Directory to store log files.
        Defaults to None (uses default log path).
        log_filename (str, optional): Name of the log file. Defaults to 'application.log'.
    """
    # Determine log directory
    if log_dir is None:
        log_dir = get_log_path()

    # Ensure log directory exists
    os.makedirs(log_dir, exist_ok=True)

    # Full path to log file
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
    Get a configured logger instance.

    Args:
        name (Optional[str], optional): Name of the logger.
        Defaults to None (uses root logger).

    Returns:
        logging.Logger: Configured logger instance.
    """
    return logging.getLogger(name)


def log_error(
    error: Exception,
    context: Optional[str] = None,
    logger_name: Optional[str] = None
) -> None:
    """
    Log an error with optional context.

    Args:
        error (Exception): The error to log.
        context (Optional[str], optional): Additional context about the error.
        Defaults to None.
        logger_name (Optional[str], optional): Name of the logger.
        Defaults to None.
    """
    logger = get_logger(logger_name)
    error_message = str(error)

    if context:
        logger.error(f"{context}: {error_message}")
    else:
        logger.error(error_message)


def log_info(
    message: str,
    logger_name: Optional[str] = None
) -> None:
    """
    Log an informational message.

    Args:
        message (str): The message to log.
        logger_name (Optional[str], optional): Name of the logger.
        Defaults to None.
    """
    logger = get_logger(logger_name)
    logger.info(message)


def log_debug(
    message: str,
    logger_name: Optional[str] = None
) -> None:
    """
    Log a debug message.

    Args:
        message (str): The message to log.
        logger_name (Optional[str], optional): Name of the logger.
        Defaults to None.
    """
    logger = get_logger(logger_name)
    logger.debug(message)
