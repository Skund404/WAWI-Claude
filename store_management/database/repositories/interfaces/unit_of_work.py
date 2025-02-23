# database/repositories/interfaces/unit_of_work.py

from abc import ABC, abstractmethod
from database.repositories.interfaces.pattern_repository import IPatternRepository
from database.repositories.interfaces.leather_repository import ILeatherRepository


class IUnitOfWork(ABC):
    """Interface for Unit of Work pattern."""

    patterns: IPatternRepository
    leather_inventory: ILeatherRepository

    @abstractmethod
    def __enter__(self):
        """Start a new transaction."""
        pass

    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        """End the transaction."""
        pass

    @abstractmethod
    def commit(self):
        """Commit the transaction."""
        pass

    @abstractmethod
    def rollback(self):
        """Rollback the transaction."""
        pass