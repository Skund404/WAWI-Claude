from di.core import inject
from services.interfaces import (
    MaterialService,
    ProjectService,
    InventoryService,
    OrderService,
)

"""Leatherworking Model Transformation

Revision ID: leatherworking_model_transformation
Revises: previous_revision
Create Date: 2024-02-22

"""
revision = "leatherworking_model_transformation"
down_revision = "previous_revision"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_table("patterns")
    op.drop_table("recipe_items")
    op.create_table(
        "projects",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("version", sa.String(length=20), nullable=True),
        sa.Column(
            "project_type",
            sa.Enum(
                "WALLET",
                "BAG",
                "BELT",
                "JACKET",
                "ACCESSORY",
                "SHOE",
                "GLOVES",
                "CUSTOM",
                name="projecttype",
            ),
            nullable=False,
        ),
        sa.Column(
            "skill_level",
            sa.Enum(
                "BEGINNER", "INTERMEDIATE", "ADVANCED", "MASTER", name="skilllevel"
            ),
            nullable=False,
        ),
        sa.Column(
            "production_status",
            sa.Enum(
                "DESIGN",
                "PROTOTYPE",
                "IN_PRODUCTION",
                "COMPLETED",
                "ON_HOLD",
                name="productionstatus",
            ),
            nullable=True,
        ),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("design_notes", sa.String(length=1000), nullable=True),
        sa.Column("estimated_hours", sa.Float(), nullable=True),
        sa.Column("actual_production_hours", sa.Float(), nullable=True),
        sa.Column("primary_leather_type", sa.String(
            length=100), nullable=True),
        sa.Column("leather_grade", sa.String(length=50), nullable=True),
        sa.Column("estimated_leather_consumption", sa.Float(), nullable=True),
        sa.Column("width", sa.Float(), nullable=True),
        sa.Column("height", sa.Float(), nullable=True),
        sa.Column("depth", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("quality_score", sa.Float(), nullable=True),
        sa.Column("wastage_percentage", sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "project_components",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column(
            "component_type",
            sa.Enum(
                "MAIN_BODY",
                "STRAP",
                "POCKET",
                "LINING",
                "HARDWARE_ATTACHMENT",
                "CLOSURE",
                "DECORATIVE",
                "OTHER",
                name="componenttype",
            ),
            nullable=False,
        ),
        sa.Column("length", sa.Float(), nullable=True),
        sa.Column("width", sa.Float(), nullable=True),
        sa.Column("material_type", sa.String(length=100), nullable=True),
        sa.Column("material_thickness", sa.Float(), nullable=True),
        sa.Column("cutting_pattern_reference",
                  sa.String(length=50), nullable=True),
        sa.Column("estimated_cutting_time", sa.Float(), nullable=True),
        sa.Column("quality_score", sa.Float(), nullable=True),
        sa.Column("wastage_percentage", sa.Float(), nullable=True),
        sa.Column("cutting_instructions", sa.String(
            length=500), nullable=True),
        sa.Column("special_notes", sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "hardware",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("manufacturer", sa.String(length=100), nullable=True),
        sa.Column(
            "hardware_type",
            sa.Enum(
                "BUCKLE",
                "RIVET",
                "SNAP",
                "ZIPPER",
                "D_RING",
                "LOCK",
                "CLASP",
                "BUTTON",
                "HOOK",
                "CHAIN",
                "BRACKET",
                "SLIDER",
                "CONNECTOR",
                "OTHER",
                name="hardwaretype",
            ),
            nullable=False,
        ),
        sa.Column(
            "material",
            sa.Enum(
                "BRASS",
                "STAINLESS_STEEL",
                "NICKEL",
                "BRONZE",
                "ALUMINUM",
                "GOLD_PLATED",
                "SILVER",
                "COPPER",
                "TITANIUM",
                "PLASTIC",
                name="hardwarematerial",
            ),
            nullable=False,
        ),
        sa.Column("width", sa.Float(), nullable=True),
        sa.Column("length", sa.Float(), nullable=True),
        sa.Column("thickness", sa.Float(), nullable=True),
        sa.Column("weight", sa.Float(), nullable=True),
        sa.Column("load_capacity", sa.Float(), nullable=True),
        sa.Column("stock_quantity", sa.Integer(), nullable=True),
        sa.Column("reorder_threshold", sa.Integer(), nullable=True),
        sa.Column("finish_type", sa.String(length=50), nullable=True),
        sa.Column("corrosion_resistance", sa.Float(), nullable=True),
        sa.Column("supplier_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["supplier_id"], ["suppliers.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "project_component_hardware",
        sa.Column("project_component_id", sa.Integer(), nullable=True),
        sa.Column("hardware_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["hardware_id"], ["hardware.id"]),
        sa.ForeignKeyConstraint(["project_component_id"], [
                                "project_components.id"]),
    )

    def downgrade():
        op.drop_table("project_component_hardware")
        op.drop_table("hardware")
        op.drop_table("project_components")
        op.drop_table("projects")
