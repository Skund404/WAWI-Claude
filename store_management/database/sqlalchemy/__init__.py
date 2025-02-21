# File: store_management/database/sqlalchemy/__init__.py
"""
Initialize SQLAlchemy components for the Store Management System.

This module provides access to core SQLAlchemy models and functionality.
"""

# Attempt safe import of models
try:
    from store_management.database.sqlalchemy.models.product import Product
    from store_management.database.sqlalchemy.models.storage import Storage
except ImportError as e:
    import warnings
    warnings.warn(f"Could not import models: {e}", ImportWarning)
    Product = None
    Storage = None

# Dynamically build __all__ based on successful imports
__all__ = []
if Product is not None:
    __all__.append('Product')
if Storage is not None:
    __all__.append('Storage')