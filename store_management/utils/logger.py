# store_management/utils/logger.py

import logging
import logging.handlers
import os
from pathlib import Path
from typing import Optional
from store_management.config import LOG_DIR


class AppLogger:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize_logger()
        return cls._instance

    def _initialize_logger(self):
        """Initialize the application logger with file and console handlers."""
        # Create logs directory if it doesn't exist
        LOG_DIR.mkdir(parents=True, exist_ok=True)

        # Create logger
        self.logger = logging.getLogger('store_management')
        self.logger.setLevel(logging.DEBUG)

        # Prevent duplicate handlers
        if not self.logger.handlers:
            # File handler
            log_file = LOG_DIR / 'store_management.log'
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=5 * 1024 * 1024,  # 5MB
                backupCount=5
            )
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)

            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_formatter = logging.Formatter(
                '%(levelname)s: %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)

    def get_logger(self):
        """Get the configured logger instance."""
        return self.logger


# Global logger instance
logger_instance = AppLogger()
logger = logger_instance.get_logger()


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a logger instance, optionally with a specific name.

    Args:
        name: Optional name for the logger. If provided, returns a child logger
             of the main application logger.

    Returns:
        logging.Logger: Configured logger instance
    """
    if name:
        return logging.getLogger(f'store_management.{name}')
    return logger


def log_error(error: Exception, context: Optional[dict] = None):
    """Log an error with optional context information.

    Args:
        error: The exception to log
        context: Optional dictionary with additional context
    """
    error_msg = f"Error: {str(error)}"
    if context:
        error_msg += f" Context: {context}"
    logger.error(error_msg, exc_info=True)


def log_info(message: str):
    """Log an info message.

    Args:
        message: The message to log
    """
    logger.info(message)


def log_debug(message: str):
    """Log a debug message.

    Args:
        message: The message to log
    """
    logger.debug(message)