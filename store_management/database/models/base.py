# database/models/base.py
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import DateTime, Float, Integer, MetaData, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, validates


class Base(DeclarativeBase):
    """Base class for all database models following SQLAlchemy 2.0 standards."""
    metadata = MetaData()


# Move validate_length out of Base to be a standalone function
def validate_length(key, value, max_lengths=None):
    """
    Generic validation method for string length.

    Args:
        key: Field name
        value: Value to validate
        max_lengths: Optional dict of max lengths, defaults to common fields

    Returns:
        The value if validation passes

    Raises:
        ValueError: If validation fails
    """
    if not max_lengths:
        max_lengths = {
            'name': 255,
            'description': 500,
            'email': 255,
            'created_by': 100,
            'last_modified_by': 100
        }

    if isinstance(value, str) and key in max_lengths and len(value) > max_lengths[key]:
        raise ValueError(f"{key} cannot exceed {max_lengths[key]} characters")
    return value


class ModelValidationError(ValueError):
    """Exception raised when model validation fails."""
    pass


class ModelRegistry:
    """Central registry for model classes."""
    _models: Dict[str, type] = {}

    @classmethod
    def register(cls, model: type) -> None:
        """
        Register a model in the central registry.

        Args:
            model (type): The model class to register
        """
        model_name = model.__name__
        cls._models[model_name] = model

    @classmethod
    def get_model(cls, model_name: str) -> Optional[type]:
        """
        Get a model by name from the registry.

        Args:
            model_name (str): Name of the model to retrieve

        Returns:
            Optional[type]: The model class if found, None otherwise
        """
        return cls._models.get(model_name)

    @classmethod
    def get_all_models(cls) -> List[type]:
        """
        Get all registered models.

        Returns:
            List[type]: A list of all registered model classes
        """
        return list(cls._models.values())


class ValidationMixin:
    """Mixin for model validation methods."""

    def validate(self) -> None:
        """
        Validate the model instance.
        Override in subclasses with specific validation logic.

        Raises:
            ModelValidationError: If validation fails
        """
        pass

    # Example of how to properly use validates in a mixin
    @validates('name', 'description', 'email', 'created_by', 'last_modified_by')
    def validate_string_fields(self, key, value):
        """Validate string fields for length."""
        return validate_length(key, value)


class TimestampMixin:
    """Mixin for models that need timestamp tracking."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        onupdate=datetime.utcnow
    )


class CostingMixin:
    """Mixin for models with cost tracking."""

    cost_price: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True
    )

    def calculate_margin(self, selling_price: float) -> float:
        """
        Calculate margin percentage.

        Args:
            selling_price (float): The price at which the item is sold

        Returns:
            float: Margin percentage
        """
        if not self.cost_price or self.cost_price <= 0:
            return 0
        return ((selling_price - self.cost_price) / selling_price) * 100


class TrackingMixin:
    """Mixin for tracking creation and updates."""

    created_by: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )
    last_modified_by: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )


class ComplianceMixin:
    """Mixin for compliance tracking."""

    compliance_verified: Mapped[Optional[bool]] = mapped_column(
        default=False,
        nullable=True
    )
    compliance_notes: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )


class AuditMixin:
    """Mixin for audit tracking."""

    audit_timestamp: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
    )
    audit_user: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )


class AbstractBase(Base, TimestampMixin):
    """Abstract base class for all concrete models."""
    __abstract__ = True

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    def __repr__(self) -> str:
        """
        String representation of the instance.

        Returns:
            str: A string representation of the model instance
        """
        return f"<{self.__class__.__name__}(id={self.id})>"