#!/usr/bin/env python
# initialize_database.py
"""
Database initialization script for the leatherworking application.
This version includes sample data loading from JSON with robust error handling.
"""

import argparse
import importlib
import logging
import os
import sys
import traceback
import json
from pathlib import Path
from datetime import datetime, timedelta

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.inspection import inspect

from database.models.component_material import ComponentMaterial

# Configure logging
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_database_path() -> str:
    """
    Determine the path for the SQLite database inside the 'data' directory.

    Returns:
        str: Absolute path to the database file
    """
    base_dir = Path(__file__).resolve().parent
    data_dir = base_dir / 'data'  # Create a Path object pointing to 'data'
    data_dir.mkdir(parents=True, exist_ok=True)  # Ensure 'data' directory exists
    db_path = str(data_dir / 'leatherworking_database.db')
    logger.debug(f"Database path determined: {db_path}")
    return db_path


def filter_model_data(model_class, data_dict):
    """
    Filter a dictionary to only include fields that exist in the model.

    Args:
        model_class: SQLAlchemy model class
        data_dict: Dictionary of data to filter

    Returns:
        Dictionary with only valid model fields
    """
    try:
        # Get all column names of the model
        valid_columns = inspect(model_class).columns.keys()

        # Filter the dictionary to only include valid columns
        filtered_data = {k: v for k, v in data_dict.items() if k in valid_columns}
        return filtered_data
    except Exception as e:
        logger.warning(f"Error filtering data for {model_class.__name__}: {e}")
        # Fall back to the original dictionary if something goes wrong
        return data_dict


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
            PurchaseStatus, ToolCategory
        )

        from database.models.supplier import Supplier
        from database.models.customer import Customer
        from database.models.material import Material, Leather, Hardware, Supplies
        from database.models.component import Component

        # Critical: Import component_material directly to ensure the table is properly registered
        from database.models.component_material import component_material_table, ComponentMaterial

        from database.models.tool import Tool

        # Import the new models for tool management
        from database.models.tool_maintenance import ToolMaintenance
        from database.models.tool_checkout import ToolCheckout

        # Import the rest of the models
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
            'ToolMaintenance': ToolMaintenance,
            'ToolCheckout': ToolCheckout,
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
            'PurchaseStatus': PurchaseStatus,
            'ToolCategory': ToolCategory
        }

        logger.info("All models imported successfully")
        return True, models
    except Exception as e:
        logger.error(f"Failed to import models: {e}")
        traceback.print_exc()
        return False, {}


def initialize_database(recreate: bool = False) -> bool:
    """
    Initialize a minimal database by creating tables using SQLAlchemy models.

    Args:
        recreate (bool): Whether to recreate the database from scratch

    Returns:
        bool: True if database was initialized successfully
    """
    try:
        # Import models directly
        success, models = import_models_directly()
        if not success:
            logger.error("Model import failed, database initialization aborted.")
            return False

        Base = models['Base']

        # Get database path
        db_path = get_database_path()
        logger.info(f"Using database path: {db_path}")

        # Create backup before recreation if database exists
        if os.path.exists(db_path) and recreate:
            backup_dir = os.path.join(os.path.dirname(db_path), 'database', 'backups')
            os.makedirs(backup_dir, exist_ok=True)

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = os.path.join(backup_dir, f"db_backup_before_init_{timestamp}.db")

            import shutil
            shutil.copy2(db_path, backup_path)
            logger.info(f"Database backed up to {backup_path}")

        # Create database connection
        connection_string = f"sqlite:///{db_path}"
        engine_args = {
            'echo': True,  # Enable SQL echoing for debugging
            'connect_args': {
                'check_same_thread': False,
                'timeout': 30
            }
        }

        engine = create_engine(connection_string, **engine_args)
        inspector = inspect(engine)  # inspector to look at database

        # Drop all tables if recreate is True
        if recreate:
            try:
                logger.info("Dropping all tables...")
                Base.metadata.drop_all(engine)
                logger.info("All tables dropped successfully")
            except Exception as e:
                logger.error(f"Error dropping tables: {e}")
                logger.error(traceback.format_exc())
                return False

        try:
            # Create all tables based on the models
            logger.info("Creating tables using SQLAlchemy models...")
            Base.metadata.create_all(engine)
            logger.info("Successfully created tables using SQLAlchemy models")

            # Verify the tables
            inspector = inspect(engine)
            created_tables = inspector.get_table_names()
            essential_tables = [
                'suppliers', 'customers', 'materials', 'components', 'tools',
                'component_materials', 'patterns', 'products', 'pattern_components',
                'product_patterns', 'projects', 'project_components', 'sales',
                'sales_items', 'inventory', 'picking_lists', 'picking_list_items',
                'tool_lists', 'tool_list_items', 'purchases', 'purchase_items',
                'tool_maintenance', 'tool_checkouts'
            ]

            missing_tables = set(essential_tables) - set(created_tables)

            if missing_tables:
                logger.error(f"Some essential tables were not created: {missing_tables}")
                logger.error(f"Missing table Details {missing_tables}")
                return False

            return True

        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            logger.error(traceback.format_exc())
            return False
    except Exception as e:
        logger.error(f"General top level exception in initialize: {e}")
        logger.error(traceback.format_exc())
        return False


def load_sample_data(json_file_path: str) -> bool:
    """
    Load sample data from a JSON file into the database.

    Args:
        json_file_path (str): Path to the JSON file with sample data

    Returns:
        bool: True if data was loaded successfully
    """
    try:
        # Check if the file exists
        if not os.path.exists(json_file_path):
            logger.error(f"Sample data file not found: {json_file_path}")
            return False

        # Load the JSON data with explicit UTF-8 encoding
        with open(json_file_path, 'r', encoding='utf-8') as file:
            sample_data = json.load(file)

        # Get database connection
        db_path = get_database_path()
        connection_string = f"sqlite:///{db_path}"
        engine = create_engine(connection_string)
        Session = sessionmaker(bind=engine)
        session = Session()

        try:
            # Import necessary models
            from database.models.supplier import Supplier
            from database.models.customer import Customer
            from database.models.material import Leather, Hardware, Supplies, Material
            from database.models.tool import Tool
            from database.models.pattern import Pattern
            from database.models.product import Product
            from database.models.tool_maintenance import ToolMaintenance
            from database.models.tool_checkout import ToolCheckout
            from database.models.project import Project
            from database.models.component import Component
            from database.models.enums import (
                ToolCategory, SupplierStatus, CustomerStatus, CustomerTier,
                CustomerSource, LeatherType, LeatherFinish, HardwareType,
                HardwareMaterial, HardwareFinish, SkillLevel, ProjectType,
                ProjectStatus
            )

            # Insert suppliers
            if 'suppliers' in sample_data:
                for supplier_data in sample_data['suppliers']:
                    # Filter data to include only valid fields for the Supplier model
                    filtered_data = filter_model_data(Supplier, supplier_data)

                    # Ensure required fields are present
                    if 'name' not in filtered_data:
                        logger.warning(f"Skipping supplier without name: {supplier_data}")
                        continue

                    # Add defaults for required fields if missing
                    if 'status' not in filtered_data:
                        filtered_data['status'] = 'ACTIVE'

                    # Special handling for contact name in notes
                    if 'contact_name' in supplier_data and 'notes' in filtered_data:
                        if filtered_data['notes']:
                            filtered_data['notes'] += f" Contact: {supplier_data['contact_name']}"
                        else:
                            filtered_data['notes'] = f"Contact: {supplier_data['contact_name']}"

                    # Create the supplier
                    try:
                        supplier = Supplier(**filtered_data)
                        session.add(supplier)
                    except Exception as e:
                        logger.error(f"Error adding supplier {filtered_data.get('name', 'UNKNOWN')}: {e}")
                        continue

                logger.info(f"Added {len(sample_data['suppliers'])} suppliers")

            # Insert customers
            if 'customers' in sample_data:
                for customer_data in sample_data['customers']:
                    # Filter data to include only valid fields for the Customer model
                    filtered_data = filter_model_data(Customer, customer_data)

                    # Ensure required fields are present
                    if 'first_name' not in filtered_data or 'last_name' not in filtered_data:
                        logger.warning(f"Skipping customer without first_name or last_name: {customer_data}")
                        continue

                    # Add defaults for required fields if missing
                    if 'status' not in filtered_data:
                        filtered_data['status'] = 'ACTIVE'

                    if 'tier' not in filtered_data:
                        filtered_data['tier'] = 'STANDARD'

                    # Create the customer
                    try:
                        customer = Customer(**filtered_data)
                        session.add(customer)
                    except Exception as e:
                        logger.error(
                            f"Error adding customer {filtered_data.get('first_name', '')} {filtered_data.get('last_name', 'UNKNOWN')}: {e}")
                        continue

                logger.info(f"Added {len(sample_data['customers'])} customers")

            # Commit to get IDs
            session.commit()

            # Get supplier reference for future use
            suppliers = {supplier.name: supplier for supplier in session.query(Supplier).all()}

            # Insert components
            if 'components' in sample_data:
                for component_data in sample_data['components']:
                    # Filter data to include only valid fields for the Component model
                    filtered_data = filter_model_data(Component, component_data)

                    # Ensure required fields are present
                    if 'name' not in filtered_data:
                        logger.warning(f"Skipping component without name: {component_data}")
                        continue

                    # Add defaults for required fields if missing
                    if 'component_type' not in filtered_data:
                        filtered_data['component_type'] = 'LEATHER'

                    # Create the component
                    try:
                        component = Component(**filtered_data)
                        session.add(component)
                    except Exception as e:
                        logger.error(f"Error adding component {filtered_data.get('name', 'UNKNOWN')}: {e}")
                        continue

                logger.info(f"Added {len(sample_data['components'])} components")
                session.commit()

            # Insert leather materials
            if 'leathers' in sample_data:
                for leather_data in sample_data['leathers']:
                    try:
                        # Map supplier ID if mentioned
                        if 'supplier_id' in leather_data and isinstance(leather_data['supplier_id'], int):
                            supplier_id = leather_data['supplier_id']
                        else:
                            supplier_id = None

                        # Create basic material data
                        leather_kwargs = {
                            'name': leather_data.get('name', f"Leather-{datetime.now().timestamp()}"),
                            'material_type': 'LEATHER',
                            'leather_type': leather_data.get('leather_type', 'VEGETABLE_TANNED'),
                            'quality': leather_data.get('quality', 'PREMIUM'),
                            'color': leather_data.get('color'),
                            'thickness': leather_data.get('thickness'),
                            'supplier_id': supplier_id,
                            'cost_price': leather_data.get('cost_price'),
                            'unit': leather_data.get('unit', 'SQUARE_FOOT'),
                            'is_full_hide': leather_data.get('is_full_hide', False),
                            'area': leather_data.get('area')
                        }

                        # Filter to valid fields
                        filtered_data = filter_model_data(Leather, leather_kwargs)
                        leather = Leather(**filtered_data)
                        session.add(leather)
                    except Exception as e:
                        logger.error(f"Error adding leather {leather_data.get('name', 'UNKNOWN')}: {e}")
                        continue

                logger.info(f"Added {len(sample_data['leathers'])} leather materials")

            # Insert hardware materials
            if 'hardware' in sample_data:
                for hw_data in sample_data['hardware']:
                    try:
                        # Map supplier ID if mentioned
                        if 'supplier_id' in hw_data and isinstance(hw_data['supplier_id'], int):
                            supplier_id = hw_data['supplier_id']
                        else:
                            supplier_id = None

                        # Create basic material data
                        hardware_kwargs = {
                            'name': hw_data.get('name', f"Hardware-{datetime.now().timestamp()}"),
                            'material_type': 'HARDWARE',
                            'hardware_type': hw_data.get('hardware_type'),
                            'hardware_material': hw_data.get('hardware_material'),
                            'finish': hw_data.get('finish'),
                            'size': hw_data.get('size'),
                            'supplier_id': supplier_id,
                            'cost_price': hw_data.get('cost_price'),
                            'unit': hw_data.get('unit', 'PIECE'),
                            'quality': hw_data.get('quality', 'PREMIUM')
                        }

                        # Filter to valid fields
                        filtered_data = filter_model_data(Hardware, hardware_kwargs)
                        hardware = Hardware(**filtered_data)
                        session.add(hardware)
                    except Exception as e:
                        logger.error(f"Error adding hardware {hw_data.get('name', 'UNKNOWN')}: {e}")
                        continue

                logger.info(f"Added {len(sample_data['hardware'])} hardware items")

            # Insert supplies materials
            if 'supplies' in sample_data:
                for supply_data in sample_data['supplies']:
                    try:
                        # Map supplier ID if mentioned
                        if 'supplier_id' in supply_data and isinstance(supply_data['supplier_id'], int):
                            supplier_id = supply_data['supplier_id']
                        else:
                            supplier_id = None

                        # Create basic material data
                        supply_kwargs = {
                            'name': supply_data.get('name', f"Supply-{datetime.now().timestamp()}"),
                            'material_type': 'SUPPLIES',
                            'supplies_type': supply_data.get('supplies_type'),
                            'color': supply_data.get('color'),
                            'thread_thickness': supply_data.get('thickness'),
                            'material_composition': supply_data.get('material_composition'),
                            'supplier_id': supplier_id,
                            'cost_price': supply_data.get('cost_price'),
                            'unit': supply_data.get('unit', 'PIECE'),
                            'quality': supply_data.get('quality', 'PREMIUM')
                        }

                        # Filter to valid fields
                        filtered_data = filter_model_data(Supplies, supply_kwargs)
                        supply = Supplies(**filtered_data)
                        session.add(supply)
                    except Exception as e:
                        logger.error(f"Error adding supply {supply_data.get('name', 'UNKNOWN')}: {e}")
                        continue

                logger.info(f"Added {len(sample_data['supplies'])} supplies")

            # Commit to get IDs
            session.commit()

            # Insert patterns
            if 'patterns' in sample_data:
                for pattern_data in sample_data['patterns']:
                    # Filter data to include only valid fields for the Pattern model
                    filtered_data = filter_model_data(Pattern, pattern_data)

                    # Ensure required fields are present
                    if 'name' not in filtered_data:
                        logger.warning(f"Skipping pattern without name: {pattern_data}")
                        continue

                    # Add defaults for required fields if missing
                    if 'skill_level' not in filtered_data:
                        filtered_data['skill_level'] = 'INTERMEDIATE'

                    # Create the pattern
                    try:
                        pattern = Pattern(**filtered_data)
                        session.add(pattern)
                    except Exception as e:
                        logger.error(f"Error adding pattern {filtered_data.get('name', 'UNKNOWN')}: {e}")
                        continue

                logger.info(f"Added {len(sample_data['patterns'])} patterns")

            # Insert products
            if 'products' in sample_data:
                for product_data in sample_data['products']:
                    # Filter data to include only valid fields for the Product model
                    filtered_data = filter_model_data(Product, product_data)

                    # Ensure required fields are present
                    if 'name' not in filtered_data:
                        logger.warning(f"Skipping product without name: {product_data}")
                        continue

                    # Add defaults for required fields if missing
                    if 'price' not in filtered_data:
                        filtered_data['price'] = 0.0

                    if 'is_active' not in filtered_data:
                        filtered_data['is_active'] = True

                    # Create the product
                    try:
                        product = Product(**filtered_data)
                        session.add(product)
                    except Exception as e:
                        logger.error(f"Error adding product {filtered_data.get('name', 'UNKNOWN')}: {e}")
                        continue

                logger.info(f"Added {len(sample_data['products'])} products")

            # Commit to get IDs
            session.commit()

            # Insert projects
            customers = {f"{c.first_name} {c.last_name}": c for c in session.query(Customer).all()}

            if 'projects' in sample_data:
                for project_data in sample_data['projects']:
                    # Filter data to include only valid fields for the Project model
                    filtered_data = filter_model_data(Project, project_data)

                    # Ensure required fields are present
                    if 'name' not in filtered_data:
                        logger.warning(f"Skipping project without name: {project_data}")
                        continue

                    # Add defaults for required fields if missing
                    if 'type' not in filtered_data:
                        filtered_data['type'] = 'WALLET'

                    if 'status' not in filtered_data:
                        filtered_data['status'] = 'PLANNED'

                    # Create the project
                    try:
                        project = Project(**filtered_data)
                        session.add(project)
                    except Exception as e:
                        logger.error(f"Error adding project {filtered_data.get('name', 'UNKNOWN')}: {e}")
                        continue

                logger.info(f"Added {len(sample_data['projects'])} projects")
                session.commit()

            # Insert tools
            if 'tools' in sample_data:
                for tool_data in sample_data['tools']:
                    # Find supplier if specified
                    supplier_id = None
                    if 'supplier_id' in tool_data and isinstance(tool_data['supplier_id'], int):
                        supplier_id = tool_data['supplier_id']

                    # Create tool data
                    tool_kwargs = {
                        'name': tool_data.get('name', f"Tool-{datetime.now().timestamp()}"),
                        'description': tool_data.get('description'),
                        'category': tool_data.get('tool_category', 'CUTTING'),
                        'supplier_id': supplier_id,
                        'brand': tool_data.get('brand'),
                        'model': tool_data.get('model'),
                        'purchase_price': tool_data.get('purchase_price'),
                        'status': tool_data.get('status', 'IN_STOCK'),
                        'maintenance_interval': tool_data.get('maintenance_interval')
                    }

                    # Handle purchase date
                    if 'purchase_date' in tool_data:
                        try:
                            tool_kwargs['purchase_date'] = datetime.strptime(tool_data['purchase_date'], '%Y-%m-%d')
                        except:
                            tool_kwargs['purchase_date'] = datetime.now()

                    # Filter to valid fields
                    filtered_data = filter_model_data(Tool, tool_kwargs)

                    # Create the tool
                    try:
                        tool = Tool(**filtered_data)
                        session.add(tool)
                    except Exception as e:
                        logger.error(f"Error adding tool {filtered_data.get('name', 'UNKNOWN')}: {e}")
                        continue

                logger.info(f"Added {len(sample_data['tools'])} tools")
                session.commit()

            # Get tools and projects for maintenance and checkout records
            tools = {tool.name: tool for tool in session.query(Tool).all()}
            projects = {project.name: project for project in session.query(Project).all()}

            # Add tool maintenance records
            if 'tool_maintenance' in sample_data:
                for maint_data in sample_data['tool_maintenance']:
                    tool = None
                    if 'tool_id' in maint_data and isinstance(maint_data['tool_id'], int):
                        # Try to get tool by ID
                        try:
                            tool = session.query(Tool).get(maint_data['tool_id'])
                        except:
                            pass

                    if tool is None and 'tool' in maint_data and maint_data['tool'] in tools:
                        # Try to get tool by name
                        tool = tools[maint_data['tool']]

                    if tool is None:
                        logger.warning(f"Skipping maintenance record: tool not found - {maint_data}")
                        continue

                    # Parse dates
                    maintenance_date = datetime.now() - timedelta(days=30)

                    # Create maintenance record data
                    maintenance_kwargs = {
                        'tool_id': tool.id,
                        'maintenance_type': maint_data.get('maintenance_type', 'Regular maintenance'),
                        'maintenance_date': maintenance_date,
                        'performed_by': maint_data.get('performed_by'),
                        'cost': maint_data.get('cost'),
                        'status': maint_data.get('status', 'COMPLETED'),
                        'details': maint_data.get('details'),
                        'parts_used': maint_data.get('parts_used'),
                        'maintenance_interval': tool.maintenance_interval,
                        'condition_before': maint_data.get('condition_before'),
                        'condition_after': maint_data.get('condition_after')
                    }

                    # Calculate next maintenance date if interval is provided
                    if tool.maintenance_interval:
                        maintenance_kwargs['next_maintenance_date'] = maintenance_date + timedelta(
                            days=tool.maintenance_interval)

                    # Filter to valid fields
                    filtered_data = filter_model_data(ToolMaintenance, maintenance_kwargs)

                    # Create the maintenance record
                    try:
                        maintenance = ToolMaintenance(**filtered_data)
                        session.add(maintenance)
                    except Exception as e:
                        logger.error(f"Error adding tool maintenance for tool {tool.name}: {e}")
                        continue

                logger.info(f"Added {len(sample_data['tool_maintenance'])} tool maintenance records")

            # Add tool checkout records
            if 'tool_checkouts' in sample_data:
                for checkout_data in sample_data['tool_checkouts']:
                    tool = None
                    if 'tool_id' in checkout_data and isinstance(checkout_data['tool_id'], int):
                        # Try to get tool by ID
                        try:
                            tool = session.query(Tool).get(checkout_data['tool_id'])
                        except:
                            pass

                    if tool is None and 'tool' in checkout_data and checkout_data['tool'] in tools:
                        # Try to get tool by name
                        tool = tools[checkout_data['tool']]

                    if tool is None:
                        logger.warning(f"Skipping checkout record: tool not found - {checkout_data}")
                        continue

                    # Find project if specified
                    project_id = None
                    if 'project_id' in checkout_data and isinstance(checkout_data['project_id'], int):
                        project_id = checkout_data['project_id']
                    elif 'project' in checkout_data and checkout_data['project'] in projects:
                        project_id = projects[checkout_data['project']].id

                    # Parse dates
                    checked_out_date = datetime.now() - timedelta(days=5)
                    due_date = datetime.now() + timedelta(days=5)
                    returned_date = None
                    if checkout_data.get('status') == 'RETURNED':
                        returned_date = datetime.now() - timedelta(days=1)

                    # Create checkout data
                    checkout_kwargs = {
                        'tool_id': tool.id,
                        'project_id': project_id,
                        'checked_out_by': checkout_data.get('checked_out_by', 'Unknown user'),
                        'checked_out_date': checked_out_date,
                        'due_date': due_date,
                        'returned_date': returned_date,
                        'status': checkout_data.get('status', 'CHECKED_OUT'),
                        'notes': checkout_data.get('notes'),
                        'condition_before': checkout_data.get('condition_before'),
                        'condition_after': checkout_data.get('condition_after')
                    }

                    # Filter to valid fields
                    filtered_data = filter_model_data(ToolCheckout, checkout_kwargs)

                    # Create the checkout record
                    try:
                        checkout = ToolCheckout(**filtered_data)
                        session.add(checkout)

                        # Update tool status
                        if checkout_data.get('status') == 'CHECKED_OUT':
                            tool.status = 'CHECKED_OUT'
                            session.add(tool)
                    except Exception as e:
                        logger.error(f"Error adding tool checkout for tool {tool.name}: {e}")
                        continue

                logger.info(f"Added {len(sample_data['tool_checkouts'])} tool checkout records")

            # Add component-material relationships if available
            if 'component_materials' in sample_data:
                components = {component.name: component for component in session.query(Component).all()}
                materials = {material.name: material for material in session.query(Material).all()}

                for cm_data in sample_data['component_materials']:
                    # Get component and material IDs
                    component_id = None
                    material_id = None

                    if 'component_id' in cm_data and isinstance(cm_data['component_id'], int):
                        component_id = cm_data['component_id']
                    elif 'component' in cm_data and cm_data['component'] in components:
                        component_id = components[cm_data['component']].id

                    if 'material_id' in cm_data and isinstance(cm_data['material_id'], int):
                        material_id = cm_data['material_id']
                    elif 'material' in cm_data and cm_data['material'] in materials:
                        material_id = materials[cm_data['material']].id

                    if not component_id or not material_id:
                        logger.warning(f"Skipping component-material: missing references - {cm_data}")
                        continue

                    # Create the relationship
                    try:
                        cm = ComponentMaterial(
                            component_id=component_id,
                            material_id=material_id,
                            quantity=cm_data.get('quantity', 1.0)
                        )
                        session.add(cm)
                    except Exception as e:
                        logger.error(f"Error adding component-material relationship: {e}")
                        continue

                logger.info(f"Added {len(sample_data['component_materials'])} component-material relationships")

            # Commit all remaining changes
            session.commit()
            logger.info("All sample data committed successfully")

            return True

        except Exception as e:
            session.rollback()
            logger.error(f"Error loading sample data: {e}")
            logger.error(traceback.format_exc())
            return False

        finally:
            session.close()

    except Exception as e:
        logger.error(f"Error setting up sample data: {e}")
        logger.error(traceback.format_exc())
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

        try:
            columns = {col['name'] for col in inspector.get_columns('materials')}
            logger.info(f"Materials table has columns: {', '.join(columns)}")
        except:
            # Table might not exist yet
            columns = set()
            logger.warning("Could not inspect materials table columns")

        # Create session
        Session = sessionmaker(bind=engine)
        session = Session()

        try:
            # Import necessary models
            from database.models.supplier import Supplier
            from database.models.customer import Customer
            from database.models.material import Leather, Material
            from database.models.component import Component
            from database.models.tool import Tool
            from database.models.enums import (
                SupplierStatus, CustomerStatus, MaterialType, ComponentType,
                SaleStatus, PaymentStatus, InventoryStatus, PurchaseStatus, ToolCategory
            )

            # Add a supplier using direct SQL to avoid ORM relationship issues
            from sqlalchemy.sql import text
            from datetime import datetime, timedelta

            with engine.connect() as conn:
                # Insert supplier using raw SQL
                try:
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
                except Exception as e:
                    logger.error(f"Error creating supplier: {e}")
                    return False

                # Insert customer
                try:
                    customer_result = conn.execute(
                        text(
                            "INSERT INTO customers (first_name, last_name, email, status, created_at, updated_at) "
                            "VALUES (:first_name, :last_name, :email, :status, :created, :updated)"
                        ),
                        {
                            "first_name": "John",
                            "last_name": "Smith",
                            "email": "john.smith@example.com",
                            "status": "ACTIVE",
                            "created": datetime.now(),
                            "updated": datetime.now()
                        }
                    )
                    conn.commit()
                except Exception as e:
                    logger.error(f"Error creating customer: {e}")
                    return False

                # Insert material
                try:
                    if 'name' in columns and 'material_type' in columns:
                        # Insert material - the basic columns should exist
                        material_cols = ['name', 'description', 'material_type', 'supplier_id', 'created_at',
                                         'updated_at']
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
                        logger.warning(
                            "Materials table doesn't have expected columns, attempting alternative insertion")

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
                except Exception as e:
                    logger.error(f"Error creating material: {e}")
                    # Continue anyway

                # Insert component
                try:
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
                except Exception as e:
                    logger.error(f"Error creating component: {e}")
                    # Continue anyway

                # Get material ID
                try:
                    result = conn.execute(text("SELECT id FROM materials LIMIT 1"))
                    material_id = result.scalar()
                except Exception as e:
                    logger.error(f"Error getting material ID: {e}")
                    material_id = None

                # Get component ID
                try:
                    result = conn.execute(text("SELECT id FROM components WHERE name = 'Wallet Body'"))
                    component_id = result.scalar()
                except Exception as e:
                    logger.error(f"Error getting component ID: {e}")
                    component_id = None

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
                pattern_id = None
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
                    pattern_id = None

                # Create a product
                product_id = None
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
                    product_id = None

                # Create a sales record
                sales_id = None
                try:
                    # Get customer ID
                    result = conn.execute(
                        text("SELECT id FROM customers WHERE first_name = :first_name AND last_name = :last_name"),
                        {"first_name": "John", "last_name": "Smith"}
                    )
                    customer_id = result.scalar()

                    if customer_id:
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
                project_id = None
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

                        # Create a tool and add it to the project
                        tool_id = None
                        try:
                            conn.execute(
                                text(
                                    "INSERT INTO tools (name, description, category, supplier_id, created_at, updated_at) VALUES (:name, :desc, :category, :supplier_id, :created, :updated)"),
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

                            # Create a tool maintenance record
                            if tool_id and "tool_maintenance" in tables:
                                conn.execute(
                                    text(
                                        """
                                        INSERT INTO tool_maintenance (
                                            tool_id, maintenance_type, maintenance_date, performed_by,
                                            status, details, maintenance_interval, next_maintenance_date,
                                            created_at, updated_at
                                        ) VALUES (
                                            :tool_id, :type, :date, :performed_by,
                                            :status, :details, :interval, :next_date,
                                            :created, :updated
                                        )
                                        """
                                    ),
                                    {
                                        "tool_id": tool_id,
                                        "type": "Cleaning and Sharpening",
                                        "date": datetime.now() - timedelta(days=30),
                                        "performed_by": "John Smith",
                                        "status": "COMPLETED",
                                        "details": "Regular maintenance to keep tool in good condition",
                                        "interval": 90,  # 90 days
                                        "next_date": datetime.now() + timedelta(days=60),
                                        "created": datetime.now(),
                                        "updated": datetime.now()
                                    }
                                )
                                logger.info("Created tool maintenance record")

                            # Create a tool checkout record
                            if tool_id and project_id and "tool_checkouts" in tables:
                                conn.execute(
                                    text(
                                        """
                                        INSERT INTO tool_checkouts (
                                            tool_id, project_id, checked_out_by, checked_out_date,
                                            due_date, status, notes, created_at, updated_at
                                        ) VALUES (
                                            :tool_id, :project_id, :checked_out_by, :checked_out_date,
                                            :due_date, :status, :notes, :created, :updated
                                        )
                                        """
                                    ),
                                    {
                                        "tool_id": tool_id,
                                        "project_id": project_id,
                                        "checked_out_by": "John Smith",
                                        "checked_out_date": datetime.now() - timedelta(days=2),
                                        "due_date": datetime.now() + timedelta(days=5),
                                        "status": "CHECKED_OUT",
                                        "notes": "Needed for wallet stitching",
                                        "created": datetime.now(),
                                        "updated": datetime.now()
                                    }
                                )
                                logger.info("Created tool checkout record")

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
                                    result = conn.execute(
                                        text("SELECT id FROM tool_lists WHERE project_id = :project_id"),
                                        {"project_id": project_id})
                                    tool_list_id = result.scalar()

                                    if tool_list_id and tool_id and "tool_list_items" in tables:
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
                        except Exception as e:
                            logger.error(f"Error creating tool data: {e}")

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

                # Create inventory records for materials, products, and tools
                try:
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
    parser.add_argument('--load-sample', type=str, help='Path to sample data JSON file to load')
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

    # Load sample data if provided
    if args.load_sample and success:
        logger.info(f"Loading sample data from {args.load_sample}")
        if not load_sample_data(args.load_sample):
            logger.error("Sample data loading failed")
            return 1

        logger.info("Sample data loading completed successfully")

    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)