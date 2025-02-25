# File: database/models/types.py
import enum
from typing import Any

class MaterialType(enum.Enum):
    """
    Enum representing different types of materials.
    """
    LEATHER = 'Leather'
    THREAD = 'Thread'
    HARDWARE = 'Hardware'
    FABRIC = 'Fabric'
    OTHER = 'Other'


class MaterialQualityGrade(enum.Enum):
    """
    Enum representing material quality grades.
    """
    PREMIUM = 'Premium'
    HIGH = 'High'
    STANDARD = 'Standard'
    LOW = 'Low'