# File: database/sqlalchemy/migrations/versions/[generate a unique revision ID]_comprehensive_model_relationships.py
"""Comprehensive model relationships

Revision ID: [generate a unique ID]
Revises:
Create Date: [current date]

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite
from enum import Enum

# Import your enum types (if using custom enums)
from database.sqlalchemy.models import InventoryStatus, ProductionStatus, TransactionType


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###

    # Supplier relationships (already exists, just ensuring)
    op.create_table('suppliers',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('name', sa.String(length=100), nullable=False),
                    sa.Column('contact_info', sa.Text(), nullable=True),
                    sa.Column('created_at', sa.DateTime(), nullable=True),
                    sa.Column('modified_at', sa.DateTime(), nullable=True),
                    sa.PrimaryKeyConstraint('id')
                    )

    # Parts table with supplier relationship
    op.create_table('parts',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('name', sa.String(length=100), nullable=False),
                    sa.Column('quantity', sa.Integer(), nullable=True),
                    sa.Column('unit_price', sa.Float(), nullable=True),
                    sa.Column('status', sa.Enum(InventoryStatus), nullable=True),
                    sa.Column('supplier_id', sa.Integer(), nullable=False),
                    sa.Column('created_at', sa.DateTime(), nullable=True),
                    sa.Column('modified_at', sa.DateTime(), nullable=True),
                    sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id'], ondelete='RESTRICT'),
                    sa.PrimaryKeyConstraint('id')
                    )

    # Leather table with supplier relationship
    op.create_table('leathers',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('name', sa.String(length=100), nullable=False),
                    sa.Column('total_area', sa.Float(), nullable=True),
                    sa.Column('available_area', sa.Float(), nullable=True),
                    sa.Column('unit_price', sa.Float(), nullable=True),
                    sa.Column('status', sa.Enum(InventoryStatus), nullable=True),
                    sa.Column('supplier_id', sa.Integer(), nullable=False),
                    sa.Column('created_at', sa.DateTime(), nullable=True),
                    sa.Column('modified_at', sa.DateTime(), nullable=True),
                    sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id'], ondelete='RESTRICT'),
                    sa.PrimaryKeyConstraint('id')
                    )

    # Recipes table
    op.create_table('recipes',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('name', sa.String(length=100), nullable=False),
                    sa.Column('description', sa.Text(), nullable=True),
                    sa.Column('created_at', sa.DateTime(), nullable=True),
                    sa.Column('modified_at', sa.DateTime(), nullable=True),
                    sa.PrimaryKeyConstraint('id')
                    )

    # Recipe Items table
    op.create_table('recipe_items',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('quantity', sa.Float(), nullable=False),
                    sa.Column('recipe_id', sa.Integer(), nullable=False),
                    sa.Column('part_id', sa.Integer(), nullable=True),
                    sa.Column('leather_id', sa.Integer(), nullable=True),
                    sa.Column('created_at', sa.DateTime(), nullable=True),
                    sa.Column('modified_at', sa.DateTime(), nullable=True),
                    sa.ForeignKeyConstraint(['recipe_id'], ['recipes.id'], ondelete='CASCADE'),
                    sa.ForeignKeyConstraint(['part_id'], ['parts.id'], ondelete='RESTRICT'),
                    sa.ForeignKeyConstraint(['leather_id'], ['leathers.id'], ondelete='RESTRICT'),
                    sa.PrimaryKeyConstraint('id')
                    )

    # Production Orders table
    op.create_table('production_orders',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('quantity', sa.Integer(), nullable=False),
                    sa.Column('status', sa.Enum(ProductionStatus), nullable=True),
                    sa.Column('recipe_id', sa.Integer(), nullable=False),
                    sa.Column('created_at', sa.DateTime(), nullable=True),
                    sa.Column('modified_at', sa.DateTime(), nullable=True),
                    sa.ForeignKeyConstraint(['recipe_id'], ['recipes.id'], ondelete='RESTRICT'),
                    sa.PrimaryKeyConstraint('id')
                    )

    # Produced Items table
    op.create_table('produced_items',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('serial_number', sa.String(length=50), nullable=True),
                    sa.Column('production_order_id', sa.Integer(), nullable=False),
                    sa.Column('recipe_id', sa.Integer(), nullable=False),
                    sa.Column('created_at', sa.DateTime(), nullable=True),
                    sa.Column('modified_at', sa.DateTime(), nullable=True),
                    sa.ForeignKeyConstraint(['production_order_id'], ['production_orders.id'], ondelete='CASCADE'),
                    sa.ForeignKeyConstraint(['recipe_id'], ['recipes.id'], ondelete='RESTRICT'),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('serial_number')
                    )

    # Inventory Transactions table
    op.create_table('inventory_transactions',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('quantity', sa.Float(), nullable=False),
                    sa.Column('transaction_type', sa.Enum(TransactionType), nullable=False),
                    sa.Column('notes', sa.Text(), nullable=True),
                    sa.Column('part_id', sa.Integer(), nullable=False),
                    sa.Column('production_order_id', sa.Integer(), nullable=True),
                    sa.Column('created_at', sa.DateTime(), nullable=True),
                    sa.Column('modified_at', sa.DateTime(), nullable=True),
                    sa.ForeignKeyConstraint(['part_id'], ['parts.id'], ondelete='RESTRICT'),
                    sa.ForeignKeyConstraint(['production_order_id'], ['production_orders.id'], ondelete='SET NULL'),
                    sa.PrimaryKeyConstraint('id')
                    )

    # Leather Transactions table
    op.create_table('leather_transactions',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('area', sa.Float(), nullable=False),
                    sa.Column('transaction_type', sa.Enum(TransactionType), nullable=False),
                    sa.Column('notes', sa.Text(), nullable=True),
                    sa.Column('leather_id', sa.Integer(), nullable=False),
                    sa.Column('production_order_id', sa.Integer(), nullable=True),
                    sa.Column('created_at', sa.DateTime(), nullable=True),
                    sa.Column('modified_at', sa.DateTime(), nullable=True),
                    sa.ForeignKeyConstraint(['leather_id'], ['leathers.id'], ondelete='RESTRICT'),
                    sa.ForeignKeyConstraint(['production_order_id'], ['production_orders.id'], ondelete='SET NULL'),
                    sa.PrimaryKeyConstraint('id')
                    )

    # Shopping Lists table
    op.create_table('shopping_lists',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('name', sa.String(length=100), nullable=False),
                    sa.Column('status', sa.String(length=50), nullable=True),
                    sa.Column('created_at', sa.DateTime(), nullable=True),
                    sa.Column('modified_at', sa.DateTime(), nullable=True),
                    sa.PrimaryKeyConstraint('id')
                    )

    # Shopping List Items table
    op.create_table('shopping_list_items',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('quantity', sa.Float(), nullable=False),
                    sa.Column('shopping_list_id', sa.Integer(), nullable=False),
                    sa.Column('part_id', sa.Integer(), nullable=True),
                    sa.Column('leather_id', sa.Integer(), nullable=True),
                    sa.Column('created_at', sa.DateTime(), nullable=True),
                    sa.Column('modified_at', sa.DateTime(), nullable=True),
                    sa.ForeignKeyConstraint(['shopping_list_id'], ['shopping_lists.id'], ondelete='CASCADE'),
                    sa.ForeignKeyConstraint(['part_id'], ['parts.id'], ondelete='RESTRICT'),
                    sa.ForeignKeyConstraint(['leather_id'], ['leathers.id'], ondelete='RESTRICT'),
                    sa.PrimaryKeyConstraint('id')
                    )

    # Orders table
    op.create_table('orders',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('order_date', sa.DateTime(), nullable=True),
                    sa.Column('status', sa.String(length=50), nullable=True),
                    sa.Column('supplier_id', sa.Integer(), nullable=False),
                    sa.Column('created_at', sa.DateTime(), nullable=True),
                    sa.Column('modified_at', sa.DateTime(), nullable=True),
                    sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id'], ondelete='RESTRICT'),
                    sa.PrimaryKeyConstraint('id')
                    )

    # Order Items table
    op.create_table('order_items',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('quantity', sa.Float(), nullable=False),
                    sa.Column('unit_price', sa.Float(), nullable=False),
                    sa.Column('order_id', sa.Integer(), nullable=False),
                    sa.Column('part_id', sa.Integer(), nullable=True),
                    sa.Column('leather_id', sa.Integer(), nullable=True),
                    sa.Column('created_at', sa.DateTime(), nullable=True),
                    sa.Column('modified_at', sa.DateTime(), nullable=True),
                    sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
                    sa.ForeignKeyConstraint(['part_id'], ['parts.id'], ondelete='RESTRICT'),
                    sa.ForeignKeyConstraint(['leather_id'], ['leathers.id'], ondelete='RESTRICT'),
                    sa.PrimaryKeyConstraint('id')
                    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('order_items')
    op.drop_table('orders')
    op.drop_table('shopping_list_items')
    op.drop_table('shopping_lists')
    op.drop_table('leather_transactions')
    op.drop_table('inventory_transactions')
    op.drop_table('produced_items')
    op.drop_table('production_orders')
    op.drop_table('recipe_items')
    op.drop_table('recipes')
    op.drop_table('leathers')
    op.drop_table('parts')
    op.drop_table('suppliers')
    # ### end Alembic commands ###