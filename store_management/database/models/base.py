# database/models/base.py
"""
Enhanced Base Model for Leatherworking Management System

Provides a centralized, flexible foundation for database models with:
- Advanced metaclass resolution
- Comprehensive model registration
- Robust inheritance strategies
- Flexible mixin support
- Advanced validation and tracking capabilities
"""

import abc
import enum
import uuid
import logging
import re
import inspect
import time
import json
from datetime import datetime
from typing import (
    Any, Dict, List, Optional, Type, TypeVar, Callable,
    Union, Set, Tuple, cast, ClassVar, get_type_hints
)

# Import SQLAlchemy components
from sqlalchemy import (
    MetaData, create_engine, Column, DateTime, Boolean,
    Float, String, Enum as SQLAlchemyEnum, CheckConstraint,
    event, Table, Index, ForeignKey, text, func, Integer
)
from sqlalchemy.orm import (
    DeclarativeMeta, DeclarativeBase,
    Mapped, mapped_column, declared_attr,
    relationship, Session, registry, MappedAsDataclass,
    declarative_base
)
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import func
from sqlalchemy.dialects.sqlite import TEXT  # For SQLite compatibility

# Create metadata FIRST before any imports that might use it
metadata = MetaData()
mapper_registry = registry(metadata=metadata)

# Import circular import resolver for advanced dependency management
from utils.circular_import_resolver import (
    CircularImportResolver,
    register_lazy_import,
    resolve_lazy_import
)

# Setup logging
logger = logging.getLogger(__name__)

# Type variable for generic model typing
T = TypeVar('T')
ModelType = TypeVar('ModelType')

# Define the Base class using DeclarativeBase
class Base(DeclarativeBase):
    """Base class for all models"""
    metadata = metadata
    registry = mapper_registry

# For backwards compatibility
BaseModel = Base

# The rest of the file remains unchanged...

# Update BaseModel creation for SQLAlchemy 2.0
BaseModel = declarative_base()
BaseModel.metadata = metadata


class ModelValidationError(Exception):
    """
    Custom exception for comprehensive model validation errors.
    Provides detailed error tracking and reporting.
    """

    def __init__(
            self,
            message: str,
            errors: Optional[Dict[str, List[str]]] = None,
            model_name: Optional[str] = None
    ):
        """
        Initialize validation error with optional detailed error mapping.

        Args:
            message: Primary error message
            errors: Dictionary of field-specific validation errors
            model_name: Name of the model that failed validation
        """
        super().__init__(message)
        self.errors = errors or {}
        self.model_name = model_name

    def __str__(self) -> str:
        """
        Generate a comprehensive error string.

        Returns:
            Detailed error representation
        """
        base_message = super().__str__()
        if self.model_name:
            base_message = f"[{self.model_name}] {base_message}"

        if self.errors:
            error_details = "\n".join([
                f"{field}: {', '.join(field_errors)}"
                for field, field_errors in self.errors.items()
            ])
            return f"{base_message}\n\nValidation Errors:\n{error_details}"
        return base_message


class ValidationMixin:
    """
    Advanced validation mixin with comprehensive validation strategies.
    Provides robust validation methods for model data.
    """

    # Class-level validation registry
    _field_validators: ClassVar[Dict[str, List[Callable]]] = {}
    _model_validators: ClassVar[List[Callable]] = []
    _schema: ClassVar[Optional[Dict[str, Any]]] = None

    @classmethod
    def register_field_validator(
            cls,
            field_name: str,
            validator_func: Callable[[Any], Optional[str]]
    ) -> None:
        """
        Register a field-level validator function.

        Args:
            field_name: Name of the field to validate
            validator_func: Function that validates the field
                            Returns None if valid, or error message if invalid
        """
        if field_name not in cls._field_validators:
            cls._field_validators[field_name] = []
        cls._field_validators[field_name].append(validator_func)
        logger.debug(f"Registered field validator for {cls.__name__}.{field_name}")

    @classmethod
    def register_model_validator(
            cls,
            validator_func: Callable[['ValidationMixin'], Optional[str]]
    ) -> None:
        """
        Register a model-level validator function.

        Args:
            validator_func: Function that validates the entire model
                            Returns None if valid, or error message if invalid
        """
        cls._model_validators.append(validator_func)
        logger.debug(f"Registered model validator for {cls.__name__}")

    @classmethod
    def set_schema(cls, schema: Dict[str, Any]) -> None:
        """
        Set a JSON schema for model validation.

        Args:
            schema: JSON schema dictionary
        """
        cls._schema = schema
        logger.debug(f"Set JSON schema for {cls.__name__}")

    @classmethod
    def validate(cls, data: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Comprehensive validation method with detailed error reporting.

        Args:
            data: Dictionary of attributes to validate

        Returns:
            Dictionary of validation errors
        """
        errors: Dict[str, List[str]] = {}

        # Validate required fields
        for key, value in data.items():
            # Check for None values in required fields
            if value is None:
                column = getattr(cls, key, None)
                if column is not None and hasattr(column, 'nullable') and not column.nullable:
                    errors.setdefault('required_fields', []).append(
                        f"{key} cannot be None"
                    )

            # Apply field validators
            if key in cls._field_validators:
                for validator in cls._field_validators[key]:
                    try:
                        result = validator(value)
                        if result:
                            errors.setdefault(key, []).append(result)
                    except Exception as e:
                        errors.setdefault(key, []).append(f"Validation error: {str(e)}")

            # Validate known field types using specific validation methods
            try:
                validation_method = getattr(cls, f'validate_{key}', None)
                if validation_method:
                    validation_result = validation_method(value)
                    if validation_result:
                        errors.setdefault(key, []).append(validation_result)
            except Exception as e:
                errors.setdefault(key, []).append(str(e))

        # Validate with JSON schema if available
        if cls._schema and data:
            try:
                import jsonschema
                try:
                    jsonschema.validate(data, cls._schema)
                except jsonschema.exceptions.ValidationError as e:
                    errors.setdefault('_schema', []).append(str(e))
            except ImportError:
                logger.warning("jsonschema package not available for schema validation")

        return errors

    @classmethod
    def validate_enum(
            cls,
            value: Any,
            enum_class: Type[enum.Enum],
            field_name: str
    ) -> Optional[str]:
        """
        Validate that a value is a valid enum member.

        Args:
            value: Value to validate
            enum_class: Enum class to validate against
            field_name: Name of the field being validated

        Returns:
            Error message if validation fails, None otherwise
        """
        try:
            if value is None:
                return f"{field_name} cannot be None"

            if not isinstance(value, enum_class):
                # Attempt to convert string to enum
                if isinstance(value, str):
                    try:
                        enum_class[value.upper()]
                    except (KeyError, ValueError):
                        return f"{field_name} must be a valid {enum_class.__name__}"
                else:
                    return f"{field_name} must be a valid {enum_class.__name__}"
            return None
        except Exception:
            return f"Invalid {field_name} value"

    def validate_model(self) -> Dict[str, List[str]]:
        """
        Validate the entire model instance.

        Returns:
            Dictionary of validation errors
        """
        errors: Dict[str, List[str]] = {}

        # Convert model to dictionary
        data = self.to_dict()

        # Field-level validation
        field_errors = self.validate(data)
        if field_errors:
            errors.update(field_errors)

        # Model-level validation
        for validator in self._model_validators:
            try:
                result = validator(self)
                if result:
                    errors.setdefault('_model', []).append(result)
            except Exception as e:
                errors.setdefault('_model', []).append(f"Model validation error: {str(e)}")

        return errors

    def is_valid(self) -> bool:
        """
        Check if the current model instance is valid.

        Returns:
            True if the model is valid, False otherwise
        """
        validation_errors = self.validate_model()
        return len(validation_errors) == 0

    def validate_and_raise(self) -> None:
        """
        Validate the model and raise an exception if invalid.

        Raises:
            ModelValidationError: If validation fails
        """
        errors = self.validate_model()
        if errors:
            model_name = self.__class__.__name__
            raise ModelValidationError(
                f"Validation failed for {model_name}",
                errors=errors,
                model_name=model_name
            )


class TimestampMixin:
    """
    Enhanced timestamp tracking for database models.
    Provides creation and modification timestamp tracking.
    """
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    @classmethod
    def get_recent_records(cls, session: Session, days: int = 30):
        """
        Retrieve records created within the specified number of days.

        Args:
            session: Database session
            days: Number of days to look back (default 30)

        Returns:
            Query of recent records
        """
        return session.query(cls).filter(
            cls.created_at >= func.date('now', f'-{days} days')
        )

    @property
    def age_in_days(self) -> int:
        """
        Calculate the age of the record in days.

        Returns:
            Age in days (int)
        """
        if self.created_at:
            delta = datetime.now().astimezone() - self.created_at
            return delta.days
        return 0

    @property
    def last_updated_days_ago(self) -> int:
        """
        Calculate days since last update.

        Returns:
            Days since last update (int)
        """
        if self.updated_at:
            delta = datetime.now().astimezone() - self.updated_at
            return delta.days
        return 0


class CostingMixin:
    """
    Advanced costing tracking for financial entities.
    """
    # Base costing attributes
    unit_cost: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
        info={'description': 'Cost per unit'}
    )
    total_cost: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
        info={'description': 'Total cost'}
    )

    # Quality and pricing attributes
    quality_grade: Mapped[enum.Enum] = mapped_column(
        SQLAlchemyEnum("QualityGrade", name='quality_grade_enum'),
        nullable=False,
        info={'description': 'Quality grade of the item'}
    )

    # Constraints to ensure financial integrity
    __table_args__ = (
        CheckConstraint('unit_cost >= 0', name='check_unit_cost_non_negative'),
        CheckConstraint('total_cost >= 0', name='check_total_cost_non_negative')
    )

    # Cost calculation methods
    def calculate_total_cost(
            self,
            unit_cost: Optional[float] = None,
            quantity: Optional[float] = 1.0
    ) -> float:
        """
        Calculate total cost with optional overrides.

        Args:
            unit_cost: Optional unit cost override
            quantity: Quantity to calculate cost for

        Returns:
            Calculated total cost
        """
        cost_per_unit = unit_cost if unit_cost is not None else self.unit_cost
        return cost_per_unit * (quantity or 1.0)

    def update_cost(
            self,
            unit_cost: float,
            total_cost: Optional[float] = None
    ) -> None:
        """
        Update costing information.

        Args:
            unit_cost: New unit cost
            total_cost: Optional total cost (will be calculated if not provided)

        Raises:
            ValueError: If unit cost is negative
        """
        if unit_cost < 0:
            raise ValueError("Unit cost cannot be negative")

        self.unit_cost = unit_cost
        self.total_cost = total_cost or self.calculate_total_cost()

        # Update quality grade based on cost thresholds
        # This can be customized based on your business rules
        from .enums import QualityGrade
        if unit_cost <= 10:
            self.quality_grade = QualityGrade.ECONOMY
        elif 10 < unit_cost <= 50:
            self.quality_grade = QualityGrade.STANDARD
        else:
            self.quality_grade = QualityGrade.PREMIUM

    def calculate_profit_margin(self, selling_price: float) -> float:
        """
        Calculate profit margin percentage.

        Args:
            selling_price: The selling price

        Returns:
            Profit margin as a percentage

        Raises:
            ValueError: If selling price is zero or negative
        """
        if selling_price <= 0:
            raise ValueError("Selling price must be positive")

        if self.total_cost <= 0:
            return 100.0  # Pure profit if no cost

        profit = selling_price - self.total_cost
        margin = (profit / selling_price) * 100
        return round(margin, 2)


class TrackingMixin:
    """
    Advanced tracking capabilities for database entities.
    """
    # Unique tracking identifier
    tracking_id: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
        default=lambda: str(uuid.uuid4())
    )

    # Inventory and status tracking
    material_type: Mapped[Optional[enum.Enum]] = mapped_column(
        SQLAlchemyEnum("MaterialType", name='material_type_enum'),
        nullable=True
    )

    inventory_status: Mapped[enum.Enum] = mapped_column(
        SQLAlchemyEnum("InventoryStatus", name='inventory_status_enum'),
        nullable=False
    )

    # Tracking methods
    def generate_tracking_id(self) -> str:
        """
        Generate a new unique tracking identifier.

        Returns:
            Unique tracking ID
        """
        return str(uuid.uuid4())

    def update_tracking_id(self) -> None:
        """
        Update the tracking identifier.
        """
        self.tracking_id = self.generate_tracking_id()

    def update_inventory_status(
            self,
            new_status: enum.Enum,
            threshold: Optional[float] = None,
            session: Optional[Session] = None
    ) -> None:
        """
        Update inventory status with optional threshold logic.

        Args:
            new_status: New inventory status
            threshold: Optional threshold for status determination
            session: Optional session for transactional updates

        Raises:
            ValueError: If the status transition is invalid
        """
        from .enums import InventoryStatus

        # Implement status transition rules
        valid_transitions = {
            InventoryStatus.IN_STOCK: [
                InventoryStatus.LOW_STOCK,
                InventoryStatus.OUT_OF_STOCK
            ],
            InventoryStatus.LOW_STOCK: [
                InventoryStatus.IN_STOCK,
                InventoryStatus.OUT_OF_STOCK
            ],
            InventoryStatus.OUT_OF_STOCK: [
                InventoryStatus.IN_STOCK,
                InventoryStatus.LOW_STOCK
            ]
        }

        # Validate status transition
        if (self.inventory_status in valid_transitions and
                new_status not in valid_transitions[self.inventory_status]):
            raise ValueError(f"Invalid status transition from {self.inventory_status} to {new_status}")

        # Additional threshold-based logic
        if threshold is not None:
            if threshold <= 0:
                new_status = InventoryStatus.OUT_OF_STOCK
            elif 0 < threshold < 10:
                new_status = InventoryStatus.LOW_STOCK

        # Update status
        old_status = self.inventory_status
        self.inventory_status = new_status

        # Log the status change
        logger.info(f"Updated inventory status from {old_status} to {new_status}")

        # If session provided, record the status change in history
        if session and hasattr(self, 'id'):
            try:
                # This assumes you have a StatusHistory model
                # If not, this code will be skipped
                from .status_history import StatusHistory

                history = StatusHistory(
                    model_name=self.__class__.__name__,
                    record_id=self.id,
                    field_name='inventory_status',
                    old_value=str(old_status),
                    new_value=str(new_status),
                    changed_at=datetime.now().astimezone()
                )
                session.add(history)
            except ImportError:
                pass  # StatusHistory model not available


class ComplianceMixin:
    """
    Advanced compliance and audit tracking mixin.
    """
    # Compliance and audit tracking
    is_compliant: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        info={'description': 'Compliance status flag'}
    )
    compliance_notes: Mapped[Optional[str]] = mapped_column(
        TEXT,
        nullable=True,
        info={'description': 'Compliance notes and comments'}
    )
    last_compliance_check: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        onupdate=datetime.utcnow,
        info={'description': 'Timestamp of last compliance check'}
    )

    def mark_compliance(
            self,
            is_compliant: bool,
            notes: Optional[str] = None
    ) -> None:
        """
        Update compliance status.

        Args:
            is_compliant: Compliance status
            notes: Optional compliance notes
        """
        self.is_compliant = is_compliant
        self.compliance_notes = notes
        self.last_compliance_check = datetime.utcnow()

    def log_compliance_check(
            self,
            check_method: Callable[..., bool],
            *args,
            **kwargs
    ) -> bool:
        """
        Perform a compliance check and log the results.

        Args:
            check_method: Method to perform the compliance check
            *args: Positional arguments for the check method
            **kwargs: Keyword arguments for the check method

        Returns:
            Result of the compliance check
        """
        try:
            compliance_result = check_method(*args, **kwargs)

            # Update compliance status
            self.mark_compliance(
                is_compliant=compliance_result,
                notes=f"Compliance check via {check_method.__name__}"
            )

            return compliance_result
        except Exception as e:
            # Log any errors during compliance check
            self.mark_compliance(
                is_compliant=False,
                notes=f"Compliance check failed: {str(e)}"
            )
            logger.error(f"Compliance check error: {e}")
            return False

    def get_compliance_history(self, session: Session) -> List[Dict[str, Any]]:
        """
        Get compliance history for this record.

        Args:
            session: Database session

        Returns:
            List of compliance history records
        """
        try:
            # This assumes you have a ComplianceHistory model
            # If not, this will return an empty list
            from .compliance_history import ComplianceHistory

            if hasattr(self, 'id'):
                history = session.query(ComplianceHistory).filter(
                    ComplianceHistory.model_name == self.__class__.__name__,
                    ComplianceHistory.record_id == self.id
                ).order_by(ComplianceHistory.check_date.desc()).all()

                return [h.to_dict() for h in history]
        except ImportError:
            pass

        return []


class AuditMixin:
    """
    Advanced audit tracking mixin.
    Tracks creation, modification, and deletion information.
    """
    created_by: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        info={'description': 'User who created the record'}
    )
    updated_by: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        info={'description': 'User who last updated the record'}
    )
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        info={'description': 'Soft deletion flag'}
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        info={'description': 'When the record was soft-deleted'}
    )
    deleted_by: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        info={'description': 'User who deleted the record'}
    )

    def record_creation(self, user_id: str) -> None:
        """
        Record creation audit information.

        Args:
            user_id: ID of the user creating the record
        """
        self.created_by = user_id
        self.updated_by = user_id

    def record_update(self, user_id: str) -> None:
        """
        Record update audit information.

        Args:
            user_id: ID of the user updating the record
        """
        self.updated_by = user_id

    def soft_delete(self, user_id: str) -> None:
        """
        Perform a soft delete with audit information.

        Args:
            user_id: ID of the user deleting the record
        """
        self.is_deleted = True
        self.deleted_at = datetime.now().astimezone()
        self.deleted_by = user_id

    def restore(self, user_id: str) -> None:
        """
        Restore a soft-deleted record with audit information.

        Args:
            user_id: ID of the user restoring the record
        """
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.updated_by = user_id


class ModelRegistry:
    """
    Centralized model registration and management system.

    Provides comprehensive tracking and resolution of database models
    with advanced dependency management.
    """
    _registry: Dict[str, Type] = {}
    _lazy_imports: Dict[str, str] = {}
    _relationship_configs: Dict[str, Dict[str, Any]] = {}
    _model_cache: Dict[str, Type] = {}  # Performance optimization
    _initialization_time: Dict[str, float] = {}  # Performance metrics

    @classmethod
    def register(
            cls,
            model_name: str,
            model_class: Type,
            module_path: Optional[str] = None
    ) -> None:
        """
        Register a model class with comprehensive tracking.

        Args:
            model_name: Unique identifier for the model
            model_class: The model class to register
            module_path: Optional module path for lazy loading
        """
        start_time = time.time()

        try:
            cls._registry[model_name] = model_class
            cls._model_cache[model_name] = model_class  # Update cache

            if module_path:
                register_lazy_import(
                    model_name,
                    module_path,
                    model_class.__name__
                )

            # Record initialization time for performance metrics
            cls._initialization_time[model_name] = time.time() - start_time

            logger.debug(f"Registered model: {model_name} (took {cls._initialization_time[model_name]:.4f}s)")
        except Exception as e:
            logger.error(f"Model registration failed for {model_name}: {e}")
            # Attempt to recover from registration failure
            if model_name in cls._registry:
                del cls._registry[model_name]
            if model_name in cls._model_cache:
                del cls._model_cache[model_name]

    @classmethod
    def get(cls, model_name: str) -> Optional[Type]:
        """
        Retrieve a registered model, with lazy import support.

        Args:
            model_name: Name of the model to retrieve

        Returns:
            The model class or None if not found
        """
        # Check cache first for performance
        if model_name in cls._model_cache:
            return cls._model_cache[model_name]

        if model_name not in cls._registry:
            try:
                # Attempt lazy import
                model_class = resolve_lazy_import(model_name)
                if model_class:
                    # Update cache
                    cls._model_cache[model_name] = model_class
                return model_class
            except Exception as e:
                logger.warning(f"Failed to lazy import {model_name}: {e}")
                return None

        return cls._registry[model_name]

    @classmethod
    def register_relationship(
            cls,
            model_name: str,
            relationship_name: str,
            config: Dict[str, Any]
    ) -> None:
        """
        Register a relationship configuration for a model.

        Args:
            model_name: Name of the model
            relationship_name: Name of the relationship
            config: Relationship configuration dictionary
        """
        if model_name not in cls._relationship_configs:
            cls._relationship_configs[model_name] = {}

        cls._relationship_configs[model_name][relationship_name] = config
        logger.debug(f"Registered relationship: {model_name}.{relationship_name}")

    @classmethod
    def get_registered_models(cls) -> List[str]:
        """
        Get a list of all registered model names.

        Returns:
            List of model names
        """
        return list(cls._registry.keys())

    @classmethod
    def get_model_metrics(cls) -> Dict[str, Dict[str, Any]]:
        """
        Get performance metrics for model initialization.

        Returns:
            Dictionary of model metrics
        """
        metrics = {}
        for model_name, init_time in cls._initialization_time.items():
            metrics[model_name] = {
                'initialization_time': init_time,
                'relationships': len(cls._relationship_configs.get(model_name, {})),
                'lazy_loaded': model_name in cls._lazy_imports
            }
        return metrics

    @classmethod
    def clear_caches(cls) -> None:
        """
        Clear model caches for memory optimization.
        """
        cls._model_cache.clear()
        logger.debug("Cleared model registry caches")

    @classmethod
    def reset(cls) -> None:
        """
        Reset the entire registry. Useful for testing.
        """
        cls._registry.clear()
        cls._lazy_imports.clear()
        cls._relationship_configs.clear()
        cls._model_cache.clear()
        cls._initialization_time.clear()
        logger.info("Model registry reset complete")


class EnhancedMetaclass(DeclarativeMeta):
    """
    Advanced metaclass for model creation with enhanced capabilities:
    - Intelligent mixin resolution
    - Automatic relationship registration
    - Dynamic attribute injection
    - Performance metrics collection
    """

    def __new__(mcs, name, bases, attrs, **kwargs):
        # Start performance timer
        start_time = time.time()

        # Record original MRO for diagnostics
        original_mro = [b.__name__ for b in bases]
        logger.debug(f"Creating {name} with bases: {original_mro}")

        # Intelligent mixin resolution
        resolved_bases = []
        seen_base_types = set()

        for base in bases:
            base_type = type(base)
            if base_type not in seen_base_types:
                resolved_bases.append(base)
                seen_base_types.add(base_type)

        # Prioritize DeclarativeMeta bases
        declarative_bases = [
            base for base in resolved_bases
            if isinstance(base, DeclarativeMeta)
        ]
        other_bases = [
            base for base in resolved_bases
            if not isinstance(base, DeclarativeMeta)
        ]

        # Combine bases with DeclarativeMeta first
        final_bases = declarative_bases + other_bases

        # Inject table naming convention if not present
        if '__tablename__' not in attrs:
            attrs['__tablename__'] = mcs._generate_tablename(name)

        # Inject improved to_dict method if not present
        if 'to_dict' not in attrs:
            attrs['to_dict'] = mcs._generate_to_dict()

        # Inject update_from_dict method if not present
        if 'update_from_dict' not in attrs:
            attrs['update_from_dict'] = mcs._generate_update_from_dict()

        # Create the class with enhanced base resolution
        new_class = super().__new__(
            mcs,
            name,
            tuple(final_bases),
            attrs,
            **kwargs
        )

        # Record creation time
        creation_time = time.time() - start_time

        # Add performance metrics to the class
        setattr(new_class, '_creation_time', creation_time)

        # Log performance metrics
        logger.debug(f"Created {name} in {creation_time:.4f}s")

        # Automatic relationship and lazy import registration
        try:
            ModelRegistry.register(
                name,
                new_class,
                module_path=new_class.__module__
            )
        except Exception as e:
            logger.warning(f"Could not register model {name}: {e}")

        return new_class

    @staticmethod
    def _generate_tablename(class_name: str) -> str:
        """
        Generate a table name from a class name.
        Converts PascalCase to snake_case and pluralizes.

        Args:
            class_name: The class name in PascalCase

        Returns:
            Table name in snake_case, pluralized
        """
        # Convert camelCase or PascalCase to snake_case
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', class_name)
        s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

        # Pluralize with simple approach
        return f"{s2}s" if not s2.endswith('s') else s2

    @staticmethod
    def _generate_to_dict():
        """
        Generate an enhanced to_dict method.

        Returns:
            Method for converting a model to a dictionary
        """

        def to_dict(
                self,
                exclude_fields: Optional[List[str]] = None,
                include_fields: Optional[List[str]] = None,
                include_relationships: bool = False,
                max_depth: int = 1,
                _current_depth: int = 0
        ) -> Dict[str, Any]:
            """
            Convert model instance to a dictionary.

            Args:
                exclude_fields: Optional list of fields to exclude
                include_fields: Optional list of fields to include (overrides exclude)
                include_relationships: Whether to include relationship attributes
                max_depth: Maximum depth for relationships to prevent circular references
                _current_depth: Current recursion depth (internal use)

            Returns:
                Dictionary representation of the model
            """
            exclude_fields = exclude_fields or []
            result = {}

            # Handle explicit include list
            if include_fields is not None:
                for field in include_fields:
                    if hasattr(self, field):
                        value = getattr(self, field)
                        # Handle enum values
                        if isinstance(value, enum.Enum):
                            result[field] = value.name
                        else:
                            result[field] = value
                return result

            # Get all columns
            columns = getattr(self, '__table__').columns
            for column in columns:
                if column.name not in exclude_fields:
                    value = getattr(self, column.name)
                    # Handle enum values
                    if isinstance(value, enum.Enum):
                        result[column.name] = value.name
                    elif isinstance(value, datetime):
                        result[column.name] = value.isoformat()
                    else:
                        result[column.name] = value

            # Include relationships if requested
            if include_relationships and _current_depth < max_depth:
                for rel_name, rel_obj in inspect.getmembers(type(self)):
                    if rel_name.startswith('_') or rel_name in exclude_fields:
                        continue

                    if hasattr(rel_obj, 'prop') and hasattr(rel_obj.prop, 'target'):
                        related_obj = getattr(self, rel_name)

                        if related_obj is None:
                            result[rel_name] = None
                        elif isinstance(related_obj, list):
                            result[rel_name] = [
                                item.to_dict(
                                    exclude_fields=exclude_fields,
                                    include_relationships=include_relationships,
                                    max_depth=max_depth,
                                    _current_depth=_current_depth + 1
                                ) if hasattr(item, 'to_dict') else str(item)
                                for item in related_obj
                            ]
                        elif hasattr(related_obj, 'to_dict'):
                            result[rel_name] = related_obj.to_dict(
                                exclude_fields=exclude_fields,
                                include_relationships=include_relationships,
                                max_depth=max_depth,
                                _current_depth=_current_depth + 1
                            )
                        else:
                            result[rel_name] = str(related_obj)

            return result

        return to_dict

    @staticmethod
    def _generate_update_from_dict():
        """
        Generate an enhanced update_from_dict method.

        Returns:
            Method for updating a model from a dictionary
        """

        def update_from_dict(
                self,
                update_dict: Dict[str, Any],
                allow_partial: bool = True,
                exclude_fields: Optional[List[str]] = None,
                validate: bool = True
        ) -> None:
            """
            Update model instance from a dictionary.

            Args:
                update_dict: Dictionary of fields to update
                allow_partial: Allow partial updates (default True)
                exclude_fields: Optional list of fields to exclude from update
                validate: Whether to validate after update

            Raises:
                ValueError: If update is not allowed and a required field is missing
                ModelValidationError: If validation fails after update
            """
            exclude_fields = exclude_fields or []
            exclude_fields.extend(['id', 'uuid'])  # Always exclude primary identifiers

            # Get all updatable columns
            updatable_columns = [
                column.name for column in self.__table__.columns
                if column.name not in exclude_fields
                   and not column.primary_key  # Exclude primary key
            ]

            # Validate update completeness
            if not allow_partial:
                # Check if all columns are present
                missing_fields = set(updatable_columns) - set(update_dict.keys())
                if missing_fields:
                    raise ValueError(f"Missing required fields for update: {missing_fields}")

            # Track modified fields for logging
            modified_fields = []

            # Perform update
            for field in updatable_columns:
                if field in update_dict:
                    old_value = getattr(self, field)
                    new_value = update_dict[field]

                    # Handle enum values
                    if isinstance(old_value, enum.Enum) and isinstance(new_value, str):
                        enum_class = type(old_value)
                        try:
                            new_value = enum_class[new_value]
                        except KeyError:
                            raise ValueError(f"Invalid value for enum field {field}: {new_value}")

                    if old_value != new_value:
                        setattr(self, field, new_value)
                        modified_fields.append((field, old_value, new_value))

            # Update audit fields if present
            if hasattr(self, 'updated_at'):
                self.updated_at = datetime.now().astimezone()

            # Log changes
            if modified_fields:
                fields_str = ', '.join(f"{field}" for field, _, _ in modified_fields)
                logger.debug(f"Updated {len(modified_fields)} fields on {self.__class__.__name__}: {fields_str}")

            # Validate if requested
            if validate and hasattr(self, 'validate_and_raise'):
                self.validate_and_raise()

        return update_from_dict


def create_base_model(
        mixins: Optional[List[Type]] = None,
        base_class: Type = DeclarativeBase,
        include_audit: bool = True
) -> Type:
    """
    Create a dynamically configured base model with advanced capabilities.

    Args:
        mixins: Optional list of mixin classes to apply
        base_class: Base declarative class to use
        include_audit: Whether to include audit tracking

    Returns:
        A dynamically created base model class
    """
    # Prepare mixins
    applied_mixins = []
    if mixins:
        applied_mixins.extend(mixins)

    # Add AuditMixin if requested
    if include_audit and AuditMixin not in applied_mixins:
        applied_mixins.append(AuditMixin)

    # Create a custom base with enhanced metaclass
    class BaseModel(DeclarativeBase, metaclass=EnhancedMetaclass):
        """
        Comprehensive base model with advanced features.
        """
        # Connect the registry - this is critical for SQLAlchemy 2.0
        registry = mapper_registry
        metadata = mapper_registry.metadata

        # Standard columns for tracking and identification
        id: Mapped[int] = mapped_column(primary_key=True)
        uuid: Mapped[str] = mapped_column(
            String(36),
            unique=True,
            default=lambda: str(uuid.uuid4())
        )
        is_active: Mapped[bool] = mapped_column(
            Boolean,
            default=True,
            nullable=False
        )

        created_at: Mapped[datetime] = mapped_column(
            DateTime(timezone=True),
            server_default=func.now()
        )
        updated_at: Mapped[datetime] = mapped_column(
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now()
        )

        @declared_attr
        def __tablename__(cls):
            """
            Intelligent table name generation.
            Converts class names to snake_case and pluralizes.
            """
            # Convert camelCase or PascalCase to snake_case
            s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', cls.__name__)
            s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

            # Pluralize with simple approach
            return f"{s2}s" if not s2.endswith('s') else s2

        def to_dict(
                self,
                exclude_fields: Optional[List[str]] = None,
                include_fields: Optional[List[str]] = None,
                include_relationships: bool = False,
                max_depth: int = 1
        ) -> Dict[str, Any]:
            """
            Convert model instance to a dictionary.

            Args:
                exclude_fields: Optional list of fields to exclude
                include_fields: Optional list of fields to include (overrides exclude)
                include_relationships: Whether to include relationship attributes
                max_depth: Maximum depth for relationships to prevent circular references

            Returns:
                Dictionary representation of the model
            """
            exclude_fields = exclude_fields or []

            if include_fields is not None:
                # If include_fields is specified, use only those fields
                return {
                    field: getattr(self, field)
                    for field in include_fields
                    if hasattr(self, field)
                }

            result = {
                column.name: getattr(self, column.name)
                for column in self.__table__.columns
                if column.name not in exclude_fields
            }

            # Convert Enum values to strings
            for key, value in result.items():
                if isinstance(value, enum.Enum):
                    result[key] = value.name
                elif isinstance(value, datetime):
                    result[key] = value.isoformat()

            # Include relationships if requested
            if include_relationships and max_depth > 0:
                for rel_name, rel_obj in inspect.getmembers(type(self)):
                    if rel_name.startswith('_') or rel_name in exclude_fields:
                        continue

                    if hasattr(rel_obj, 'prop') and hasattr(rel_obj.prop, 'target'):
                        related_obj = getattr(self, rel_name)

                        if related_obj is None:
                            result[rel_name] = None
                        elif isinstance(related_obj, list):
                            result[rel_name] = [
                                item.to_dict(
                                    exclude_fields=exclude_fields,
                                    include_relationships=include_relationships,
                                    max_depth=max_depth - 1
                                ) if hasattr(item, 'to_dict') else str(item)
                                for item in related_obj
                            ]
                        elif hasattr(related_obj, 'to_dict'):
                            result[rel_name] = related_obj.to_dict(
                                exclude_fields=exclude_fields,
                                include_relationships=include_relationships,
                                max_depth=max_depth - 1
                            )
                        else:
                            result[rel_name] = str(related_obj)

            return result

        def update_from_dict(
                self,
                update_dict: Dict[str, Any],
                allow_partial: bool = True,
                exclude_fields: Optional[List[str]] = None,
                validate: bool = True
        ) -> None:
            """
            Update model instance from a dictionary.

            Args:
                update_dict: Dictionary of fields to update
                allow_partial: Allow partial updates (default True)
                exclude_fields: Optional list of fields to exclude from update
                validate: Whether to validate after update

            Raises:
                ValueError: If update is not allowed and a required field is missing
                ModelValidationError: If validation fails
            """
            exclude_fields = exclude_fields or []
            exclude_fields.extend(['id', 'uuid'])  # Always exclude primary identifiers

            # Get all updatable columns
            updatable_columns = [
                column.name for column in self.__table__.columns
                if column.name not in exclude_fields
                   and not column.primary_key  # Exclude primary key
            ]

            # Validate update
            if not allow_partial:
                # Check if all columns are present
                missing_fields = set(updatable_columns) - set(update_dict.keys())
                if missing_fields:
                    raise ValueError(f"Missing required fields for update: {missing_fields}")

            # Perform update
            for field in updatable_columns:
                if field in update_dict:
                    # Handle enum values
                    value = update_dict[field]
                    if hasattr(self, field):
                        current_value = getattr(self, field)
                        if isinstance(current_value, enum.Enum) and isinstance(value, str):
                            try:
                                # Convert string to enum
                                enum_class = type(current_value)
                                value = enum_class[value]
                            except KeyError:
                                raise ValueError(f"Invalid enum value for {field}: {value}")

                    setattr(self, field, value)

            # Validate if requested
            if validate and hasattr(self, 'validate_and_raise'):
                self.validate_and_raise()

        def soft_delete(self) -> None:
            """
            Perform a soft delete by marking the record as inactive.
            """
            self.is_active = False
            if hasattr(self, 'is_deleted'):
                self.is_deleted = True
                self.deleted_at = datetime.now().astimezone()

            logger.info(f"Soft deleted {self.__class__.__name__} with ID {self.id}")

        def restore(self) -> None:
            """
            Restore a soft-deleted record.
            """
            self.is_active = True
            if hasattr(self, 'is_deleted'):
                self.is_deleted = False
                self.deleted_at = None
                self.deleted_by = None

            logger.info(f"Restored {self.__class__.__name__} with ID {self.id}")

        def clone(
                self,
                session: Optional[Session] = None,
                exclude_fields: Optional[List[str]] = None,
                override_values: Optional[Dict[str, Any]] = None
        ) -> 'BaseModel':
            """
            Create a clone of this record.

            Args:
                session: Optional session to add the clone to
                exclude_fields: Fields to exclude from cloning
                override_values: Values to override in the clone

            Returns:
                Cloned record instance
            """
            exclude = exclude_fields or []
            exclude.extend(['id', 'uuid', 'created_at', 'updated_at'])

            # Get a dictionary of the current instance
            data = self.to_dict(exclude_fields=exclude)

            # Apply overrides
            if override_values:
                data.update(override_values)

            # Create a new instance
            model_class = self.__class__
            clone_instance = model_class(**data)

            # Generate a new UUID
            clone_instance.uuid = str(uuid.uuid4())

            # Add to session if provided
            if session:
                session.add(clone_instance)

            return clone_instance

        @classmethod
        def get_by_id(cls, session: Session, record_id: int) -> Optional['BaseModel']:
            """
            Get a record by its ID.

            Args:
                session: Database session
                record_id: ID of the record to retrieve

            Returns:
                Record instance or None if not found
            """
            return session.query(cls).filter(cls.id == record_id).first()

        @classmethod
        def get_by_uuid(cls, session: Session, record_uuid: str) -> Optional['BaseModel']:
            """
            Get a record by its UUID.

            Args:
                session: Database session
                record_uuid: UUID of the record to retrieve

            Returns:
                Record instance or None if not found
            """
            return session.query(cls).filter(cls.uuid == record_uuid).first()

        @classmethod
        def get_active(cls, session: Session) -> List['BaseModel']:
            """
            Get all active records.

            Args:
                session: Database session

            Returns:
                List of active records
            """
            return session.query(cls).filter(cls.is_active == True).all()

    return BaseModel


# Create the primary base model with comprehensive mixins
Base = create_base_model(
    mixins=[
        ValidationMixin,
        TimestampMixin,
        CostingMixin,
        TrackingMixin,
        ComplianceMixin,
        AuditMixin
    ]
)


class ModelFactory:
    """
    Advanced model creation and configuration factory.

    Provides flexible mechanisms for creating and configuring database models
    with dynamic mixin and base class support.
    """

    @staticmethod
    def create(
            name: str,
            base: Optional[Type] = None,
            mixins: Optional[List[Type]] = None,
            columns: Optional[Dict[str, Any]] = None,
            relationships: Optional[Dict[str, Any]] = None,
            table_args: Optional[Tuple[Any, ...]] = None,
            **kwargs
    ) -> Type:
        """
        Dynamically create a model class with flexible configuration.

        Args:
            name: Name of the model class
            base: Base class to use (defaults to Base)
            mixins: List of additional mixins to apply
            columns: Additional columns to add
            relationships: Relationships to configure
            table_args: Additional table arguments (constraints, indexes, etc.)
            **kwargs: Additional class attributes

        Returns:
            Dynamically created model class
        """
        # Use default Base if not specified
        base = base or Base

        # Prepare mixins
        all_mixins = [base]
        if mixins:
            all_mixins.extend(mixins)

        # Prepare attributes
        attributes = {}

        # Add columns
        if columns:
            attributes.update(columns)

        # Add relationships
        if relationships:
            attributes.update(relationships)

        # Add table_args
        if table_args:
            attributes['__table_args__'] = table_args

        # Add additional attributes
        if kwargs:
            attributes.update(kwargs)

        # Create the model class
        model_class = type(
            name,
            tuple(all_mixins),
            attributes
        )

        # Register the model
        ModelRegistry.register(name, model_class)

        return model_class

    @staticmethod
    def create_association_table(
            name: str,
            left_model: str,
            right_model: str,
            metadata: Optional[MetaData] = None,
            **kwargs
    ) -> Table:
        """
        Create an association table for many-to-many relationships.

        Args:
            name: Name of the association table
            left_model: Name of the left model
            right_model: Name of the right model
            metadata: Metadata object (defaults to the global metadata)
            **kwargs: Additional column definitions

        Returns:
            SQLAlchemy Table object
        """
        # Use global metadata if not specified
        meta = metadata or globals()['metadata']

        # Standardize model names
        left_model_name = left_model.lower()
        right_model_name = right_model.lower()

        # Create the association table
        table = Table(
            name,
            meta,
            Column(f"{left_model_name}_id", Integer, ForeignKey(f"{left_model_name}s.id"), primary_key=True),
            Column(f"{right_model_name}_id", Integer, ForeignKey(f"{right_model_name}s.id"), primary_key=True),
            **kwargs
        )

        return table

    @staticmethod
    def set_event_listeners(
            model_class: Type,
            events: Dict[str, Callable],
    ) -> None:
        """
        Set event listeners for a model class.

        Args:
            model_class: Model class
            events: Dictionary mapping event names to handler functions
        """
        for event_name, handler in events.items():
            if event_name == 'before_insert':
                event.listen(model_class, 'before_insert', handler)
            elif event_name == 'after_insert':
                event.listen(model_class, 'after_insert', handler)
            elif event_name == 'before_update':
                event.listen(model_class, 'before_update', handler)
            elif event_name == 'after_update':
                event.listen(model_class, 'after_update', handler)
            elif event_name == 'before_delete':
                event.listen(model_class, 'before_delete', handler)
            elif event_name == 'after_delete':
                event.listen(model_class, 'after_delete', handler)
            else:
                logger.warning(f"Unknown event name: {event_name}")


def apply_mixins(base_class: Type, *mixins) -> Type:
    """
    Apply mixins to a base class, properly handling method resolution.

    Args:
        base_class: The base class to apply mixins to
        *mixins: Variable number of mixin classes to apply

    Returns:
        New class with mixins applied
    """
    # Start with a copy of the base class attributes
    attrs = {
        name: attr for name, attr in inspect.getmembers(base_class)
        if not name.startswith('__') or name in ('__tablename__', '__table_args__')
    }

    # Apply mixins in reverse order to respect method resolution order
    # Convert to list if it's not already
    mixin_list = list(mixins)

    for mixin in reversed(mixin_list):
        for name, attr in inspect.getmembers(mixin):
            if not name.startswith('__'):
                attrs[name] = attr

    # Create a new class with the base class and mixins
    class_name = base_class.__name__
    new_class = type(
        class_name,
        (base_class,),
        attrs
    )

    logger.debug(f"Applied {len(mixin_list)} mixins to {class_name}")
    return new_class


# Add database events to track model changes
@event.listens_for(Base, 'after_insert', propagate=True)
def after_insert(mapper, connection, target):
    """Log after a record is inserted."""
    logger.info(f"Created {target.__class__.__name__} with ID {target.id}")


@event.listens_for(Base, 'after_update', propagate=True)
def after_update(mapper, connection, target):
    """Log after a record is updated."""
    logger.info(f"Updated {target.__class__.__name__} with ID {target.id}")


@event.listens_for(Base, 'after_delete', propagate=True)
def after_delete(mapper, connection, target):
    """Log after a record is deleted."""
    logger.info(f"Deleted {target.__class__.__name__} with ID {target.id}")




# Export key components
__all__ = [
    'Base',
    'ModelRegistry',
    'ModelFactory',
    'EnhancedMetaclass',
    'create_base_model',
    'ModelValidationError',
    'metadata',
    'mapper_registry',
    'apply_mixins',  # Add this line

    # Mixins
    'ValidationMixin',
    'TimestampMixin',
    'CostingMixin',
    'TrackingMixin',
    'ComplianceMixin',
    'AuditMixin'
]