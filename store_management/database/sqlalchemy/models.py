# File: database/sqlalchemy/models/enums.py
# Purpose: Centralized enum definitions for database models

from enum import Enum, auto

class InventoryStatus(Enum):
    """
    Inventory status for parts and materials.
    """
    IN_STOCK = auto()
    LOW_STOCK = auto()
    OUT_OF_STOCK = auto()
    RESERVED = auto()

class OrderStatus(Enum):
    """
    Order processing status.
    """
    PENDING = auto()
    CONFIRMED = auto()
    PROCESSING = auto()
    SHIPPED = auto()
    DELIVERED = auto()
    CANCELLED = auto()

class PaymentStatus(Enum):
    """
    Payment processing status.
    """
    PENDING = auto()
    PAID = auto()
    PARTIAL = auto()
    REFUNDED = auto()
    FAILED = auto()

class TransactionType(Enum):
    """
    Types of inventory transactions.
    """
    PURCHASE = auto()
    SALE = auto()
    TRANSFER = auto()
    ADJUSTMENT = auto()
    RETURN = auto()

class ProductionStatus(Enum):
    """
    Status of production processes.
    """
    PLANNED = auto()
    IN_PROGRESS = auto()
    COMPLETED = auto()
    HALTED = auto()
    QUALITY_CHECK = auto()