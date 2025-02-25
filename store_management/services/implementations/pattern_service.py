#!/usr/bin/env python3
# Path: pattern_service.py
"""
Pattern Service Implementation

Provides functionality for managing patterns, components, and pattern validation.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from sqlalchemy import or_

from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
from models.pattern import Pattern
from exceptions import ApplicationError, ValidationError

logger = logging.getLogger(__name__)


class PatternService(IPatternService):
    """
    Implementation of pattern management service.

    Provides operations for managing patterns, their components, and related functionality.
    """

    def __init__(self, session_factory):
        """
        Initialize service with database session factory.

        Args:
            session_factory: SQLAlchemy session factory
        """
        self.session_factory = session_factory

    def get_all_patterns(self) -> List[Pattern]:
        """
        Get all patterns.

        Returns:
            List[Pattern]: A list of all patterns

        Raises:
            ApplicationError: If an error occurs during retrieval
        """
        try:
            with self.session_factory() as session:
                return session.query(Pattern).all()
        except Exception as e:
            logger.error(f'Failed to get patterns: {str(e)}')
            raise ApplicationError('Failed to retrieve patterns', str(e))

    def get_pattern_by_id(self, pattern_id: int) -> Optional[Pattern]:
        """
        Get pattern by ID.

        Args:
            pattern_id (int): The ID of the pattern to retrieve

        Returns:
            Optional[Pattern]: The pattern if found, None otherwise

        Raises:
            ApplicationError: If an error occurs during retrieval
        """
        try:
            with self.session_factory() as session:
                return session.query(Pattern).filter(Pattern.id == pattern_id).first()
        except Exception as e:
            logger.error(f'Failed to get pattern {pattern_id}: {str(e)}')
            raise ApplicationError(f'Failed to retrieve pattern {pattern_id}', str(e))