# File: database/sqlalchemy/models/base.py
# Purpose: Provide base declarative model for SQLAlchemy

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, DateTime
from datetime import datetime

# Create base declarative class
Base = declarative_base()


class BaseModel(Base):
    """
    Abstract base model providing common fields and behaviors.

    Automatically adds:
    - Primary key (id)
    - Creation timestamp
    - Last update timestamp
    """
    __abstract__ = True

    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

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
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }