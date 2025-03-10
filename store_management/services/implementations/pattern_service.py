# services/implementations/pattern_service.py
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from di.core import inject
from sqlalchemy.orm import Session

from database.models.enums import SkillLevel
from database.repositories.component_repository import ComponentRepository
from database.repositories.material_repository import MaterialRepository
from database.repositories.pattern_repository import PatternRepository

from services.base_service import BaseService, NotFoundError, ValidationError
from services.interfaces.pattern_service import IPatternService


class PatternService(BaseService, IPatternService):
    """Implementation of the pattern service interface.

    This class provides functionality for managing patterns,
    including creation, retrieval, updating, and deletion.
    """

    @inject
    def __init__(
            self,
            session: Session,
            pattern_repository: PatternRepository,
            component_repository: ComponentRepository,
            material_repository: MaterialRepository
    ):
        """Initialize the PatternService with required repositories.

        Args:
            session: SQLAlchemy database session
            pattern_repository: Repository for pattern operations
            component_repository: Repository for component operations
            material_repository: Repository for material operations
        """
        super().__init__(session)
        self._logger = logging.getLogger(__name__)
        self._pattern_repository = pattern_repository
        self._component_repository = component_repository
        self._material_repository = material_repository

    def get_all_patterns(self) -> List[Dict[str, Any]]:
        """Get all patterns.

        Returns:
            List[Dict[str, Any]]: List of pattern dictionaries
        """
        self._logger.info("Retrieving all patterns")
        patterns = self._pattern_repository.get_all()
        return [self._to_dict(pattern) for pattern in patterns]

    def get_pattern_by_id(self, pattern_id: int) -> Dict[str, Any]:
        """Get pattern by ID.

        Args:
            pattern_id: ID of the pattern

        Returns:
            Dict[str, Any]: Pattern dictionary

        Raises:
            NotFoundError: If pattern not found
        """
        self._logger.info(f"Retrieving pattern with ID: {pattern_id}")
        pattern = self._pattern_repository.get_by_id(pattern_id)
        if not pattern:
            self._logger.error(f"Pattern with ID {pattern_id} not found")
            raise NotFoundError(f"Pattern with ID {pattern_id} not found")
        return self._to_dict(pattern)

    def create_pattern(self, pattern_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new pattern.

        Args:
            pattern_data: Pattern data dictionary

        Returns:
            Dict[str, Any]: Created pattern dictionary

        Raises:
            ValidationError: If validation fails
        """
        self._logger.info("Creating new pattern")
        self._validate_pattern_data(pattern_data)

        try:
            pattern = self._pattern_repository.create(pattern_data)
            self._session.commit()
            self._logger.info(f"Created pattern with ID: {pattern.id}")
            return self._to_dict(pattern)
        except Exception as e:
            self._session.rollback()
            self._logger.error(f"Failed to create pattern: {str(e)}")
            raise ValidationError(f"Failed to create pattern: {str(e)}")

    def update_pattern(self, pattern_id: int, pattern_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing pattern.

        Args:
            pattern_id: ID of the pattern to update
            pattern_data: Updated pattern data

        Returns:
            Dict[str, Any]: Updated pattern dictionary

        Raises:
            NotFoundError: If pattern not found
            ValidationError: If validation fails
        """
        self._logger.info(f"Updating pattern with ID: {pattern_id}")
        pattern = self._pattern_repository.get_by_id(pattern_id)
        if not pattern:
            self._logger.error(f"Pattern with ID {pattern_id} not found")
            raise NotFoundError(f"Pattern with ID {pattern_id} not found")

        self._validate_pattern_data(pattern_data)

        try:
            updated_pattern = self._pattern_repository.update(pattern_id, pattern_data)
            self._session.commit()
            self._logger.info(f"Updated pattern with ID: {pattern_id}")
            return self._to_dict(updated_pattern)
        except Exception as e:
            self._session.rollback()
            self._logger.error(f"Failed to update pattern: {str(e)}")
            raise ValidationError(f"Failed to update pattern: {str(e)}")

    def delete_pattern(self, pattern_id: int) -> bool:
        """Delete a pattern.

        Args:
            pattern_id: ID of the pattern to delete

        Returns:
            bool: True if successful

        Raises:
            NotFoundError: If pattern not found
        """
        self._logger.info(f"Deleting pattern with ID: {pattern_id}")
        pattern = self._pattern_repository.get_by_id(pattern_id)
        if not pattern:
            self._logger.error(f"Pattern with ID {pattern_id} not found")
            raise NotFoundError(f"Pattern with ID {pattern_id} not found")

        try:
            self._pattern_repository.delete(pattern_id)
            self._session.commit()
            self._logger.info(f"Deleted pattern with ID: {pattern_id}")
            return True
        except Exception as e:
            self._session.rollback()
            self._logger.error(f"Failed to delete pattern: {str(e)}")
            raise ValidationError(f"Failed to delete pattern: {str(e)}")

    def get_patterns_by_skill_level(self, skill_level: str) -> List[Dict[str, Any]]:
        """Get patterns by skill level.

        Args:
            skill_level: Skill level to filter by

        Returns:
            List[Dict[str, Any]]: List of matching pattern dictionaries
        """
        self._logger.info(f"Retrieving patterns with skill level: {skill_level}")
        try:
            skill_level_enum = SkillLevel[skill_level.upper()]
            patterns = self._pattern_repository.get_by_skill_level(skill_level_enum)
            return [self._to_dict(pattern) for pattern in patterns]
        except KeyError:
            self._logger.warning(f"Invalid skill level: {skill_level}")
            return []

    def _validate_pattern_data(self, pattern_data: Dict[str, Any]) -> None:
        """Validate pattern data.

        Args:
            pattern_data: Pattern data to validate

        Raises:
            ValidationError: If validation fails
        """
        # Required fields
        required_fields = ['name', 'description']
        for field in required_fields:
            if field not in pattern_data:
                raise ValidationError(f"Missing required field: {field}")

        # Name length validation
        if len(pattern_data.get('name', '')) < 3:
            raise ValidationError("Pattern name must be at least 3 characters")

        # Skill level validation if provided
        if 'skill_level' in pattern_data:
            try:
                SkillLevel[pattern_data['skill_level'].upper()]
            except KeyError:
                raise ValidationError(f"Invalid skill level: {pattern_data['skill_level']}")

    def _to_dict(self, pattern) -> Dict[str, Any]:
        """Convert pattern model to dictionary.

        Args:
            pattern: Pattern model object

        Returns:
            Dict[str, Any]: Pattern dictionary
        """
        return {
            'id': pattern.id,
            'name': pattern.name,
            'description': pattern.description,
            'skill_level': pattern.skill_level.name if pattern.skill_level else None,
            'created_at': pattern.created_at.isoformat() if pattern.created_at else None,
            'updated_at': pattern.updated_at.isoformat() if pattern.updated_at else None,
            'components': [
                {
                    'id': component.id,
                    'name': component.name,
                    'component_type': component.component_type.name if component.component_type else None
                }
                for component in getattr(pattern, 'components', [])
            ]
        }