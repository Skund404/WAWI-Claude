# database/models/base.py
"""
Comprehensive base model for SQLAlchemy models with advanced utility methods.
"""

from .model_metaclass import BaseModelInterface
import enum
import uuid
import logging
import re
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
    Custom metaclass to resolve inheritance conflicts and track model registrations.
    """


    # Class-level dictionary to track registered models with full paths
    _registered_models: Dict[str, Type] = {}

    def __new__(mcs, name, bases, attrs):
        """
        Custom metaclass method to apply interface validation and mixin application.

        Args:
            mcs: The metaclass
            name: Name of the class being created
            bases: Base classes of the new class
            attrs: Attributes of the new class

        Returns:
            The newly created class
        """
        # Create the class using SQLAlchemy's metaclass behavior
        new_class = super().__new__(mcs, name, bases, attrs)

        # Skip registration for abstract classes
        if attrs.get('__abstract__', False):
            return new_class

        # Generate full path for the model with module and class name
        full_path = f"{new_class.__module__}.{new_class.__name__}"

        try:
            # Log model registration
            print(f"Registering model: {full_path}")

            # Register the model
            mcs._registered_models[full_path] = new_class

            # Intelligent mixin application
            available_mixins = [TimestampMixin, ValidationMixin, CostingMixin, TrackingMixin]
            applied_mixins = []

            for mixin in available_mixins:
                # Skip if mixin methods are already present in the class or its bases
                should_apply = True
                mixin_methods = {key for key in dir(mixin) if
                                 not key.startswith('__') and callable(getattr(mixin, key))}

                for base in bases + (new_class,):
                    base_methods = {key for key in dir(base) if
                                    not key.startswith('__') and callable(getattr(base, key))}
                    if mixin_methods.intersection(base_methods):
                        should_apply = False
                        break

                if should_apply:
                    # Apply mixin methods
                    for key, value in mixin.__dict__.items():
                        if not key.startswith('__') and key not in attrs and callable(value):
                            setattr(new_class, key, value)
                    applied_mixins.append(mixin.__name__)

            # Log applied mixins
            if applied_mixins:
                print(f"Mixins applied to {name}: {', '.join(applied_mixins)}")

        except Exception as e:
            logging.error(f"Error registering model {full_path}: {e}")

        return new_class

    @classmethod
    def get_registered_models(cls) -> Dict[str, List[Type]]:
        """
        Get all registered models with full paths.

        Returns:
            Dict[str, List[Type]]: Dictionary of registered model names and their classes
        """
        return cls._registered_models

    @classmethod
    def debug_registered_models(cls) -> Dict[str, List[str]]:
        """
        Comprehensive and safe debugging of registered models.

        Returns:
            Dict[str, List[str]]: Detailed information about registered models
        """
        debug_info = {}

        try:
            logger.info("===== Registered Models Debug =====")

            # Safely iterate through registered models
            for full_path, registered_item in cls._registered_models.items():
                try:
                    # Normalize to list if it's a single class
                    models = [registered_item] if isinstance(registered_item, type) else registered_item

                    # Filter out non-class items
                    models = [model for model in models if isinstance(model, type)]

                    if not models:
                        continue

                    # Collect model details
                    model_details = []
                    for model in models:
                        try:
                            # Get model attributes safely
                            model_details.append(f"{model.__module__}.{model.__name__}")
                        except Exception as model_error:
                            logger.warning(f"Error processing model details: {model_error}")

                    # Store in debug info
                    debug_info[full_path] = model_details

                    # Log details
                    logger.info(f"{full_path}: {len(model_details)} model(s)")
                    for detail in model_details:
                        logger.info(f"  - {detail}")

                except Exception as path_error:
                    logger.error(f"Error processing registered models for {full_path}: {path_error}")

        except Exception as e:
            logger.critical(f"Catastrophic error in debug_registered_models: {e}", exc_info=True)

        return debug_info

    def find_problematic_registrations(cls):
        """
        Identify potentially problematic model registrations.

        Returns:
            Dict[str, Any]: Detailed information about potentially duplicate or incorrectly registered models
        """
        problematic_registrations = {}

        try:
            logger.info("===== Analyzing Model Registrations =====")

            # Check for duplicate or unexpected registrations
            for full_path, registered_item in cls._registered_models.items():
                # Determine the type of registration
                if isinstance(registered_item, type):
                    # Single model registration
                    continue
                elif isinstance(registered_item, list):
                    # Multiple models registered under same path
                    if len(registered_item) > 1:
                        problematic_registrations[full_path] = {
                            'models': [f"{model.__module__}.{model.__name__}" for model in registered_item],
                            'issue': 'Multiple models registered under same path'
                        }
                else:
                    # Unexpected registration type
                    problematic_registrations[full_path] = {
                        'type': type(registered_item).__name__,
                        'issue': 'Unexpected registration type'
                    }

            # Log problematic registrations
            if problematic_registrations:
                logger.warning("Problematic model registrations found:")
                for path, details in problematic_registrations.items():
                    logger.warning(f"{path}: {details}")
            else:
                logger.info("No problematic model registrations found.")

        except Exception as e:
            logger.error(f"Error analyzing model registrations: {e}", exc_info=True)

        return problematic_registrations



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