#!/usr/bin/env python
"""
Database initialization and seeding script for the leatherworking application.
This version leverages SQLAlchemy ORM and the new model constructors/mixins.
"""

import argparse
import json
import logging
import os
import sys
import traceback
from pathlib import Path
from datetime import datetime, timedelta

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

# Import the base and models via their new structure.
from database.models.base import Base
from database.models.customer import Customer
from database.models.supplier import Supplier
from database.models.material import Material, Leather, Hardware, Supplies
from database.models.component import Component
from database.models.component_material import ComponentMaterial
from database.models.pattern import Pattern
from database.models.product import Product
from database.models.sales import Sales
from database.models.sales_item import SalesItem
from database.models.project import Project
from database.models.project_component import ProjectComponent
from database.models.picking_list import PickingList
from database.models.picking_list_item import PickingListItem
from database.models.tool import Tool
from database.models.tool_maintenance import ToolMaintenance
from database.models.tool_checkout import ToolCheckout
from database.models.tool_list import ToolList
from database.models.tool_list_item import ToolListItem
from database.models.inventory import Inventory
from database.models.purchase import Purchase
from database.models.purchase_item import PurchaseItem

# Basic logging configuration.
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def get_database_path() -> str:
    """
    Determine the database file path and create the data folder if necessary.
    """
    base_dir = Path(__file__).resolve().parent
    data_dir = base_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    db_path = data_dir / "leatherworking_database.db"
    return str(db_path)


def create_engine_and_session(recreate: bool = False):
    """
    Create SQLAlchemy engine and sessionmaker. Optionally drop and recreate tables.
    """
    db_path = get_database_path()
    connection_string = f"sqlite:///{db_path}"
    engine = create_engine(
        connection_string,
        echo=False,
        connect_args={"check_same_thread": False, "timeout": 30},
    )
    if recreate:
        # Optionally backup the existing database.
        if os.path.exists(db_path):
            backup_dir = Path(db_path).parent / "backups"
            backup_dir.mkdir(parents=True, exist_ok=True)
            backup_path = backup_dir / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            try:
                import shutil

                shutil.copy2(db_path, backup_path)
                logger.info(f"Database backed up to {backup_path}")
            except Exception as e:
                logger.error(f"Error during backup: {e}")

        # Drop and recreate tables using metadata.
        Base.metadata.drop_all(engine)
        logger.info("Dropped all tables (recreate flag set)")
    Base.metadata.create_all(engine)
    logger.info("Created all tables based on model metadata")
    Session = sessionmaker(bind=engine)
    return engine, Session


def seed_minimal_data(Session) -> bool:
    """
    Use ORM model constructors (with validation) to seed a minimal set of records.
    """
    try:
        with Session() as session:
            # Create a supplier.
            supplier = Supplier(
                name="Tandy Leather",
                contact_email="sales@tandyleather.com",
                status="ACTIVE",
            )
            session.add(supplier)
            session.commit()  # Commit to assign an ID.

            # Create a customer.
            customer = Customer(
                first_name="John",
                last_name="Smith",
                email="john.smith@example.com",
                status="ACTIVE",
            )
            session.add(customer)
            session.commit()

            # Create a Leather material.
            leather = Leather(
                name="Veg-tan Leather",
                material_type="LEATHER",
                leather_type="VEGETABLE_TANNED",
                quality="PREMIUM",
                supplier_id=supplier.id,
                cost_price=15.99,
                unit="SQUARE_FOOT",
                is_full_hide=True,
                area=50.0,
            )
            session.add(leather)
            session.commit()

            # Create a component.
            component = Component(
                name="Wallet Body",
                description="Main piece for wallet",
                component_type="LEATHER",
            )
            session.add(component)
            session.commit()

            # Link component and material.
            comp_mat = ComponentMaterial(
                component_id=component.id, material_id=leather.id, quantity=1.0
            )
            session.add(comp_mat)

            # Create a pattern.
            pattern = Pattern(
                name="Basic Bifold Wallet",
                description="Simple wallet pattern",
                skill_level="INTERMEDIATE",
            )
            session.add(pattern)
            session.commit()

            # Create a product.
            product = Product(
                name="Handcrafted Leather Wallet",
                description="Premium bifold wallet",
                price=79.99,
            )
            session.add(product)
            session.commit()

            # Create a sales record and corresponding sales item.
            sales = Sales(
                customer_id=customer.id,
                total_amount=79.99,
                status="DESIGN_APPROVAL",
                payment_status="DEPOSIT_RECEIVED",
                created_at=datetime.now(),
            )
            session.add(sales)
            session.commit()

            sales_item = SalesItem(
                quantity=1,
                price=79.99,
                sales_id=sales.id,
                product_id=product.id,
            )
            session.add(sales_item)
            session.commit()

            # Create a project.
            project = Project(
                name="Custom Wallet Project #1",
                description="Custom project for John Smith",
                type="WALLET",
                status="PLANNED",
                sales_id=sales.id,
                start_date=datetime.now(),
                end_date=datetime.now() + timedelta(days=30),
            )
            session.add(project)
            session.commit()

            # Link component with the project.
            proj_comp = ProjectComponent(
                project_id=project.id, component_id=component.id, quantity=1
            )
            session.add(proj_comp)

            # Create a picking list and an item in it.
            picking_list = PickingList(
                sales_id=sales.id, status="DRAFT", created_at=datetime.now()
            )
            session.add(picking_list)
            session.commit()

            pli = PickingListItem(
                picking_list_id=picking_list.id,
                component_id=component.id,
                material_id=leather.id,
                quantity_ordered=1,
                quantity_picked=0,
            )
            session.add(pli)

            # Create a tool.
            tool = Tool(
                name="Stitching Awl",
                description="A stitching awl tool",
                tool_category="STITCHING",
                supplier_id=supplier.id,
                brand="Tandy",
                model="TA-1000",
                purchase_price=25.0,
                status="IN_STOCK",
                purchase_date=datetime.now(),
            )
            session.add(tool)
            session.commit()

            # Create a tool maintenance record.
            tool_maintenance = ToolMaintenance(
                tool_id=tool.id,
                maintenance_type="Regular maintenance",
                maintenance_date=datetime.now() - timedelta(days=30),
                performed_by="John Smith",
                cost=5.0,
                status="COMPLETED",
                details="Cleaned and sharpened",
                maintenance_interval=90,
                next_maintenance_date=datetime.now() + timedelta(days=60),
            )
            session.add(tool_maintenance)

            # Create a tool checkout record.
            tool_checkout = ToolCheckout(
                tool_id=tool.id,
                project_id=project.id,
                checked_out_by="John Smith",
                checked_out_date=datetime.now() - timedelta(days=2),
                due_date=datetime.now() + timedelta(days=5),
                status="CHECKED_OUT",
                notes="Used for stitching",
            )
            session.add(tool_checkout)

            # Create a tool list with an item.
            tool_list = ToolList(
                project_id=project.id, status="DRAFT", created_at=datetime.now()
            )
            session.add(tool_list)
            session.commit()

            tool_list_item = ToolListItem(
                tool_list_id=tool_list.id, tool_id=tool.id, quantity=1
            )
            session.add(tool_list_item)

            # Create inventory records.
            inv_material = Inventory(
                item_type="material",
                item_id=leather.id,
                quantity=10.0,
                status="IN_STOCK",
                storage_location="Shelf A1",
            )
            inv_product = Inventory(
                item_type="product",
                item_id=product.id,
                quantity=5.0,
                status="IN_STOCK",
                storage_location="Shelf B2",
            )
            inv_tool = Inventory(
                item_type="tool",
                item_id=tool.id,
                quantity=3.0,
                status="IN_STOCK",
                storage_location="Drawer C3",
            )
            session.add_all([inv_material, inv_product, inv_tool])

            # Create a purchase record and its purchase items.
            purchase = Purchase(
                supplier_id=supplier.id,
                total_amount=159.90,
                status="ORDERED",
                purchase_order_number="PO-2025-001",
                created_at=datetime.now(),
                order_date=datetime.now(),
                expected_delivery=datetime.now() + timedelta(days=7),
            )
            session.add(purchase)
            session.commit()

            purchase_item_material = PurchaseItem(
                purchase_id=purchase.id,
                item_type="material",
                item_id=leather.id,
                quantity=10.0,
                price=15.99,
            )
            purchase_item_tool = PurchaseItem(
                purchase_id=purchase.id,
                item_type="tool",
                item_id=tool.id,
                quantity=2.0,
                price=25.0,
            )
            session.add_all([purchase_item_material, purchase_item_tool])
            session.commit()

            logger.info("Minimal seeding completed successfully.")
            return True

    except Exception as e:
        logger.error(f"Error seeding minimal data: {e}")
        logger.error(traceback.format_exc())
        return False


def load_sample_data(Session, json_file_path: str) -> bool:
    """
    Load sample data from a JSON file in the correct order to respect foreign key relationships.

    Args:
        Session: SQLAlchemy sessionmaker
        json_file_path: Path to the JSON file containing sample data

    Returns:
        bool: Success or failure
    """
    import dateutil.parser
    from collections import defaultdict

    try:
        if not os.path.exists(json_file_path):
            logger.error(f"Sample data file not found: {json_file_path}")
            return False

        with open(json_file_path, "r", encoding="utf-8") as file:
            sample_data = json.load(file)

        # Define field mappings for each model to handle inconsistencies
        field_mappings = {
            'supplies': {'thickness': 'thread_thickness'}
        }

        # Define fields to remove for specific models that have custom __init__ methods
        # or to prevent unique constraint violations
        fields_to_remove = {
            'componentMaterials': ['id'],  # ComponentMaterial doesn't accept 'id' in __init__
        }

        # Track loaded entities for reporting
        loaded_counts = defaultdict(int)
        error_counts = defaultdict(int)

        def process_entity(entity_data, entity_type, model_class, session):
            """Process a single entity: map fields, convert dates, and add to session"""
            try:
                # Create a copy of the entity data
                processed_data = entity_data.copy()

                # Remove fields that should be excluded for this entity type
                if entity_type in fields_to_remove:
                    for field in fields_to_remove[entity_type]:
                        if field in processed_data:
                            del processed_data[field]

                # Apply field mappings if they exist for this entity type
                if entity_type in field_mappings:
                    for source_field, target_field in field_mappings[entity_type].items():
                        if source_field in processed_data:
                            processed_data[target_field] = processed_data.pop(source_field)

                # Convert date strings to datetime objects
                for key, value in list(processed_data.items()):
                    if isinstance(value, str) and (
                            key.endswith('_date') or key.endswith('_at') or
                            'date' in key or 'time' in key
                    ):
                        try:
                            processed_data[key] = dateutil.parser.parse(value)
                        except (ValueError, TypeError):
                            # Not a valid date string, leave as is
                            pass

                # Create and add the entity
                entity = model_class(**processed_data)
                session.add(entity)
                loaded_counts[entity_type] += 1
                return True
            except Exception as e:
                logger.error(f"Error adding {entity_type}: {e}")
                error_counts[entity_type] += 1
                return False

        with Session() as session:
            # 1. Basic entities with no foreign key dependencies
            if "customers" in sample_data:
                for customer_data in sample_data["customers"]:
                    process_entity(customer_data, "customers", Customer, session)
                session.flush()
                logger.info(f"Loaded {loaded_counts['customers']} customers")

            if "suppliers" in sample_data:
                for supplier_data in sample_data["suppliers"]:
                    process_entity(supplier_data, "suppliers", Supplier, session)
                session.flush()
                logger.info(f"Loaded {loaded_counts['suppliers']} suppliers")

            if "patterns" in sample_data:
                for pattern_data in sample_data["patterns"]:
                    process_entity(pattern_data, "patterns", Pattern, session)
                session.flush()
                logger.info(f"Loaded {loaded_counts['patterns']} patterns")

            # 2. Load materials (leathers, hardware, supplies)
            if "leathers" in sample_data:
                for leather_data in sample_data["leathers"]:
                    process_entity(leather_data, "leathers", Leather, session)
                session.flush()
                logger.info(f"Loaded {loaded_counts['leathers']} leather materials")

            if "hardwares" in sample_data:
                for hardware_data in sample_data["hardwares"]:
                    process_entity(hardware_data, "hardwares", Hardware, session)
                session.flush()
                logger.info(f"Loaded {loaded_counts['hardwares']} hardware materials")

            if "supplies" in sample_data:
                for supply_data in sample_data["supplies"]:
                    process_entity(supply_data, "supplies", Supplies, session)
                session.flush()
                logger.info(f"Loaded {loaded_counts['supplies']} supply materials")

            # 3. Load components and tools
            if "components" in sample_data:
                for component_data in sample_data["components"]:
                    process_entity(component_data, "components", Component, session)
                session.flush()
                logger.info(f"Loaded {loaded_counts['components']} components")

            if "tools" in sample_data:
                for tool_data in sample_data["tools"]:
                    process_entity(tool_data, "tools", Tool, session)
                session.flush()
                logger.info(f"Loaded {loaded_counts['tools']} tools")

            # 4. Load component materials (junction table) - special handling
            if "componentMaterials" in sample_data:
                for cm_data in sample_data["componentMaterials"]:
                    try:
                        # Create directly without the ID field
                        comp_mat = ComponentMaterial(
                            component_id=cm_data['component_id'],
                            material_id=cm_data['material_id'],
                            quantity=cm_data.get('quantity', 1.0)
                        )
                        session.add(comp_mat)
                        loaded_counts["componentMaterials"] += 1
                    except Exception as e:
                        logger.error(f"Error adding component material: {e}")
                        error_counts["componentMaterials"] += 1
                session.flush()
                logger.info(f"Loaded {loaded_counts['componentMaterials']} component materials")

            # Load products
            if "products" in sample_data:
                for product_data in sample_data["products"]:
                    process_entity(product_data, "products", Product, session)
                session.flush()
                logger.info(f"Loaded {loaded_counts['products']} products")

            # 5. Load sales and purchases
            if "sales" in sample_data:
                for sale_data in sample_data["sales"]:
                    process_entity(sale_data, "sales", Sales, session)
                session.flush()
                logger.info(f"Loaded {loaded_counts['sales']} sales")

            if "purchases" in sample_data:
                for purchase_data in sample_data["purchases"]:
                    process_entity(purchase_data, "purchases", Purchase, session)
                session.flush()
                logger.info(f"Loaded {loaded_counts['purchases']} purchases")

            # Load sales items
            if "salesItems" in sample_data:
                for item_data in sample_data["salesItems"]:
                    process_entity(item_data, "salesItems", SalesItem, session)
                session.flush()
                logger.info(f"Loaded {loaded_counts['salesItems']} sales items")

            # Load purchase items - special handling for validation errors
            if "purchaseItems" in sample_data:
                for item_data in sample_data["purchaseItems"]:
                    try:
                        # Create a completely clean copy of the data
                        purchase_data = {}

                        # Handle required fields with appropriate defaults
                        purchase_data['purchase_id'] = item_data.get('purchase_id')
                        purchase_data['item_type'] = item_data.get('item_type', 'material')
                        purchase_data['item_id'] = item_data.get('item_id')

                        # Ensure numeric fields have proper numeric values, not None
                        purchase_data['quantity'] = float(
                            item_data.get('quantity', 1.0) or 1.0)  # Default to 1.0 if None or missing
                        purchase_data['price'] = float(
                            item_data.get('price', 0.0) or 0.0)  # Default to 0.0 if None or missing
                        purchase_data['received_quantity'] = float(
                            item_data.get('received_quantity', 0.0) or 0.0)  # Default to 0.0 if None

                        # Add createdAt and updatedAt if needed
                        purchase_data['created_at'] = datetime.now()

                        # Verify that required relationships exist
                        if not purchase_data['purchase_id']:
                            raise ValueError("purchase_id is required and cannot be null")

                        if not purchase_data['item_id']:
                            raise ValueError("item_id is required and cannot be null")

                        # Create the PurchaseItem with our clean data
                        purchase_item = PurchaseItem(**purchase_data)
                        session.add(purchase_item)
                        loaded_counts["purchaseItems"] += 1

                    except Exception as e:
                        logger.error(f"Error adding purchase item: {e}")
                        error_counts["purchaseItems"] += 1

                session.flush()
                logger.info(f"Loaded {loaded_counts['purchaseItems']} purchase items")

            # 6. Load inventory
            if "inventory" in sample_data:
                for inventory_data in sample_data["inventory"]:
                    process_entity(inventory_data, "inventory", Inventory, session)
                session.flush()
                logger.info(f"Loaded {loaded_counts['inventory']} inventory items")

            # 7. Load projects
            if "projects" in sample_data:
                for project_data in sample_data["projects"]:
                    process_entity(project_data, "projects", Project, session)
                session.flush()
                logger.info(f"Loaded {loaded_counts['projects']} projects")

            if "projectComponents" in sample_data:
                for pc_data in sample_data["projectComponents"]:
                    process_entity(pc_data, "projectComponents", ProjectComponent, session)
                session.flush()
                logger.info(f"Loaded {loaded_counts['projectComponents']} project components")

            # 8. Load picking lists and tool lists
            if "pickingLists" in sample_data:
                for list_data in sample_data["pickingLists"]:
                    process_entity(list_data, "pickingLists", PickingList, session)
                session.flush()
                logger.info(f"Loaded {loaded_counts['pickingLists']} picking lists")

            # Special handling for picking list items - auto-generate IDs and handle validation
            if "pickingListItems" in sample_data:
                for item_data in sample_data["pickingListItems"]:
                    try:
                        # Create a copy to modify
                        pli_data = item_data.copy()

                        # Always remove the ID to let SQLAlchemy auto-generate it
                        if 'id' in pli_data:
                            del pli_data['id']

                        # Convert date fields
                        for key, value in list(pli_data.items()):
                            if isinstance(value, str) and (
                                    key.endswith('_date') or key.endswith('_at') or
                                    'date' in key or 'time' in key
                            ):
                                try:
                                    pli_data[key] = dateutil.parser.parse(value)
                                except (ValueError, TypeError):
                                    pass

                        # Handle validation requirements - either component_id or material_id, not both
                        if 'component_id' in pli_data and 'material_id' in pli_data and pli_data['component_id'] and \
                                pli_data['material_id']:
                            # Strategy: Create one record with only material_id and ignore component_id
                            material_version = pli_data.copy()
                            material_version['component_id'] = None
                            pli = PickingListItem(**material_version)
                            session.add(pli)
                            loaded_counts["pickingListItems"] += 1
                        else:
                            # Only one or none of the IDs is set, so proceed normally
                            pli = PickingListItem(**pli_data)
                            session.add(pli)
                            loaded_counts["pickingListItems"] += 1
                    except Exception as e:
                        logger.error(f"Error adding picking list item: {e}")
                        error_counts["pickingListItems"] += 1
                session.flush()
                logger.info(f"Loaded {loaded_counts['pickingListItems']} picking list items")

            if "toolLists" in sample_data:
                for list_data in sample_data["toolLists"]:
                    process_entity(list_data, "toolLists", ToolList, session)
                session.flush()
                logger.info(f"Loaded {loaded_counts['toolLists']} tool lists")

            if "toolListItems" in sample_data:
                for item_data in sample_data["toolListItems"]:
                    process_entity(item_data, "toolListItems", ToolListItem, session)
                session.flush()
                logger.info(f"Loaded {loaded_counts['toolListItems']} tool list items")

            # 9. Load tool maintenance and checkouts
            if "toolMaintenance" in sample_data:
                for maint_data in sample_data["toolMaintenance"]:
                    process_entity(maint_data, "toolMaintenance", ToolMaintenance, session)
                session.flush()
                logger.info(f"Loaded {loaded_counts['toolMaintenance']} tool maintenance records")

            if "toolCheckouts" in sample_data:
                for checkout_data in sample_data["toolCheckouts"]:
                    process_entity(checkout_data, "toolCheckouts", ToolCheckout, session)
                session.flush()
                logger.info(f"Loaded {loaded_counts['toolCheckouts']} tool checkouts")

            # Final commit for all data
            session.commit()

            # Report summary
            total_loaded = sum(loaded_counts.values())
            total_errors = sum(error_counts.values())

            if total_errors == 0:
                logger.info(f"Sample data loaded successfully: {total_loaded} total records")
                return True
            else:
                logger.warning(f"Sample data loaded with some errors: {total_loaded} loaded, {total_errors} failed")
                return total_loaded > 0  # Return True if at least some data was loaded

    except Exception as e:
        logger.error(f"Error loading sample data: {e}")
        logger.error(traceback.format_exc())
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Initialize leatherworking database"
    )
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Drop and recreate all tables",
    )
    parser.add_argument(
        "--seed",
        action="store_true",
        help="Add minimal seed data to the database",
    )
    parser.add_argument(
        "--load-sample",
        type=str,
        help="Path to sample data JSON file to load",
    )
    args = parser.parse_args()

    try:
        engine, Session = create_engine_and_session(recreate=args.recreate)
    except Exception as e:
        logger.error(f"Error setting up engine and session: {e}")
        return 1

    if args.seed:
        if not seed_minimal_data(Session):
            logger.error("Minimal seeding failed.")
            return 1

    if args.load_sample:
        if not load_sample_data(Session, args.load_sample):
            logger.error("Loading sample data failed.")
            return 1

    logger.info("Database initialization completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
