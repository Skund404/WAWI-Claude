import logging
import sys
from datetime import datetime
from pathlib import Path
from logging.handlers import RotatingFileHandler


class AppLogger:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AppLogger, cls).__new__(cls)
            cls._instance._initialize_logger()
        return cls._instance

    def _initialize_logger(self):
        """Initialize the logger with both file and console handlers"""
        self.logger = logging.getLogger('StoreManagement')
        self.logger.setLevel(logging.DEBUG)

        # Create logs directory if it doesn't exist
        log_dir = Path(__file__).parent.parent / 'logs'
        log_dir.mkdir(exist_ok=True)

        # Create formatters
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
        )
        console_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )

        # File handler (rotates at 5MB, keeps 5 backup files)
        today = datetime.now().strftime('%Y-%m-%d')
        file_handler = RotatingFileHandler(
            log_dir / f'store_management_{today}.log',
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(file_formatter)

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(console_formatter)

        # Add handlers to logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def get_logger(self):
        """Get the logger instance"""
        return self.logger


# Create a global logger instance
logger = AppLogger().get_logger()


def log_error(error, context=""):
    """Utility function to log errors with stack trace"""
    import traceback
    error_msg = f"{context} - {str(error)}\n{traceback.format_exc()}"
    logger.error(error_msg)
    return error_msg


def log_info(message):
    """Utility function to log info messages"""
    logger.info(message)


def log_debug(message):
    """Utility function to log debug messages"""
    logger.debug(message)