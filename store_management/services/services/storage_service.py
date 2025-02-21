# store_management/services/interfaces/storage_service.py
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any


class IStorageService(ABC):
    """Interface for storage service operations."""

    @abstractmethod
    def get_all_storage_locations(self) -> List[Dict[str, Any]]:
        """Get all storage locations."""
        pass

    @abstractmethod
    def get_storage_by_id(self, storage_id: int) -> Optional[Dict[str, Any]]:
        """Get a storage location by ID."""
        pass

    # Add other method signatures