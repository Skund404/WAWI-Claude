from di.core import inject
from services.interfaces import (
    MaterialService,
    ProjectService,
    InventoryService,
    OrderService,
)

"""
F:/WAWI Homebrew/WAWI Claude/store_management/database/initialize.py

Functions for initializing and setting up the database with improved error handling.
"""
logger = logging.getLogger(__name__)


def create_tables(engine) -> bool:
    """
    Create all database tables based on the defined models.

    Args:
        engine: SQLAlchemy engine instance.

    Returns:
        True if successful, False otherwise.
    """
    logger.info("Creating database tables")
    try:
        try:
            from .models.base import Base

            try:
                from .models.supplier import Supplier
                from .models.storage import Storage
                from .models.product import Product
            except ImportError as e:
                logger.warning(f"Some models could not be imported: {e}")
            Base.metadata.create_all(engine)
            logger.info(
                "Database tables created successfully using SQLAlchemy models")
            return True
        except Exception as e:
            logger.error(f"Error with SQLAlchemy model imports: {e}")
            logger.warning("Falling back to direct SQL table creation")
            return create_tables_fallback(engine.url.database)
    except Exception as e:
        logger.error(f"Failed to create database tables: {str(e)}")
        return False


def create_tables_fallback(db_path: str) -> bool:
    """
    Fallback method to create database tables using direct SQL.

    Args:
        db_path: Path to the SQLite database file.

    Returns:
        True if successful, False otherwise.
    """
    try:
        logger.info(f"Using fallback method to create tables in {db_path}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS suppliers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        contact_name TEXT,
        email TEXT,
        phone TEXT,
        address TEXT,
        tax_id TEXT UNIQUE,
        website TEXT,
        notes TEXT,
        rating REAL DEFAULT 0.0,
        reliability_score REAL DEFAULT 0.0,
        quality_score REAL DEFAULT 0.0,
        price_score REAL DEFAULT 0.0,
        is_active INTEGER DEFAULT 1,
        is_preferred INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        )
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS storage (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        location TEXT,
        capacity REAL DEFAULT 0.0,
        current_occupancy REAL DEFAULT 0.0,
        type TEXT,
        description TEXT,
        status TEXT DEFAULT 'Active',
        width REAL,
        height REAL,
        depth REAL,
        temperature_controlled INTEGER DEFAULT 0,
        humidity_controlled INTEGER DEFAULT 0,
        fire_resistant INTEGER DEFAULT 0
        )
        """
        )
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        sku TEXT UNIQUE,
        description TEXT,
        price REAL NOT NULL DEFAULT 0.0,
        cost_price REAL NOT NULL DEFAULT 0.0,
        stock_quantity INTEGER DEFAULT 0,
        minimum_stock INTEGER DEFAULT 0,
        reorder_point INTEGER DEFAULT 5,
        material_type TEXT,
        weight REAL,
        dimensions TEXT,
        is_active INTEGER DEFAULT 1,
        is_featured INTEGER DEFAULT 0,
        supplier_id INTEGER,
        storage_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (supplier_id) REFERENCES suppliers (id),
        FOREIGN KEY (storage_id) REFERENCES storage (id)
        )
        """
        )
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        project_type TEXT NOT NULL,
        skill_level TEXT NOT NULL,
        status TEXT DEFAULT 'Planning',
        estimated_hours REAL DEFAULT 0.0,
        actual_hours REAL DEFAULT 0.0,
        material_budget REAL DEFAULT 0.0,
        actual_cost REAL DEFAULT 0.0,
        start_date TIMESTAMP,
        due_date TIMESTAMP,
        completion_date TIMESTAMP,
        is_template INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        )
        conn.commit()
        conn.close()
        logger.info("Database tables created successfully using direct SQL")
        return True
    except Exception as e:
        logger.error(
            f"Failed to create database tables using fallback method: {str(e)}"
        )
        return False


def add_sample_data(session: Session) -> bool:
    """
    Add sample data to the database for testing.

    Args:
        session: SQLAlchemy session.

    Returns:
        True if successful, False otherwise.
    """
    logger.info("Adding sample data to the database")
    try:
        try:
            from .models.storage import Storage
            from .models.supplier import Supplier

            try:
                storage_count = session.query(Storage).count()
                if storage_count == 0:
                    sample_storages = [
                        Storage(
                            name="Main Storage",
                            location="Warehouse A",
                            capacity=1000.0,
                            current_occupancy=0.0,
                            type="Warehouse",
                            description="Main storage location",
                            status="Active",
                        ),
                        Storage(
                            name="Secondary Storage",
                            location="Warehouse B",
                            capacity=500.0,
                            current_occupancy=0.0,
                            type="Warehouse",
                            description="Secondary storage location",
                            status="Active",
                        ),
                        Storage(
                            name="Workshop Storage",
                            location="Workshop",
                            capacity=200.0,
                            current_occupancy=0.0,
                            type="Workshop",
                            description="Workshop storage location",
                            status="Active",
                        ),
                    ]
                    for storage in sample_storages:
                        session.add(storage)
                    logger.info("Added sample storage locations")
            except Exception as e:
                logger.error(f"Failed to add sample storage data: {str(e)}")
            try:
                supplier_count = session.query(Supplier).count()
                if supplier_count == 0:
                    sample_suppliers = [
                        Supplier(
                            name="Leather Supply Co.",
                            contact_name="John Smith",
                            email="john@leathersupply.com",
                            phone="555-1234",
                            address="123 Main St, Leather City",
                            tax_id="LS12345",
                        ),
                        Supplier(
                            name="Hardware Emporium",
                            contact_name="Jane Doe",
                            email="jane@hardwareemporium.com",
                            phone="555-5678",
                            address="456 Market St, Hardware Town",
                            tax_id="HE67890",
                        ),
                    ]
                    for supplier in sample_suppliers:
                        session.add(supplier)
                    logger.info("Added sample suppliers")
            except Exception as e:
                logger.error(f"Failed to add sample supplier data: {str(e)}")
            session.commit()
            logger.info("Sample data added successfully")
            return True
        except Exception as e:
            logger.error(f"Error with SQLAlchemy model imports: {e}")
            logger.warning("Falling back to direct SQL sample data insertion")
            session.rollback()
            return add_sample_data_fallback(session.get_bind().url.database)
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to add sample data: {str(e)}")
        return False


def add_sample_data_fallback(db_path: str) -> bool:
    """
    Fallback method to add sample data using direct SQL.

    Args:
        db_path: Path to the SQLite database file.

    Returns:
        True if successful, False otherwise.
    """
    try:
        logger.info(f"Using fallback method to add sample data to {db_path}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM suppliers")
        if cursor.fetchone()[0] == 0:
            logger.info("Adding sample suppliers")
            sample_suppliers = [
                (
                    "Leather Supply Co.",
                    "John Smith",
                    "john@leathersupply.com",
                    "555-1234",
                    "123 Main St, Leather City",
                    "LS12345",
                ),
                (
                    "Hardware Emporium",
                    "Jane Doe",
                    "jane@hardwareemporium.com",
                    "555-5678",
                    "456 Market St, Hardware Town",
                    "HE67890",
                ),
            ]
            for supplier in sample_suppliers:
                cursor.execute(
                    """
                INSERT INTO suppliers (name, contact_name, email, phone, address, tax_id)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                    supplier,
                )
        cursor.execute("SELECT COUNT(*) FROM storage")
        if cursor.fetchone()[0] == 0:
            logger.info("Adding sample storage locations")
            sample_storages = [
                (
                    "Main Storage",
                    "Warehouse A",
                    1000.0,
                    0.0,
                    "Warehouse",
                    "Main storage location",
                    "Active",
                ),
                (
                    "Secondary Storage",
                    "Warehouse B",
                    500.0,
                    0.0,
                    "Warehouse",
                    "Secondary storage location",
                    "Active",
                ),
                (
                    "Workshop Storage",
                    "Workshop",
                    200.0,
                    0.0,
                    "Workshop",
                    "Workshop storage location",
                    "Active",
                ),
            ]
            for storage in sample_storages:
                cursor.execute(
                    """
                INSERT INTO storage (name, location, capacity, current_occupancy, type, description, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    storage,
                )
        conn.commit()
        conn.close()
        logger.info("Sample data added successfully using direct SQL")
        return True
    except Exception as e:
        logger.error(
            f"Failed to add sample data using fallback method: {str(e)}")
        return False


def initialize_database(
    drop_existing: bool = False, use_fallback: bool = False
) -> bool:
    """
    Initialize the database, creating tables and adding sample data.

    Args:
        drop_existing: Whether to drop existing tables before creating new ones.
        use_fallback: Whether to use the fallback methods directly.

    Returns:
        True if successful, False otherwise.
    """
    logger.info("Initializing database")
    try:
        db_config = DatabaseConfig.get_database_config()
        database_url = db_config["database_url"]
        if use_fallback and database_url.startswith("sqlite:///"):
            db_path = database_url.replace("sqlite:///", "")
            if drop_existing:
                backup_path = os.path.join(os.path.dirname(db_path), "backups")
                os.makedirs(backup_path, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = os.path.join(
                    backup_path, f"backup_before_init_{timestamp}.db"
                )
                if os.path.exists(db_path):
                    import shutil

                    shutil.copy2(db_path, backup_file)
                    logger.info(f"Created database backup at {backup_file}")
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            conn = sqlite3.connect(db_path)
            if drop_existing:
                logger.warning("Dropping existing tables")
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                for table in tables:
                    if table[0] != "sqlite_sequence":
                        cursor.execute(f"DROP TABLE IF EXISTS {table[0]}")
            conn.close()
            success_tables = create_tables_fallback(db_path)
            success_data = add_sample_data_fallback(db_path)
            return success_tables and success_data
        engine = create_engine(database_url)
        inspector = inspect(engine)
        tables_exist = len(inspector.get_table_names()) > 0
        if drop_existing and tables_exist:
            try:
                from .models.base import Base

                logger.warning("Dropping all existing tables")
                Base.metadata.drop_all(engine)
                tables_exist = False
            except Exception as e:
                logger.error(
                    f"Failed to drop tables using SQLAlchemy: {str(e)}")
                if database_url.startswith("sqlite:///"):
                    logger.warning("Trying to drop tables using direct SQL")
                    db_path = database_url.replace("sqlite:///", "")
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'")
                    tables = cursor.fetchall()
                    for table in tables:
                        if table[0] != "sqlite_sequence":
                            cursor.execute(f"DROP TABLE IF EXISTS {table[0]}")
                    conn.close()
                    tables_exist = False
        if not tables_exist:
            success = create_tables(engine)
            if not success:
                return False
        SessionFactory = sessionmaker(bind=engine)
        session = SessionFactory()
        success = add_sample_data(session)
        session.close()
        if success:
            logger.info("Database initialization completed successfully")
            return True
        else:
            logger.error("Database initialization completed with errors")
            return False
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        return False
