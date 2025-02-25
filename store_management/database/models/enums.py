# database/models/enums.py
"""
Enumeration definitions for the database models.
"""

from enum import Enum, auto

class ProjectStatus(str, Enum):
    """
    Enum representing different project statuses.
    """
    PLANNING = 'planning'
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'
    ON_HOLD = 'on_hold'
    CANCELLED = 'cancelled'

class SkillLevel(str, Enum):
    """
    Enum representing skill levels for projects.
    """
    BEGINNER = 'beginner'
    INTERMEDIATE = 'intermediate'
    ADVANCED = 'advanced'
    EXPERT = 'expert'

class ProjectType(str, Enum):
    """
    Enum representing different types of projects.
    """
    WALLET = 'wallet'
    BAG = 'bag'
    ACCESSORY = 'accessory'
    CUSTOM = 'custom'

def validate_project_status(status):
    """
    Validate a project status.

    Args:
        status: The status to validate

    Returns:
        bool: Whether the status is valid
    """
    return status in ProjectStatus.__members__