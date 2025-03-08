from database.models.base import metadata
from sqlalchemy.orm import declarative_base
# database/models/base.py
import logging
from sqlalchemy import Column, DateTime, Integer
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import declared_attr, DeclarativeMeta
from sqlalchemy import func
from typing import Any, Dict, Optional, Type, TypeVar
from utils.logger import get_logger

# Type variable for generic methods
T = TypeVar('T')

# Get a logger for this module
logger = get_logger(__name__)


# Create the base class for SQLAlchemy models
class Base:
    """Base class for all SQLAlchemy models."""

    @declared_attr
    def __tablename__(cls):
        """
        Generates the table name automatically from the class name.

        Returns:
            str: The lowercase class name as the table name.
        """
        return cls.__name__.lower()

    # Common columns for all models
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


# Create the declarative base with our custom Base class
BaseModel = declarative_base()
BaseModel.metadata = metadata


# No need for this class as it creates a duplicate base class issue
# class ExtendedModel(base_model, BaseModel):  <- This was causing the error

# Instead, extend BaseModel directly
class ExtendedModel(BaseModel):
    """
    Extended model class with additional utility methods.

    This class extends the base SQLAlchemy model with additional
    methods for CRUD operations and serialization.
    """

    def to_dict(self, exclude_fields=None) -> Dict[str, Any]:
        """
        Convert the model instance to a dictionary.

        Args:
            exclude_fields: Optional list of field names to exclude

        Returns:
            Dict containing the model data
        """
        if exclude_fields is None:
            exclude_fields = []

        data = {}
        for column in self.__table__.columns:
            if column.name not in exclude_fields:
                data[column.name] = getattr(self, column.name)

        return data

    def update(self, **kwargs):
        """
        Update the model instance with the provided values.

        Args:
            **kwargs: Keyword arguments with field names and values

        Returns:
            self: The updated instance
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                logger.warning(f"Attribute '{key}' not found in {self.__class__.__name__}")

        return self

    @classmethod
    def create(cls, **kwargs):
        """
        Create a new instance of the model.

        Args:
            **kwargs: Keyword arguments with field names and values

        Returns:
            A new instance of the model
        """
        return cls(**kwargs)

    def __repr__(self):
        """
        String representation of the model.

        Returns:
            str: A string representation including class name and ID
        """
        return f"<{self.__class__.__name__} id={self.id}>"