

from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService


class IUnitOfWork(ABC):
    """Interface for Unit of Work pattern."""
    patterns: IPatternRepository
    leather_inventory: ILeatherRepository

    @abstractmethod
    @inject(MaterialService)
        def __enter__(self):
        """Start a new transaction."""
        pass

        @abstractmethod
        @inject(MaterialService)
            def __exit__(self, exc_type, exc_val, exc_tb):
            """End the transaction."""
            pass

            @abstractmethod
            @inject(MaterialService)
                def commit(self):
                """Commit the transaction."""
                pass

                @abstractmethod
                @inject(MaterialService)
                    def rollback(self):
                    """Rollback the transaction."""
                    pass
