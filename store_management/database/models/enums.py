# database/models/enums.py
"""
Comprehensive Enumeration classes for the leatherworking store management system.

This module defines all enum types used throughout the application,
covering various aspects of the business from sales to project management.
"""

import enum
from enum import Enum, auto
from typing import Dict, Any, List


# Sales and Order Management Enums
class SaleStatus(Enum):
    """Detailed enumeration of sale statuses for custom leatherwork."""
    QUOTE_REQUEST = "quote_request"
    DESIGN_CONSULTATION = "design_consultation"
    DESIGN_APPROVAL = "design_approval"
    MATERIALS_SOURCING = "materials_sourcing"
    DEPOSIT_RECEIVED = "deposit_received"
    IN_PRODUCTION = "in_production"
    QUALITY_REVIEW = "quality_review"
    READY_FOR_PICKUP = "ready_for_pickup"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    # Additional statuses for backward compatibility
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"


# Alias for SaleStatus to maintain compatibility with existing code
SalesStatus = SaleStatus


class PaymentStatus(Enum):
    """Payment status for orders and transactions."""
    PENDING = "pending"
    PAID = "paid"
    PARTIALLY_PAID = "partially_paid"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class PurchaseStatus(Enum):
    """Status values for purchase orders from suppliers."""
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    # Additional statuses for backward compatibility
    DRAFT = "draft"
    ORDERED = "ordered"
    PARTIALLY_RECEIVED = "partially_received"
    RECEIVED = "received"


# Customer-related Enums
class CustomerStatus(Enum):
    """Represents the current status of a customer in the system."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"
    POTENTIAL = "potential"
    # Additional status for backward compatibility
    BLOCKED = "blocked"
    LEAD = "lead"


class CustomerTier(Enum):
    """Represents different customer loyalty or spending tiers."""
    STANDARD = "standard"
    PREMIUM = "premium"
    VIP = "vip"
    NEW = "new"
    # Additional tiers for backward compatibility
    WHOLESALE = "wholesale"


class CustomerSource(Enum):
    """Represents the source or channel through which the customer was acquired."""
    WEBSITE = "website"
    RETAIL = "retail"
    REFERRAL = "referral"
    MARKETING = "marketing"
    SOCIAL_MEDIA = "social_media"
    TRADE_SHOW = "trade_show"
    WORD_OF_MOUTH = "word_of_mouth"
    EMAIL_CAMPAIGN = "email_campaign"
    OTHER = "other"
    # Additional sources for backward compatibility
    EXHIBITION = "exhibition"
    DIRECT = "direct"


# Inventory and Material Management Enums
class InventoryStatus(Enum):
    """Enumeration of inventory status values."""
    IN_STOCK = "in_stock"
    LOW_STOCK = "low_stock"
    OUT_OF_STOCK = "out_of_stock"
    DISCONTINUED = "discontinued"
    ON_ORDER = "on_order"
    # Additional statuses for backward compatibility
    AVAILABLE = "available"
    RESERVED = "reserved"
    DAMAGED = "damaged"
    PENDING_ARRIVAL = "pending_arrival"
    QUARANTINE = "quarantine"


class MaterialType(Enum):
    """Comprehensive material types for leatherworking."""
    LEATHER = "leather"
    THREAD = "thread"
    HARDWARE = "hardware"
    LINING = "lining"
    INTERFACING = "interfacing"
    ADHESIVE = "adhesive"
    DYE = "dye"
    FINISH = "finish"
    EDGE_PAINT = "edge_paint"
    WAX = "wax"
    RIVETS = "rivets"
    BUCKLES = "buckles"
    ZIPPERS = "zippers"
    SNAPS = "snaps"
    ELASTIC = "elastic"
    PADDING = "padding"
    OTHER = "other"
    # Additional types for backward compatibility
    EDGE_COAT = "edge_coat"


# For backward compatibility
MaterialQualityGrade = Enum('MaterialQualityGrade', [
    ('PREMIUM', 'premium'),
    ('STANDARD', 'standard'),
    ('ECONOMY', 'economy'),
    ('SECONDS', 'seconds'),
    ('SCRAP', 'scrap')
])


# Hardware-related Enums
class HardwareType(Enum):
    """Types of hardware used in leatherworking projects."""
    BUCKLE = "buckle"
    SNAP = "snap"
    RIVET = "rivet"
    ZIPPER = "zipper"
    CLASP = "clasp"
    BUTTON = "button"
    D_RING = "d_ring"
    O_RING = "o_ring"
    MAGNETIC_CLOSURE = "magnetic_closure"
    KEY_RING = "key_ring"
    CONCHO = "concho"
    EYELET = "eyelet"
    GROMMET = "grommet"
    HOOK = "hook"
    STUD = "stud"
    SCREW = "screw"
    LOCK = "lock"
    PLATE = "plate"
    CORNER = "corner"
    OTHER = "other"
    # Additional types for backward compatibility
    CORNER_PROTECTOR = "corner_protector"


class HardwareMaterial(Enum):
    """Materials that hardware items can be made of."""
    BRASS = "brass"
    STEEL = "steel"
    STAINLESS_STEEL = "stainless_steel"
    NICKEL = "nickel"
    SILVER = "silver"
    GOLD = "gold"
    BRONZE = "bronze"
    ALUMINUM = "aluminum"
    COPPER = "copper"
    ZINC = "zinc"
    PEWTER = "pewter"
    TITANIUM = "titanium"
    PLASTIC = "plastic"
    NYLON = "nylon"
    CARBON_FIBER = "carbon_fiber"
    WOOD = "wood"
    CERAMIC = "ceramic"
    OTHER = "other"


class HardwareFinish(Enum):
    """Finishes that can be applied to hardware items."""
    POLISHED = "polished"
    BRUSHED = "brushed"
    ANTIQUE = "antique"
    MATTE = "matte"
    CHROME = "chrome"
    NICKEL_PLATED = "nickel_plated"
    BRASS_PLATED = "brass_plated"
    GOLD_PLATED = "gold_plated"
    BLACK_OXIDE = "black_oxide"
    PAINTED = "painted"
    POWDER_COATED = "powder_coated"
    COPPER_PLATED = "copper_plated"
    SATIN = "satin"
    NATURAL = "natural"
    DISTRESSED = "distressed"
    HAMMERED = "hammered"
    PATINA = "patina"
    GALVANIZED = "galvanized"
    ANODIZED = "anodized"
    OTHER = "other"


# Leather-related Enums
class LeatherType(Enum):
    """Extensive enumeration of leather types and characteristics."""
    # Tanning Methods
    VEGETABLE_TANNED = "vegetable_tanned"
    CHROME_TANNED = "chrome_tanned"
    BRAIN_TANNED = "brain_tanned"
    OIL_TANNED = "oil_tanned"

    # Leather Grades
    FULL_GRAIN = "full_grain"
    TOP_GRAIN = "top_grain"
    CORRECTED_GRAIN = "corrected_grain"
    SPLIT = "split"

    # Specialty Leathers
    NUBUCK = "nubuck"
    SUEDE = "suede"
    SHELL_CORDOVAN = "shell_cordovan"
    EXOTIC = "exotic"

    # Animal Sources
    COWHIDE = "cowhide"
    CALFSKIN = "calfskin"
    GOATSKIN = "goatskin"
    SHEEPSKIN = "sheepskin"
    PIGSKIN = "pigskin"
    HORSE = "horse"
    BUFFALO = "buffalo"
    KANGAROO = "kangaroo"

    # Additional types for backward compatibility
    SYNTHETIC = "synthetic"


class LeatherFinish(Enum):
    """Detailed enumeration of leather finishing techniques."""
    ANILINE = "aniline"
    SEMI_ANILINE = "semi_aniline"
    PIGMENTED = "pigmented"
    WAX_PULL_UP = "wax_pull_up"
    OIL_PULL_UP = "oil_pull_up"
    BURNISHED = "burnished"
    DISTRESSED = "distressed"
    PATENT = "patent"
    NAPPA = "nappa"


# Product and Project Management Enums
class ProjectType(Enum):
    """Comprehensive enumeration of leatherworking project types."""
    WALLET = "wallet"
    BRIEFCASE = "briefcase"
    MESSENGER_BAG = "messenger_bag"
    TOTE_BAG = "tote_bag"
    BACKPACK = "backpack"
    BELT = "belt"
    WATCH_STRAP = "watch_strap"
    NOTEBOOK_COVER = "notebook_cover"
    PHONE_CASE = "phone_case"
    LAPTOP_SLEEVE = "laptop_sleeve"
    CAMERA_STRAP = "camera_strap"
    HOLSTER = "holster"
    DOG_COLLAR = "dog_collar"
    LUGGAGE_TAG = "luggage_tag"
    CARD_HOLDER = "card_holder"
    KEY_CASE = "key_case"
    TOOL_ROLL = "tool_roll"
    GUITAR_STRAP = "guitar_strap"
    CUSTOM = "custom"
    OTHER = "other"
    # Additional types for backward compatibility
    PRODUCTION = "production"
    PROTOTYPE = "prototype"
    REPAIR = "repair"
    SAMPLE = "sample"


class ProjectStatus(Enum):
    """Detailed project status for custom leatherwork."""
    INITIAL_CONSULTATION = "initial_consultation"
    DESIGN_PHASE = "design_phase"
    PATTERN_DEVELOPMENT = "pattern_development"
    CLIENT_APPROVAL = "client_approval"
    MATERIAL_SELECTION = "material_selection"
    MATERIAL_PURCHASED = "material_purchased"
    CUTTING = "cutting"
    SKIVING = "skiving"
    PREPARATION = "preparation"
    ASSEMBLY = "assembly"
    STITCHING = "stitching"
    EDGE_FINISHING = "edge_finishing"
    HARDWARE_INSTALLATION = "hardware_installation"
    CONDITIONING = "conditioning"
    QUALITY_CHECK = "quality_check"
    FINAL_TOUCHES = "final_touches"
    PHOTOGRAPHY = "photography"
    PACKAGING = "packaging"
    COMPLETED = "completed"
    ON_HOLD = "on_hold"
    CANCELLED = "cancelled"
    # Additional statuses for backward compatibility
    PLANNED = "planned"
    MATERIALS_READY = "materials_ready"
    IN_PROGRESS = "in_progress"


class SkillLevel(Enum):
    """Skill levels for leatherworking techniques and projects."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    MASTER = "master"
    EXPERT = "expert"


# Component-related Enums
class ComponentType(Enum):
    """Enumeration of component types used in patterns and projects."""
    LEATHER = "leather"
    HARDWARE = "hardware"
    LINING = "lining"
    THREAD = "thread"
    ADHESIVE = "adhesive"
    REINFORCEMENT = "reinforcement"
    EDGE_FINISH = "edge_finish"
    TEMPLATE = "template"
    TOOL = "tool"
    OTHER = "other"


# Tool-related Enums
class ToolCategory(enum.Enum):
    """Categorization of leatherworking tools."""
    CUTTING = "CUTTING"
    PUNCHING = "PUNCHING"
    STITCHING = "STITCHING"
    MEASURING = "MEASURING"
    FINISHING = "FINISHING"
    EDGE_WORK = "EDGE_WORK"
    DYEING = "DYEING"
    CONDITIONING = "CONDITIONING"
    HARDWARE_INSTALLATION = "HARDWARE_INSTALLATION"
    PATTERN_MAKING = "PATTERN_MAKING"


# For backward compatibility - ToolCategory is used in uppercase in some places and lowercase in others
ToolType = Enum('ToolType', [
    ('cutting', 'cutting'),
    ('punching', 'punching'),
    ('stitching', 'stitching'),
    ('edge_finishing', 'edge_finishing'),
    ('stamping', 'stamping'),
    ('measurement', 'measurement'),
    ('assembly', 'assembly'),
    ('other', 'other')
])


# Edge Finishing Enums
class EdgeFinishType(Enum):
    """Comprehensive edge finishing techniques for leatherwork."""
    BURNISHED = "burnished"
    PAINTED = "painted"
    RAW = "raw"
    BEVELED = "beveled"
    SEALED = "sealed"
    POLISHED = "polished"
    ROUGH = "rough"
    WAXED = "waxed"
    GLOSSY = "glossy"
    MATTE = "matte"


# Transaction and Inventory Management Enums
class TransactionType(Enum):
    """Enumeration of transaction types."""
    PURCHASE = "purchase"
    USAGE = "usage"
    ADJUSTMENT = "adjustment"
    RETURN = "return"
    WASTE = "waste"
    TRANSFER = "transfer"
    REVERSAL = "reversal"


class InventoryAdjustmentType(Enum):
    """Types of inventory adjustments."""
    INITIAL_STOCK = "initial_stock"
    RESTOCK = "restock"
    USAGE = "usage"
    DAMAGE = "damage"
    LOST = "lost"
    FOUND = "found"
    RETURN = "return"


# Supplier-related Enums
class SupplierStatus(Enum):
    """Enumeration of supplier status values."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    BLACKLISTED = "blacklisted"
    # Additional statuses for backward compatibility
    ON_HOLD = "on_hold"


# Storage-related Enums
class StorageLocationType(Enum):
    """Enumeration of storage location types."""
    SHELF = "shelf"
    BIN = "bin"
    DRAWER = "drawer"
    CABINET = "cabinet"
    RACK = "rack"
    BOX = "box"
    OTHER = "other"


# Measurement and Quality Enums
class MeasurementUnit(Enum):
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
    # Additional units for backward compatibility
    CENTIMETER = "centimeter"
    INCHES = "inches"
    FEET = "feet"
    OUNCE = "ounce"
    POUND = "pound"
    OTHER = "other"


class QualityGrade(Enum):
    """Detailed quality grading for leatherwork."""
    PREMIUM = "premium"
    PROFESSIONAL = "professional"
    STANDARD = "standard"
    WORKSHOP = "workshop"
    PROTOTYPE = "prototype"
    PRACTICE = "practice"
    # Additional grades for backward compatibility
    ECONOMY = "economy"
    SECONDS = "seconds"
    DAMAGED = "damaged"


class PickingListStatus(Enum):
    """
    Enumeration of picking list status values.
    Represents the current state of a picking list in the workflow.
    """
    DRAFT = "draft"
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ON_HOLD = "on_hold"


class ToolListStatus(Enum):
    """
    Enumeration of tool list status values.
    Represents the current state of a tool list in the workflow.
    """
    DRAFT = "draft"
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ON_HOLD = "on_hold"
    ACTIVE = "active"
    READY = "ready"
    IN_USE = "in_use"


class ComponentType(Enum):
    """
    Enumeration of component types used in patterns and projects.

    Represents the different categories of components that can be used
    in leatherworking patterns and project compositions.
    """
    # Basic material components
    LEATHER = auto()
    HARDWARE = auto()
    THREAD = auto()
    LINING = auto()
    REINFORCEMENT = auto()

    # Structural components
    TEMPLATE = auto()
    PATTERN_PIECE = auto()
    CUTOUT = auto()

    # Functional components
    FASTENER = auto()
    EDGE_FINISH = auto()
    STRAP = auto()
    POCKET = auto()
    CLOSURE = auto()

    # Decorative components
    EMBELLISHMENT = auto()
    LOGO = auto()
    TRIM = auto()

    # Specialized components
    PADDING = auto()
    REINFORCEMENT_STRIP = auto()
    BINDING = auto()

    # Catch-all for unique or custom components
    OTHER = auto()