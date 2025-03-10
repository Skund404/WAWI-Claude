# services/interfaces/repositories.py
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Type, TypeVar, Union

T = TypeVar('T')


class IBaseService(ABC):
    """Base interface for all service operations."""

    @abstractmethod
    def get_by_id(self, item_id: int) -> Dict[str, Any]:
        """Retrieve an item by its unique identifier."""
        pass

    @abstractmethod
    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new item."""
        pass

    @abstractmethod
    def update(self, item_id: int, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing item."""
        pass

    @abstractmethod
    def delete(self, item_id: int) -> bool:
        """Delete an item."""
        pass

    @abstractmethod
    def list(self,
             filters: Optional[Dict[str, Any]] = None,
             page: int = 1,
             per_page: int = 20,
             sort_by: Optional[str] = None) -> Dict[str, Any]:
        """List items with optional filtering, pagination, and sorting."""
        pass


class IComponentService(IBaseService):
    """Service for managing components."""

    @abstractmethod
    def get_components_by_type(self, component_type: str) -> List[Dict[str, Any]]:
        """Retrieve components by a specific type."""
        pass

    @abstractmethod
    def add_material_to_component(self,
                                  component_id: int,
                                  material_id: int,
                                  quantity: float) -> Dict[str, Any]:
        """Add a material to a component with specified quantity."""
        pass


class ICustomerService(IBaseService):
    """Service for managing customer-related operations."""

    @abstractmethod
    def get_customer_sales_history(self,
                                   customer_id: int,
                                   start_date: Optional[str] = None,
                                   end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve sales history for a specific customer."""
        pass

    @abstractmethod
    def update_customer_status(self, customer_id: int, status: str) -> Dict[str, Any]:
        """Update customer status."""
        pass


class IMaterialService(IBaseService):
    """Base interface for material-related services."""

    @abstractmethod
    def get_low_stock_materials(self) -> List[Dict[str, Any]]:
        """Retrieve materials with low stock levels."""
        pass

    @abstractmethod
    def adjust_inventory(self,
                         material_id: int,
                         quantity_change: float,
                         adjustment_type: str) -> Dict[str, Any]:
        """Adjust material inventory."""
        pass


class ILeatherService(IMaterialService):
    """Service for managing leather-specific operations."""

    @abstractmethod
    def filter_leather_by_type(self, leather_type: str) -> List[Dict[str, Any]]:
        """Filter leather by specific type."""
        pass


class IHardwareService(IMaterialService):
    """Service for managing hardware-related operations."""

    @abstractmethod
    def filter_hardware_by_type(self, hardware_type: str) -> List[Dict[str, Any]]:
        """Filter hardware by specific type."""
        pass


class ISuppliesService(IMaterialService):
    """Service for managing supplies-related operations."""

    @abstractmethod
    def filter_supplies_by_type(self, supplies_type: str) -> List[Dict[str, Any]]:
        """Filter supplies by specific type."""
        pass


class IInventoryService(IBaseService):
    """Service for managing inventory-related operations."""

    @abstractmethod
    def get_inventory_status(self, item_id: int, item_type: str) -> Dict[str, Any]:
        """Get inventory status for a specific item."""
        pass

    @abstractmethod
    def generate_inventory_report(self,
                                  start_date: Optional[str] = None,
                                  end_date: Optional[str] = None) -> Dict[str, Any]:
        """Generate comprehensive inventory report."""
        pass


class IPatternService(IBaseService):
    """Service for managing pattern-related operations."""

    @abstractmethod
    def get_patterns_by_skill_level(self, skill_level: str) -> List[Dict[str, Any]]:
        """Retrieve patterns by skill level."""
        pass

    @abstractmethod
    def get_pattern_components(self, pattern_id: int) -> List[Dict[str, Any]]:
        """Retrieve components for a specific pattern."""
        pass


class IProductService(IBaseService):
    """Service for managing product-related operations."""

    @abstractmethod
    def get_product_patterns(self, product_id: int) -> List[Dict[str, Any]]:
        """Retrieve patterns associated with a product."""
        pass

    @abstractmethod
    def update_product_price(self, product_id: int, price: float) -> Dict[str, Any]:
        """Update product pricing."""
        pass


class ISalesService(IBaseService):
    """Service for managing sales-related operations."""

    @abstractmethod
    def create_sales_order(self, sales_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new sales order."""
        pass

    @abstractmethod
    def add_sales_item(self,
                       sales_id: int,
                       product_id: int,
                       quantity: int,
                       price: float) -> Dict[str, Any]:
        """Add an item to an existing sales order."""
        pass

    @abstractmethod
    def update_sales_status(self, sales_id: int, status: str) -> Dict[str, Any]:
        """Update sales order status."""
        pass


class IPurchaseService(IBaseService):
    """Service for managing purchase-related operations."""

    @abstractmethod
    def create_purchase_order(self, purchase_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new purchase order."""
        pass

    @abstractmethod
    def add_purchase_item(self,
                          purchase_id: int,
                          item_id: int,
                          item_type: str,
                          quantity: int,
                          price: float) -> Dict[str, Any]:
        """Add an item to an existing purchase order."""
        pass

    @abstractmethod
    def update_purchase_status(self, purchase_id: int, status: str) -> Dict[str, Any]:
        """Update purchase order status."""
        pass


class ISupplierService(IBaseService):
    """Service for managing supplier-related operations."""

    @abstractmethod
    def get_supplier_purchases(self,
                               supplier_id: int,
                               start_date: Optional[str] = None,
                               end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve purchase history for a specific supplier."""
        pass

    @abstractmethod
    def update_supplier_status(self, supplier_id: int, status: str) -> Dict[str, Any]:
        """Update supplier status."""
        pass


class IProjectService(IBaseService):
    """Service for managing project-related operations."""

    @abstractmethod
    def get_project_components(self, project_id: int) -> List[Dict[str, Any]]:
        """Retrieve components for a specific project."""
        pass

    @abstractmethod
    def update_project_status(self, project_id: int, status: str) -> Dict[str, Any]:
        """Update project status."""
        pass

    @abstractmethod
    def generate_project_timeline(self, project_id: int) -> Dict[str, Any]:
        """Generate project timeline."""
        pass


class IToolService(IBaseService):
    """Service for managing tool-related operations."""

    @abstractmethod
    def get_tools_by_category(self, tool_category: str) -> List[Dict[str, Any]]:
        """Retrieve tools by specific category."""
        pass

    @abstractmethod
    def schedule_tool_maintenance(self, tool_id: int, maintenance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Schedule maintenance for a tool."""
        pass


class IPickingListService(IBaseService):
    """Service for managing picking list operations."""

    @abstractmethod
    def generate_picking_list(self, sales_id: int) -> Dict[str, Any]:
        """Generate a picking list for a sales order."""
        pass

    @abstractmethod
    def update_picking_list_status(self, picking_list_id: int, status: str) -> Dict[str, Any]:
        """Update picking list status."""
        pass


class IToolListService(IBaseService):
    """Service for managing tool list operations."""

    @abstractmethod
    def generate_tool_list(self, project_id: int) -> Dict[str, Any]:
        """Generate a tool list for a project."""
        pass

    @abstractmethod
    def update_tool_list_status(self, tool_list_id: int, status: str) -> Dict[str, Any]:
        """Update tool list status."""
        pass