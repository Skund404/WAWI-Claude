# database/repositories/pattern_repository.py
"""
Repository for managing Pattern entities.

This repository handles database operations for the Pattern model, including
creation, retrieval, update, and deletion of patterns.
"""

import logging
from typing import Any, Dict, List, Optional, Union, Tuple

from sqlalchemy import and_, or_, func
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError

from database.models.pattern import Pattern
from database.models.enums import SkillLevel
from database.repositories.base_repository import BaseRepository
from database.exceptions import DatabaseError, ModelNotFoundError

# Setup logger
logger = logging.getLogger(__name__)


class PatternRepository(BaseRepository[Pattern]):
    """Repository for managing Pattern entities."""

    def __init__(self, session: Session) -> None:
        """
        Initialize the Pattern Repository.

        Args:
            session (Session): SQLAlchemy database session
        """
        super().__init__(session, Pattern)
        logger.debug("PatternRepository initialized")

    def get_by_name(self, name: str) -> Optional[Pattern]:
        """
        Get a pattern by name.

        Args:
            name (str): The pattern name to search for

        Returns:
            Optional[Pattern]: The pattern if found, None otherwise
        """
        try:
            pattern = self.session.query(Pattern).filter(Pattern.name == name).first()
            return pattern
        except SQLAlchemyError as e:
            error_msg = f"Error retrieving pattern by name '{name}': {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(error_msg)

    def get_by_skill_level(self, skill_level: SkillLevel) -> List[Pattern]:
        """
        Get patterns by skill level.

        Args:
            skill_level (SkillLevel): The skill level to filter by

        Returns:
            List[Pattern]: List of patterns matching the skill level
        """
        try:
            query = self.session.query(Pattern).filter(Pattern.skill_level == skill_level)
            patterns = query.all()
            logger.debug(f"Retrieved {len(patterns)} patterns with skill level {skill_level.name}")
            return patterns
        except SQLAlchemyError as e:
            error_msg = f"Error retrieving patterns by skill level '{skill_level.name}': {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(error_msg)

    def search_patterns(self,
                        search_term: Optional[str] = None,
                        skill_level: Optional[SkillLevel] = None,
                        is_active: bool = True,
                        limit: int = 100,
                        offset: int = 0) -> Tuple[List[Pattern], int]:
        """
        Search for patterns with filtering capabilities.

        Args:
            search_term (Optional[str]): Text to search in name and description
            skill_level (Optional[SkillLevel]): Skill level to filter by
            is_active (bool): Whether to include only active patterns
            limit (int): Maximum number of patterns to return
            offset (int): Number of patterns to skip for pagination

        Returns:
            Tuple[List[Pattern], int]: List of matching patterns and total count
        """
        try:
            # Start with base query
            query = self.session.query(Pattern)
            count_query = self.session.query(func.count(Pattern.id))

            # Apply filters
            if search_term:
                search_filter = or_(
                    Pattern.name.ilike(f"%{search_term}%"),
                    Pattern.description.ilike(f"%{search_term}%")
                )
                query = query.filter(search_filter)
                count_query = count_query.filter(search_filter)

            if skill_level:
                query = query.filter(Pattern.skill_level == skill_level)
                count_query = count_query.filter(Pattern.skill_level == skill_level)

            query = query.filter(Pattern.is_active == is_active)
            count_query = count_query.filter(Pattern.is_active == is_active)

            # Get total count
            total_count = count_query.scalar()

            # Apply pagination
            query = query.order_by(Pattern.name)
            query = query.limit(limit).offset(offset)

            # Execute query
            patterns = query.all()
            logger.debug(f"Retrieved {len(patterns)} of {total_count} matching patterns")

            return patterns, total_count
        except SQLAlchemyError as e:
            error_msg = f"Error searching patterns: {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(error_msg)

    def get_patterns_with_products(self, include_inactive: bool = False) -> List[Pattern]:
        """
        Get all patterns with their associated products eagerly loaded.

        Args:
            include_inactive (bool): Whether to include inactive patterns

        Returns:
            List[Pattern]: List of patterns with products loaded
        """
        try:
            query = self.session.query(Pattern)

            if not include_inactive:
                query = query.filter(Pattern.is_active == True)

            # Eager load product associations
            query = query.options(joinedload(Pattern.products))

            patterns = query.all()
            logger.debug(f"Retrieved {len(patterns)} patterns with products")
            return patterns
        except SQLAlchemyError as e:
            error_msg = f"Error retrieving patterns with products: {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(error_msg)