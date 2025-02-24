

from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
class StorageManager(BaseManager):
    """
    Specialized manager for Storage model operations.

    This class extends BaseManager with storage-specific operations.
    """

        @inject(MaterialService)
        def __init__(self, session_factory: Callable[[], Session]):
        """
        Initialize the StorageManager.

        Args:
            session_factory: A callable that returns a SQLAlchemy Session.
        """
        super().__init__(Storage, session_factory)
