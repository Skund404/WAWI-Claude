from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
"""
F:/WAWI Homebrew/WAWI Claude/store_management/tools/manual_migration_fixed.py

Script to manually create database schema without using Alembic, skipping problematic models.
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


def create_database_schema(reset_db=False):
    """Create database schema using SQLAlchemy models directly."""
    project_root = find_project_root()
    sys.path.insert(0, str(project_root))
    try:
        from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text
        from sqlalchemy.ext.declarative import declarative_base
        from sqlalchemy.orm import sessionmaker, relationship
        import datetime
    except ImportError as e:
        logger.error(f'Failed to import SQLAlchemy modules: {e}')
        return False
    try:
        Base = declarative_base()


        class Supplier(Base):
            __tablename__ = 'suppliers'
            id = Column(Integer, primary_key=True)
            name = Column(String(100), nullable=False, index=True)
            contact_name = Column(String(100), nullable=True)
            email = Column(String(100), nullable=True)
            phone = Column(String(20), nullable=True)
            address = Column(String(255), nullable=True)
            tax_id = Column(String(50), nullable=True, unique=True)
            website = Column(String(255), nullable=True)
            notes = Column(String(500), nullable=True)
            rating = Column(Float, default=0.0)
            reliability_score = Column(Float, default=0.0)
            quality_score = Column(Float, default=0.0)
            price_score = Column(Float, default=0.0)
            is_active = Column(Boolean, default=True)
            is_preferred = Column(Boolean, default=False)
            created_at = Column(DateTime, default=datetime.datetime.utcnow)
            updated_at = Column(DateTime, default=datetime.datetime.utcnow,
                onupdate=datetime.datetime.utcnow)


        class Storage(Base):
            __tablename__ = 'storage'
            id = Column(Integer, primary_key=True)
            name = Column(String(100), nullable=False, index=True)
            location = Column(String(255), nullable=True)
            capacity = Column(Float, default=0.0)
            current_occupancy = Column(Float, default=0.0)
            type = Column(String(50), nullable=True)
            description = Column(Text, nullable=True)
            status = Column(String(20), default='Active')
            width = Column(Float, nullable=True)
            height = Column(Float, nullable=True)
            depth = Column(Float, nullable=True)
            temperature_controlled = Column(Boolean, default=False)
            humidity_controlled = Column(Boolean, default=False)
            fire_resistant = Column(Boolean, default=False)


        class Product(Base):
            __tablename__ = 'products'
            id = Column(Integer, primary_key=True)
            name = Column(String(100), nullable=False, index=True)
            sku = Column(String(50), unique=True, nullable=True)
            description = Column(Text, nullable=True)
            price = Column(Float, nullable=False, default=0.0)
            cost_price = Column(Float, nullable=False, default=0.0)
            stock_quantity = Column(Integer, default=0)
            minimum_stock = Column(Integer, default=0)
            reorder_point = Column(Integer, default=5)
            material_type = Column(String(50), nullable=True)
            weight = Column(Float, nullable=True)
            dimensions = Column(String(100), nullable=True)
            is_active = Column(Boolean, default=True)
            is_featured = Column(Boolean, default=False)
            supplier_id = Column(Integer, ForeignKey('suppliers.id'),
                nullable=True)
            storage_id = Column(Integer, ForeignKey('storage.id'), nullable
                =True)
            created_at = Column(DateTime, default=datetime.datetime.utcnow)
            updated_at = Column(DateTime, default=datetime.datetime.utcnow,
                onupdate=datetime.datetime.utcnow)


        class Project(Base):
            __tablename__ = 'projects'
            id = Column(Integer, primary_key=True)
            name = Column(String(100), nullable=False, index=True)
            description = Column(Text, nullable=True)
            project_type = Column(String(50), nullable=False)
            skill_level = Column(String(50), nullable=False)
            status = Column(String(50), default='Planning')
            estimated_hours = Column(Float, default=0.0)
            actual_hours = Column(Float, default=0.0)
            material_budget = Column(Float, default=0.0)
            actual_cost = Column(Float, default=0.0)
            start_date = Column(DateTime, nullable=True)
            due_date = Column(DateTime, nullable=True)
            completion_date = Column(DateTime, nullable=True)
            is_template = Column(Boolean, default=False)
            is_active = Column(Boolean, default=True)
            created_at = Column(DateTime, default=datetime.datetime.utcnow)
            updated_at = Column(DateTime, default=datetime.datetime.utcnow,
                onupdate=datetime.datetime.utcnow)
        from database.config import DatabaseConfig
        database_url = DatabaseConfig.get_database_url()
        logger.info(f'Database URL: {database_url}')
        if reset_db:
            if database_url.startswith('sqlite:///'):
                db_path = database_url.replace('sqlite:///', '')
                if os.path.exists(db_path):
                    backup_dir = project_root / 'data' / 'backups'
                    os.makedirs(backup_dir, exist_ok=True)
                    timestamp = datetime.datetime.now().strftime(
                        '%Y%m%d_%H%M%S')
                    backup_path = (backup_dir /
                        f'db_backup_before_manual_migration_{timestamp}.db')
                    shutil.copy2(db_path, backup_path)
                    logger.info(f'Created database backup at {backup_path}')
            else:
                logger.warning(
                    'Database backup only supported for SQLite databases')
        engine = create_engine(database_url)
        if reset_db:
            logger.warning('Dropping all existing tables')
            Base.metadata.drop_all(engine)
        logger.info('Creating all tables')
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        logger.info('Adding sample data')
        if session.query(Supplier).count() == 0:
            sample_suppliers = [Supplier(name='Leather Supply Co.',
                contact_name='John Smith', email='john@leathersupply.com',
                phone='555-1234', address='123 Main St, Leather City',
                tax_id='LS12345'), Supplier(name='Hardware Emporium',
                contact_name='Jane Doe', email='jane@hardwareemporium.com',
                phone='555-5678', address='456 Market St, Hardware Town',
                tax_id='HE67890')]
            for supplier in sample_suppliers:
                session.add(supplier)
            logger.info('Added sample suppliers')
        if session.query(Storage).count() == 0:
            sample_storages = [Storage(name='Main Storage', location=
                'Warehouse A', capacity=1000.0, current_occupancy=0.0, type
                ='Warehouse', description='Main storage location', status=
                'Active'), Storage(name='Secondary Storage', location=
                'Warehouse B', capacity=500.0, current_occupancy=0.0, type=
                'Warehouse', description='Secondary storage location',
                status='Active'), Storage(name='Workshop Storage', location
                ='Workshop', capacity=200.0, current_occupancy=0.0, type=
                'Workshop', description='Workshop storage location', status
                ='Active')]
            for storage in sample_storages:
                session.add(storage)
            logger.info('Added sample storage locations')
        session.commit()
        session.close()
        logger.info('Database schema created successfully')
        return True
    except Exception as e:
        logger.error(f'Failed to create database schema: {e}')
        return False


def main():
    """Main entry point."""
    logger.info('Starting fixed manual database migration...')
    reset_db = input('Reset database (drop all tables)? (y/N): ').strip(
        ).lower() == 'y'
    success = create_database_schema(reset_db=reset_db)
    if success:
        logger.info('Manual migration completed successfully')
    else:
        logger.error('Manual migration failed')
        sys.exit(1)


if __name__ == '__main__':
    main()
