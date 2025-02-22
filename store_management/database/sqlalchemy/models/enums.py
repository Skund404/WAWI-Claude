# File: store_management/database/sqlalchemy/models/enums.py
from enum import Enum, auto


class InventoryStatus(Enum):
    """Inventory status for parts and materials."""

    IN_STOCK = auto()
    LOW_STOCK = auto()
    OUT_OF_STOCK = auto()
    ON_ORDER = auto()


class ProductionStatus(Enum):
    """Status of production processes."""

    PLANNED = auto()
    IN_PROGRESS = auto()
    COMPLETED = auto()
    CANCELLED = auto()


class TransactionType(Enum):
    """Types of inventory transactions."""

    PURCHASE = auto()
    SALE = auto()
    PRODUCTION = auto()
    TRANSFER = auto()
    ADJUSTMENT = auto()
    RETURN = auto()
    WASTAGE = auto()


class OrderStatus(Enum):
    """Order processing status."""

    NEW = auto()  # Added NEW status
    DRAFT = auto()
    PENDING = auto()
    PROCESSING = auto()
    SHIPPED = auto()
    DELIVERED = auto()
    CANCELLED = auto()


class PaymentStatus(Enum):
    """Payment processing status."""

    UNPAID = auto()
    PARTIAL = auto()
    PAID = auto()
    REFUNDED = auto()
