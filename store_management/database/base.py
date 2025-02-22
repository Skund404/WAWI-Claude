# Path: database/base.py
"""
Defines the SQLAlchemy base class for all models.
"""
import logging
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.declarative import declared_attr

logger = logging.getLogger(__name__)

# Create the declarative base
Base = declarative_base()


class BaseModel(Base):
    """
    Base model class that adds common functionality to all models.
    """
    __abstract__ = True

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    def __repr__(self):
        """Create a string representation of the model."""
        attrs = []
        for col in self.__table__.columns:
            attrs.append(f"{col.name}={getattr(self, col.name)}")
        return f"<{self.__class__.__name__}({', '.join(attrs)})>"

    def to_dict(self):
        """Convert the model to a dictionary."""
        result = {}
        for col in self.__table__.columns:
            result[col.name] = getattr(self, col.name)
        return result


logger.debug("Base and BaseModel classes defined")