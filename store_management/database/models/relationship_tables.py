# database/models/relationship_tables.py
"""
This module defines association tables for many-to-many relationships in the leatherworking database system.
"""

from sqlalchemy import Table, Column, ForeignKey, Integer, String, Float, UniqueConstraint
from database.models.base import Base

# Association table for Component-Material relationship
component_material_table = Table(
    'component_materials',
    Base.metadata,
    Column('component_id', Integer, ForeignKey('components.id', ondelete='CASCADE'), nullable=False),
    Column('material_id', Integer, ForeignKey('materials.id', ondelete='CASCADE'), nullable=False),
    Column('quantity', Float, nullable=False, default=1.0),
    UniqueConstraint('component_id', 'material_id', name='uq_component_material'),
    extend_existing=True  # This helps avoid "table already exists" errors
)

# Association table for Product-Pattern relationship
product_pattern_table = Table(
    'product_patterns',
    Base.metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('product_id', Integer, ForeignKey('products.id', ondelete='CASCADE'), nullable=False),
    Column('pattern_id', Integer, ForeignKey('patterns.id', ondelete='CASCADE'), nullable=False),
    Column('is_primary', Integer, default=0, nullable=False),
    Column('scale_factor', Float, default=1.0, nullable=False),
    Column('notes', String(255), nullable=True),
    UniqueConstraint('product_id', 'pattern_id', name='uq_product_pattern'),
    extend_existing=True
)

# Association table for Pattern-Component relationship
pattern_component_table = Table(
    'pattern_components',
    Base.metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('pattern_id', Integer, ForeignKey('patterns.id', ondelete='CASCADE'), nullable=False),
    Column('component_id', Integer, ForeignKey('components.id', ondelete='CASCADE'), nullable=False),
    Column('quantity', Float, nullable=False, default=1.0),
    Column('position', String(100), nullable=True),
    Column('notes', String(255), nullable=True),
    UniqueConstraint('pattern_id', 'component_id', name='uq_pattern_component'),
    extend_existing=True
)