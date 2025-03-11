# gui/utils/gui_logger.py
"""
Logging utilities for the GUI application.
Provides a logger configuration specifically for the GUI.
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from datetime import datetime


def setup_gui_logger(level="INFO", log_dir="logs"):
    """
    Configure logging for the GUI application.

    Args:
        level: The log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory to store log files
    """
    # Create logs directory if it doesn't exist
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Create log file path with timestamp
    timestamp = datetime.now().strftime("%Y%m%d")
    log_file = os.path.join(log_dir, f"gui_{timestamp}.log")

    # Set up level
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create rotating file handler
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5
    )
    file_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_format)
    file_handler.setLevel(log_level)
    root_logger.addHandler(file_handler)

    # Create console handler if running in development environment
    console_handler = logging.StreamHandler(sys.stdout)
    console_format = logging.Formatter(
        '%(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_format)
    console_handler.setLevel(log_level)
    root_logger.addHandler(console_handler)

    # Log that logging has been set up
    logging.info(f"GUI logging set up with level {level}")

    return root_logger


def get_logger(name):
    """
    Get a logger for a specific module.

    Args:
        name: The name of the module

    Returns:
        Logger instance
    """
    return logging.getLogger(name)