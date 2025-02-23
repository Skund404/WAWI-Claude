# database/repositories/interfaces/base_repository.py

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List, Optional

T = TypeVar('T')


class IBaseRepository(ABC, Generic[T]):
    """Base interface for all repositories."""

    @abstractmethod
    def get_by_id(self, id: int) -> Optional[T]:
        """Get entity by ID."""
        pass

    @abstractmethod
    def get_all(self) -> List[T]:
        """Get all entities."""
        pass

    @abstractmethod
    def add(self, entity: T) -> T:
        """Add new entity."""
        pass

    @abstractmethod
    def update(self, entity: T) -> T:
        """Update existing entity."""
        pass

    @abstractmethod
    def delete(self, id: int) -> bool:
        """Delete entity by ID."""
        pass