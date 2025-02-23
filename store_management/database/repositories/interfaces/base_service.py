# database/services/interfaces/base_service.py

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List, Optional

T = TypeVar('T')


class IBaseService(ABC, Generic[T]):
    """Base interface for all services."""

    @abstractmethod
    def get_by_id(self, id: int) -> Optional[T]:
        """Get entity by ID."""
        pass

    @abstractmethod
    def get_all(self) -> List[T]:
        """Get all entities."""
        pass

    @abstractmethod
    def create(self, data: dict) -> T:
        """Create new entity."""
        pass

    @abstractmethod
    def update(self, id: int, data: dict) -> Optional[T]:
        """Update existing entity."""
        pass

    @abstractmethod
    def delete(self, id: int) -> bool:
        """Delete entity."""
        pass