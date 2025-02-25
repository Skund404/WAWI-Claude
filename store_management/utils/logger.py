# path: utils/logger.py
"""
Logger configuration module for the store management application.

This module provides utility functions for setting up and configuring
the application's logging system.
"""

import os
import logging
import datetime
from typing import Optional, Union, Dict, Any

# Import settings carefully to avoid circular imports
try:
    from config.settings import get_log_path
except ImportError:
    # Fallback if we can't import directly
    def get_log_path() -> str:
        """Fallback implementation to get the log directory."""
        # Use a default logs directory in the current working directory
        log_dir = os.path.join(os.getcwd(), 'logs')
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        return log_dir


def setup_logging(log_level: Union[int, str] = logging.INFO,
                  log_dir: Optional[str] = None,
                  log_filename: Optional[str] = None) -> None:
    """
    Set up the application's logging configuration.

    Args:
        log_level: Logging level (default: INFO)
        log_dir: Directory for log files (default: from settings)
        log_filename: Name of the log file (default: based on current date)
    """
    # Convert string log level to int if needed
    if isinstance(log_level, str):
        log_level = getattr(logging, log_level.upper(), logging.INFO)

    # Determine log directory
    if log_dir is None:
        log_dir = get_log_path()

    # Ensure log directory exists
    os.makedirs(log_dir, exist_ok=True)

    # Generate log filename if not provided
    if log_filename is None:
        current_date = datetime.datetime.now().strftime('%Y-%m-%d')
        log_filename = f'store_management_{current_date}.log'

    # Full path to log file
    log_file_path = os.path.join(log_dir, log_filename)

    # Configure logging
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file_path),
            logging.StreamHandler()  # Also output to console
        ]
    )

    # Log startup information
    root_logger = logging.getLogger()
    root_logger.info(f"Logging initialized. Log file: {log_file_path}")
    root_logger.debug(f"Log level set to: {logging.getLevelName(log_level)}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.

    Args:
        name: The name for the logger, typically __name__

    Returns:
        A configured logger instance
    """
    return logging.getLogger(name)


def configure_logging(log_level: Union[int, str] = logging.INFO,
                      log_file: Optional[str] = None) -> None:
    """
    Configure logging with the specified settings.

    This is a convenience wrapper around setup_logging.

    Args:
        log_level: Logging level (default: INFO)
        log_file: Path to log file (default: auto-generated)
    """
    if log_file:
        log_dir = os.path.dirname(log_file)
        log_filename = os.path.basename(log_file)
        setup_logging(log_level, log_dir, log_filename)
    else:
        setup_logging(log_level)


def log_error(error: Exception, context: Optional[Dict[str, Any]] = None,
              logger_name: str = __name__) -> None:
    """
    Log an error with context information.

    Args:
        error: The exception to log
        context: Additional context information
        logger_name: Name of the logger to use
    """
    logger = get_logger(logger_name)

    # Format context information
    context_str = ""
    if context:
        context_str = " | Context: " + ", ".join(f"{k}={v}" for k, v in context.items())

    # Log the error
    logger.error(f"Error: {str(error)}{context_str}")
    logger.debug(f"Error details:", exc_info=True)


def log_info(message: str, logger_name: str = __name__) -> None:
    """
    Log an informational message.

    Args:
        message: The message to log
        logger_name: Name of the logger to use
    """
    logger = get_logger(logger_name)
    logger.info(message)


def log_debug(message: str, logger_name: str = __name__) -> None:
    """
    Log a debug message.

    Args:
        message: The message to log
        logger_name: Name of the logger to use
    """
    logger = get_logger(logger_name)
    logger.debug(message)


# Automatically set up basic logging when the module is imported
try:
    # Only set up basic logging if it hasn't been configured yet
    if not logging.getLogger().handlers:
        setup_logging()
except Exception as e:
    # In case of any errors during setup, configure a basic fallback
    print(f"Warning: Failed to set up logging: {e}")
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )