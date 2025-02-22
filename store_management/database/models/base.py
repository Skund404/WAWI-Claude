"""
File: database/models/base.py
Base model definition for all SQLAlchemy models.
Provides common functionality for model classes.
"""
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import inspect

# Create a single base class for all models
Base = declarative_base()


def to_dict(self):
    """
    Convert model instance to dictionary.

    Returns:
        dict: Dictionary representation of the model
    """
    return {c.key: getattr(self, c.key)
            for c in inspect(self).mapper.column_attrs}


# Add common method to all models
Base.to_dict = to_dict