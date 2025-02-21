# File: F:\WAWI Homebrew\WAWI Claude\store_management\database\sqlalchemy\models\base.py

"""
This file defines the Base class for SQLAlchemy models.
"""

from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, DateTime
from datetime import datetime

class Base(DeclarativeBase):
    """
    Base declarative model for all database models.
    Provides common fields and behaviors.
    """

    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        """
        Default string representation of the model.

        Returns:
            String representation with class name and ID
        """
        return f"<{self.__class__.__name__}(id={self.id})>"

    def to_dict(self):
        """
        Convert model instance to dictionary.

        Returns:
            Dictionary representation of the model
        """
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}