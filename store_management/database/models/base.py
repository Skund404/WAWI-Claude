# database/models/base.py
"""
Comprehensive base model for SQLAlchemy models with advanced utility methods.
"""

import enum
import uuid
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Type, TypeVar

from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean,
    inspect, event
)
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm import DeclarativeMeta, Mapper
from sqlalchemy.sql import func

# Setup logging
logger = logging.getLogger(__name__)

T = TypeVar('T')


class ModelValidationError(Exception):
    """Custom exception for model validation errors."""
    pass


class BaseModelMixin:
    """
    Enhanced base model mixin with comprehensive utility methods.
    """
    # Primary key
    id = Column(Integer, primary_key=True)

    # Soft delete support
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    # Tracking columns
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

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

    def to_dict(self,
                include_relationships: bool = False,
                exclude_fields: Optional[List[str]] = None
                ) -> Dict[str, Any]:
        """
        Convert model instance to dictionary with advanced options.

        Args:
            include_relationships (bool): Whether to include relationship data
            exclude_fields (Optional[List[str]]): Fields to exclude from the output

        Returns:
            Dict[str, Any]: Dictionary representation of the model
        """
        try:
            # Default exclusion list
            exclude = set(exclude_fields or [])
            exclude.update(['_sa_instance_state'])

            # Get all columns and their values
            mapper = inspect(self.__class__).mapper
            columns = [c.key for c in mapper.columns if c.key not in exclude]

            # Convert to dictionary
            result = {c: getattr(self, c) for c in columns}

            # Convert datetime to ISO format
            for key in ['created_at', 'updated_at', 'deleted_at']:
                if result.get(key) and isinstance(result[key], datetime):
                    result[key] = result[key].isoformat()

            # Optionally include relationships
            if include_relationships:
                for rel in mapper.relationships:
                    if hasattr(self, rel.key):
                        related = getattr(self, rel.key)
                        if related is not None:
                            if isinstance(related, list):
                                result[rel.key] = [
                                    item.to_dict(include_relationships=False)
                                    for item in related
                                ]
                            else:
                                result[rel.key] = related.to_dict(include_relationships=False)

            return result
        except Exception as e:
            logger.error(f"Error converting {self.__class__.__name__} to dict: {e}")
            return {}

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
        try:
            # Perform any pre-creation validation
            cls._validate_creation(kwargs)

            # Create instance
            instance = cls(**kwargs)

            # Perform post-creation validation
            instance._validate_instance()

            return instance
        except Exception as e:
            logger.error(f"Error creating {cls.__name__}: {e}")
            raise ModelValidationError(f"Could not create {cls.__name__}: {str(e)}")

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
        try:
            # Perform pre-update validation
            self._validate_update(kwargs)

            # Update attributes
            for key, value in kwargs.items():
                if hasattr(self, key):
                    try:
                        setattr(self, key, value)
                    except Exception as e:
                        logger.warning(f"Could not update {key}: {e}")
                else:
                    logger.warning(f"Attribute {key} does not exist in {self.__class__.__name__}")

            # Perform post-update validation
            self._validate_instance()
        except Exception as e:
            logger.error(f"Error updating {self.__class__.__name__}: {e}")
            raise ModelValidationError(f"Could not update {self.__class__.__name__}: {str(e)}")

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
    try:
        # Example: Ensure UUID is set
        if not target.uuid:
            target.uuid = str(uuid.uuid4())
    except Exception as e:
        logger.error(f"Pre-insert error for {target.__class__.__name__}: {e}")
        raise


@event.listens_for(Mapper, 'before_update')
def receive_before_update(mapper, connection, target):
    """
    Global event listener for pre-update operations.
    Can be used for additional validation or tracking.
    """
    try:
        # You can add global update validations or tracking here
        pass
    except Exception as e:
        logger.error(f"Pre-update error for {target.__class__.__name__}: {e}")
        raise