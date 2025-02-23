# database\models\enums.py
from enum import Enum
from enum import auto


class OrderStatus(Enum):
    """Enumeration of possible order statuses."""
    PENDING = "Pending"
    PROCESSING = "Processing"
    SHIPPED = "Shipped"
    DELIVERED = "Delivered"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


class MaterialType(Enum):
    """Enumeration of material types used in leatherworking projects."""
    LEATHER = "Leather"
    HARDWARE = "Hardware"
    THREAD = "Thread"
    ADHESIVE = "Adhesive"
    OTHER = "Other"


class LeatherType(Enum):
    """Enumeration of leather types."""
    FULL_GRAIN = "Full Grain"
    TOP_GRAIN = "Top Grain"
    CORRECTED_GRAIN = "Corrected Grain"
    SPLIT_GRAIN = "Split Grain"
    BONDED_LEATHER = "Bonded Leather"


class MaterialQualityGrade(Enum):
    """Enumeration of material quality grades."""
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"


class InventoryStatus(Enum):
    """Enumeration of inventory statuses."""
    IN_STOCK = "In Stock"
    LOW_STOCK = "Low Stock"
    OUT_OF_STOCK = "Out of Stock"


class ProjectType(Enum):
    """Enumeration of project types in leatherworking."""
    BAG = "Bag"
    WALLET = "Wallet"
    BELT = "Belt"
    ACCESSORY = "Accessory"
    OTHER = "Other"


class SkillLevel(Enum):
    """Enumeration of skill levels for projects."""
    BEGINNER = "Beginner"
    INTERMEDIATE = "Intermediate"
    ADVANCED = "Advanced"
    EXPERT = "Expert"


class ProjectStatus(Enum):
    """Enumeration of project statuses."""
    PLANNING = "Planning"
    IN_PROGRESS = "In Progress"
    ON_HOLD = "On Hold"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


class SupplierStatus(Enum):
    """Enumeration of supplier statuses."""
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    PENDING = "Pending"


class StorageLocationType(Enum):
    """Enumeration of storage location types."""
    SHELF = "Shelf"
    CONTAINER = "Container"
    RACK = "Rack"
    WAREHOUSE = "Warehouse"


class MeasurementUnit(Enum):
    """Enumeration of measurement units."""
    INCH = "Inch"
    CENTIMETER = "Centimeter"
    FOOT = "Foot"
    METER = "Meter"


class Priority(Enum):
    """Enumeration of priority levels for tasks."""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"

class TransactionType(Enum):
    PURCHASE = "purchase"
    SALE = "sale"
    ADJUSTMENT = "adjustment"
    WASTE = "waste"


class QualityCheckStatus(Enum):
    """Represents the status of a quality check performed on a produced item."""
    PASSED = "PASSED"
    FAILED = "FAILED"
    PENDING = "PENDING"

class PaymentStatus(Enum):
    """Payment status for orders"""
    PENDING = "PENDING"
    PARTIALLY_PAID = "PARTIALLY_PAID"
    PAID = "PAID"
    REFUNDED = "REFUNDED"