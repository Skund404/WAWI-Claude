#!/usr/bin/env python
# simplified_initialize_database.py
"""
Simplified database initialization script for the leatherworking application.
This version creates tables directly in the correct order to avoid foreign key issues.
"""

import argparse
import importlib
import logging
import os
import sys
import traceback
from pathlib import Path
from datetime import datetime, timedelta
import json

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

# Configure logging
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_database_path() -> str:
    """
    Determine the path for the SQLite database.

    Returns:
        str: Absolute path to the database file
    """
    base_dir = Path(__file__).resolve().parent
    return str(base_dir / 'leatherworking_database.db')


def import_models_directly():
    """
    Import models directly to avoid circular imports and initialization issues.

    Returns:
        tuple: (success_flag, dictionary of model classes)
    """
    try:
        # First import base
        from database.models.base import Base
        logger.info("Base model imported successfully")

        # Import models in dependency order
        import database.models.enums
        from database.models.enums import (
            MaterialType, SupplierStatus, CustomerStatus,
            ComponentType, SkillLevel, ProjectType, ProjectStatus,
            SaleStatus, PaymentStatus, InventoryStatus, TransactionType,
            InventoryAdjustmentType, PickingListStatus, ToolListStatus,
            PurchaseStatus
        )

        from database.models.supplier import Supplier
        from database.models.customer import Customer
        from database.models.material import Material, Leather, Hardware, Supplies
        from database.models.component import Component

        # Critical: Import component_material directly to ensure the table is properly registered
        from database.models.component_material import component_material_table, ComponentMaterial

        from database.models.tool import Tool

        # Import the new models
        from database.models.pattern import Pattern, pattern_component_table
        from database.models.product import Product, product_pattern_table
        from database.models.project import Project
        from database.models.project_component import ProjectComponent
        from database.models.sales import Sales
        from database.models.sales_item import SalesItem
        from database.models.inventory import Inventory
        from database.models.picking_list import PickingList
        from database.models.picking_list_item import PickingListItem
        from database.models.tool_list import ToolList
        from database.models.tool_list_item import ToolListItem
        from database.models.purchase import Purchase
        from database.models.purchase_item import PurchaseItem

        models = {
            'Base': Base,
            'Supplier': Supplier,
            'Customer': Customer,
            'Material': Material,
            'Leather': Leather,
            'Hardware': Hardware,
            'Supplies': Supplies,
            'Component': Component,
            'component_material_table': component_material_table,
            'ComponentMaterial': ComponentMaterial,
            'Tool': Tool,
            'Pattern': Pattern,
            'pattern_component_table': pattern_component_table,
            'Product': Product,
            'product_pattern_table': product_pattern_table,
            'Project': Project,
            'ProjectComponent': ProjectComponent,
            'Sales': Sales,
            'SalesItem': SalesItem,
            'Inventory': Inventory,
            'PickingList': PickingList,
            'PickingListItem': PickingListItem,
            'ToolList': ToolList,
            'ToolListItem': ToolListItem,
            'Purchase': Purchase,
            'PurchaseItem': PurchaseItem,
            'MaterialType': MaterialType,
            'SupplierStatus': SupplierStatus,
            'CustomerStatus': CustomerStatus,
            'ComponentType': ComponentType,
            'SkillLevel': SkillLevel,
            'ProjectType': ProjectType,
            'ProjectStatus': ProjectStatus,
            'SaleStatus': SaleStatus,
            'PaymentStatus': PaymentStatus,
            'InventoryStatus': InventoryStatus,
            'TransactionType': TransactionType,
            'InventoryAdjustmentType': InventoryAdjustmentType,
            'PickingListStatus': PickingListStatus,
            'ToolListStatus': ToolListStatus,
            'PurchaseStatus': PurchaseStatus
        }

        logger.info("Core models imported successfully")
        return True, models
    except Exception as e:
        logger.error(f"Failed to import models: {e}")
        traceback.print_exc()
        return False, {}


def initialize_database(recreate: bool = False) -> bool:
    """
    Initialize a minimal database by creating tables directly in the correct order.

    Args:
        recreate (bool): Whether to recreate the database from scratch

    Returns:
        bool: True if database was initialized successfully
    """
    try:
        # Import models directly
        success, models = import_models_directly()
        if not success:
            return False

        Base = models['Base']

        # Get database path
        db_path = get_database_path()
        logger.info(f"Using database path: {db_path}")

        # Create backup before recreation if database exists
        if os.path.exists(db_path) and recreate:
            from datetime import datetime
            backup_dir = os.path.join(os.path.dirname(db_path), 'database', 'backups')
            os.makedirs(backup_dir, exist_ok=True)

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = os.path.join(backup_dir, f"db_backup_before_direct_init_{timestamp}.db")

            import shutil
            shutil.copy2(db_path, backup_path)
            logger.info(f"Database backed up to {backup_path}")

        # Create database connection
        connection_string = f"sqlite:///{db_path}"
        engine_args = {
            'echo': False,
            'connect_args': {
                'check_same_thread': False,
                'timeout': 30
            }
        }

        engine = create_engine(connection_string, **engine_args)

        # Drop all tables if recreate is True
        if recreate:
            try:
                # Use direct SQL to drop tables in the correct order to avoid circular dependency issues
                with engine.connect() as conn:
                    # Drop order: dependent tables first, then base tables
                    tables_to_drop = [
                        'purchase_items', 'purchases',
                        'tool_list_items', 'tool_lists',
                        'picking_list_items', 'picking_lists',
                        'project_components', 'projects',
                        'sales_items', 'inventory',
                        'product_patterns', 'pattern_components', 'component_materials',
                        'sales', 'products', 'patterns',
                        'components', 'materials', 'tools',
                        'suppliers', 'customers'
                    ]

                    for table in tables_to_drop:
                        try:
                            conn.execute(text(f"DROP TABLE IF EXISTS {table}"))
                            logger.info(f"Dropped table: {table}")
                        except Exception as e:
                            logger.warning(f"Could not drop table {table}: {e}")

                    conn.commit()
                logger.info("Existing tables dropped successfully")
            except Exception as e:
                logger.error(f"Error dropping tables: {e}")
                raise

        # -------- CREATE TABLES IN DEPENDENCY ORDER ----------

        # Phase 1: Create base tables with no dependencies
        base_tables = [
            'suppliers', 'customers', 'materials', 'components', 'tools',
            'patterns', 'products'
        ]

        for table_name in base_tables:
            try:
                if table_name in Base.metadata.tables:
                    Base.metadata.tables[table_name].create(engine, checkfirst=True)
                    logger.info(f"Created {table_name} table")
            except Exception as e:
                logger.error(f"Error creating {table_name} table: {e}")

        # Phase 2: Create sales table explicitly before other tables that depend on it
        try:
            # Create sales table using direct SQL to avoid any issues
            with engine.connect() as conn:
                conn.execute(text("""
                CREATE TABLE IF NOT EXISTS sales (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    total_amount FLOAT NOT NULL DEFAULT 0.0,
                    status VARCHAR(50) NOT NULL,
                    payment_status VARCHAR(50) NOT NULL,
                    customer_id INTEGER,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL,
                    cost_price FLOAT,
                    FOREIGN KEY(customer_id) REFERENCES customers(id) ON DELETE SET NULL
                )
                """))
                conn.commit()
            logger.info("Created sales table using direct SQL")
        except Exception as e:
            logger.error(f"Error creating sales table with direct SQL: {e}")

        # Phase 3: Create junction tables that depend on base tables
        junction_tables = [
            'component_materials', 'pattern_components', 'product_patterns'
        ]

        for table_name in junction_tables:
            try:
                if table_name == 'component_materials':
                    models['ComponentMaterial'].__table__.create(engine, checkfirst=True)
                    logger.info(f"Created {table_name} table")
                elif table_name in Base.metadata.tables:
                    Base.metadata.tables[table_name].create(engine, checkfirst=True)
                    logger.info(f"Created {table_name} table")
            except Exception as e:
                logger.error(f"Error creating {table_name} table: {e}")

                # Fallback to direct SQL
                try:
                    with engine.connect() as conn:
                        if table_name == 'component_materials':
                            conn.execute(text("""
                            CREATE TABLE IF NOT EXISTS component_materials (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                component_id INTEGER NOT NULL,
                                material_id INTEGER NOT NULL,
                                quantity FLOAT NOT NULL DEFAULT 1.0,
                                FOREIGN KEY(component_id) REFERENCES components (id) ON DELETE CASCADE,
                                FOREIGN KEY(material_id) REFERENCES materials (id) ON DELETE CASCADE,
                                UNIQUE (component_id, material_id)
                            )
                            """))
                        elif table_name == 'pattern_components':
                            conn.execute(text("""
                            CREATE TABLE IF NOT EXISTS pattern_components (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                pattern_id INTEGER NOT NULL,
                                component_id INTEGER NOT NULL,
                                quantity FLOAT NOT NULL DEFAULT 1.0,
                                position VARCHAR(100),
                                notes VARCHAR(255),
                                FOREIGN KEY(pattern_id) REFERENCES patterns (id) ON DELETE CASCADE,
                                FOREIGN KEY(component_id) REFERENCES components (id) ON DELETE CASCADE,
                                UNIQUE (pattern_id, component_id)
                            )
                            """))
                        elif table_name == 'product_patterns':
                            conn.execute(text("""
                            CREATE TABLE IF NOT EXISTS product_patterns (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                product_id INTEGER NOT NULL,
                                pattern_id INTEGER NOT NULL,
                                is_primary INTEGER NOT NULL DEFAULT 0,
                                scale_factor FLOAT NOT NULL DEFAULT 1.0,
                                notes VARCHAR(255),
                                FOREIGN KEY(product_id) REFERENCES products (id) ON DELETE CASCADE,
                                FOREIGN KEY(pattern_id) REFERENCES patterns (id) ON DELETE CASCADE,
                                UNIQUE (product_id, pattern_id)
                            )
                            """))
                        conn.commit()
                        logger.info(f"Created {table_name} table using direct SQL")
                except Exception as e2:
                    logger.error(f"Error creating {table_name} table with direct SQL: {e2}")

        # Phase 4: Create sales_items table which depends on sales
        try:
            # Always create with direct SQL to ensure proper dependencies
            with engine.connect() as conn:
                conn.execute(text("""
                CREATE TABLE IF NOT EXISTS sales_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    quantity INTEGER NOT NULL DEFAULT 1,
                    price FLOAT NOT NULL DEFAULT 0.0,
                    sales_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL,
                    FOREIGN KEY(sales_id) REFERENCES sales(id) ON DELETE CASCADE,
                    FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE
                )
                """))
                conn.commit()
            logger.info("Created sales_items table using direct SQL")
        except Exception as e:
            logger.error(f"Error creating sales_items table with direct SQL: {e}")

        # Phase 5: Create tables with circular dependencies (projects and project_components)
        try:
            # Create projects table
            with engine.connect() as conn:
                conn.execute(text("""
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    type VARCHAR(50) NOT NULL,
                    status VARCHAR(50) NOT NULL DEFAULT 'PLANNED',
                    start_date TIMESTAMP,
                    end_date TIMESTAMP,
                    sales_id INTEGER,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL,
                    FOREIGN KEY(sales_id) REFERENCES sales(id) ON DELETE SET NULL
                )
                """))
                conn.commit()
                logger.info("Created projects table using direct SQL")
        except Exception as e:
            logger.error(f"Error creating projects table: {e}")

        try:
            # Create project_components table
            with engine.connect() as conn:
                conn.execute(text("""
                CREATE TABLE IF NOT EXISTS project_components (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    component_id INTEGER NOT NULL,
                    quantity FLOAT NOT NULL DEFAULT 1.0,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL,
                    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE,
                    FOREIGN KEY(component_id) REFERENCES components(id) ON DELETE CASCADE,
                    UNIQUE(project_id, component_id)
                )
                """))
                conn.commit()
                logger.info("Created project_components table using direct SQL")
        except Exception as e:
            logger.error(f"Error creating project_components table: {e}")

        # Phase 6: Create inventory table which depends on materials, products, and tools
        try:
            # Create inventory table
            with engine.connect() as conn:
                conn.execute(text("""
                CREATE TABLE IF NOT EXISTS inventory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_type VARCHAR(50) NOT NULL,
                    item_id INTEGER NOT NULL,
                    quantity FLOAT NOT NULL DEFAULT 0,
                    status VARCHAR(50) NOT NULL,
                    min_stock_level FLOAT,
                    reorder_point FLOAT,
                    reorder_quantity FLOAT,
                    storage_location VARCHAR(255),
                    location_details JSON,
                    last_count_date TIMESTAMP,
                    last_movement_date TIMESTAMP,
                    transaction_history JSON,
                    unit_cost FLOAT,
                    notes TEXT,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL,
                    created_by VARCHAR(100),
                    updated_by VARCHAR(100),
                    UNIQUE(item_type, item_id),
                    CHECK(item_type IN ('material', 'product', 'tool'))
                )
                """))
                conn.commit()
            logger.info("Created inventory table using direct SQL")
        except Exception as e:
            logger.error(f"Error creating inventory table: {e}")

        # Phase 7: Create picking lists and picking list items tables
        try:
            # Create picking lists table
            with engine.connect() as conn:
                conn.execute(text("""
                CREATE TABLE IF NOT EXISTS picking_lists (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sales_id INTEGER,
                    status VARCHAR(50) NOT NULL DEFAULT 'DRAFT',
                    completed_at TIMESTAMP,
                    notes TEXT,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL,
                    created_by VARCHAR(100),
                    updated_by VARCHAR(100),
                    FOREIGN KEY(sales_id) REFERENCES sales(id) ON DELETE SET NULL
                )
                """))
                conn.commit()
            logger.info("Created picking_lists table using direct SQL")
        except Exception as e:
            logger.error(f"Error creating picking_lists table: {e}")

        try:
            # Create picking list items table
            with engine.connect() as conn:
                conn.execute(text("""
                CREATE TABLE IF NOT EXISTS picking_list_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    picking_list_id INTEGER NOT NULL,
                    component_id INTEGER,
                    material_id INTEGER,
                    quantity_ordered INTEGER NOT NULL,
                    quantity_picked INTEGER NOT NULL DEFAULT 0,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL,
                    created_by VARCHAR(100),
                    updated_by VARCHAR(100),
                    FOREIGN KEY(picking_list_id) REFERENCES picking_lists(id) ON DELETE CASCADE,
                    FOREIGN KEY(component_id) REFERENCES components(id) ON DELETE SET NULL,
                    FOREIGN KEY(material_id) REFERENCES materials(id) ON DELETE SET NULL,
                    CHECK((component_id IS NULL AND material_id IS NOT NULL) OR (component_id IS NOT NULL AND material_id IS NULL))
                )
                """))
                conn.commit()
            logger.info("Created picking_list_items table using direct SQL")
        except Exception as e:
            logger.error(f"Error creating picking_list_items table: {e}")

        # Phase 8: Create tool lists and tool list items tables
        try:
            # Create tool lists table
            with engine.connect() as conn:
                conn.execute(text("""
                CREATE TABLE IF NOT EXISTS tool_lists (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    status VARCHAR(50) NOT NULL DEFAULT 'DRAFT',
                    notes TEXT,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL,
                    created_by VARCHAR(100),
                    updated_by VARCHAR(100),
                    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
                )
                """))
                conn.commit()
            logger.info("Created tool_lists table using direct SQL")
        except Exception as e:
            logger.error(f"Error creating tool_lists table: {e}")

        try:
            # Create tool list items table
            with engine.connect() as conn:
                conn.execute(text("""
                CREATE TABLE IF NOT EXISTS tool_list_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tool_list_id INTEGER NOT NULL,
                    tool_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL DEFAULT 1,
                    is_checked_out INTEGER NOT NULL DEFAULT 0,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL,
                    created_by VARCHAR(100),
                    updated_by VARCHAR(100),
                    FOREIGN KEY(tool_list_id) REFERENCES tool_lists(id) ON DELETE CASCADE,
                    FOREIGN KEY(tool_id) REFERENCES tools(id) ON DELETE CASCADE
                )
                """))
                conn.commit()
            logger.info("Created tool_list_items table using direct SQL")
        except Exception as e:
            logger.error(f"Error creating tool_list_items table: {e}")

        # Phase 9: Create purchases and purchase items tables
        try:
            # Create purchases table
            with engine.connect() as conn:
                conn.execute(text("""
                CREATE TABLE IF NOT EXISTS purchases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    supplier_id INTEGER NOT NULL,
                    total_amount FLOAT NOT NULL DEFAULT 0.0,
                    status VARCHAR(50) NOT NULL DEFAULT 'DRAFT',
                    notes TEXT,
                    order_date TIMESTAMP,
                    expected_delivery TIMESTAMP,
                    delivery_date TIMESTAMP,
                    purchase_order_number VARCHAR(100),
                    invoice_number VARCHAR(100),
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL,
                    created_by VARCHAR(100),
                    updated_by VARCHAR(100),
                    FOREIGN KEY(supplier_id) REFERENCES suppliers(id) ON DELETE CASCADE
                )
                """))
                conn.commit()
            logger.info("Created purchases table using direct SQL")
        except Exception as e:
            logger.error(f"Error creating purchases table: {e}")

        try:
            # Create purchase_items table
            with engine.connect() as conn:
                conn.execute(text("""
                CREATE TABLE IF NOT EXISTS purchase_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    purchase_id INTEGER NOT NULL,
                    item_type VARCHAR(50) NOT NULL,
                    item_id INTEGER NOT NULL,
                    quantity FLOAT NOT NULL,
                    price FLOAT NOT NULL,
                    received_quantity FLOAT NOT NULL DEFAULT 0.0,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL,
                    created_by VARCHAR(100),
                    updated_by VARCHAR(100),
                    FOREIGN KEY(purchase_id) REFERENCES purchases(id) ON DELETE CASCADE,
                    CHECK(item_type IN ('material', 'tool'))
                )
                """))
                conn.commit()
            logger.info("Created purchase_items table using direct SQL")
        except Exception as e:
            logger.error(f"Error creating purchase_items table: {e}")

        # Verify created tables
        inspector = inspect(engine)
        created_tables = set(inspector.get_table_names())
        essential_tables = {
            'suppliers', 'customers', 'materials', 'components', 'tools',
            'component_materials', 'patterns', 'products', 'pattern_components',
            'product_patterns', 'projects', 'project_components', 'sales',
            'sales_items', 'inventory', 'picking_lists', 'picking_list_items',
            'tool_lists', 'tool_list_items', 'purchases', 'purchase_items'
        }
        missing_tables = essential_tables - created_tables

        if missing_tables:
            logger.warning(f"Some essential tables were not created: {missing_tables}")

            # Last ditch effort to create missing tables
            for table_name in missing_tables:
                logger.warning(f"Attempting to create missing table: {table_name}")
                try:
                    with engine.connect() as conn:
                        if table_name == 'projects':
                            conn.execute(text("""
                            CREATE TABLE IF NOT EXISTS projects (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                name VARCHAR(255) NOT NULL,
                                description TEXT,
                                type VARCHAR(50) NOT NULL,
                                status VARCHAR(50) NOT NULL DEFAULT 'PLANNED',
                                start_date TIMESTAMP,
                                end_date TIMESTAMP,
                                sales_id INTEGER,
                                created_at TIMESTAMP NOT NULL,
                                updated_at TIMESTAMP NOT NULL
                            )
                            """))
                        elif table_name == 'project_components':
                            conn.execute(text("""
                            CREATE TABLE IF NOT EXISTS project_components (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                project_id INTEGER NOT NULL,
                                component_id INTEGER NOT NULL,
                                quantity FLOAT NOT NULL DEFAULT 1.0,
                                created_at TIMESTAMP NOT NULL,
                                updated_at TIMESTAMP NOT NULL
                            )
                            """))
                        elif table_name == 'sales':
                            conn.execute(text("""
                            CREATE TABLE IF NOT EXISTS sales (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                total_amount FLOAT NOT NULL DEFAULT 0.0,
                                status VARCHAR(50) NOT NULL DEFAULT 'QUOTE_REQUEST',
                                payment_status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
                                customer_id INTEGER,
                                created_at TIMESTAMP NOT NULL,
                                updated_at TIMESTAMP NOT NULL,
                                cost_price FLOAT
                            )
                            """))
                        elif table_name == 'sales_items':
                            conn.execute(text("""
                            CREATE TABLE IF NOT EXISTS sales_items (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                quantity INTEGER NOT NULL DEFAULT 1,
                                price FLOAT NOT NULL DEFAULT 0.0,
                                sales_id INTEGER NOT NULL,
                                product_id INTEGER NOT NULL,
                                created_at TIMESTAMP NOT NULL,
                                updated_at TIMESTAMP NOT NULL
                            )
                            """))
                        elif table_name == 'inventory':
                            conn.execute(text("""
                            CREATE TABLE IF NOT EXISTS inventory (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                item_type VARCHAR(50) NOT NULL,
                                item_id INTEGER NOT NULL,
                                quantity FLOAT NOT NULL DEFAULT 0,
                                status VARCHAR(50) NOT NULL,
                                min_stock_level FLOAT,
                                reorder_point FLOAT,
                                reorder_quantity FLOAT,
                                storage_location VARCHAR(255),
                                location_details JSON,
                                last_count_date TIMESTAMP,
                                last_movement_date TIMESTAMP,
                                transaction_history JSON,
                                unit_cost FLOAT,
                                notes TEXT,
                                created_at TIMESTAMP NOT NULL,
                                updated_at TIMESTAMP NOT NULL,
                                created_by VARCHAR(100),
                                updated_by VARCHAR(100),
                                UNIQUE(item_type, item_id)
                            )
                            """))
                        elif table_name == 'picking_lists':
                            conn.execute(text("""
                            CREATE TABLE IF NOT EXISTS picking_lists (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                sales_id INTEGER,
                                status VARCHAR(50) NOT NULL DEFAULT 'DRAFT',
                                completed_at TIMESTAMP,
                                notes TEXT,
                                created_at TIMESTAMP NOT NULL,
                                updated_at TIMESTAMP NOT NULL,
                                created_by VARCHAR(100),
                                updated_by VARCHAR(100),
                                FOREIGN KEY(sales_id) REFERENCES sales(id) ON DELETE SET NULL
                            )
                            """))
                        elif table_name == 'picking_list_items':
                            conn.execute(text("""
                            CREATE TABLE IF NOT EXISTS picking_list_items (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                picking_list_id INTEGER NOT NULL,
                                component_id INTEGER,
                                material_id INTEGER,
                                quantity_ordered INTEGER NOT NULL,
                                quantity_picked INTEGER NOT NULL DEFAULT 0,
                                created_at TIMESTAMP NOT NULL,
                                updated_at TIMESTAMP NOT NULL,
                                created_by VARCHAR(100),
                                updated_by VARCHAR(100),
                                FOREIGN KEY(picking_list_id) REFERENCES picking_lists(id) ON DELETE CASCADE
                            )
                            """))
                        elif table_name == 'tool_lists':
                            conn.execute(text("""
                            CREATE TABLE IF NOT EXISTS tool_lists (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                project_id INTEGER NOT NULL,
                                status VARCHAR(50) NOT NULL DEFAULT 'DRAFT',
                                notes TEXT,
                                created_at TIMESTAMP NOT NULL,
                                updated_at TIMESTAMP NOT NULL,
                                created_by VARCHAR(100),
                                updated_by VARCHAR(100),
                                FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
                            )
                            """))
                        elif table_name == 'tool_list_items':
                            conn.execute(text("""
                            CREATE TABLE IF NOT EXISTS tool_list_items (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                tool_list_id INTEGER NOT NULL,
                                tool_id INTEGER NOT NULL,
                                quantity INTEGER NOT NULL DEFAULT 1,
                                is_checked_out INTEGER NOT NULL DEFAULT 0,
                                created_at TIMESTAMP NOT NULL,
                                updated_at TIMESTAMP NOT NULL,
                                created_by VARCHAR(100),
                                updated_by VARCHAR(100),
                                FOREIGN KEY(tool_list_id) REFERENCES tool_lists(id) ON DELETE CASCADE
                            )
                            """))
                        elif table_name == 'purchases':
                            conn.execute(text("""
                            CREATE TABLE IF NOT EXISTS purchases (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                supplier_id INTEGER NOT NULL,
                                total_amount FLOAT NOT NULL DEFAULT 0.0,
                                status VARCHAR(50) NOT NULL DEFAULT 'DRAFT',
                                notes TEXT,
                                order_date TIMESTAMP,
                                expected_delivery TIMESTAMP,
                                delivery_date TIMESTAMP,
                                purchase_order_number VARCHAR(100),
                                invoice_number VARCHAR(100),
                                created_at TIMESTAMP NOT NULL,
                                updated_at TIMESTAMP NOT NULL,
                                created_by VARCHAR(100),
                                updated_by VARCHAR(100),
                                FOREIGN KEY(supplier_id) REFERENCES suppliers(id)
                            )
                            """))
                        elif table_name == 'purchase_items':
                            conn.execute(text("""
                            CREATE TABLE IF NOT EXISTS purchase_items (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                purchase_id INTEGER NOT NULL,
                                item_type VARCHAR(50) NOT NULL,
                                item_id INTEGER NOT NULL,
                                quantity FLOAT NOT NULL,
                                price FLOAT NOT NULL,
                                received_quantity FLOAT NOT NULL DEFAULT 0.0,
                                created_at TIMESTAMP NOT NULL,
                                updated_at TIMESTAMP NOT NULL,
                                created_by VARCHAR(100),
                                updated_by VARCHAR(100),
                                FOREIGN KEY(purchase_id) REFERENCES purchases(id)
                            )
                            """))
                        conn.commit()
                        logger.info(f"Created {table_name} table as last resort")
                except Exception as e:
                    logger.error(f"Final attempt to create {table_name} table failed: {e}")

            # Check again after last attempt
            created_tables = set(inspector.get_table_names())
            missing_tables = essential_tables - created_tables
            if len(missing_tables) > 0:
                logger.warning(f"Still missing tables after final attempt: {missing_tables}")

            if len(missing_tables) > len(essential_tables) / 2:
                logger.error("Too many essential tables are missing")
                return False

        logger.info(f"Created tables: {', '.join(created_tables)}")
        return True

    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        traceback.print_exc()
        return False


def seed_minimal_data() -> bool:
    """
    Seed the database with minimal essential data.

    Returns:
        bool: True if seeding was successful
    """
    try:
        # Get database connection
        db_path = get_database_path()
        connection_string = f"sqlite:///{db_path}"
        engine = create_engine(connection_string)

        # First, let's verify the schema of the materials table
        inspector = inspect(engine)
        columns = {col['name'] for col in inspector.get_columns('materials')}
        logger.info(f"Materials table has columns: {', '.join(columns)}")

        # Create session
        Session = sessionmaker(bind=engine)
        session = Session()

        try:
            # Import necessary models
            from database.models.supplier import Supplier
            from database.models.customer import Customer
            from database.models.material import Leather, Material
            from database.models.component import Component
            from database.models.enums import (
                SupplierStatus, CustomerStatus, MaterialType, ComponentType,
                SaleStatus, PaymentStatus, InventoryStatus, PurchaseStatus
            )

            # Add a supplier using direct SQL to avoid ORM relationship issues
            from sqlalchemy.sql import text
            from datetime import datetime, timedelta

            with engine.connect() as conn:
                # Insert supplier using raw SQL
                supplier_result = conn.execute(
                    text(
                        "INSERT INTO suppliers (name, contact_email, status, created_at, updated_at) VALUES (:name, :email, :status, :created, :updated)"),
                    {
                        "name": "Tandy Leather",
                        "email": "sales@tandyleather.com",
                        "status": "ACTIVE",
                        "created": datetime.now(),
                        "updated": datetime.now()
                    }
                )
                conn.commit()

                # Get the supplier ID
                result = conn.execute(text("SELECT id FROM suppliers WHERE name = 'Tandy Leather'"))
                supplier_id = result.scalar()

                if not supplier_id:
                    logger.error("Failed to get supplier ID")
                    return False

                # Insert customer
                conn.execute(
                    text(
                        "INSERT INTO customers (name, email, status, created_at, updated_at) VALUES (:name, :email, :status, :created, :updated)"),
                    {
                        "name": "John Smith",
                        "email": "john.smith@example.com",
                        "status": "ACTIVE",
                        "created": datetime.now(),
                        "updated": datetime.now()
                    }
                )

                # Building the SQL dynamically based on the actual columns
                if 'name' in columns and 'material_type' in columns:
                    # Insert material - the basic columns should exist
                    material_cols = ['name', 'description', 'material_type', 'supplier_id', 'created_at', 'updated_at']
                    material_values = ['Veg-tan Leather', 'Vegetable tanned leather', 'LEATHER', supplier_id,
                                       datetime.now(), datetime.now()]

                    # Build column and parameter lists
                    col_list = ", ".join(material_cols)
                    param_list = ", ".join([f":{col}" for col in material_cols])

                    # Build parameters dict
                    params = {material_cols[i]: material_values[i] for i in range(len(material_cols))}

                    # Execute the SQL
                    conn.execute(
                        text(f"INSERT INTO materials ({col_list}) VALUES ({param_list})"),
                        params
                    )
                    logger.info("Inserted material record")
                else:
                    # If name column doesn't exist, try to figure out which columns do exist and use them
                    logger.warning("Materials table doesn't have expected columns, attempting alternative insertion")

                    # Check what AbstractBase might provide
                    abstract_cols = ['id', 'created_at', 'updated_at']
                    available_cols = [col for col in abstract_cols if col in columns]

                    if available_cols:
                        col_list = ", ".join(available_cols)
                        param_list = ", ".join([f":{col}" for col in available_cols])
                        params = {col: (1 if col == 'id' else datetime.now()) for col in available_cols}

                        conn.execute(
                            text(f"INSERT INTO materials ({col_list}) VALUES ({param_list})"),
                            params
                        )
                        logger.info("Inserted minimal material record using available columns")

                # Insert component
                conn.execute(
                    text(
                        "INSERT INTO components (name, description, component_type, created_at, updated_at) VALUES (:name, :desc, :type, :created, :updated)"),
                    {
                        "name": "Wallet Body",
                        "desc": "Main body piece for bifold wallet",
                        "type": "LEATHER",
                        "created": datetime.now(),
                        "updated": datetime.now()
                    }
                )

                # Get material ID
                result = conn.execute(text("SELECT id FROM materials LIMIT 1"))
                material_id = result.scalar()

                # Get component ID
                result = conn.execute(text("SELECT id FROM components WHERE name = 'Wallet Body'"))
                component_id = result.scalar()

                # Insert component-material relationship if both IDs exist
                if 'component_materials' in inspector.get_table_names() and material_id and component_id:
                    try:
                        # Check the structure of component_materials table
                        cm_columns = {col['name'] for col in inspector.get_columns('component_materials')}
                        logger.info(f"Component_materials table has columns: {', '.join(cm_columns)}")

                        # Determine if it has an id column or uses composite primary key
                        if 'id' in cm_columns:
                            conn.execute(
                                text(
                                    "INSERT INTO component_materials (component_id, material_id, quantity) VALUES (:component_id, :material_id, :quantity)"),
                                {
                                    "component_id": component_id,
                                    "material_id": material_id,
                                    "quantity": 1.5
                                }
                            )
                        else:
                            conn.execute(
                                text(
                                    "INSERT INTO component_materials (component_id, material_id, quantity) VALUES (:component_id, :material_id, :quantity)"),
                                {
                                    "component_id": component_id,
                                    "material_id": material_id,
                                    "quantity": 1.5
                                }
                            )
                        logger.info("Created component-material relationship")
                    except Exception as e:
                        logger.error(f"Error creating component-material relationship: {e}")

                # Create a pattern
                try:
                    conn.execute(
                        text(
                            "INSERT INTO patterns (name, description, skill_level, created_at, updated_at) VALUES (:name, :desc, :skill, :created, :updated)"),
                        {
                            "name": "Basic Bifold Wallet",
                            "desc": "Simple bifold wallet pattern with card slots",
                            "skill": "INTERMEDIATE",
                            "created": datetime.now(),
                            "updated": datetime.now()
                        }
                    )
                    logger.info("Created pattern record")

                    # Get pattern ID
                    result = conn.execute(text("SELECT id FROM patterns WHERE name = 'Basic Bifold Wallet'"))
                    pattern_id = result.scalar()

                    # Connect pattern to component if both exist
                    if pattern_id and component_id:
                        # Check pattern_components table structure
                        if 'pattern_components' in inspector.get_table_names():
                            pc_columns = {col['name'] for col in inspector.get_columns('pattern_components')}

                            if 'id' in pc_columns:
                                # Table has id primary key
                                conn.execute(
                                    text(
                                        "INSERT INTO pattern_components (pattern_id, component_id, quantity) VALUES (:pattern_id, :component_id, :quantity)"),
                                    {
                                        "pattern_id": pattern_id,
                                        "component_id": component_id,
                                        "quantity": 1.0
                                    }
                                )
                            else:
                                # Table has composite primary key
                                conn.execute(
                                    text(
                                        "INSERT INTO pattern_components (pattern_id, component_id, quantity) VALUES (:pattern_id, :component_id, :quantity)"),
                                    {
                                        "pattern_id": pattern_id,
                                        "component_id": component_id,
                                        "quantity": 1.0
                                    }
                                )
                            logger.info("Connected pattern to component")
                except Exception as e:
                    logger.error(f"Error creating pattern data: {e}")

                # Create a product
                try:
                    conn.execute(
                        text(
                            "INSERT INTO products (name, description, price, is_active, created_at, updated_at) VALUES (:name, :desc, :price, :active, :created, :updated)"),
                        {
                            "name": "Handcrafted Leather Wallet",
                            "desc": "Premium handcrafted leather bifold wallet",
                            "price": 79.99,
                            "active": 1,
                            "created": datetime.now(),
                            "updated": datetime.now()
                        }
                    )
                    logger.info("Created product record")

                    # Get product ID
                    result = conn.execute(text("SELECT id FROM products WHERE name = 'Handcrafted Leather Wallet'"))
                    product_id = result.scalar()

                    # Connect product to pattern if both exist
                    if product_id and pattern_id:
                        # Check product_patterns table structure
                        if 'product_patterns' in inspector.get_table_names():
                            pp_columns = {col['name'] for col in inspector.get_columns('product_patterns')}

                            if 'id' in pp_columns:
                                conn.execute(
                                    text(
                                        "INSERT INTO product_patterns (product_id, pattern_id, is_primary, scale_factor) VALUES (:product_id, :pattern_id, :is_primary, :scale_factor)"),
                                    {
                                        "product_id": product_id,
                                        "pattern_id": pattern_id,
                                        "is_primary": 1,
                                        "scale_factor": 1.0
                                    }
                                )
                            else:
                                conn.execute(
                                    text(
                                        "INSERT INTO product_patterns (product_id, pattern_id, is_primary, scale_factor) VALUES (:product_id, :pattern_id, :is_primary, :scale_factor)"),
                                    {
                                        "product_id": product_id,
                                        "pattern_id": pattern_id,
                                        "is_primary": 1,
                                        "scale_factor": 1.0
                                    }
                                )
                            logger.info("Connected product to pattern")
                except Exception as e:
                    logger.error(f"Error creating product data: {e}")

                # Create a sales record
                try:
                    # Get customer ID
                    result = conn.execute(text("SELECT id FROM customers WHERE name = 'John Smith'"))
                    customer_id = result.scalar()

                    conn.execute(
                        text(
                            "INSERT INTO sales (total_amount, status, payment_status, customer_id, created_at, updated_at) VALUES (:total, :status, :payment, :customer_id, :created, :updated)"),
                        {
                            "total": 79.99,
                            "status": "DESIGN_APPROVAL",
                            "payment": "DEPOSIT_RECEIVED",
                            "customer_id": customer_id,
                            "created": datetime.now(),
                            "updated": datetime.now()
                        }
                    )
                    logger.info("Created sales record")

                    # Get sales ID
                    result = conn.execute(text("SELECT id FROM sales WHERE customer_id = :customer_id"),
                                          {"customer_id": customer_id})
                    sales_id = result.scalar()

                    # Create sales item if product exists
                    if product_id and sales_id:
                        conn.execute(
                            text(
                                "INSERT INTO sales_items (quantity, price, sales_id, product_id, created_at, updated_at) VALUES (:quantity, :price, :sales_id, :product_id, :created, :updated)"),
                            {
                                "quantity": 1,
                                "price": 79.99,
                                "sales_id": sales_id,
                                "product_id": product_id,
                                "created": datetime.now(),
                                "updated": datetime.now()
                            }
                        )
                        logger.info("Created sales item record")

                except Exception as e:
                    logger.error(f"Error creating sales records: {e}")
                    sales_id = None

                # Create a project
                # First check if the projects table exists
                tables = inspector.get_table_names()
                if "projects" in tables:
                    try:
                        conn.execute(
                            text(
                                "INSERT INTO projects (name, description, type, status, sales_id, created_at, updated_at) VALUES (:name, :desc, :type, :status, :sales_id, :created, :updated)"),
                            {
                                "name": "Custom Wallet Project #1",
                                "desc": "Custom wallet for John Smith",
                                "type": "WALLET",
                                "status": "PLANNED",
                                "sales_id": sales_id,
                                "created": datetime.now(),
                                "updated": datetime.now()
                            }
                        )
                        logger.info("Created project record")

                        # Get project ID
                        result = conn.execute(text("SELECT id FROM projects WHERE name = 'Custom Wallet Project #1'"))
                        project_id = result.scalar()

                        # Connect project to component if both exist
                        if "project_components" in tables and project_id and component_id:
                            conn.execute(
                                text(
                                    "INSERT INTO project_components (project_id, component_id, quantity, created_at, updated_at) VALUES (:project_id, :component_id, :quantity, :created, :updated)"),
                                {
                                    "project_id": project_id,
                                    "component_id": component_id,
                                    "quantity": 1.0,
                                    "created": datetime.now(),
                                    "updated": datetime.now()
                                }
                            )
                            logger.info("Connected project to component")

                        # Create a tool list for the project if tool_lists table exists
                        if "tool_lists" in tables and project_id:
                            try:
                                conn.execute(
                                    text(
                                        "INSERT INTO tool_lists (project_id, status, created_at, updated_at) VALUES (:project_id, :status, :created, :updated)"),
                                    {
                                        "project_id": project_id,
                                        "status": "DRAFT",
                                        "created": datetime.now(),
                                        "updated": datetime.now()
                                    }
                                )
                                logger.info("Created tool list record")

                                # Get tool list ID
                                result = conn.execute(text("SELECT id FROM tool_lists WHERE project_id = :project_id"),
                                                      {"project_id": project_id})
                                tool_list_id = result.scalar()

                                # Create a tool and add it to the tool list
                                if tool_list_id:
                                    # Create a tool
                                    conn.execute(
                                        text(
                                            "INSERT INTO tools (name, description, tool_category, supplier_id, created_at, updated_at) VALUES (:name, :desc, :category, :supplier_id, :created, :updated)"),
                                        {
                                            "name": "Stitching Awl",
                                            "desc": "Diamond point stitching awl for leatherwork",
                                            "category": "STITCHING",
                                            "supplier_id": supplier_id,
                                            "created": datetime.now(),
                                            "updated": datetime.now()
                                        }
                                    )
                                    logger.info("Created tool record")

                                    # Get tool ID
                                    result = conn.execute(text("SELECT id FROM tools WHERE name = 'Stitching Awl'"))
                                    tool_id = result.scalar()

                                    if tool_id and "tool_list_items" in tables:
                                        conn.execute(
                                            text(
                                                "INSERT INTO tool_list_items (tool_list_id, tool_id, quantity, created_at, updated_at) VALUES (:tool_list_id, :tool_id, :quantity, :created, :updated)"),
                                            {
                                                "tool_list_id": tool_list_id,
                                                "tool_id": tool_id,
                                                "quantity": 1,
                                                "created": datetime.now(),
                                                "updated": datetime.now()
                                            }
                                        )
                                        logger.info("Added tool to tool list")
                            except Exception as e:
                                logger.error(f"Error creating tool list data: {e}")

                        # Create a picking list for the sales record if picking_lists table exists
                        if "picking_lists" in tables and sales_id:
                            try:
                                conn.execute(
                                    text(
                                        "INSERT INTO picking_lists (sales_id, status, created_at, updated_at) VALUES (:sales_id, :status, :created, :updated)"),
                                    {
                                        "sales_id": sales_id,
                                        "status": "DRAFT",
                                        "created": datetime.now(),
                                        "updated": datetime.now()
                                    }
                                )
                                logger.info("Created picking list record")

                                # Get picking list ID
                                result = conn.execute(text("SELECT id FROM picking_lists WHERE sales_id = :sales_id"),
                                                      {"sales_id": sales_id})
                                picking_list_id = result.scalar()

                                # Add material to picking list
                                if picking_list_id and material_id and "picking_list_items" in tables:
                                    conn.execute(
                                        text(
                                            "INSERT INTO picking_list_items (picking_list_id, material_id, quantity_ordered, created_at, updated_at) VALUES (:picking_list_id, :material_id, :quantity, :created, :updated)"),
                                        {
                                            "picking_list_id": picking_list_id,
                                            "material_id": material_id,
                                            "quantity": 2,
                                            "created": datetime.now(),
                                            "updated": datetime.now()
                                        }
                                    )
                                    logger.info("Added material to picking list")
                            except Exception as e:
                                logger.error(f"Error creating picking list data: {e}")
                    except Exception as e:
                        logger.error(f"Error creating project data: {e}")
                else:
                    # Projects table doesn't exist, try to create it and then seed it
                    logger.warning("Projects table not found, trying to create it before seeding")
                    try:
                        with engine.connect() as conn:
                            conn.execute(text("""
                            CREATE TABLE IF NOT EXISTS projects (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                name VARCHAR(255) NOT NULL,
                                description TEXT,
                                type VARCHAR(50) NOT NULL,
                                status VARCHAR(50) NOT NULL DEFAULT 'PLANNED',
                                start_date TIMESTAMP,
                                end_date TIMESTAMP,
                                sales_id INTEGER,
                                created_at TIMESTAMP NOT NULL,
                                updated_at TIMESTAMP NOT NULL,
                                FOREIGN KEY(sales_id) REFERENCES sales(id) ON DELETE SET NULL
                            )
                            """))
                            conn.commit()
                            logger.info("Created projects table during seeding")

                            # Now try to insert the project
                            conn.execute(
                                text(
                                    "INSERT INTO projects (name, description, type, status, sales_id, created_at, updated_at) VALUES (:name, :desc, :type, :status, :sales_id, :created, :updated)"),
                                {
                                    "name": "Custom Wallet Project #1",
                                    "desc": "Custom wallet for John Smith",
                                    "type": "WALLET",
                                    "status": "PLANNED",
                                    "sales_id": sales_id,
                                    "created": datetime.now(),
                                    "updated": datetime.now()
                                }
                            )
                            logger.info("Created project record after creating table")

                            # Check if we need to create project_components table too
                            if "project_components" not in tables:
                                conn.execute(text("""
                                CREATE TABLE IF NOT EXISTS project_components (
                                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                                    project_id INTEGER NOT NULL,
                                    component_id INTEGER NOT NULL,
                                    quantity FLOAT NOT NULL DEFAULT 1.0,
                                    created_at TIMESTAMP NOT NULL,
                                    updated_at TIMESTAMP NOT NULL,
                                    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE,
                                    FOREIGN KEY(component_id) REFERENCES components(id) ON DELETE CASCADE,
                                    UNIQUE(project_id, component_id)
                                )
                                """))
                                conn.commit()
                                logger.info("Created project_components table during seeding")
                    except Exception as e:
                        logger.error(f"Error creating projects table during seeding: {e}")

                # Create inventory records for materials, products, and tools
                try:
                    # Create a tool for inventory tracking if it doesn't exist yet
                    if not tool_id:
                        conn.execute(
                            text(
                                "INSERT INTO tools (name, description, tool_category, supplier_id, created_at, updated_at) VALUES (:name, :desc, :category, :supplier_id, :created, :updated)"),
                            {
                                "name": "Stitching Awl",
                                "desc": "Diamond point stitching awl for leatherwork",
                                "category": "STITCHING",
                                "supplier_id": supplier_id,
                                "created": datetime.now(),
                                "updated": datetime.now()
                            }
                        )

                        # Get tool ID
                        result = conn.execute(text("SELECT id FROM tools WHERE name = 'Stitching Awl'"))
                        tool_id = result.scalar()

                    # Create material inventory
                    if material_id and 'inventory' in inspector.get_table_names():
                        # Prepare transaction history
                        transaction_history = json.dumps([{
                            'date': datetime.now().isoformat(),
                            'previous_quantity': 0,
                            'new_quantity': 10.5,
                            'change': 10.5,
                            'transaction_type': 'INITIAL_STOCK',
                            'notes': 'Initial inventory setup'
                        }])

                        conn.execute(
                            text(
                                """
                                INSERT INTO inventory (
                                    item_type, item_id, quantity, status, min_stock_level, 
                                    reorder_point, reorder_quantity, storage_location, 
                                    transaction_history, unit_cost, created_at, updated_at
                                ) VALUES (
                                    :item_type, :item_id, :quantity, :status, :min_stock_level, 
                                    :reorder_point, :reorder_quantity, :storage_location, 
                                    :transaction_history, :unit_cost, :created_at, :updated_at
                                )
                                """
                            ),
                            {
                                "item_type": "material",
                                "item_id": material_id,
                                "quantity": 10.5,
                                "status": "IN_STOCK",
                                "min_stock_level": 5.0,
                                "reorder_point": 7.5,
                                "reorder_quantity": 20.0,
                                "storage_location": "Shelf A1",
                                "transaction_history": transaction_history,
                                "unit_cost": 15.99,
                                "created_at": datetime.now(),
                                "updated_at": datetime.now()
                            }
                        )
                        logger.info("Created material inventory record")

                    # Create product inventory if product exists
                    if product_id and 'inventory' in inspector.get_table_names():
                        # Prepare transaction history
                        transaction_history = json.dumps([{
                            'date': datetime.now().isoformat(),
                            'previous_quantity': 0,
                            'new_quantity': 5,
                            'change': 5,
                            'transaction_type': 'INITIAL_STOCK',
                            'notes': 'Initial inventory setup'
                        }])

                        conn.execute(
                            text(
                                """
                                INSERT INTO inventory (
                                    item_type, item_id, quantity, status, min_stock_level, 
                                    reorder_point, reorder_quantity, storage_location, 
                                    transaction_history, unit_cost, created_at, updated_at
                                ) VALUES (
                                    :item_type, :item_id, :quantity, :status, :min_stock_level, 
                                    :reorder_point, :reorder_quantity, :storage_location, 
                                    :transaction_history, :unit_cost, :created_at, :updated_at
                                )
                                """
                            ),
                            {
                                "item_type": "product",
                                "item_id": product_id,
                                "quantity": 5,
                                "status": "IN_STOCK",
                                "min_stock_level": 2,
                                "reorder_point": 3,
                                "reorder_quantity": 10,
                                "storage_location": "Shelf B2",
                                "transaction_history": transaction_history,
                                "unit_cost": 45.50,
                                "created_at": datetime.now(),
                                "updated_at": datetime.now()
                            }
                        )
                        logger.info("Created product inventory record")

                    # Create tool inventory
                    if tool_id and 'inventory' in inspector.get_table_names():
                        # Prepare transaction history
                        transaction_history = json.dumps([{
                            'date': datetime.now().isoformat(),
                            'previous_quantity': 0,
                            'new_quantity': 3,
                            'change': 3,
                            'transaction_type': 'INITIAL_STOCK',
                            'notes': 'Initial inventory setup'
                        }])

                        conn.execute(
                            text(
                                """
                                INSERT INTO inventory (
                                    item_type, item_id, quantity, status, min_stock_level, 
                                    reorder_point, reorder_quantity, storage_location, 
                                    transaction_history, unit_cost, created_at, updated_at
                                ) VALUES (
                                    :item_type, :item_id, :quantity, :status, :min_stock_level, 
                                    :reorder_point, :reorder_quantity, :storage_location, 
                                    :transaction_history, :unit_cost, :created_at, :updated_at
                                )
                                """
                            ),
                            {
                                "item_type": "tool",
                                "item_id": tool_id,
                                "quantity": 3,
                                "status": "IN_STOCK",
                                "min_stock_level": 1,
                                "reorder_point": 2,
                                "reorder_quantity": 5,
                                "storage_location": "Drawer C3",
                                "transaction_history": transaction_history,
                                "unit_cost": 12.99,
                                "created_at": datetime.now(),
                                "updated_at": datetime.now()
                            }
                        )
                        logger.info("Created tool inventory record")
                except Exception as e:
                    logger.error(f"Error creating inventory records: {e}")

                # Create purchase records
                try:
                    if supplier_id and material_id and 'purchases' in inspector.get_table_names():
                        # Create a purchase order
                        conn.execute(
                            text(
                                """
                                INSERT INTO purchases (
                                    supplier_id, total_amount, status, purchase_order_number,
                                    order_date, expected_delivery, created_at, updated_at
                                ) VALUES (
                                    :supplier_id, :total_amount, :status, :po_number,
                                    :order_date, :expected_delivery, :created_at, :updated_at
                                )
                                """
                            ),
                            {
                                "supplier_id": supplier_id,
                                "total_amount": 159.90,
                                "status": "ORDERED",
                                "po_number": "PO-2025-001",
                                "order_date": datetime.now(),
                                "expected_delivery": datetime.now() + timedelta(days=7),
                                "created_at": datetime.now(),
                                "updated_at": datetime.now()
                            }
                        )
                        logger.info("Created purchase record")

                        # Get purchase ID
                        result = conn.execute(
                            text("SELECT id FROM purchases WHERE purchase_order_number = 'PO-2025-001'"))
                        purchase_id = result.scalar()

                        # Add material to purchase
                        if purchase_id and 'purchase_items' in inspector.get_table_names():
                            conn.execute(
                                text(
                                    """
                                    INSERT INTO purchase_items (
                                        purchase_id, item_type, item_id, quantity, price,
                                        created_at, updated_at
                                    ) VALUES (
                                        :purchase_id, :item_type, :item_id, :quantity, :price,
                                        :created_at, :updated_at
                                    )
                                    """
                                ),
                                {
                                    "purchase_id": purchase_id,
                                    "item_type": "material",
                                    "item_id": material_id,
                                    "quantity": 10.0,
                                    "price": 15.99,
                                    "created_at": datetime.now(),
                                    "updated_at": datetime.now()
                                }
                            )
                            logger.info("Added material to purchase")

                            # Add tool to purchase
                            if tool_id:
                                conn.execute(
                                    text(
                                        """
                                        INSERT INTO purchase_items (
                                            purchase_id, item_type, item_id, quantity, price,
                                            created_at, updated_at
                                        ) VALUES (
                                            :purchase_id, :item_type, :item_id, :quantity, :price,
                                            :created_at, :updated_at
                                        )
                                        """
                                    ),
                                    {
                                        "purchase_id": purchase_id,
                                        "item_type": "tool",
                                        "item_id": tool_id,
                                        "quantity": 2.0,
                                        "price": 12.99,
                                        "created_at": datetime.now(),
                                        "updated_at": datetime.now()
                                    }
                                )
                                logger.info("Added tool to purchase")

                            # Simulate partial receipt
                            conn.execute(
                                text(
                                    """
                                    UPDATE purchase_items 
                                    SET received_quantity = 5.0, updated_at = :updated_at
                                    WHERE purchase_id = :purchase_id AND item_type = 'material'
                                    """
                                ),
                                {
                                    "purchase_id": purchase_id,
                                    "updated_at": datetime.now()
                                }
                            )

                            # Update the purchase status to partially received
                            conn.execute(
                                text(
                                    """
                                    UPDATE purchases 
                                    SET status = 'PARTIALLY_RECEIVED', updated_at = :updated_at
                                    WHERE id = :purchase_id
                                    """
                                ),
                                {
                                    "purchase_id": purchase_id,
                                    "updated_at": datetime.now()
                                }
                            )
                            logger.info("Updated purchase with partial receipt")
                except Exception as e:
                    logger.error(f"Error creating purchase records: {e}")

                conn.commit()

            logger.info("Database seeded with minimal data using direct SQL")
            return True

        except Exception as e:
            session.rollback()
            logger.error(f"Error seeding database: {e}")
            traceback.print_exc()
            return False

        finally:
            session.close()

    except Exception as e:
        logger.error(f"Error connecting to database for seeding: {e}")
        traceback.print_exc()
        return False


def main():
    """
    Initialize the database and optionally seed it with minimal data.
    """
    parser = argparse.ArgumentParser(description='Initialize leatherworking database')
    parser.add_argument('--recreate', action='store_true', help='Drop and recreate all tables')
    parser.add_argument('--seed', action='store_true', help='Add minimal sample data to database')
    args = parser.parse_args()

    # Initialize database
    logger.info(f"Initializing database (recreate={args.recreate})")
    success = initialize_database(recreate=args.recreate)

    if not success:
        logger.error("Database initialization failed")
        return 1

    logger.info("Database initialization completed successfully")

    # Seed database if requested
    if args.seed and success:
        logger.info("Seeding database with minimal data")
        if not seed_minimal_data():
            logger.error("Database seeding failed")
            return 1

        logger.info("Database seeding completed successfully")

    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)