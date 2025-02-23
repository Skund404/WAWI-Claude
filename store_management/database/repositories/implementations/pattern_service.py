# database/repositories/implementations/pattern_repository.py
"""
Pattern Repository Implementation for Leatherworking Store Management System.

This module provides concrete implementations for pattern-related database operations,
with a focus on leather-specific pattern management and validation.
"""

from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from database.models.pattern import Pattern
from database.models.enums import SkillLevel
from database.repositories.interfaces.pattern_repository import IPatternRepository
from database.repositories.interfaces.base_repository import IBaseRepository
from utils.error_handler import ApplicationError, ValidationError
from utils.logger import get_logger

logger = get_logger(__name__)


class PatternRepository(IPatternRepository, IBaseRepository):
    """
    Concrete implementation of Pattern Repository for leatherworking patterns.

    Provides methods for CRUD operations and specialized pattern queries.
    """

    def __init__(self, session: Session):
        """
        Initialize the Pattern Repository with a database session.

        Args:
            session (Session): SQLAlchemy database session
        """
        self._session = session

    def get_by_id(self, pattern_id: int) -> Pattern:
        """
        Retrieve a pattern by its unique identifier.

        Args:
            pattern_id (int): Unique identifier for the pattern

        Returns:
            Pattern: Retrieved pattern instance

        Raises:
            ApplicationError: If pattern is not found
        """
        try:
            pattern = self._session.query(Pattern).filter(Pattern.id == pattern_id).first()
            if not pattern:
                raise ApplicationError(f"Pattern with ID {pattern_id} not found")
            return pattern
        except Exception as e:
            logger.error(f"Error retrieving pattern: {e}")
            raise ApplicationError(f"Could not retrieve pattern: {e}")

    def get_by_skill_level(self, skill_level: SkillLevel) -> List[Pattern]:
        """
        Retrieve patterns matching a specific skill level.

        Args:
            skill_level (SkillLevel): Skill level enum

        Returns:
            List[Pattern]: List of patterns matching the skill level
        """
        try:
            return (self._session.query(Pattern)
                    .filter(Pattern.skill_level == skill_level)
                    .all())
        except Exception as e:
            logger.error(f"Error retrieving patterns by skill level: {e}")
            return []

    def get_with_components(self, pattern_id: int) -> Pattern:
        """
        Retrieve a pattern with its associated components.

        Args:
            pattern_id (int): Unique identifier for the pattern

        Returns:
            Pattern: Pattern with fully loaded components

        Raises:
            ApplicationError: If pattern is not found
        """
        try:
            pattern = (self._session.query(Pattern)
                       .filter(Pattern.id == pattern_id)
                       .options(joinedload(Pattern.components))
                       .first())

            if not pattern:
                raise ApplicationError(f"Pattern with ID {pattern_id} not found")

            return pattern
        except Exception as e:
            logger.error(f"Error retrieving pattern with components: {e}")
            raise ApplicationError(f"Could not retrieve pattern components: {e}")

    def search_by_criteria(self, criteria: Dict[str, Any]) -> List[Pattern]:
        """
        Search patterns using flexible criteria.

        Args:
            criteria (Dict[str, Any]): Search parameters

        Returns:
            List[Pattern]: Matching patterns
        """
        try:
            query = self._session.query(Pattern)

            # Build dynamic search conditions
            conditions = []
            if 'name' in criteria:
                conditions.append(Pattern.name.ilike(f"%{criteria['name']}%"))

            if 'skill_level' in criteria:
                conditions.append(Pattern.skill_level == criteria['skill_level'])

            if 'min_complexity' in criteria:
                conditions.append(Pattern.complexity >= criteria['min_complexity'])

            if conditions:
                query = query.filter(and_(*conditions))

            return query.all()
        except Exception as e:
            logger.error(f"Error searching patterns: {e}")
            return []

    def add(self, pattern: Pattern) -> Pattern:
        """
        Add a new pattern to the database.

        Args:
            pattern (Pattern): Pattern to be added

        Returns:
            Pattern: Added pattern with assigned ID

        Raises:
            ValidationError: If pattern validation fails
        """
        try:
            self._validate_pattern(pattern)
            self._session.add(pattern)
            self._session.commit()
            return pattern
        except ValidationError as ve:
            logger.warning(f"Pattern validation failed: {ve}")
            raise
        except Exception as e:
            self._session.rollback()
            logger.error(f"Error adding pattern: {e}")
            raise ApplicationError(f"Could not add pattern: {e}")

    def update(self, pattern: Pattern) -> Pattern:
        """
        Update an existing pattern.

        Args:
            pattern (Pattern): Pattern to be updated

        Returns:
            Pattern: Updated pattern

        Raises:
            ValidationError: If pattern validation fails
        """
        try:
            existing_pattern = self.get_by_id(pattern.id)
            self._validate_pattern(pattern)

            # Update individual attributes
            existing_pattern.name = pattern.name
            existing_pattern.skill_level = pattern.skill_level
            existing_pattern.complexity = pattern.complexity

            self._session.commit()
            return existing_pattern
        except ValidationError as ve:
            logger.warning(f"Pattern validation failed: {ve}")
            raise
        except Exception as e:
            self._session.rollback()
            logger.error(f"Error updating pattern: {e}")
            raise ApplicationError(f"Could not update pattern: {e}")

    def delete(self, pattern_id: int) -> bool:
        """
        Delete a pattern by its ID.

        Args:
            pattern_id (int): Unique identifier for the pattern

        Returns:
            bool: True if deletion was successful

        Raises:
            ApplicationError: If deletion fails
        """
        try:
            pattern = self.get_by_id(pattern_id)
            self._session.delete(pattern)
            self._session.commit()
            return True
        except Exception as e:
            self._session.rollback()
            logger.error(f"Error deleting pattern: {e}")
            raise ApplicationError(f"Could not delete pattern: {e}")

    def _validate_pattern(self, pattern: Pattern) -> None:
        """
        Validate pattern data before database operations.

        Args:
            pattern (Pattern): Pattern to validate

        Raises:
            ValidationError: If validation fails
        """
        errors = []

        if not pattern.name or len(pattern.name) < 3:
            errors.append("Pattern name must be at least 3 characters long")

        if pattern.complexity is None or pattern.complexity < 0:
            errors.append("Pattern complexity must be a non-negative number")

        if pattern.skill_level is None:
            errors.append("Skill level must be specified")

        if errors:
            raise ValidationError("\n".join(errors))