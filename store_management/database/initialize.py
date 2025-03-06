# database/initialize.py

import logging
import os
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
import random
from typing import Optional, List, Dict, Any

import sqlalchemy
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session

from database.models.base import Base
from utils.circular_import_resolver import resolve_lazy_import

logger = logging.getLogger(__name__)


def get_database_path() -> Path:
    """
    Get the path to the SQLite database file.

    Returns:
        Path: The absolute path to the database file.
    """
    # You can adjust this to match your actual database configuration
    from config.settings import get_database_path
    return get_database_path()


def initialize_database(reset_db: bool = False) -> None:
    """
    Initialize the database, creating tables if they don't exist.

    Args:
        reset_db (bool): If True, existing tables will be dropped before creation.
    """
    logger.info("Initializing database...")

    db_path = get_database_path()
    directory = os.path.dirname(db_path)

    # Create the directory if it doesn't exist
    if not os.path.exists(directory):
        os.makedirs(directory)
        logger.info(f"Created database directory: {directory}")

    # Create SQLAlchemy engine
    db_url = f"sqlite:///{db_path}"
    engine = create_engine(db_url)

    # Check for existing tables
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    if reset_db and existing_tables:
        logger.warning("Resetting database - all data will be lost!")
        Base.metadata.drop_all(engine)
        existing_tables = []

    # Create tables if they don't exist
    if not existing_tables:
        logger.info("Creating database tables...")
        Base.metadata.create_all(engine)
        logger.info("Database tables created successfully")
    else:
        logger.info(f"Database already contains tables: {', '.join(existing_tables)}")

    logger.info("Database initialization complete")


def add_sample_data(session=None) -> None:
    """
    Add comprehensive sample data to the database for testing and demonstration.

    Populates the database with realistic data for a leatherworking business including:
    - Suppliers
    - Materials (leather, hardware, thread, etc.)
    - Storage locations
    - Products
    - Projects
    - Orders
    - Shopping lists

    Args:
        session: SQLAlchemy session to use. If None, a new session will be created.
    """
    logger.info("Adding sample data to database...")

    if session is None:
        from database.sqlalchemy.session import get_db_session
        session = get_db_session()

    try:
        # Import models here to avoid circular imports
        from database.models.supplier import Supplier
        from database.models.storage import Storage
        from database.models.material import Material
        from database.models.hardware import Hardware
        from database.models.leather import Leather
        from database.models.product import Product
        from database.models.project import Project, ProjectComponent
        from database.models.sale import Sale, SaleItem
        from database.models.shopping_list import ShoppingList, ShoppingListItem
        from database.models.pattern import Pattern
        from database.models.enums import (
            MaterialType, MaterialQualityGrade, InventoryStatus,
            LeatherType, StorageLocationType, ProjectType, ProjectStatus,
            SkillLevel, SupplierStatus, SaleStatus, PaymentStatus, Priority
        )

        # Check if data already exists
        if session.query(Supplier).count() > 0:
            logger.info("Sample data already exists in database")
            return

        # 1. Create suppliers
        suppliers = [
            Supplier(
                name="Premium Leather Supply",
                contact_name="Emily Johnson",
                email="emily@premiumleather.com",
                phone="555-123-4567",
                address="123 Tannery Way, Portland, OR 97205",
                website="www.premiumleathersupply.com",
                status=SupplierStatus.ACTIVE,
                notes="High-quality leather supplier, good for premium projects",
                rating=4.8
            ),
            Supplier(
                name="Buckaroo Hardware",
                contact_name="Michael Torres",
                email="mtorres@buckaroohardware.net",
                phone="555-765-1234",
                address="456 Metal Alley, Denver, CO 80202",
                website="www.buckaroohardware.net",
                status=SupplierStatus.ACTIVE,
                notes="Reliable hardware supplier with good selection",
                rating=4.5
            ),
            Supplier(
                name="Craftsman's Thread",
                contact_name="Lisa Wong",
                email="lwong@craftsmanthread.com",
                phone="555-987-6543",
                address="789 Stitch Lane, Nashville, TN 37203",
                website="www.craftsmanthread.com",
                status=SupplierStatus.ACTIVE,
                notes="Specialized in high-strength thread for leatherworking",
                rating=4.7
            ),
            Supplier(
                name="Tannery Direct",
                contact_name="Robert Wilson",
                email="rwilson@tannerydirect.com",
                phone="555-246-8024",
                address="321 Leather Road, Chicago, IL 60611",
                website="www.tannerydirect.com",
                status=SupplierStatus.ACTIVE,
                notes="Direct from tannery, good for bulk purchases",
                rating=4.2
            ),
            Supplier(
                name="Exotic Leathers Inc.",
                contact_name="Sarah Martinez",
                email="smartinez@exoticleathers.biz",
                phone="555-369-1478",
                address="852 Scale Street, Miami, FL 33130",
                website="www.exoticleathersinc.biz",
                status=SupplierStatus.ACTIVE,
                notes="Specializes in exotic leathers, premium pricing",
                rating=4.6
            )
        ]
        session.add_all(suppliers)
        session.flush()
        logger.info(f"Added {len(suppliers)} suppliers")

        # 2. Create storage locations
        storage_locations = [
            Storage(
                name="Main Shelf A",
                location_type=StorageLocationType.SHELF,
                capacity=100.0,
                current_usage=45.0,
                description="Primary storage for premium leather materials",
                notes="Keep organized by leather type"
            ),
            Storage(
                name="Hardware Cabinet B",
                location_type=StorageLocationType.CABINET,
                capacity=200.0,
                current_usage=120.0,
                description="Storage for various hardware components",
                notes="Organized by hardware type and size"
            ),
            Storage(
                name="Thread Drawer C",
                location_type=StorageLocationType.DRAWER,
                capacity=50.0,
                current_usage=35.0,
                description="Thread storage organized by color and weight",
                notes="Keep drawer closed to prevent dust"
            ),
            Storage(
                name="Tool Rack D",
                location_type=StorageLocationType.RACK,
                capacity=75.0,
                current_usage=60.0,
                description="Hanging storage for frequently used tools",
                notes="Clean tools before returning to rack"
            ),
            Storage(
                name="Exotic Leather Box E",
                location_type=StorageLocationType.BOX,
                capacity=30.0,
                current_usage=12.0,
                description="Climate-controlled storage for exotic leathers",
                notes="Check humidity levels weekly"
            ),
            Storage(
                name="Supply Bin F",
                location_type=StorageLocationType.BIN,
                capacity=150.0,
                current_usage=90.0,
                description="General supply storage",
                notes="Miscellaneous supplies and small items"
            )
        ]
        session.add_all(storage_locations)
        session.flush()
        logger.info(f"Added {len(storage_locations)} storage locations")

        # 3. Create materials - Leather
        leathers = [
            Leather(
                name="Vintage Brown Full Grain",
                material_type=MaterialType.LEATHER,
                supplier_id=suppliers[0].id,
                leather_type=LeatherType.FULL_GRAIN,
                quality_grade=MaterialQualityGrade.PREMIUM,
                thickness=4.5,  # in mm
                area=10.5,  # in square feet
                color="Vintage Brown",
                price_per_unit=12.99,
                units_in_stock=15.0,
                reorder_level=5.0,
                status=InventoryStatus.IN_STOCK,
                location_id=storage_locations[0].id,
                description="Premium full grain leather with beautiful pull-up effect"
            ),
            Leather(
                name="Black Chromexcel",
                material_type=MaterialType.LEATHER,
                supplier_id=suppliers[0].id,
                leather_type=LeatherType.FULL_GRAIN,
                quality_grade=MaterialQualityGrade.PREMIUM,
                thickness=2.0,  # in mm
                area=12.0,  # in square feet
                color="Black",
                price_per_unit=14.50,
                units_in_stock=10.0,
                reorder_level=3.0,
                status=InventoryStatus.IN_STOCK,
                location_id=storage_locations[0].id,
                description="Horween Chromexcel leather, excellent for wallets and bags"
            ),
            Leather(
                name="Honey Harness",
                material_type=MaterialType.LEATHER,
                supplier_id=suppliers[3].id,
                leather_type=LeatherType.VEG_TAN,
                quality_grade=MaterialQualityGrade.STANDARD,
                thickness=3.2,  # in mm
                area=15.0,  # in square feet
                color="Honey",
                price_per_unit=10.75,
                units_in_stock=8.0,
                reorder_level=4.0,
                status=InventoryStatus.IN_STOCK,
                location_id=storage_locations[0].id,
                description="Flexible harness leather with honey finish"
            ),
            Leather(
                name="Natural Veg Tan",
                material_type=MaterialType.LEATHER,
                supplier_id=suppliers[3].id,
                leather_type=LeatherType.VEG_TAN,
                quality_grade=MaterialQualityGrade.PREMIUM,
                thickness=3.8,  # in mm
                area=20.0,  # in square feet
                color="Natural",
                price_per_unit=11.25,
                units_in_stock=12.0,
                reorder_level=6.0,
                status=InventoryStatus.IN_STOCK,
                location_id=storage_locations[0].id,
                description="Tooling leather perfect for carved projects"
            ),
            Leather(
                name="Burgundy Chevre",
                material_type=MaterialType.LEATHER,
                supplier_id=suppliers[4].id,
                leather_type=LeatherType.EXOTIC,
                quality_grade=MaterialQualityGrade.PREMIUM,
                thickness=1.6,  # in mm
                area=6.0,  # in square feet
                color="Burgundy",
                price_per_unit=18.50,
                units_in_stock=4.0,
                reorder_level=2.0,
                status=InventoryStatus.LOW_STOCK,
                location_id=storage_locations[4].id,
                description="Premium goatskin with distinctive grain pattern"
            ),
            Leather(
                name="Navy Blue Buttero",
                material_type=MaterialType.LEATHER,
                supplier_id=suppliers[0].id,
                leather_type=LeatherType.VEG_TAN,
                quality_grade=MaterialQualityGrade.PREMIUM,
                thickness=1.8,  # in mm
                area=8.0,  # in square feet
                color="Navy Blue",
                price_per_unit=15.75,
                units_in_stock=5.0,
                reorder_level=2.0,
                status=InventoryStatus.IN_STOCK,
                location_id=storage_locations[0].id,
                description="Italian vegetable tanned leather with smooth finish"
            ),
            Leather(
                name="Olive Green Pueblo",
                material_type=MaterialType.LEATHER,
                supplier_id=suppliers[3].id,
                leather_type=LeatherType.VEG_TAN,
                quality_grade=MaterialQualityGrade.PREMIUM,
                thickness=2.2,  # in mm
                area=7.5,  # in square feet
                color="Olive Green",
                price_per_unit=14.25,
                units_in_stock=0.0,
                reorder_level=3.0,
                status=InventoryStatus.OUT_OF_STOCK,
                location_id=storage_locations[0].id,
                description="Textured vegetable tanned leather with natural feel"
            )
        ]
        session.add_all(leathers)
        session.flush()
        logger.info(f"Added {len(leathers)} leather materials")

        # 4. Create hardware items
        hardware_items = [
            Hardware(
                name="Solid Brass Buckle 1\"",
                material_type=MaterialType.HARDWARE,
                supplier_id=suppliers[1].id,
                hardware_type="BUCKLE",
                hardware_material="BRASS",
                hardware_finish="POLISHED",
                size="1 inch",
                price_per_unit=3.99,
                units_in_stock=50,
                reorder_level=15,
                status=InventoryStatus.IN_STOCK,
                location_id=storage_locations[1].id,
                description="Solid brass center-bar buckle, 1 inch width"
            ),
            Hardware(
                name="Antique Brass Snap Buttons",
                material_type=MaterialType.HARDWARE,
                supplier_id=suppliers[1].id,
                hardware_type="SNAP",
                hardware_material="BRASS",
                hardware_finish="ANTIQUE",
                size="15mm",
                price_per_unit=0.75,
                units_in_stock=200,
                reorder_level=50,
                status=InventoryStatus.IN_STOCK,
                location_id=storage_locations[1].id,
                description="Line 24 snap buttons with antique brass finish"
            ),
            Hardware(
                name="Nickel Chicago Screws",
                material_type=MaterialType.HARDWARE,
                supplier_id=suppliers[1].id,
                hardware_type="OTHER",
                hardware_material="NICKEL",
                hardware_finish="POLISHED",
                size="6mm",
                price_per_unit=0.40,
                units_in_stock=300,
                reorder_level=100,
                status=InventoryStatus.IN_STOCK,
                location_id=storage_locations[1].id,
                description="6mm binding screws for leather projects"
            ),
            Hardware(
                name="Black D-Rings 3/4\"",
                material_type=MaterialType.HARDWARE,
                supplier_id=suppliers[1].id,
                hardware_type="D_RING",
                hardware_material="STEEL",
                hardware_finish="BLACK_OXIDE",
                size="3/4 inch",
                price_per_unit=1.25,
                units_in_stock=75,
                reorder_level=25,
                status=InventoryStatus.IN_STOCK,
                location_id=storage_locations[1].id,
                description="Black oxide finish D-rings for straps"
            ),
            Hardware(
                name="Copper Rivets",
                material_type=MaterialType.HARDWARE,
                supplier_id=suppliers[1].id,
                hardware_type="RIVET",
                hardware_material="COPPER",
                hardware_finish="NATURAL",
                size="9mm",
                price_per_unit=0.35,
                units_in_stock=250,
                reorder_level=100,
                status=InventoryStatus.IN_STOCK,
                location_id=storage_locations[1].id,
                description="Solid copper rivets for reinforcement"
            ),
            Hardware(
                name="Brass Zipper #5",
                material_type=MaterialType.HARDWARE,
                supplier_id=suppliers[1].id,
                hardware_type="ZIPPER",
                hardware_material="BRASS",
                hardware_finish="POLISHED",
                size="#5",
                price_per_unit=2.50,
                units_in_stock=20,
                reorder_level=10,
                status=InventoryStatus.LOW_STOCK,
                location_id=storage_locations[1].id,
                description="Continuous brass zipper roll, #5 size"
            ),
            Hardware(
                name="Magnetic Snaps",
                material_type=MaterialType.HARDWARE,
                supplier_id=suppliers[1].id,
                hardware_type="MAGNETIC_CLOSURE",
                hardware_material="STEEL",
                hardware_finish="NICKEL_PLATED",
                size="18mm",
                price_per_unit=1.99,
                units_in_stock=40,
                reorder_level=20,
                status=InventoryStatus.IN_STOCK,
                location_id=storage_locations[1].id,
                description="Strong magnetic snaps for closures"
            )
        ]
        session.add_all(hardware_items)
        session.flush()
        logger.info(f"Added {len(hardware_items)} hardware items")

        # 5. Create materials - Thread, Adhesives, etc.
        other_materials = [
            Material(
                name="Ritza Tiger Thread",
                material_type=MaterialType.THREAD,
                supplier_id=suppliers[2].id,
                price_per_unit=29.99,
                units_in_stock=15,
                reorder_level=5,
                status=InventoryStatus.IN_STOCK,
                location_id=storage_locations[2].id,
                description="0.6mm polyester thread, 25m spool, cream color",
                notes="Premium hand-stitching thread"
            ),
            Material(
                name="Black Waxed Thread",
                material_type=MaterialType.THREAD,
                supplier_id=suppliers[2].id,
                price_per_unit=24.99,
                units_in_stock=12,
                reorder_level=4,
                status=InventoryStatus.IN_STOCK,
                location_id=storage_locations[2].id,
                description="0.8mm polyester thread, 25m spool, black",
                notes="Good contrast stitching thread"
            ),
            Material(
                name="Contact Cement",
                material_type=MaterialType.ADHESIVE,
                supplier_id=suppliers[1].id,
                price_per_unit=12.50,
                units_in_stock=8,
                reorder_level=3,
                status=InventoryStatus.IN_STOCK,
                location_id=storage_locations[5].id,
                description="8oz can of water-based contact cement",
                notes="Strong bonding but repositionable"
            ),
            Material(
                name="Edge Coat",
                material_type=MaterialType.FINISH,
                supplier_id=suppliers[0].id,
                price_per_unit=15.75,
                units_in_stock=6,
                reorder_level=2,
                status=InventoryStatus.IN_STOCK,
                location_id=storage_locations[5].id,
                description="4oz bottle of black edge finish",
                notes="Use with wool dauber for best results"
            ),
            Material(
                name="Neatsfoot Oil",
                material_type=MaterialType.FINISH,
                supplier_id=suppliers[0].id,
                price_per_unit=9.99,
                units_in_stock=4,
                reorder_level=2,
                status=InventoryStatus.LOW_STOCK,
                location_id=storage_locations[5].id,
                description="8oz bottle of pure neatsfoot oil",
                notes="For conditioning vegetable tanned leather"
            ),
            Material(
                name="Red Dye",
                material_type=MaterialType.DYE,
                supplier_id=suppliers[0].id,
                price_per_unit=11.25,
                units_in_stock=3,
                reorder_level=2,
                status=InventoryStatus.IN_STOCK,
                location_id=storage_locations[5].id,
                description="4oz bottle of alcohol-based leather dye, red",
                notes="Use with wool dauber and wear gloves"
            )
        ]
        session.add_all(other_materials)
        session.flush()
        logger.info(f"Added {len(other_materials)} other materials")

        # 6. Create patterns
        patterns = [
            Pattern(
                name="Classic Bifold Wallet",
                description="Traditional bifold wallet with card slots and bill compartment",
                difficulty_level=SkillLevel.INTERMEDIATE,
                estimated_time=120,  # minutes
                estimated_cost=35.50,
                materials_needed="2 sq ft of leather, thread, edge coat",
                instructions="Step 1: Cut all pieces according to template...",
                version="1.2",
                created_by="John Smith",
                created_at=datetime.now() - timedelta(days=120)
            ),
            Pattern(
                name="Minimalist Card Holder",
                description="Slim card holder with 3 pockets",
                difficulty_level=SkillLevel.BEGINNER,
                estimated_time=60,  # minutes
                estimated_cost=15.75,
                materials_needed="0.75 sq ft of leather, thread",
                instructions="Step 1: Cut the leather to size...",
                version="1.0",
                created_by="Emily Johnson",
                created_at=datetime.now() - timedelta(days=90)
            ),
            Pattern(
                name="Messenger Bag",
                description="Medium-sized messenger bag with adjustable strap",
                difficulty_level=SkillLevel.ADVANCED,
                estimated_time=480,  # minutes
                estimated_cost=125.00,
                materials_needed="8 sq ft of leather, hardware, thread, lining",
                instructions="Step 1: Start by cutting the main body panels...",
                version="2.1",
                created_by="Mark Williams",
                created_at=datetime.now() - timedelta(days=180)
            ),
            Pattern(
                name="Basic Belt",
                description="Simple 1.5-inch belt with buckle",
                difficulty_level=SkillLevel.BEGINNER,
                estimated_time=90,  # minutes
                estimated_cost=28.50,
                materials_needed="4 sq ft of leather, buckle, thread",
                instructions="Step 1: Measure and cut the leather strap...",
                version="1.1",
                created_by="Sarah Thompson",
                created_at=datetime.now() - timedelta(days=150)
            ),
            Pattern(
                name="Watch Strap",
                description="Handcrafted watch strap with quick-release pins",
                difficulty_level=SkillLevel.INTERMEDIATE,
                estimated_time=150,  # minutes
                estimated_cost=22.00,
                materials_needed="0.5 sq ft of leather, buckle, spring bars",
                instructions="Step 1: Measure wrist and determine strap length...",
                version="1.3",
                created_by="David Chen",
                created_at=datetime.now() - timedelta(days=60)
            )
        ]
        session.add_all(patterns)
        session.flush()
        logger.info(f"Added {len(patterns)} patterns")

        # 7. Create products
        products = [
            Product(
                name="Handcrafted Bifold Wallet",
                sku="BFW-001",
                description="Classic bifold wallet made with premium leather",
                price=89.99,
                cost=35.00,
                stock_quantity=12,
                reorder_level=5,
                weight=100.0,  # grams
                dimensions="4.5x3.5x0.5 inches",
                pattern_id=patterns[0].id,
                material_type=MaterialType.LEATHER,
                color="Brown",
                image_path="/images/bifold-wallet.jpg",
                status="ACTIVE"
            ),
            Product(
                name="Slim Card Holder",
                sku="SCH-001",
                description="Minimalist card holder for essential cards",
                price=39.99,
                cost=14.00,
                stock_quantity=18,
                reorder_level=8,
                weight=40.0,  # grams
                dimensions="4x2.8x0.2 inches",
                pattern_id=patterns[1].id,
                material_type=MaterialType.LEATHER,
                color="Black",
                image_path="/images/card-holder.jpg",
                status="ACTIVE"
            ),
            Product(
                name="Leather Messenger Bag",
                sku="LMB-001",
                description="Spacious messenger bag for daily use",
                price=249.99,
                cost=105.00,
                stock_quantity=5,
                reorder_level=3,
                weight=950.0,  # grams
                dimensions="15x11x4 inches",
                pattern_id=patterns[2].id,
                material_type=MaterialType.LEATHER,
                color="Dark Brown",
                image_path="/images/messenger-bag.jpg",
                status="ACTIVE"
            ),
            Product(
                name="Classic Belt",
                sku="BLT-001",
                description="Durable full-grain leather belt with brass buckle",
                price=79.99,
                cost=28.00,
                stock_quantity=15,
                reorder_level=7,
                weight=220.0,  # grams
                dimensions="44x1.5 inches",
                pattern_id=patterns[3].id,
                material_type=MaterialType.LEATHER,
                color="Tan",
                image_path="/images/leather-belt.jpg",
                status="ACTIVE"
            ),
            Product(
                name="Premium Watch Strap",
                sku="WS-001",
                description="Custom watch strap for 20mm lug width",
                price=59.99,
                cost=19.00,
                stock_quantity=8,
                reorder_level=4,
                weight=30.0,  # grams
                dimensions="7.5x0.8 inches",
                pattern_id=patterns[4].id,
                material_type=MaterialType.LEATHER,
                color="Navy Blue",
                image_path="/images/watch-strap.jpg",
                status="ACTIVE"
            ),
            Product(
                name="Custom Passport Holder",
                sku="PH-001",
                description="Handmade passport cover with card slots",
                price=69.99,
                cost=25.00,
                stock_quantity=0,
                reorder_level=5,
                weight=80.0,  # grams
                dimensions="5.5x4x0.3 inches",
                pattern_id=None,
                material_type=MaterialType.LEATHER,
                color="Burgundy",
                image_path="/images/passport-holder.jpg",
                status="OUT_OF_STOCK"
            )
        ]
        session.add_all(products)
        session.flush()
        logger.info(f"Added {len(products)} products")

        # 8. Create projects
        projects = [
            Project(
                name="Custom Wallet for John",
                project_type=ProjectType.WALLET,
                status=ProjectStatus.COMPLETED,
                skill_level=SkillLevel.INTERMEDIATE,
                start_date=datetime.now() - timedelta(days=45),
                due_date=datetime.now() - timedelta(days=30),
                completion_date=datetime.now() - timedelta(days=28),
                pattern_id=patterns[0].id,
                customer_name="John Doe",
                customer_email="john.doe@example.com",
                estimated_cost=45.00,
                actual_cost=42.50,
                estimated_hours=3.0,
                actual_hours=3.5,
                description="Custom bifold wallet with monogram",
                notes="Customer preferred antique brass hardware"
            ),
            Project(
                name="Messenger Bag Commission",
                project_type=ProjectType.BAG,
                status=ProjectStatus.IN_PROGRESS,
                skill_level=SkillLevel.ADVANCED,
                start_date=datetime.now() - timedelta(days=15),
                due_date=datetime.now() + timedelta(days=15),
                completion_date=None,
                pattern_id=patterns[2].id,
                customer_name="Sarah Williams",
                customer_email="sarah.w@example.com",
                estimated_cost=140.00,
                actual_cost=0.00,
                estimated_hours=10.0,
                actual_hours=5.5,
                description="Custom messenger bag with laptop compartment",
                notes="Currently in the stitching phase"
            ),
            Project(
                name="Custom Belt Order",
                project_type=ProjectType.BELT,
                status=ProjectStatus.PLANNING,
                skill_level=SkillLevel.BEGINNER,
                start_date=datetime.now() - timedelta(days=5),
                due_date=datetime.now() + timedelta(days=25),
                completion_date=None,
                pattern_id=patterns[3].id,
                customer_name="Michael Brown",
                customer_email="mbrown@example.com",
                estimated_cost=85.00,
                actual_cost=0.00,
                estimated_hours=2.5,
                actual_hours=0.0,
                description="38\" belt with custom buckle",
                notes="Waiting for materials to arrive"
            ),
            Project(
                name="Custom iPad Case",
                project_type=ProjectType.CASE,
                status=ProjectStatus.MATERIAL_SELECTION,
                skill_level=SkillLevel.INTERMEDIATE,
                start_date=datetime.now() - timedelta(days=10),
                due_date=datetime.now() + timedelta(days=20),
                completion_date=None,
                pattern_id=None,
                customer_name="Emma Garcia",
                customer_email="emma.g@example.com",
                estimated_cost=110.00,
                actual_cost=0.00,
                estimated_hours=6.0,
                actual_hours=1.0,
                description="Protective leather case for iPad Pro 12.9\"",
                notes="Customer needs to confirm leather selection"
            ),
            Project(
                name="Watch Strap Production Run",
                project_type=ProjectType.ACCESSORY,
                status=ProjectStatus.CUTTING,
                skill_level=SkillLevel.INTERMEDIATE,
                start_date=datetime.now() - timedelta(days=7),
                due_date=datetime.now() + timedelta(days=14),
                completion_date=None,
                pattern_id=patterns[4].id,
                customer_name="Retail Stock",
                customer_email=None,
                estimated_cost=200.00,
                actual_cost=75.00,
                estimated_hours=15.0,
                actual_hours=4.0,
                description="Production of 10 watch straps for inventory",
                notes="Using navy blue Buttero leather"
            )
        ]
        session.add_all(projects)
        session.flush()
        logger.info(f"Added {len(projects)} projects")

        # 9. Create project components
        project_components = []
        for i, project in enumerate(projects):
            if i == 0:  # Components for completed wallet project
                project_components.extend([
                    ProjectComponent(
                        project_id=project.id,
                        name="Wallet Exterior",
                        description="Outer shell of the wallet",
                        quantity=1.0,
                        material_id=leathers[0].id,
                        material_amount=0.5,  # sq ft
                        cost=6.50,
                        notes="Cut from the cleanest part of the hide"
                    ),
                    ProjectComponent(
                        project_id=project.id,
                        name="Card Slots",
                        description="Interior card slots",
                        quantity=6.0,
                        material_id=leathers[0].id,
                        material_amount=0.3,  # sq ft
                        cost=3.90,
                        notes="Skived edges for folding"
                    ),
                    ProjectComponent(
                        project_id=project.id,
                        name="Stitching",
                        description="0.6mm cream thread",
                        quantity=1.0,
                        material_id=other_materials[0].id,
                        material_amount=5.0,  # meters
                        cost=2.20,
                        notes="Saddle stitch at 5 SPI"
                    )
                ])
            elif i == 1:  # Components for in-progress messenger bag
                project_components.extend([
                    ProjectComponent(
                        project_id=project.id,
                        name="Main Body",
                        description="Exterior panels for the bag",
                        quantity=1.0,
                        material_id=leathers[2].id,
                        material_amount=4.0,  # sq ft
                        cost=43.00,
                        notes="Include reinforcement at stress points"
                    ),
                    ProjectComponent(
                        project_id=project.id,
                        name="Strap",
                        description="Adjustable shoulder strap",
                        quantity=1.0,
                        material_id=leathers[2].id,
                        material_amount=1.5,  # sq ft
                        cost=16.13,
                        notes="Double layer for durability"
                    ),
                    ProjectComponent(
                        project_id=project.id,
                        name="Hardware Set",
                        description="Buckles and D-rings",
                        quantity=1.0,
                        material_id=hardware_items[3].id,
                        material_amount=6.0,  # pieces
                        cost=7.50,
                        notes="Black oxide finish to match aesthetic"
                    )
                ])

        session.add_all(project_components)
        session.flush()
        logger.info(f"Added {len(project_components)} project components")

        # 10. Create orders
        # Sample customer orders
        customer_orders = [
            Sale(
                order_date=datetime.now() - timedelta(days=60),
                customer_name="Alice Johnson",
                customer_email="alice.j@example.com",
                customer_phone="555-123-4567",
                shipping_address="123 Main St, Anytown, USA 12345",
                billing_address="123 Main St, Anytown, USA 12345",
                status=SaleStatus.DELIVERED,
                payment_status=PaymentStatus.PAID,
                shipping_cost=5.99,
                tax_amount=8.75,
                total_amount=104.73,
                tracking_number="TRK123456789",
                notes="Gift wrapped as requested",
                delivery_date=datetime.now() - timedelta(days=55)
            ),
            Sale(
                order_date=datetime.now() - timedelta(days=30),
                customer_name="Bob Smith",
                customer_email="bob.smith@example.com",
                customer_phone="555-987-6543",
                shipping_address="456 Oak Ave, Somewhere, USA 67890",
                billing_address="456 Oak Ave, Somewhere, USA 67890",
                status=SaleStatus.SHIPPED,
                payment_status=PaymentStatus.PAID,
                shipping_cost=7.99,
                tax_amount=12.50,
                total_amount=170.48,
                tracking_number="TRK987654321",
                notes="Customer requested expedited shipping",
                delivery_date=None
            ),
            Sale(
                order_date=datetime.now() - timedelta(days=10),
                customer_name="Carol Martinez",
                customer_email="carol.m@example.com",
                customer_phone="555-456-7890",
                shipping_address="789 Pine Ln, Elsewhere, USA 54321",
                billing_address="789 Pine Ln, Elsewhere, USA 54321",
                status=SaleStatus.PROCESSING,
                payment_status=PaymentStatus.PAID,
                shipping_cost=5.99,
                tax_amount=5.60,
                total_amount=75.58,
                tracking_number=None,
                notes="Include care instructions",
                delivery_date=None
            ),
            Sale(
                order_date=datetime.now() - timedelta(days=3),
                customer_name="David Wilson",
                customer_email="david.w@example.com",
                customer_phone="555-234-5678",
                shipping_address="321 Cedar Rd, Nowhere, USA 13579",
                billing_address="321 Cedar Rd, Nowhere, USA 13579",
                status=SaleStatus.PENDING,
                payment_status=PaymentStatus.PENDING,
                shipping_cost=9.99,
                tax_amount=22.40,
                total_amount=282.38,
                tracking_number=None,
                notes="Waiting for payment confirmation",
                delivery_date=None
            )
        ]

        # Sample supplier orders
        supplier_orders = [
            Sale(
                order_date=datetime.now() - timedelta(days=45),
                supplier_id=suppliers[0].id,
                status=SaleStatus.DELIVERED,
                payment_status=PaymentStatus.PAID,
                shipping_cost=15.00,
                tax_amount=30.40,
                total_amount=354.40,
                tracking_number="SUP123456",
                notes="Regular leather restock",
                delivery_date=datetime.now() - timedelta(days=38)
            ),
            Sale(
                order_date=datetime.now() - timedelta(days=20),
                supplier_id=suppliers[1].id,
                status=SaleStatus.SHIPPED,
                payment_status=PaymentStatus.PAID,
                shipping_cost=9.50,
                tax_amount=12.75,
                total_amount=149.25,
                tracking_number="SUP789012",
                notes="Hardware restock",
                delivery_date=None
            ),
            Sale(
                order_date=datetime.now() - timedelta(days=2),
                supplier_id=suppliers[4].id,
                status=SaleStatus.PENDING,
                payment_status=PaymentStatus.PENDING,
                shipping_cost=25.00,
                tax_amount=45.60,
                total_amount=546.60,
                tracking_number=None,
                notes="Special sale exotic leathers",
                delivery_date=None
            )
        ]

        # Combine all orders
        orders = customer_orders + supplier_orders
        session.add_all(orders)
        session.flush()
        logger.info(f"Added {len(orders)} orders")

        # 11. Create sale items
        order_items = []

        # Add items to customer orders
        order_items.extend([
            # Items for first customer sale
            SaleItem(
                order_id=customer_orders[0].id,
                product_id=products[0].id,
                quantity=1,
                unit_price=89.99,
                discount=0.00,
                total_price=89.99,
                notes="Standard bifold wallet"
            ),

            # Items for second customer sale
            SaleItem(
                order_id=customer_orders[1].id,
                product_id=products[2].id,
                quantity=1,
                unit_price=249.99,
                discount=25.00,  # $25 discount
                total_price=224.99,
                notes="Messenger bag with custom strap length"
            ),
            SaleItem(
                order_id=customer_orders[1].id,
                product_id=products[4].id,
                quantity=1,
                unit_price=59.99,
                discount=0.00,
                total_price=59.99,
                notes="Watch strap to match bag"
            ),

            # Items for third customer sale
            SaleItem(
                order_id=customer_orders[2].id,
                product_id=products[1].id,
                quantity=1,
                unit_price=39.99,
                discount=0.00,
                total_price=39.99,
                notes="Card holder with monogram"
            ),
            SaleItem(
                order_id=customer_orders[2].id,
                product_id=products[4].id,
                quantity=1,
                unit_price=59.99,
                discount=10.00,  # $10 discount for bundle
                total_price=49.99,
                notes="Matching watch strap"
            ),

            # Items for fourth customer sale
            SaleItem(
                order_id=customer_orders[3].id,
                product_id=products[2].id,
                quantity=1,
                unit_price=249.99,
                discount=0.00,
                total_price=249.99,
                notes="Standard messenger bag"
            )
        ])

        # Add items to supplier orders
        order_items.extend([
            # Items for first supplier sale (leather restock)
            SaleItem(
                order_id=supplier_orders[0].id,
                product_id=None,
                quantity=20.0,  # square feet
                unit_price=12.99,
                discount=0.00,
                total_price=259.80,
                notes="Vintage Brown Full Grain Leather"
            ),
            SaleItem(
                order_id=supplier_orders[0].id,
                product_id=None,
                quantity=10.0,  # square feet
                unit_price=14.50,
                discount=0.00,
                total_price=145.00,
                notes="Black Chromexcel Leather"
            ),

            # Items for second supplier sale (hardware restock)
            SaleItem(
                order_id=supplier_orders[1].id,
                product_id=None,
                quantity=100,
                unit_price=0.75,
                discount=0.00,
                total_price=75.00,
                notes="Antique Brass Snap Buttons"
            ),
            SaleItem(
                order_id=supplier_orders[1].id,
                product_id=None,
                quantity=50,
                unit_price=1.25,
                discount=0.00,
                total_price=62.50,
                notes="Black D-Rings 3/4\""
            ),

            # Items for third supplier sale (exotic leather)
            SaleItem(
                order_id=supplier_orders[2].id,
                product_id=None,
                quantity=10.0,  # square feet
                unit_price=28.50,
                discount=0.00,
                total_price=285.00,
                notes="Ostrich Leather, Cognac"
            ),
            SaleItem(
                order_id=supplier_orders[2].id,
                product_id=None,
                quantity=10.0,  # square feet
                unit_price=18.50,
                discount=0.00,
                total_price=185.00,
                notes="Burgundy Chevre Leather"
            )
        ])

        session.add_all(order_items)
        session.flush()
        logger.info(f"Added {len(order_items)} sale items")

        # 12. Create shopping lists
        shopping_lists = [
            ShoppingList(
                name="Weekly Restock",
                description="Regular inventory replenishment",
                created_at=datetime.now() - timedelta(days=5),
                priority=Priority.MEDIUM,
                status="ACTIVE",
                notes="Order by Friday for next week delivery"
            ),
            ShoppingList(
                name="Special Materials",
                description="Specialty items for custom projects",
                created_at=datetime.now() - timedelta(days=15),
                priority=Priority.HIGH,
                status="ACTIVE",
                notes="Check with multiple suppliers for best prices"
            ),
            ShoppingList(
                name="Tools Upgrade",
                description="New tools for expanding capabilities",
                created_at=datetime.now() - timedelta(days=30),
                priority=Priority.LOW,
                status="PENDING",
                notes="Research options before purchasing"
            )
        ]
        session.add_all(shopping_lists)
        session.flush()
        logger.info(f"Added {len(shopping_lists)} shopping lists")

        # 13. Create shopping list items
        shopping_list_items = [
            # Items for weekly restock
            ShoppingListItem(
                shopping_list_id=shopping_lists[0].id,
                name="Vegetable Tanned Leather",
                description="3-4 oz veg tan for general use",
                quantity=15.0,  # square feet
                estimated_cost=165.00,
                priority=Priority.HIGH,
                supplier_id=suppliers[0].id,
                notes="Check if on sale"
            ),
            ShoppingListItem(
                shopping_list_id=shopping_lists[0].id,
                name="Thread Restock",
                description="Various colors of Tiger Thread",
                quantity=5.0,  # spools
                estimated_cost=125.00,
                priority=Priority.MEDIUM,
                supplier_id=suppliers[2].id,
                notes="Need black, brown, and natural"
            ),

            # Items for special materials
            ShoppingListItem(
                shopping_list_id=shopping_lists[1].id,
                name="Exotic Leather Samples",
                description="Sample swatches of new exotics",
                quantity=1.0,  # set
                estimated_cost=75.00,
                priority=Priority.MEDIUM,
                supplier_id=suppliers[4].id,
                notes="For client presentations"
            ),
            ShoppingListItem(
                shopping_list_id=shopping_lists[1].id,
                name="Premium Hardware Set",
                description="Gold-plated hardware for luxury commission",
                quantity=1.0,  # set
                estimated_cost=120.00,
                priority=Priority.HIGH,
                supplier_id=suppliers[1].id,
                notes="For the Johnson wedding gift project"
            ),

            # Items for tools upgrade
            ShoppingListItem(
                shopping_list_id=shopping_lists[2].id,
                name="Adjustable Creasing Tool",
                description="Heated creasing iron with multiple tips",
                quantity=1.0,
                estimated_cost=185.00,
                priority=Priority.MEDIUM,
                supplier_id=None,
                notes="Compare Palosanto vs Sinabroks"
            ),
            ShoppingListItem(
                shopping_list_id=shopping_lists[2].id,
                name="Stitching Pony Upgrade",
                description="Better stitching horse for production",
                quantity=1.0,
                estimated_cost=250.00,
                priority=Priority.LOW,
                supplier_id=None,
                notes="Consider ergonomic models"
            )
        ]
        session.add_all(shopping_list_items)
        session.flush()
        logger.info(f"Added {len(shopping_list_items)} shopping list items")

        session.commit()
        logger.info("Successfully added all sample data to the database")

    except Exception as e:
        session.rollback()
        logger.error(f"Error adding sample data to database: {e}")
        raise
    finally:
        session.close()