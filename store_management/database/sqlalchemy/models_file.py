# Relative path: store_management/database/sqlalchemy/models_file.py

"""
Centralized model configuration and exports.

This module provides a comprehensive list of models and their associated types,
serving as a central point for model-related definitions and exports.
"""

from enum import Enum, auto
from typing import List, Dict, Any, Type

class EnumBase(Enum):
    """
    Base enumeration with automatic value generation and additional utilities.
    """
    @classmethod
    def list(cls) -> List[str]:
        """
        Get a list of all enum values.

        Returns:
            List[str]: List of enum value names
        """
        return [item.name for item in cls]

    @classmethod
    def dict(cls) -> Dict[str, Any]:
        """
        Get a dictionary of enum values.

        Returns:
            Dict[str, Any]: Dictionary of enum name to value
        """
        return {item.name: item.value for item in cls}

# Define common enumerations used across models
class OrderStatus(EnumBase):
    """Represents the possible statuses of an order."""
    PENDING = auto()
    PROCESSING = auto()
    SHIPPED = auto()
    DELIVERED = auto()
    CANCELLED = auto()

class PaymentStatus(EnumBase):
    """Represents the possible payment statuses."""
    UNPAID = auto()
    PARTIAL = auto()
    PAID = auto()
    REFUNDED = auto()

class TransactionType(EnumBase):
    """Represents types of inventory transactions."""
    PURCHASE = auto()
    SALE = auto()
    TRANSFER = auto()
    ADJUSTMENT = auto()

class MaterialType(EnumBase):
    """Represents different types of materials."""
    RAW = auto()
    PROCESSED = auto()
    FINISHED = auto()

class LeatherType(EnumBase):
    """Represents different types of leather."""
    FULL_GRAIN = auto()
    TOP_GRAIN = auto()
    GENUINE = auto()
    SUEDE = auto()

class MaterialQualityGrade(EnumBase):
    """Represents material quality grades."""
    PREMIUM = auto()
    HIGH = auto()
    STANDARD = auto()
    LOW = auto()

class InventoryStatus(EnumBase):
    """Represents inventory statuses."""
    IN_STOCK = auto()
    LOW_STOCK = auto()
    OUT_OF_STOCK = auto()
    RESERVED = auto()

class ProjectType(EnumBase):
    """Represents different types of projects."""
    CUSTOM = auto()
    STANDARD = auto()
    PROTOTYPE = auto()
    SAMPLE = auto()

class SkillLevel(EnumBase):
    """Represents skill levels for projects or employees."""
    BEGINNER = auto()
    INTERMEDIATE = auto()
    ADVANCED = auto()
    EXPERT = auto()

class ProjectStatus(EnumBase):
    """Represents the possible statuses of a project."""
    PLANNING = auto()
    IN_PROGRESS = auto()
    ON_HOLD = auto()
    COMPLETED = auto()
    CANCELLED = auto()

class SupplierStatus(EnumBase):
    """Represents the possible statuses of a supplier."""
    ACTIVE = auto()
    INACTIVE = auto()
    SUSPENDED = auto()

class StorageLocationType(EnumBase):
    """Represents different types of storage locations."""
    WAREHOUSE = auto()
    WORKSHOP = auto()
    RETAIL = auto()
    EXTERNAL = auto()

class MeasurementUnit(EnumBase):
    """Represents standard measurement units."""
    METER = auto()
    SQUARE_METER = auto()
    KILOGRAM = auto()
    PIECE = auto()

class Priority(EnumBase):
    """Represents priority levels."""
    LOW = auto()
    MEDIUM = auto()
    HIGH = auto()
    URGENT = auto()

class QualityCheckStatus(EnumBase):
    """Represents quality check statuses."""
    PENDING = auto()
    IN_PROGRESS = auto()
    PASSED = auto()
    FAILED = auto()

# Export all enumerations
__all__ = [
    'OrderStatus', 'PaymentStatus', 'TransactionType', 'MaterialType',
    'LeatherType', 'MaterialQualityGrade', 'InventoryStatus', 'ProjectType',
    'SkillLevel', 'ProjectStatus', 'SupplierStatus', 'StorageLocationType',
    'MeasurementUnit', 'Priority', 'QualityCheckStatus'
]