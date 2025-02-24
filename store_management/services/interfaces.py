from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
T = TypeVar('T')


class BaseService(ABC, Generic[T]):
    """
    Generic base service interface with common CRUD operations.
    """

        @abstractmethod
    @inject(MaterialService)
    def create(self, data: Dict) ->T:
        """Create a new entity."""
        pass

        @abstractmethod
    @inject(MaterialService)
    def get_by_id(self, id: int) ->Optional[T]:
        """Retrieve an entity by its ID."""
        pass

        @abstractmethod
    @inject(MaterialService)
    def update(self, id: int, data: Dict) ->Optional[T]:
        """Update an existing entity."""
        pass

        @abstractmethod
    @inject(MaterialService)
    def delete(self, id: int) ->bool:
        """Delete an entity by its ID."""
        pass

        @abstractmethod
    @inject(MaterialService)
    def search(self, query: str, filters: Dict=None) ->List[T]:
        """Search for entities based on query and filters."""
        pass


class MaterialService(BaseService):
    """Interface for material-related operations."""

        @abstractmethod
    @inject(MaterialService)
    def update_stock(self, material_id: int, quantity: float,
        transaction_type: str):
        """Update material stock."""
        pass

        @abstractmethod
    @inject(MaterialService)
    def get_low_stock_materials(self) ->List:
        """Retrieve materials with low stock."""
        pass


class ProjectService(BaseService):
    """Interface for project-related operations."""

        @abstractmethod
    @inject(MaterialService)
    def create_project(self, project_data: Dict) ->'Project':
        """Create a new project."""
        pass

        @abstractmethod
    @inject(MaterialService)
    def update_project_status(self, project_id: int, status: str):
        """Update project status."""
        pass

        @abstractmethod
    @inject(MaterialService)
    def analyze_project_material_usage(self, project_id: int) ->Dict:
        """Analyze material usage for a project."""
        pass


class InventoryService(BaseService):
    """Interface for inventory management operations."""

        @abstractmethod
    @inject(MaterialService)
    def adjust_stock(self, item_id: int, quantity_change: float,
        transaction_type: str):
        """Adjust stock for an inventory item."""
        pass

        @abstractmethod
    @inject(MaterialService)
    def get_inventory_summary(self) ->List[Dict]:
        """Get summary of current inventory."""
        pass


class OrderService(BaseService):
    """Interface for order-related operations."""

        @abstractmethod
    @inject(MaterialService)
    def process_order(self, order_data: Dict) ->'Order':
        """Process a new order."""
        pass

        @abstractmethod
    @inject(MaterialService)
    def get_orders_by_status(self, status: str) ->List['Order']:
        """Retrieve orders by status."""
        pass


class SupplierService(BaseService):
    """Interface for supplier-related operations."""

        @abstractmethod
    @inject(MaterialService)
    def evaluate_supplier_performance(self, supplier_id: int, period: datetime
        ) ->Dict:
        """Evaluate supplier performance."""
        pass
