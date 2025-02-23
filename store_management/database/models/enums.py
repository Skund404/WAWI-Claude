# database/models/enums.py

from enum import Enum, auto

class ProjectType(Enum):
    """Types of projects that can be created."""
    BASIC = auto()
    INTERMEDIATE = auto()
    ADVANCED = auto()
    CUSTOM = auto()

class ProjectStatus(Enum):
    """Status states for projects."""
    PLANNED = auto()
    IN_PROGRESS = auto()
    ON_HOLD = auto()
    COMPLETED = auto()
    CANCELLED = auto()

class SkillLevel(Enum):
    """Required skill levels for projects."""
    BEGINNER = 1
    INTERMEDIATE = 2
    ADVANCED = 3
    EXPERT = 4

class MaterialType(Enum):
    """Types of materials used in projects."""
    LEATHER = auto()
    HARDWARE = auto()
    THREAD = auto()
    ADHESIVE = auto()
    FINISH = auto()
    OTHER = auto()

class InventoryStatus(Enum):
    """Status of inventory items."""
    IN_STOCK = auto()
    LOW_STOCK = auto()
    OUT_OF_STOCK = auto()
    DISCONTINUED = auto()

class TransactionType(Enum):
    """Types of inventory transactions."""
    PURCHASE = auto()
    USAGE = auto()
    ADJUSTMENT = auto()
    WASTE = auto()
    RETURN = auto()

class MeasurementUnit(Enum):
    """Units of measurement."""
    PIECE = auto()
    SQUARE_FOOT = auto()
    SQUARE_METER = auto()
    LINEAR_FOOT = auto()
    LINEAR_METER = auto()
    GRAM = auto()
    KILOGRAM = auto()
    OUNCE = auto()
    POUND = auto()

class StitchType(Enum):
    """Types of stitches used in leatherworking."""
    SADDLE = auto()
    RUNNING = auto()
    CROSS = auto()
    BOX = auto()
    BACKSTITCH = auto()

class EdgeFinishType(Enum):
    """Types of edge finishing techniques."""
    BURNISHED = auto()
    PAINTED = auto()
    CREASED = auto()
    WAX_FINISHED = auto()
    RAW = auto()

class ComponentType(Enum):
    """Types of components in a leather pattern."""
    LEATHER = auto()        # Main leather pieces
    LINING = auto()         # Leather or fabric lining
    REINFORCEMENT = auto()  # Hidden reinforcement pieces
    GUSSET = auto()        # Expandable sections
    POCKET = auto()        # Interior or exterior pockets
    STRAP = auto()         # Straps or handles
    HARDWARE_MOUNT = auto() # Areas for hardware attachment
    DECORATIVE = auto()    # Decorative elements

class LeatherType(Enum):
    """Types of leather materials."""
    FULL_GRAIN = auto()
    TOP_GRAIN = auto()
    CORRECTED_GRAIN = auto()
    SPLIT = auto()
    SUEDE = auto()
    NUBUCK = auto()
    PATENT = auto()
    EXOTIC = auto()

class MaterialQualityGrade(Enum):
    """Quality grades for leather materials."""
    GRADE_A = auto()  # Premium, minimal defects
    GRADE_B = auto()  # Good quality, minor defects
    GRADE_C = auto()  # Usable, visible defects
    SECONDS = auto()  # Significant defects, usable for non-visible parts