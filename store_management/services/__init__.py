# File:\store_management\services\__init__.py

"""
This module initializes the services package and exports the necessary classes.

It imports and exposes both the interface and implementation of the StorageService,
allowing other parts of the application to access these components through a single import.
"""

from .implementations.storage_service import StorageService
from .interfaces.storage_service import IStorageService

__all__ = ["StorageService", "IStorageService"]
