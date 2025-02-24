from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
__all__ = ['Base', 'BaseModel', 'Order', 'OrderItem', 'OrderStatus',
    'PaymentStatus', 'Storage', 'Supplier', 'Product', 'Material',
    'MetricSnapshot', 'MaterialUsageLog', 'Leather', 'Part', 'Project',
    'ProjectComponent', 'LeatherTransaction', 'InventoryTransaction',
    'TransactionType', 'MaterialType', 'LeatherType',
    'MaterialQualityGrade', 'InventoryStatus', 'ProjectType', 'SkillLevel',
    'ProjectStatus', 'SupplierStatus', 'StorageLocationType',
    'MeasurementUnit', 'Priority', 'QualityCheckStatus']
