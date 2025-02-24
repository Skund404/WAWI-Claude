from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
"""
F:/WAWI Homebrew/WAWI Claude/store_management/tools/db_init.py

Direct database initialization script that avoids metaclass conflicts.
"""
logging.basicConfig(level=logging.INFO, format=
    '%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def find_project_root() ->Path:
    """
    Find the project root directory.

    Returns:
        Path object pointing to the project root.
    """
    current_dir = Path(__file__).resolve().parent
    while current_dir != current_dir.parent:
        if (current_dir / 'pyproject.toml').exists() or (current_dir /
            'setup.py').exists():
            return current_dir
        current_dir = current_dir.parent
    return Path(__file__).resolve().parent.parent


def get_db_path():
    """
    Get the SQLite database path.

    Returns:
        Path to the SQLite database file.
    """
    project_root = find_project_root()
    data_dir = project_root / 'data'
    os.makedirs(data_dir, exist_ok=True)
    return data_dir / 'store_management.db'


def create_backup(db_path, backup_dir=None):
    """
    Create a backup of the database.

    Args:
        db_path: Path to the database file.
        backup_dir: Directory to store the backup (default: project_root/data/backups).

    Returns:
        Path to the backup file, or None if backup failed.
    """
    if not os.path.exists(db_path):
        logger.info(f'No database file to backup at {db_path}')
        return None
    try:
        project_root = find_project_root()
        if backup_dir is None:
            backup_dir = project_root / 'data' / 'backups'
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = (backup_dir /
            f'db_backup_before_direct_init_{timestamp}.db')
        shutil.copy2(db_path, backup_path)
        logger.info(f'Created database backup at {backup_path}')
        return backup_path
    except Exception as e:
        logger.error(f'Failed to create backup: {e}')
        return None


def initialize_database(reset_db=False):
    """
    Initialize the database using direct SQL statements.

    Args:
        reset_db: Whether to reset the database by dropping existing tables.

    Returns:
        True if successful, False otherwise.
    """
    try:
        db_path = get_db_path()
        logger.info(f'Database path: {db_path}')
        if reset_db and os.path.exists(db_path):
            create_backup(db_path)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('PRAGMA foreign_keys = ON')
        if reset_db:
            logger.warning('Dropping existing tables')
            cursor.execute('DROP TABLE IF EXISTS suppliers')
            cursor.execute('DROP TABLE IF EXISTS storage')
            cursor.execute('DROP TABLE IF EXISTS products')
            cursor.execute('DROP TABLE IF EXISTS projects')
        logger.info('Creating tables')
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
        logger.info('Checking if sample data is needed')
        cursor.execute('SELECT COUNT(*) FROM suppliers')
        if cursor.fetchone()[0] == 0:
            logger.info('Adding sample suppliers')
            sample_suppliers = [('Leather Supply Co.', 'John Smith',
                'john@leathersupply.com', '555-1234',
                '123 Main St, Leather City', 'LS12345'), (
                'Hardware Emporium', 'Jane Doe',
                'jane@hardwareemporium.com', '555-5678',
                '456 Market St, Hardware Town', 'HE67890')]
            for supplier in sample_suppliers:
                cursor.execute(
                    """
                INSERT INTO suppliers (name, contact_name, email, phone, address, tax_id)
                VALUES (?, ?, ?, ?, ?, ?)
                """
                    , supplier)
        cursor.execute('SELECT COUNT(*) FROM storage')
        if cursor.fetchone()[0] == 0:
            logger.info('Adding sample storage locations')
            sample_storages = [('Main Storage', 'Warehouse A', 1000.0, 0.0,
                'Warehouse', 'Main storage location', 'Active'), (
                'Secondary Storage', 'Warehouse B', 500.0, 0.0, 'Warehouse',
                'Secondary storage location', 'Active'), (
                'Workshop Storage', 'Workshop', 200.0, 0.0, 'Workshop',
                'Workshop storage location', 'Active')]
            for storage in sample_storages:
                cursor.execute(
                    """
                INSERT INTO storage (name, location, capacity, current_occupancy, type, description, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """
                    , storage)
        conn.commit()
        logger.info('Database initialized successfully')
        conn.close()
        return True
    except Exception as e:
        logger.error(f'Failed to initialize database: {e}')
        return False


def main():
    """Main entry point."""
    logger.info('Starting direct database initialization...')
    reset_db = input('Reset database (drop all tables)? (y/N): ').strip(
        ).lower() == 'y'
    success = initialize_database(reset_db=reset_db)
    if success:
        logger.info('Database initialization completed successfully')
    else:
        logger.error('Database initialization failed')
        sys.exit(1)


if __name__ == '__main__':
    main()
