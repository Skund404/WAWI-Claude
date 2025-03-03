# database/models/base.py
"""
Comprehensive base model for SQLAlchemy models with advanced utility methods.
"""

import enum
import uuid
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Type, TypeVar

from sqlalchemy import Column, Integer, String, DateTime, Boolean, inspect, event
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm import DeclarativeMeta, Mapper
from sqlalchemy.sql import func

from .mixins import TimestampMixin, ValidationMixin, CostingMixin, TrackingMixin

# Setup logging
logger = logging.getLogger(__name__)

T = TypeVar('T')


class ModelValidationError(Exception):
    """Custom exception for model validation errors."""
    pass


class BaseModelMixin(TimestampMixin, ValidationMixin, CostingMixin, TrackingMixin):
    """
    Enhanced base model mixin with comprehensive utility methods.
    """
    # Primary key
    id = Column(Integer, primary_key=True)

    # Soft delete support
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    # Unique identifier
    uuid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))

    @declared_attr
    def __tablename__(cls) -> str:
        """
        Generate table name automatically from class name.
        Convert CamelCase to snake_case and pluralize.

        Returns:
            str: Automatically generated table name
        """
        import re
        # Convert camelCase or PascalCase to snake_case
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', cls.__name__)
        s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

        # Pluralize (simple approach)
        return f"{s2}s" if not s2.endswith('s') else s2

    def to_dict(self, include_relationships: bool = False, exclude_fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Convert model instance to dictionary with advanced options.

        Args:
            include_relationships (bool): Whether to include relationship data
            exclude_fields (Optional[List[str]]): Fields to exclude from the output

        Returns:
            Dict[str, Any]: Dictionary representation of the model
        """
        # Implementation remains the same as in the original code
        ...

    def soft_delete(self) -> None:
        """
        Perform a soft delete by marking the record as deleted.
        """
        if not self.is_deleted:
            self.is_deleted = True
            self.deleted_at = datetime.utcnow()

    def restore(self) -> None:
        """
        Restore a soft-deleted record.
        """
        if self.is_deleted:
            self.is_deleted = False
            self.deleted_at = None

    @classmethod
    def create(cls: Type[T], **kwargs) -> T:
        """
        Class method to create a new instance with validation.

        Args:
            **kwargs: Keyword arguments for model instantiation

        Returns:
            T: New model instance

        Raises:
            ModelValidationError: If validation fails
        """
        # Implementation remains the same as in the original code
        ...

    @classmethod
    def _validate_creation(cls, data: Dict[str, Any]) -> None:
        """
        Validate data before creating an instance.
        Override in subclasses for specific validation.

        Args:
            data (Dict[str, Any]): Data to validate

        Raises:
            ModelValidationError: If validation fails
        """
        pass

    def _validate_instance(self) -> None:
        """
        Validate the model instance after creation.
        Override in subclasses for specific validation.

        Raises:
            ModelValidationError: If validation fails
        """
        pass

    def update(self, **kwargs) -> None:
        """
        Update model instance with provided keyword arguments.

        Args:
            **kwargs: Keyword arguments to update

        Raises:
            ModelValidationError: If update fails validation
        """
        # Implementation remains the same as in the original code
        ...

    def _validate_update(self, update_data: Dict[str, Any]) -> None:
        """
        Validate data before updating an instance.
        Override in subclasses for specific validation.

        Args:
            update_data (Dict[str, Any]): Data to validate

        Raises:
            ModelValidationError: If validation fails
        """
        pass

    def __repr__(self) -> str:
        """
        Provide a string representation of the model.

        Returns:
            str: String representation with class name and ID
        """
        return f"<{self.__class__.__name__} id={self.id}, uuid={self.uuid}>"


# Create a base that uses the mixin
Base: DeclarativeMeta = declarative_base(cls=BaseModelMixin)


# Optional: Add global event listeners for additional tracking or validation
@event.listens_for(Mapper, 'before_insert')
def receive_before_insert(mapper, connection, target):
    """
    Global event listener for pre-insert operations.
    Can be used for additional validation or tracking.
    """
    # Implementation remains the same as in the original code
    ...


@event.listens_for(Mapper, 'before_update')
def receive_before_update(mapper, connection, target):
    """
    Global event listener for pre-update operations.
    Can be used for additional validation or tracking.
    """
    # Implementation remains the same as in the original code
    ...