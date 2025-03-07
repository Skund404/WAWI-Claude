# database/models/base.py
"""
Base Model Definition for Leatherworking Management System

This module defines the base model class used throughout the application,
providing common attributes and behaviors for all models.
"""

import logging
import re
import uuid
import enum
from datetime import datetime
from typing import Dict, Any, Optional, List

from sqlalchemy import Boolean, Column, DateTime, Integer, String, MetaData, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import declared_attr

from database.models.model_metaclass import BaseModelMetaclass

# Setup logger
logger = logging.getLogger(__name__)


# Define exceptions
class ModelValidationError(Exception):
    """Exception raised for model validation errors."""
    pass


# Create a declarative base with our metaclass
Base = declarative_base(metaclass=BaseModelMetaclass)


# Set common attributes and methods for all models
class Base:
    """
    Base class for all SQLAlchemy models in the system.
    Provides common attributes and functionality.
    """
    __abstract__ = True

    # Table configuration for flexibility
    __table_args__ = {
        'extend_existing': True,
        'sqlite_autoincrement': True
    }

    # Core primary key
    id = Column(Integer, primary_key=True)

    # Soft delete support
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    # Unique identifier for tracking
    uuid = Column(
        String(36),
        unique=True,
        nullable=False,
        default=lambda: str(uuid.uuid4())
    )

    @classmethod
    def initialize_relationships(cls):
        """
        Placeholder method for model-specific relationship initialization.
        Can be overridden in subclasses to define complex relationships.
        """
        pass

    @declared_attr
    def __tablename__(cls) -> str:
        """
        Generate table name automatically from class name.
        Convert CamelCase or PascalCase to snake_case and pluralize.
        """
        # Convert camelCase or PascalCase to snake_case
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', cls.__name__)
        s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

        # Pluralize with simple approach
        return f"{s2}s" if not s2.endswith('s') else s2

    @classmethod
    def validate(cls, data: Dict[str, Any]) -> bool:
        """
        Generic validation method that can be overridden by subclasses.

        Args:
            data: Dictionary of model attributes to validate

        Returns:
            bool: Whether the data is valid
        """
        return all(value is not None for value in data.values())

    def to_dict(self, exclude_fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Convert model instance to a dictionary representation.

        Args:
            exclude_fields: Optional list of fields to exclude

        Returns:
            Dictionary representation of the model instance
        """
        exclude_fields = exclude_fields or []
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
            if column.name not in exclude_fields
        }

    def soft_delete(self) -> None:
        """
        Perform a soft delete by marking the record as deleted.
        """
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
        logger.info(f"Soft deleted {self.__class__.__name__} with ID {self.id}")

    def restore(self) -> None:
        """
        Restore a soft-deleted record.
        """
        self.is_deleted = False
        self.deleted_at = None
        logger.info(f"Restored {self.__class__.__name__} with ID {self.id}")


def initialize_all_model_relationships():
    """
    Global function to initialize all model relationships.
    Serves as a centralized entry point for relationship configuration.
    """
    if hasattr(BaseModelMetaclass, 'initialize_all_relationships'):
        BaseModelMetaclass.initialize_all_relationships()
    else:
        logger.warning("BaseModelMetaclass doesn't have initialize_all_relationships method")