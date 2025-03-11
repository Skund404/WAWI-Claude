# gui/config.py
"""
Configuration settings for the GUI application.
Centralizes constants and settings used throughout the GUI.
"""

# Window dimensions
DEFAULT_WINDOW_WIDTH = 1280
DEFAULT_WINDOW_HEIGHT = 800
MIN_WINDOW_WIDTH = 800
MIN_WINDOW_HEIGHT = 600

# Table display settings
PAGE_SIZE_OPTIONS = [10, 25, 50, 100]
DEFAULT_PAGE_SIZE = 25

# File paths
ICON_PATH = "assets/icons"
REPORT_TEMPLATE_PATH = "assets/report_templates"

# Date/time formats
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

# Logging
LOG_LEVEL = "INFO"

# Cache settings
CACHE_ENABLED = True
CACHE_TIMEOUT = 300  # seconds