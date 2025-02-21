# File: store_management\database\sqlalchemy\core\specialized\storage_manager.py

from typing import Callable
from sqlalchemy.orm import Session
from store_management.database.sqlalchemy.core.base_manager import BaseManager
from store_management.database.sqlalchemy.models.storage import Storage

class StorageManager(BaseManager):
    """
    Specialized manager for Storage model operations.

    This class extends BaseManager with storage-specific operations.
    """

    def __init__(self, session_factory: Callable[[], Session]):
        """
        Initialize the StorageManager.

        Args:
            session_factory: A callable that returns a SQLAlchemy Session.
        """
        super().__init__(Storage, session_factory)

    # Add storage-specific methods here