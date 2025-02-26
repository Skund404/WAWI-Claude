# utils/logging_config.py
"""
Centralized logging configuration for the leatherworking store management application.
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime


def setup_logging(log_dir: str = None, log_level: int = logging.INFO) -> None:
    """
    Configure logging for the application.

    Args:
        log_dir (str, optional): Directory to store log files.
            Defaults to a 'logs' directory in the project root.
        log_level (int, optional): Logging level. Defaults to logging.INFO.
    """
    # Determine log directory
    if log_dir is None:
        # Get project root (assuming this file is in a utils directory)
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        log_dir = os.path.join(project_root, 'logs')

    # Create log directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)

    # Generate log filename with current date
    log_filename = f'store_management_{datetime.now().strftime("%Y-%m-%d")}.log'
    log_path = os.path.join(log_dir, log_filename)

    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[]  # Clear any existing handlers
    )

    # Create a rotating file handler
    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))

    # Create a console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(logging.Formatter(
        '%(name)s - %(levelname)s - %(message)s'
    ))

    # Add handlers to the root logger
    logging.getLogger().addHandler(file_handler)
    logging.getLogger().addHandler(console_handler)

    # Log configuration details
    logger = logging.getLogger(__name__)
    logger.info(f"Log directory: {log_dir}")
    logger.info(f"Log file: {log_path}")
    logger.info("Logging configured successfully")


def get_logger(name: str = None, level: int = logging.INFO) -> logging.Logger:
    """
    Get a configured logger for a specific module.

    Args:
        name (str, optional): Name of the logger. Defaults to None.
        level (int, optional): Logging level. Defaults to logging.INFO.

    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    return logger


# Allow direct execution for testing logging configuration
def main():
    """
    Test logging configuration.
    """
    setup_logging()

    # Test different logging levels
    logger = get_logger(__name__)
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")


if __name__ == '__main__':
    main()