# database/models/enums.py
"""
Enumeration classes for the leatherworking store management system.

This module defines all the enum types used throughout the application.
"""

import enum
from typing import Dict, Any, List


class OrderStatus(enum.Enum):
    """Enumeration of order statuses."""
    NEW = "new"
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    RETURNED = "returned"

class PickingListStatus(enum.Enum):
    """Enumeration of picking list status values."""
    DRAFT = "draft"              # Initial state when created
    IN_PROGRESS = "in_progress"  # Picking has started
    COMPLETED = "completed"      # All items have been picked
    CANCELLED = "cancelled"      # Picking list cancelled

class MaterialType(enum.Enum):
    """Enumeration of material types."""
    LEATHER = "leather"
    THREAD = "thread"
    HARDWARE = "hardware"
    ADHESIVE = "adhesive"
    DYE = "dye"
    FINISH = "finish"
    TOOL = "tool"
    OTHER = "other"


class LeatherType(enum.Enum):
    """Enumeration of leather types."""
    FULL_GRAIN = "full_grain"
    TOP_GRAIN = "top_grain"
    CORRECTED_GRAIN = "corrected_grain"
    SPLIT = "split"
    NUBUCK = "nubuck"
    SUEDE = "suede"
    EXOTIC = "exotic"
    VEGETABLE_TANNED = "vegetable_tanned"
    CHROME_TANNED = "chrome_tanned"


class MaterialQualityGrade(enum.Enum):
    """Enumeration of material quality grades."""
    PREMIUM = "premium"
    STANDARD = "standard"
    ECONOMY = "economy"
    SECONDS = "seconds"
    SCRAP = "scrap"


class InventoryStatus(enum.Enum):
    """Enumeration of inventory status values."""
    IN_STOCK = "in_stock"
    LOW_STOCK = "low_stock"
    OUT_OF_STOCK = "out_of_stock"
    DISCONTINUED = "discontinued"
    ON_ORDER = "on_order"


class ProjectType(enum.Enum):
    """Enumeration of project types."""
    WALLET = "wallet"
    BAG = "bag"
    BELT = "belt"
    NOTEBOOK_COVER = "notebook_cover"
    WATCH_STRAP = "watch_strap"
    HOLSTER = "holster"
    CUSTOM = "custom"
    OTHER = "other"


class SkillLevel(enum.Enum):
    """Enumeration of skill levels required for projects."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class ProjectStatus(enum.Enum):
    """Enumeration of project status values."""
    NEW = "new"                       # Project is newly created
    PLANNING = "planning"             # In planning phase
    MATERIAL_SELECTION = "material_selection"  # Selecting materials
    CUTTING = "cutting"               # Cutting materials
    ASSEMBLY = "assembly"             # Assembling components
    STITCHING = "stitching"           # Stitching components
    FINISHING = "finishing"           # Applying finishes
    HARDWARE_INSTALLATION = "hardware_installation"  # Installing hardware
    QUALITY_CHECK = "quality_check"   # Quality checking
    COMPLETED = "completed"           # Project is complete
    ON_HOLD = "on_hold"               # Project is on hold
    CANCELLED = "cancelled"           # Project is cancelled


class SupplierStatus(enum.Enum):
    """Enumeration of supplier status values."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    BLACKLISTED = "blacklisted"


class StorageLocationType(enum.Enum):
    """Enumeration of storage location types."""
    SHELF = "shelf"
    BIN = "bin"
    DRAWER = "drawer"
    CABINET = "cabinet"
    RACK = "rack"
    BOX = "box"
    OTHER = "other"


class MeasurementUnit(enum.Enum):
    """Enumeration of measurement units."""
    PIECE = "piece"
    METER = "meter"
    SQUARE_METER = "square_meter"
    SQUARE_FOOT = "square_foot"
    KILOGRAM = "kilogram"
    GRAM = "gram"
    LITER = "liter"
    MILLILITER = "milliliter"
    YARD = "yard"
    INCH = "inch"
    FOOT = "foot"


class Priority(enum.Enum):
    """Enumeration of priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"


class TransactionType(enum.Enum):
    """Enumeration of transaction types."""
    PURCHASE = "purchase"
    USAGE = "usage"
    ADJUSTMENT = "adjustment"
    RETURN = "return"
    WASTE = "waste"
    TRANSFER = "transfer"


class QualityCheckStatus(enum.Enum):
    """Enumeration of quality check status values."""
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"
    CONDITIONALLY_PASSED = "conditionally_passed"


class PaymentStatus(enum.Enum):
    """Enumeration of payment status values."""
    PENDING = "pending"
    PAID = "paid"
    PARTIALLY_PAID = "partially_paid"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"