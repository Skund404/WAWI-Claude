from di.core import inject
from services.interfaces import (
MaterialService,
ProjectService,
InventoryService,
OrderService,
)

"""
Script to check database contents and verify data is available.
"""
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)
logging.basicConfig(
level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("db_checker")


def find_database_path():
    pass
"""
Find the database file path by searching common locations.

Returns:
str: Path to the database file or None if not found
"""
try:
    pass
from config.settings import get_database_path

return get_database_path()
except (ImportError, ModuleNotFoundError):
    pass
logger.warning(
"Could not import config.settings module, searching for database file manually"
)
possible_paths = [
os.path.join(project_root, "database.db"),
os.path.join(project_root, "data", "database.db"),
os.path.join(project_root, "store_management.db"),
os.path.join(project_root, "data", "store_management.db"),
os.path.join(project_root, "instance", "database.db"),
]
config_file = os.path.join(project_root, "config", "config.py")
if os.path.exists(config_file):
    pass
try:
    pass
with open(config_file, "r") as f:
    pass
content = f.read()
if "database_path" in content:
    pass
logger.info(
"Found config file with database path references")
except Exception as e:
    pass
logger.error(f"Error reading config file: {e}")
for path in possible_paths:
    pass
if os.path.exists(path):
    pass
logger.info(f"Found database file at: {path}")
return path
logger.info("Searching for SQLite database files in project")
for root, dirs, files in os.walk(project_root):
    pass
for file in files:
    pass
if (
file.endswith(".db")
or file.endswith(".sqlite")
or file.endswith(".sqlite3")
):
path = os.path.join(root, file)
logger.info(f"Found potential database file: {path}")
return path
logger.error("Could not find database file")
return None


def check_database_file():
    pass
"""
Check if the database file exists and has the expected tables.

Returns:
bool: True if the database file exists and has expected tables
"""
db_path = find_database_path()
if not db_path:
    pass
logger.error("Database path could not be determined")
return False
logger.info(f"Database path: {db_path}")
if not os.path.exists(db_path):
    pass
logger.error(f"Database file not found at {db_path}")
return False
return True


def list_database_tables():
    pass
"""
List all tables in the database.

Returns:
list: List of table names
"""
db_path = find_database_path()
if not db_path:
    pass
logger.error("Cannot list tables: Database path not found")
return []
try:
    pass
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
table_names = [table[0] for table in tables]
logger.info(
f"Found {len(table_names)} tables: {', '.join(table_names)}")
return table_names
except Exception as e:
    pass
logger.error(f"Error listing tables: {str(e)}")
return []
finally:
if "conn" in locals():
    pass
conn.close()


def check_table_contents(table_name):
    pass
"""
Check the contents of a specific table.

Args:
table_name: Name of the table to check

Returns:
int: Number of rows in the table
"""
db_path = find_database_path()
if not db_path:
    pass
logger.error(
f"Cannot check table {table_name}: Database path not found")
return 0
try:
    pass
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
count = cursor.fetchone()[0]
logger.info(f"Table '{table_name}' has {count} rows")
cursor.execute(f"PRAGMA table_info({table_name});")
columns = cursor.fetchall()
column_names = [col[1] for col in columns]
logger.info(f"Table '{table_name}' columns: {', '.join(column_names)}")
if count > 0:
    pass
cursor.execute(f"SELECT * FROM {table_name} LIMIT 3;")
rows = cursor.fetchall()
for i, row in enumerate(rows):
    pass
logger.info(f"Sample row {i + 1}: {row}")
return count
except Exception as e:
    pass
logger.error(f"Error checking table {table_name}: {str(e)}")
return 0
finally:
if "conn" in locals():
    pass
conn.close()


def main():
    pass
"""
Main function to run database checks.
"""
logger.info("Starting database check")
if not check_database_file():
    pass
logger.error("Database file check failed")
return
tables = list_database_tables()
if not tables:
    pass
logger.error("No tables found in database")
return
for table in tables:
    pass
if table != "sqlite_sequence":
    pass
check_table_contents(table)
logger.info("Database check completed")


if __name__ == "__main__":
    pass
main()
