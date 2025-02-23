# database/sqlalchemy/migrations/versions/20240222_add_metrics_tables.py
"""Add metrics tables

Revision ID: 20240222_metrics
Revises: 20240222_leatherworking_model_transformation
Create Date: 2024-02-22
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20240222_metrics'
down_revision = '20240222_leatherworking_model_transformation'
branch_labels = None
depends_on = None


def upgrade():
    # Create MetricType enum
    op.execute("CREATE TYPE metrictype AS ENUM ('inventory', 'project', 'material', 'supplier')")

    # Create TimeFrame enum
    op.execute("CREATE TYPE timeframe AS ENUM ('daily', 'weekly', 'monthly')")

    # Create metric_snapshots table
    op.create_table(
        'metric_snapshots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('metric_type', postgresql.ENUM('inventory', 'project', 'material', 'supplier', name='metrictype'),
                  nullable=False),
        sa.Column('time_frame', postgresql.ENUM('daily', 'weekly', 'monthly', name='timeframe'), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),

        # Inventory metrics
        sa.Column('leather_stock_level', sa.Float(), nullable=True),
        sa.Column('hardware_stock_level', sa.Float(), nullable=True),
        sa.Column('low_stock_count', sa.Integer(), nullable=True),
        sa.Column('pending_orders', sa.Integer(), nullable=True),

        # Project metrics
        sa.Column('active_projects', sa.Integer(), nullable=True),
        sa.Column('completed_projects', sa.Integer(), nullable=True),
        sa.Column('completion_rate', sa.Float(), nullable=True),
        sa.Column('delayed_projects', sa.Integer(), nullable=True),

        # Material metrics
        sa.Column('material_usage', sa.Float(), nullable=True),
        sa.Column('material_waste', sa.Float(), nullable=True),
        sa.Column('material_efficiency', sa.Float(), nullable=True),

        # Supplier metrics
        sa.Column('supplier_id', sa.Integer(), nullable=True),
        sa.Column('quality_score', sa.Float(), nullable=True),
        sa.Column('delivery_score', sa.Float(), nullable=True),
        sa.Column('price_score', sa.Float(), nullable=True),
        sa.Column('response_score', sa.Float(), nullable=True),

        # Add created_at and updated_at from BaseModel
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id'], )
    )

    # Create material_usage_logs table
    op.create_table(
        'material_usage_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('material_id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('quantity_used', sa.Float(), nullable=False),
        sa.Column('waste_amount', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('efficiency', sa.Float(), nullable=True),
        sa.Column('notes', sa.String(length=500), nullable=True),

        # Add created_at and updated_at from BaseModel
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['material_id'], ['materials.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], )
    )

    # Create indexes
    op.create_index('ix_metric_snapshots_timestamp', 'metric_snapshots', ['timestamp'])
    op.create_index('ix_metric_snapshots_metric_type', 'metric_snapshots', ['metric_type'])
    op.create_index('ix_material_usage_logs_timestamp', 'material_usage_logs', ['timestamp'])
    op.create_index('ix_material_usage_logs_material_id', 'material_usage_logs', ['material_id'])


def downgrade():
    # Drop tables
    op.drop_table('material_usage_logs')
    op.drop_table('metric_snapshots')

    # Drop enums
    op.execute('DROP TYPE timeframe')
    op.execute('DROP TYPE metrictype')