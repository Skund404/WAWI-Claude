# database/models/base.py
from sqlalchemy import Column, DateTime, Float, Integer, MetaData, String, func
from sqlalchemy.ext.declarative import DeclarativeBase
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from typing import Any, Dict, List, Optional, Type, TypeVar

metadata = MetaData()


class Base(DeclarativeBase):
    """Base class for all database models."""
    metadata = metadata


class ModelValidationError(Exception):
    """Exception raised when model validation fails."""
    pass


class ModelRegistry:
    """Central registry for model classes."""
    _models: Dict[str, Type[Any]] = {}

    @classmethod
    def register(cls, model: Type) -> None:
        """Register a model in the central registry."""
        model_name = model.__name__
        cls._models[model_name] = model

    @classmethod
    def get_model(cls, model_name: str) -> Optional[Type]:
        """Get a model by name from the registry."""
        return cls._models.get(model_name)

    @classmethod
    def get_all_models(cls) -> List[Type]:
        """Get all registered models."""
        return list(cls._models.values())


class ValidationMixin:
    """Mixin for model validation methods."""

    def validate(self) -> None:
        """Validate the model instance. Override in subclasses."""
        pass


class TimestampMixin:
    """Mixin for models that need timestamp tracking."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, onupdate=datetime.now
    )


class CostingMixin:
    """Mixin for models with cost tracking."""

    cost_price: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )

    def calculate_margin(self, selling_price: float) -> float:
        """Calculate margin percentage."""
        if not self.cost_price or self.cost_price <= 0:
            return 0
        return ((selling_price - self.cost_price) / selling_price) * 100


class TrackingMixin:
    """Mixin for tracking creation and updates."""

    created_by: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )
    last_modified_by: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )


class ComplianceMixin:
    """Mixin for compliance tracking."""

    compliance_verified: Mapped[Optional[bool]] = mapped_column(
        default=False, nullable=True
    )
    compliance_notes: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True
    )


class AuditMixin:
    """Mixin for audit tracking."""

    audit_timestamp: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    audit_user: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )


class AbstractBase(Base, TimestampMixin):
    """Abstract base class for all concrete models."""
    __abstract__ = True

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )

    def __repr__(self) -> str:
        """String representation of the instance."""
        return f"<{self.__class__.__name__}(id={self.id})>"