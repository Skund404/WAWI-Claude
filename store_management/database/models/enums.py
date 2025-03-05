# database/models/enums.py
"""
Comprehensive Enumeration classes for the leatherworking store management system.

This module defines all enum types used throughout the application,
covering various aspects of the business from hardware to project management.
"""

import enum
from enum import Enum, auto
from typing import Dict, Any, List

# Order and Project Status Enums
class OrderStatus(enum.Enum):
    """Detailed enumeration of order statuses for custom leatherwork."""
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

class PaymentStatus(enum.Enum):
    """Payment status for orders and transactions."""
    PENDING = "pending"
    PAID = "paid"
    PARTIALLY_PAID = "partially_paid"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"

# Customer-related Enums
class CustomerStatus(enum.Enum):
    """Represents the current status of a customer in the system."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"
    POTENTIAL = "potential"

class CustomerTier(enum.Enum):
    """Represents different customer loyalty or spending tiers."""
    STANDARD = "standard"
    PREMIUM = "premium"
    VIP = "vip"
    NEW = "new"

class CustomerSource(enum.Enum):
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

# Hardware-related Enums
class HardwareType(enum.Enum):
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

class HardwareMaterial(enum.Enum):
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

class HardwareFinish(enum.Enum):
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

# Existing Enums from the previous implementation
class PickingListStatus(enum.Enum):
    """Enumeration of picking list status values."""
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

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

class ShoppingListStatus(enum.Enum):
    """Status values for shopping lists."""
    DRAFT = 'draft'
    ACTIVE = 'active'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'

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

class ComponentType(enum.Enum):
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

class ProjectType(enum.Enum):
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

class LeatherType(enum.Enum):
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

class LeatherFinish(enum.Enum):
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

class ProjectStatus(enum.Enum):
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

class ToolCategory(enum.Enum):
    """Categorization of leatherworking tools."""
    CUTTING = "cutting"
    PUNCHING = "punching"
    STITCHING = "stitching"
    MEASURING = "measuring"
    FINISHING = "finishing"
    EDGE_WORK = "edge_work"
    DYEING = "dyeing"
    CONDITIONING = "conditioning"
    HARDWARE_INSTALLATION = "hardware_installation"
    PATTERN_MAKING = "pattern_making"

class MaterialType(enum.Enum):
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

class SkillLevel(enum.Enum):
    """Skill levels for leatherworking techniques and projects."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    MASTER = "master"
    EXPERT = "expert"

class QualityGrade(enum.Enum):
    """Detailed quality grading for leatherwork."""
    PREMIUM = "premium"
    PROFESSIONAL = "professional"
    STANDARD = "standard"
    WORKSHOP = "workshop"
    PROTOTYPE = "prototype"
    PRACTICE = "practice"

class EdgeFinishType(str, Enum):
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

    def __len__(self):
        return len(self.value)