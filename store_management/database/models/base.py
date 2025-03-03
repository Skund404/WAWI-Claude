# database/models/base.py
"""
Comprehensive base model for SQLAlchemy models with advanced utility methods.
"""

import enum
import uuid
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Type, TypeVar

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, declared_attr
from sqlalchemy import String, DateTime, Boolean, Integer
from sqlalchemy import event
from sqlalchemy.orm import Mapper

# Import mixins
from .mixins import TimestampMixin, ValidationMixin, CostingMixin, TrackingMixin

# Setup logging
logger = logging.getLogger(__name__)

T = TypeVar('T')


class ModelValidationError(Exception):
    """Custom exception for model validation errors."""
    pass


class BaseModelMetaclass(DeclarativeBase.__class__):
    """
    Custom metaclass to resolve inheritance conflicts.
    """

    def __new__(mcs, name, bases, attrs):
        # Only apply mixins to models that don't inherit from another model with the same mixin
        # First check if any of the bases already includes these mixins
        skip_mixins = set()
        for base in bases:
            if hasattr(base, '__dict__'):
                for mixin in [TimestampMixin, ValidationMixin, CostingMixin, TrackingMixin]:
                    # Check if any of the mixin's methods are already present in the base
                    mixin_methods = [key for key in mixin.__dict__ if not key.startswith('__')]
                    base_methods = [key for key in base.__dict__ if not key.startswith('__')]
                    if any(method in base_methods for method in mixin_methods):
                        skip_mixins.add(mixin)

        # Add mixin methods to the class, skipping those already added via base classes
        for mixin in [TimestampMixin, ValidationMixin, CostingMixin, TrackingMixin]:
            if mixin not in skip_mixins:
                for key, value in mixin.__dict__.items():
                    if key not in attrs and not key.startswith('__'):
                        attrs[key] = value

        return super().__new__(mcs, name, bases, attrs)


class Base(DeclarativeBase, metaclass=BaseModelMetaclass):
    """
    Enhanced base model with comprehensive utility methods.
    """
    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True)

    # Soft delete support
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Unique identifier
    uuid: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))

    @declared_attr.directive
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

    def to_dict(self, include_relationships: bool = False, exclude_fields: Optional[List[str]] = None) -> Dict[
        str, Any]:
        """
        Convert model instance to dictionary with advanced options.

        Args:
            include_relationships (bool): Whether to include relationship data
            exclude_fields (Optional[List[str]]): Fields to exclude from the output

        Returns:
            Dict[str, Any]: Dictionary representation of the model
        """
        # Get all columns
        columns = [c.name for c in self.__table__.columns]

        # Create dictionary
        result = {}
        for column in columns:
            # Skip excluded fields
            if exclude_fields and column in exclude_fields:
                continue

            # Get value
            value = getattr(self, column)

            # Handle enum conversion
            if isinstance(value, enum.Enum):
                value = value.name

            # Convert datetime to ISO format
            if isinstance(value, datetime):
                value = value.isoformat()

            result[column] = value

        # Optionally include relationships (would need to be implemented carefully)
        if include_relationships:
            # This would require more complex logic to handle relationships
            pass

        return result

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
        # Validate creation data
        try:
            # Call class-specific validation if implemented
            cls._validate_creation(kwargs)
        except Exception as e:
            raise ModelValidationError(f"Validation failed: {str(e)}") from e

        # Create instance
        instance = cls(**kwargs)

        # Validate instance
        try:
            instance._validate_instance()
        except Exception as e:
            raise ModelValidationError(f"Instance validation failed: {str(e)}") from e

        return instance

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
        # Validate update data
        try:
            self._validate_update(kwargs)
        except Exception as e:
            raise ModelValidationError(f"Update validation failed: {str(e)}") from e

        # Update attributes
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

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


# Optional: Add global event listeners for additional tracking or validation
@event.listens_for(Mapper, 'before_insert')
def receive_before_insert(mapper, connection, target):
    """
    Global event listener for pre-insert operations.
    Can be used for additional validation or tracking.
    """
    try:
        # Perform any pre-insert validations or tracking
        if hasattr(target, '_validate_before_insert'):
            target._validate_before_insert()
    except Exception as e:
        logger.error(f"Pre-insert validation failed: {str(e)}")
        raise


@event.listens_for(Mapper, 'before_update')
def receive_before_update(mapper, connection, target):
    """
    Global event listener for pre-update operations.
    Can be used for additional validation or tracking.
    """
    try:
        # Perform any pre-update validations or tracking
        if hasattr(target, '_validate_before_update'):
            target._validate_before_update()
    except Exception as e:
        logger.error(f"Pre-update validation failed: {str(e)}")
        raise


# Add this after the existing Base class definition
class BaseModel(Base):
    """
    Compatibility base model that inherits from Base.

    This class is provided for backward compatibility with existing code
    that may have been using the previous BaseModel implementation.
    """
    __abstract__ = True  # Mark as abstract to prevent direct table creation

    def __init__(self, *args, **kwargs):
        """
        Initialize the base model with compatibility.

        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments for model attributes
        """
        # If no UUID is provided, generate one
        if 'uuid' not in kwargs:
            kwargs['uuid'] = str(uuid.uuid4())

        # Call parent constructor
        super().__init__(*args, **kwargs)

    def __repr__(self) -> str:
        """
        Provide a string representation of the model.

        Returns:
            str: String representation with class name and ID
        """
        pk_attrs = [
            f"{col}={getattr(self, col)}"
            for col in self.__table__.primary_key.columns.keys()
            if hasattr(self, col)
        ]
        pk_str = ', '.join(pk_attrs) if pk_attrs else 'no primary key'
        return f"{self.__class__.__name__}({pk_str})"