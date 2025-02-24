# Path: database/models/enums.py
"""
Enumeration definitions for various model statuses and types.
"""

from enum import Enum, auto
from typing import Any

class ProjectStatus(Enum):
    """
    Enum representing different statuses of a project.
    """
    PLANNING = "Planning"
    IN_PROGRESS = "In Progress"
    ON_HOLD = "On Hold"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"

class SkillLevel(Enum):
    """
    Enum representing skill levels for projects.
    """
    BEGINNER = "Beginner"
    INTERMEDIATE = "Intermediate"
    ADVANCED = "Advanced"
    EXPERT = "Expert"

class ProjectType(Enum):
    """
    Enum representing different types of projects.
    """
    LEATHERWORKING = "Leatherworking"
    PROTOTYPING = "Prototyping"
    CUSTOM_ORDER = "Custom Order"
    RESEARCH_AND_DEVELOPMENT = "Research and Development"

class ProductionStatus(Enum):
    """
    Enum representing production statuses.
    """
    PENDING = "Pending"
    IN_PRODUCTION = "In Production"
    QUALITY_CHECK = "Quality Check"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"

class MaterialType(Enum):
    """
    Enum representing different types of materials.
    """
    LEATHER = "Leather"
    THREAD = "Thread"
    HARDWARE = "Hardware"
    ADHESIVE = "Adhesive"
    FABRIC = "Fabric"

class TransactionType(Enum):
    """
    Enum representing types of inventory transactions.
    """
    PURCHASE = "Purchase"
    SALE = "Sale"
    RETURN = "Return"
    ADJUSTMENT = "Adjustment"
    TRANSFER = "Transfer"

class OrderStatus(Enum):
    """
    Enum representing different order statuses.
    """
    PENDING = "Pending"
    PROCESSING = "Processing"
    SHIPPED = "Shipped"
    DELIVERED = "Delivered"
    CANCELLED = "Cancelled"

class PaymentStatus(Enum):
    """
    Enum representing payment statuses.
    """
    UNPAID = "Unpaid"
    PARTIALLY_PAID = "Partially Paid"
    PAID = "Paid"
    REFUNDED = "Refunded"

class ShoppingListStatus(Enum):
    """
    Enum representing shopping list statuses.
    """
    ACTIVE = "Active"
    COMPLETED = "Completed"
    ARCHIVED = "Archived"

class StitchType(Enum):
    """
    Enum representing different stitch types.
    """
    LOCK_STITCH = "Lock Stitch"
    CHAIN_STITCH = "Chain Stitch"
    SADDLE_STITCH = "Saddle Stitch"
    WHIP_STITCH = "Whip Stitch"

class EdgeFinishType(Enum):
    """
    Enum representing different edge finishing techniques.
    """
    BURNISHED = "Burnished"
    PAINTED = "Painted"
    FOLDED = "Folded"
    RAW = "Raw"
    SEALED = "Sealed"