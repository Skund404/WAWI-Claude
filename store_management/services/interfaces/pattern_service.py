# store_management/services/interfaces/pattern_service.py
"""
Interface for Pattern Service in Leatherworking Store Management.

Defines the contract for pattern-related operations.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional

from di.core import inject
from utils.circular_import_resolver import CircularImportResolver

class PatternStatus(Enum):
    """
    Enumeration of possible pattern statuses.
    """
    DRAFT = "Draft"
    IN_PROGRESS = "In Progress"
    COMPLETE = "Complete"
    PUBLISHED = "Published"
    ARCHIVED = "Archived"

class IPatternService(ABC):
    """
    Abstract base class defining the interface for pattern-related operations.
    """

    @abstractmethod
    @inject('IMaterialService')
    def create_pattern(
        self,
        name: str,
        description: Optional[str] = None,
        skill_level: Optional[str] = None,
        material_service: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Create a new pattern.

        Args:
            name (str): Name of the pattern
            description (Optional[str], optional): Detailed description of the pattern
            skill_level (Optional[str], optional): Skill level required for the pattern
            material_service (Optional[Any], optional): Material service for pattern creation

        Returns:
            Dict[str, Any]: Details of the created pattern
        """
        pass

    @abstractmethod
    def update_pattern(
        self,
        pattern_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update an existing pattern.

        Args:
            pattern_id (str): Unique identifier of the pattern
            updates (Dict[str, Any]): Dictionary of fields to update

        Returns:
            Dict[str, Any]: Updated pattern details
        """
        pass

    @abstractmethod
    def get_pattern(
        self,
        pattern_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific pattern by its ID.

        Args:
            pattern_id (str): Unique identifier of the pattern

        Returns:
            Optional[Dict[str, Any]]: Pattern details, or None if not found
        """
        pass

    @abstractmethod
    def list_patterns(
        self,
        status: Optional[PatternStatus] = None,
        skill_level: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List patterns with optional filtering.

        Args:
            status (Optional[PatternStatus], optional): Filter by pattern status
            skill_level (Optional[str], optional): Filter by skill level

        Returns:
            List[Dict[str, Any]]: List of patterns matching the criteria
        """
        pass

    @abstractmethod
    def delete_pattern(
        self,
        pattern_id: str
    ) -> bool:
        """
        Delete a pattern.

        Args:
            pattern_id (str): Unique identifier of the pattern to delete

        Returns:
            bool: True if deletion was successful, False otherwise
        """
        pass