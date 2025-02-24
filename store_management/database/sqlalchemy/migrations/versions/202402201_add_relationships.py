# database/sqlalchemy/migrations/versions/202402201_add_relationships.py

"""Add relationships and constraints to models

Revision ID: 202402201
Revises: previous_revision
Create Date: 2024-02-20
"""

from alembic import op
import sqlalchemy as sa
from datetime import datetime
from sqlalchemy.dialects import sqlite

# Import enums
from database.sqlalchemy.models_file import InventoryStatus, ProductionStatus

# revision identifiers, used by Alembic.
revision = '202402201'
down_revision = 'previous_revision'
branch_labels = None
depends_on = None


def upgrade():
    # Create enum types (if using PostgreSQL)
    # For SQLite, we'll use string representation

    # Add supplier_id to Leather table
    with op.batch_alter_table('leather') as batch_op:
        batch_op.add_column(sa.Column('supplier_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'fk_leather_supplier', 'suppliers',
            ['supplier_id'], ['id'],
            ondelete='RESTRICT'
        )
        batch_op.create_index('idx_leather_supplier', ['supplier_id'])
        batch_op.add_column(sa.Column('status', sa.String(20), nullable=True))
        batch_op.add_column(sa.Column('minimum_area', sa.Float(), nullable=True))

        # Set default values for new columns
        op.execute("UPDATE leather SET status = 'in_stock' WHERE status IS NULL")
        op.execute("UPDATE leather SET minimum_area = 0 WHERE minimum_area IS NULL")

        # Make columns non-nullable after setting defaults
        batch_op.alter_column('status', nullable=False)
        batch_op.create_index('idx_leather_status', ['status'])

    # Update ProductionOrder table
    with op.batch_alter_table('production_orders') as batch_op:
        batch_op.add_column(sa.Column('recipe_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('status', sa.String(20), nullable=True))
        batch_op.add_column(sa.Column('start_date', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('completion_date', sa.DateTime(), nullable=True))

        batch_op.create_foreign_key(
            'fk_production_recipe', 'patterns',
            ['recipe_id'], ['id'],
            ondelete='RESTRICT'
        )

        # Set default values
        op.execute("UPDATE production_orders SET status = 'planned' WHERE status IS NULL")

        # Make columns non-nullable after setting defaults
        batch_op.alter_column('recipe_id', nullable=False)
        batch_op.alter_column('status', nullable=False)

        batch_op.create_index('idx_production_status', ['status'])
        batch_op.create_index('idx_production_dates', ['start_date', 'completion_date'])

    # Update ProducedItem table
    with op.batch_alter_table('produced_items') as batch_op:
        batch_op.add_column(sa.Column('recipe_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('serial_number', sa.String(50), nullable=True))
        batch_op.add_column(sa.Column('quality_check_passed', sa.Boolean(), nullable=True))

        batch_op.create_foreign_key(
            'fk_produced_recipe', 'patterns',
            ['recipe_id'], ['id'],
            ondelete='RESTRICT'
        )

        batch_op.create_unique_constraint('uq_produced_serial', ['serial_number'])
        batch_op.create_index('idx_produced_serial', ['serial_number'])

    # Update Project table
    with op.batch_alter_table('patterns') as batch_op:
        batch_op.add_column(sa.Column('version', sa.String(20), nullable=True))
        batch_op.add_column(sa.Column('is_active', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('category', sa.String(50), nullable=True))

        # Set default values
        op.execute("UPDATE patterns SET is_active = TRUE WHERE is_active IS NULL")
        op.execute("UPDATE patterns SET version = '1.0' WHERE version IS NULL")

        batch_op.create_unique_constraint('uq_recipe_name_version', ['name', 'version'])
        batch_op.create_index('idx_recipe_category', ['category'])

    # Update Order table
    with op.batch_alter_table('orders') as batch_op:
        batch_op.add_column(sa.Column('supplier_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('expected_delivery', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('total_amount', sa.Numeric(10, 2), nullable=True))

        batch_op.create_foreign_key(
            'fk_order_supplier', 'suppliers',
            ['supplier_id'], ['id'],
            ondelete='RESTRICT'
        )

        batch_op.create_index('idx_order_supplier', ['supplier_id'])
        batch_op.create_index('idx_order_dates', ['order_date', 'expected_delivery'])


def downgrade():
    # Remove added indexes
    with op.batch_alter_table('leather') as batch_op:
        batch_op.drop_index('idx_leather_supplier')
        batch_op.drop_index('idx_leather_status')
        batch_op.drop_constraint('fk_leather_supplier')
        batch_op.drop_column('supplier_id')
        batch_op.drop_column('status')
        batch_op.drop_column('minimum_area')

    with op.batch_alter_table('production_orders') as batch_op:
        batch_op.drop_index('idx_production_status')
        batch_op.drop_index('idx_production_dates')
        batch_op.drop_constraint('fk_production_recipe')
        batch_op.drop_column('recipe_id')
        batch_op.drop_column('status')
        batch_op.drop_column('start_date')
        batch_op.drop_column('completion_date')

    with op.batch_alter_table('produced_items') as batch_op:
        batch_op.drop_index('idx_produced_serial')
        batch_op.drop_constraint('uq_produced_serial')
        batch_op.drop_constraint('fk_produced_recipe')
        batch_op.drop_column('recipe_id')
        batch_op.drop_column('serial_number')
        batch_op.drop_column('quality_check_passed')

    with op.batch_alter_table('patterns') as batch_op:
        batch_op.drop_index('idx_recipe_category')
        batch_op.drop_constraint('uq_recipe_name_version')
        batch_op.drop_column('version')
        batch_op.drop_column('is_active')
        batch_op.drop_column('category')

    with op.batch_alter_table('orders') as batch_op:
        batch_op.drop_index('idx_order_supplier')
        batch_op.drop_index('idx_order_dates')
        batch_op.drop_constraint('fk_order_supplier')
        batch_op.drop_column('supplier_id')
        batch_op.drop_column('expected_delivery')
        batch_op.drop_column('total_amount')