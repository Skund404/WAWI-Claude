# database/__init__.py

from . import models
from . import repositories

# Re-export models for easier access
from database.models import (
    Base, AbstractBase, metadata,
    Storage, Customer, Supplier,
    Material, Leather, Hardware,
    Component, ComponentHardware, ComponentLeather, ComponentTool,
    BaseInventory, MaterialInventory, LeatherInventory,
    HardwareInventory, ProductInventory, ToolInventory,
    InventoryAdjustment, Project, ProjectComponent,
    Pattern, ProductPattern, Sales, SalesItem,
    Purchase, PurchaseItem, Tool,
    ToolList, ToolListItem,
    PickingList, PickingListItem,  # Ensure PickingList and PickingListItem are exported
    Product
)

__all__ = [
    'models',
    'repositories',
    # Include all models from the above import
    'Base', 'AbstractBase', 'metadata',
    'Storage', 'Customer', 'Supplier',
    'Material', 'Leather', 'Hardware',
    'Component', 'ComponentHardware', 'ComponentLeather', 'ComponentTool',
    'BaseInventory', 'MaterialInventory', 'LeatherInventory',
    'HardwareInventory', 'ProductInventory', 'ToolInventory',
    'InventoryAdjustment', 'Project', 'ProjectComponent',
    'Pattern', 'ProductPattern', 'Sales', 'SalesItem',
    'Purchase', 'PurchaseItem', 'Tool',
    'ToolList', 'ToolListItem',
    'PickingList', 'PickingListItem',  # Ensure PickingList and PickingListItem are in __all__
    'Product'
]