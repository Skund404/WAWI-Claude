

from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService


class IUnitOfWork(ABC):
    pass
"""Interface for Unit of Work pattern."""
patterns: IPatternRepository
leather_inventory: ILeatherRepository

@abstractmethod
@inject(MaterialService)
def __enter__(self):
    pass
"""Start a new transaction."""
pass

@abstractmethod
@inject(MaterialService)
def __exit__(self, exc_type, exc_val, exc_tb):
    pass
"""End the transaction."""
pass

@abstractmethod
@inject(MaterialService)
def commit(self):
    pass
"""Commit the transaction."""
pass

@abstractmethod
@inject(MaterialService)
def rollback(self):
    pass
"""Rollback the transaction."""
pass
