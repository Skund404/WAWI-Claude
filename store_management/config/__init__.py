# config/__init__.py
"""Configuration package initializer."""


from .paths import get_backup_dir, get_config_path

__all__ = [
    "APP_NAME",
    "APP_VERSION",
    "APP_DESCRIPTION",
    "DEVELOPMENT",
    "PRODUCTION",
    "TESTING",
    "get_database_path",
    "get_backup_dir",
    "get_config_path",
]