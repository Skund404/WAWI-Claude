# database/models/hardware_enums.py
"""
Enum definitions for hardware types, materials, and finishes.
These are used for categorizing and filtering hardware items.
"""

from enum import Enum

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