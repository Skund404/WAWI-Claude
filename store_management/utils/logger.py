# utils/logger.py
"""
Centralized logging configuration for the application.
"""

import os
import logging
from pathlib import Path
from typing import Optional, Union

from config.settings import get_log_path


class AppLogger:
    """
    Singleton logger class for the application.
    Ensures consistent logging configuration across the project.
    """
    _instance = None

    def __new__(cls):
        """
        Implement singleton pattern for logger.

        Returns:
            AppLogger: Single instance of the logger.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize_logger()
        return cls._instance

    def _initialize_logger(self):
        """
        Initialize the logging configuration.
        Creates log directory if it doesn't exist.
        Sets up file and console logging.
        """
        # Ensure log directory exists
        log_dir = Path(get_log_path())
        log_dir.mkdir(parents=True, exist_ok=True)

        # Configure the root logger
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                # File handler
                logging.FileHandler(
                    log_dir / 'application.log',
                    encoding='utf-8'
                ),
                # Console handler
                logging.StreamHandler()
            ]
        )

    def get_logger(self, name: Optional[str] = None) -> logging.Logger:
        """
        Retrieve a logger for a specific module.

        Args:
            name (Optional[str], optional): Name of the logger.
                                            Defaults to root logger if None.

        Returns:
            logging.Logger: Configured logger instance.
        """
        return logging.getLogger(name)


# Module-level logger functions for convenience
def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance.

    Args:
        name (Optional[str], optional): Name of the logger.
                                        Defaults to root logger if None.

    Returns:
        logging.Logger: Configured logger instance.
    """
    return AppLogger().get_logger(name)


def log_error(
        error: Union[Exception, str],
        context: Optional[str] = None
) -> None:
    """
    Log an error with optional context.

    Args:
        error (Union[Exception, str]): Error to log.
        context (Optional[str], optional): Additional context for the error.
    """
    logger = get_logger()
    error_message = str(error)

    if context:
        error_message = f"{context}: {error_message}"

    logger.error(error_message, exc_info=True)


def log_info(message: str) -> None:
    """
    Log an informational message.

    Args:
        message (str): Message to log.
    """
    logger = get_logger()
    logger.info(message)


def log_debug(message: str) -> None:
    """
    Log a debug message.

    Args:
        message (str): Message to log.
    """
    logger = get_logger()
    logger.debug(message)


# Create a default logger instance
logger = get_logger()