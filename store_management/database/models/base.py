# Relative path: store_management/database/models/base.py

"""
Base Model Module

Provides foundational classes and mixins for database models
with dependency injection and common functionality.
"""

import logging
from typing import Any, Dict, Optional, Type, TypeVar

from sqlalchemy import Column, Integer, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import declared_attr, DeclarativeMeta

from di.core import inject
from services.interfaces import MaterialService
from utils.logger import get_logger

# Configure logging
logger = get_logger(__name__)

# Type variable for generic model type
T = TypeVar('T')

# Create a base class for declarative models
Base: DeclarativeMeta = declarative_base()


class BaseModel(Base):
    """
    Base model providing common fields and methods for all database models.

    Attributes:
        id (int): Primary key for the model.
        created_at (DateTime): Timestamp of record creation.
        updated_at (DateTime): Timestamp of last record update.
    """
    __abstract__ = True

    # Primary key for all models
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Automatic timestamp tracking
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    @declared_attr
    def __tablename__(cls) -> str:
        """
        Generate table name from the class name.

        Returns:
            str: Lowercase table name derived from the class name.
        """
        return cls.__name__.lower()

    @classmethod
    def create(
        cls,
        material_service: Optional[MaterialService] = None,
        **kwargs
    ) -> 'BaseModel':
        """
        Create a new model instance with optional dependency injection.

        Args:
            material_service (Optional[MaterialService], optional):
                Material service for additional validation or processing.
            **kwargs: Keyword arguments for model instantiation.

        Returns:
            BaseModel: Newly created model instance.
        """
        # Use dependency injection for material service if not provided
        if material_service is None:
            try:
                material_service = inject(MaterialService)()
            except Exception as e:
                logger.error(f"Failed to inject MaterialService: {e}")
                material_service = None

        # Validate and process kwargs if material service is available
        if material_service:
            try:
                validated_kwargs = material_service.validate_model_creation(
                    cls.__name__,
                    kwargs
                )
            except Exception as e:
                logger.warning(f"Validation failed for {cls.__name__}: {e}")
                validated_kwargs = kwargs
        else:
            validated_kwargs = kwargs

        # Create and return the model instance
        return cls(**validated_kwargs)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert model instance to a dictionary representation.

        Returns:
            Dict[str, Any]: Dictionary of model attributes.
        """
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }

    def update(self, **kwargs) -> 'BaseModel':
        """
        Update model instance with provided attributes.

        Args:
            **kwargs: Keyword arguments to update model attributes.

        Returns:
            BaseModel: Updated model instance.
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        return self

    @classmethod
    def get_model_name(cls) -> str:
        """
        Get the name of the model class.

        Returns:
            str: Name of the model class.
        """
        return cls.__name__


def model_factory(base_model: Type[T]) -> Type[T]:
    """
    Create a model factory with additional functionality.

    Args:
        base_model (Type[T]): Base model class to extend.

    Returns:
        Type[T]: Extended model class with additional methods.
    """

    class ExtendedModel(base_model, BaseModel):
        """
        Extended model combining base model with common functionality.
        """
        pass

    return ExtendedModel
