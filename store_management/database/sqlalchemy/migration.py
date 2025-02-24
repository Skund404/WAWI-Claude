from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
"""
Database Migration and Initialization Utility

This script provides a comprehensive solution for:
- Creating a new database schema
- Dropping existing tables
- Initializing the database with the latest model definitions
"""
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..',
'..'))
sys.path.insert(0, project_root)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[logging.
FileHandler(os.path.join(project_root, 'logs', 'database_migration.log'
)), logging.StreamHandler(sys.stdout)])
logger = logging.getLogger(__name__)


class DatabaseInitializer:
    pass
"""
Comprehensive database initialization and migration utility
"""

@inject(MaterialService)
def __init__(self, db_url: str, backup_dir: Optional[str] = None):
    pass
"""
Initialize database initialization process

Args:
db_url (str): SQLAlchemy database URL
backup_dir (str, optional): Directory for database backups
"""
self.db_url = db_url
self.backup_dir = backup_dir or os.path.join(project_root,
'database', 'backups')
os.makedirs(self.backup_dir, exist_ok=True)
self.engine = create_engine(db_url)
self.SessionLocal = sessionmaker(bind=self.engine)

@inject(MaterialService)
def create_backup(self) -> Optional[str]:
"""
Create a backup of the existing database if it exists

Returns:
Optional[str]: Path to the backup file, or None if no backup created
"""
try:
    pass
if 'sqlite' in self.db_url:
    pass
db_path = self.db_url.replace('sqlite:///', '')
if os.path.exists(db_path):
    pass
backup_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
backup_filename = os.path.join(self.backup_dir,
f'database_backup_{backup_timestamp}.db')
import shutil
shutil.copy(db_path, backup_filename)
logger.info(f'Database backup created: {backup_filename}')
return backup_filename
return None
except Exception as e:
    pass
logger.error(f'Failed to create database backup: {e}')
return None

@inject(MaterialService)
def drop_all_tables(self):
    pass
"""
Drop all existing tables in the database
"""
try:
    pass
inspector = inspect(self.engine)
tables = inspector.get_table_names()
with self.engine.connect() as connection:
    pass
try:
    pass
connection.execute('PRAGMA foreign_keys=OFF')
except Exception:
    pass
pass
trans = connection.begin()
try:
    pass
for table in tables:
    pass
connection.execute(f'DROP TABLE IF EXISTS {table}')
trans.commit()
logger.info(f'Dropped {len(tables)} existing tables')
except Exception as drop_error:
    pass
trans.rollback()
logger.error(f'Failed to drop tables: {drop_error}')
raise
except Exception as e:
    pass
logger.error(f'Error during table dropping: {e}')
raise

@inject(MaterialService)
def initialize_database(self):
    pass
"""
Complete database initialization process

1. Create backup of existing database
2. Drop all existing tables
3. Create new tables based on current model definitions
"""
try:
    pass
backup_path = self.create_backup()
try:
    pass
Base.metadata.drop_all(bind=self.engine)
except Exception as drop_error:
    pass
logger.warning(
f'Alternative table dropping method failed: {drop_error}')
try:
    pass
self.drop_all_tables()
except Exception as alt_error:
    pass
logger.error(f'Failed to drop tables: {alt_error}')
raise
Base.metadata.create_all(bind=self.engine)
logger.info('Database successfully initialized with new schema')
return True
except Exception as e:
    pass
logger.error(f'Database initialization failed: {e}')
return False


def run_database_initialization(db_url: Optional[str] =
'sqlite:///./store_management.db', backup_dir: Optional[str] = None,
force: bool = False) -> bool:
"""
Execute database initialization

Args:
db_url (str, optional): SQLAlchemy database URL
backup_dir (str, optional): Directory for database backups
force (bool, optional): Force initialization even if database exists

Returns:
bool: Initialization success status
"""
try:
    pass
initializer = DatabaseInitializer(db_url, backup_dir)
if 'sqlite' not in db_url and not force:
    pass
logger.warning(
'Non-SQLite database detected. Use force=True to proceed.')
return False
initialization_success = initializer.initialize_database()
if initialization_success:
    pass
logger.info('Database initialization completed successfully')
else:
logger.error('Database initialization encountered issues')
return initialization_success
except Exception as e:
    pass
logger.error(f'Database initialization failed: {e}')
return False


if __name__ == '__main__':
    pass
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__),
'..', '..'))
backup_dir = os.path.join(project_root, 'database', 'backups')
db_url = 'sqlite:///./store_management.db'
success = run_database_initialization(
db_url=db_url, backup_dir=backup_dir, force=True)
sys.exit(0 if success else 1)
