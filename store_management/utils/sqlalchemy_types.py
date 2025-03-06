# utils/sqlalchemy_types.py
"""
Module containing SQLAlchemy types used throughout the application.

This module provides a centralized place for all SQLAlchemy type definitions
and ensures they are properly imported and available to avoid circular import issues.
"""

# Define SQLAlchemy types directly as variables
# Import actual SQLAlchemy types if available or use dummy types otherwise
try:
    from sqlalchemy import (
        Boolean, Column, DateTime, Enum, Float, ForeignKey,
        Integer, JSON, MetaData, String, Text
    )
    from sqlalchemy.orm import (
        DeclarativeBase, Mapped, Session, mapped_column, relationship
    )

    HAS_SQLALCHEMY = True
except ImportError:
    # Create dummy types if SQLAlchemy is not available
    class DummyType:
        def __init__(self, *args, **kwargs):
            pass


    Boolean = DummyType
    Column = DummyType
    DateTime = DummyType
    Enum = DummyType
    Float = DummyType
    ForeignKey = DummyType
    Integer = DummyType
    JSON = DummyType
    MetaData = DummyType
    String = DummyType
    Text = DummyType


    class DeclarativeBase:
        pass


    class Mapped:
        pass


    class Session:
        pass


    def mapped_column(*args, **kwargs):
        pass


    def relationship(*args, **kwargs):
        pass


    HAS_SQLALCHEMY = False

# Export all the types
__all__ = [
    'Boolean', 'Column', 'DateTime', 'Enum', 'Float', 'ForeignKey',
    'Integer', 'JSON', 'MetaData', 'String', 'Text',
    'DeclarativeBase', 'Mapped', 'Session', 'mapped_column', 'relationship',
    'HAS_SQLALCHEMY'
]