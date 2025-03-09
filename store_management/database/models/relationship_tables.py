# database/models/relationship_tables.py
from sqlalchemy import Column, ForeignKey, Float, Integer, String, Table, UniqueConstraint
from database.models.base import Base, metadata

# Component-Material relationship
component_material_table = Table(
    'component_materials',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('component_id', Integer, ForeignKey('components.id'), nullable=False),
    Column('material_id', Integer, ForeignKey('materials.id'), nullable=False),
    Column('quantity', Float, nullable=True),
    UniqueConstraint('component_id', 'material_id', name='uix_component_material'),
    extend_existing=True
)

# Product-Pattern relationship
product_pattern_table = Table(
    'product_patterns',
    metadata,
    Column('product_id', Integer, ForeignKey('products.id'), primary_key=True),
    Column('pattern_id', Integer, ForeignKey('patterns.id'), primary_key=True),
    extend_existing=True
)

# Pattern-Component relationship
pattern_component_table = Table(
    'pattern_components',
    metadata,
    Column('pattern_id', Integer, ForeignKey('patterns.id'), primary_key=True),
    Column('component_id', Integer, ForeignKey('components.id'), primary_key=True),
    extend_existing=True
)