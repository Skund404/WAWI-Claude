# database/models/base.py
"""
Base model definition for all SQLAlchemy models in the system.
Provides common functionality and base class for all models.
"""

from sqlalchemy import Column, Integer, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

# Create the base class
Base = declarative_base()

class BaseModel(Base):
    """
    Abstract base model that all other models should inherit from.
    Provides common columns and methods.
    """
    __abstract__ = True

    # Common columns for all tables
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        """String representation of the model instance"""
        return f"<{self.__class__.__name__}(id={getattr(self, 'id', None)})>"

    def to_dict(self):
        """
        Convert model instance to dictionary.

        Returns:
            dict: Dictionary representation of the model
        """
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)

            # Handle datetime objects
            if isinstance(value, datetime):
                value = value.isoformat()

            result[column.name] = value

        return result