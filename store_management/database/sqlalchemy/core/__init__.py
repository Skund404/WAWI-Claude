# path: database/sqlalchemy/core/__init__.py
"""
SQLAlchemy core utilities package.

This package provides core SQLAlchemy functionality for the application,
including the Base class for model definitions.
"""

from sqlalchemy.ext.declarative import declarative_base

# Create and export the declarative base
Base = declarative_base()

# Export symbols
__all__ = ['Base']