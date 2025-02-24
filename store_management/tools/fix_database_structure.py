from di.core import inject
from services.interfaces import (
MaterialService,
ProjectService,
InventoryService,
OrderService,
)

"""
Script to fix database structure issues.
"""
logging.basicConfig(
level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("db_fixer")


def find_database_file():
    pass
"""Find the SQLite database file."""
possible_locations = [
"store_management.db",
"data/store_management.db",
"database/store_management.db",
"config/database/store_management.db",
]
for location in possible_locations:
    pass
if os.path.exists(location):
    pass
return location
logger.info("Searching for database file...")
for root, _, files in os.walk(""):
    pass
for file in files:
    pass
if file.endswith(".db"):
    pass
path = os.path.join(root, file)
logger.info(f"Found database file: {path}")
return path
return None


def check_storage_table_structure():
    pass
"""Check the actual structure of the storage table."""
db_path = find_database_file()
if not db_path:
    pass
logger.error("Database file not found.")
return False
logger.info(f"Using database at: {db_path}")
try:
    pass
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute(
"""
SELECT name FROM sqlite_master
WHERE type='table' AND name='storage';
"""
)
if not cursor.fetchone():
    pass
logger.error("Storage table doesn't exist in the database.")
return False
cursor.execute("PRAGMA table_info(storage);")
columns = cursor.fetchall()
column_names = [col[1] for col in columns]
logger.info(f"Current storage table columns: {column_names}")
if "current_occupancy" not in column_names:
    pass
logger.warning(
"The 'current_occupancy' column is missing from the storage table"
)
return False
return True
except Exception as e:
    pass
logger.error(f"Error checking storage table structure: {str(e)}")
return False
finally:
if "conn" in locals():
    pass
conn.close()


def fix_storage_table():
    pass
"""Fix the structure of the storage table."""
db_path = find_database_file()
if not db_path:
    pass
logger.error("Database file not found.")
return False
try:
    pass
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(storage);")
columns = cursor.fetchall()
column_names = [col[1] for col in columns]
logger.info(f"Current storage table columns: {column_names}")
expected_columns = [
"id",
"name",
"location",
"capacity",
"current_occupancy",
"type",
"description",
"status",
]
missing_columns = [
col for col in expected_columns if col not in column_names]
if missing_columns:
    pass
logger.info(f"Missing columns: {missing_columns}")
for column in missing_columns:
    pass
if column == "id":
    pass
col_type = "INTEGER PRIMARY KEY AUTOINCREMENT"
elif column in ["capacity", "current_occupancy"]:
    pass
col_type = "REAL NOT NULL DEFAULT 0.0"
elif column in ["name", "location", "type", "status"]:
    pass
col_type = "TEXT NOT NULL DEFAULT ''"
else:
col_type = "TEXT"
try:
    pass
cursor.execute(
f"ALTER TABLE storage ADD COLUMN {column} {col_type};"
)
logger.info(f"Added column '{column}' to storage table")
except Exception as e:
    pass
logger.error(f"Error adding column '{column}': {str(e)}")
conn.commit()
logger.info("Storage table structure updated successfully")
return True
except Exception as e:
    pass
logger.error(f"Error fixing storage table: {str(e)}")
return False
finally:
if "conn" in locals():
    pass
conn.close()


def add_sample_data():
    pass
"""Add sample data to the storage table."""
db_path = find_database_file()
if not db_path:
    pass
logger.error("Database file not found.")
return False
try:
    pass
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM storage;")
count = cursor.fetchone()[0]
if count == 0:
    pass
logger.info("Adding sample data to storage table...")
sample_data = [
(
"Main Warehouse",
"Building A",
1000.0,
650.0,
"Warehouse",
"Main storage facility",
"active",
),
(
"Shelf A1",
"Main Warehouse - Section A",
50.0,
30.0,
"Shelf",
"Small parts storage",
"active",
),
(
"Shelf B2",
"Main Warehouse - Section B",
75.0,
45.0,
"Shelf",
"Medium parts storage",
"active",
),
(
"Cold Storage",
"Building B",
500.0,
200.0,
"Refrigerated",
"Temperature controlled storage",
"active",
),
(
"Archive Room",
"Building C",
300.0,
280.0,
"Archive",
"Document and sample storage",
"active",
),
]
cursor.execute("PRAGMA table_info(storage);")
columns = cursor.fetchall()
column_names = [col[1] for col in columns]
if "id" in column_names:
    pass
column_names.remove("id")
needed_columns = [
"name",
"location",
"capacity",
"current_occupancy",
"type",
"description",
"status",
]
missing_columns = [
col for col in needed_columns if col not in column_names]
if missing_columns:
    pass
logger.error(
f"Cannot add sample data: missing columns {missing_columns}"
)
return False
query = f"""
INSERT INTO storage ({', '.join(needed_columns)})
VALUES (?, ?, ?, ?, ?, ?, ?);
"""
cursor.executemany(query, sample_data)
conn.commit()
logger.info(
f"Added {len(sample_data)} sample records to the storage table."
)
return True
else:
logger.info(
"Storage table already has data, skipping sample data insertion."
)
return True
except Exception as e:
    pass
logger.error(f"Error adding sample data: {str(e)}")
return False
finally:
if "conn" in locals():
    pass
conn.close()


def backup_database():
    pass
"""Create a backup of the database before modifying it."""
db_path = find_database_file()
if not db_path:
    pass
logger.error("Database file not found.")
return False
backup_path = db_path + ".backup"
try:
    pass
import shutil

shutil.copy2(db_path, backup_path)
logger.info(f"Created database backup at: {backup_path}")
return True
except Exception as e:
    pass
logger.error(f"Error creating database backup: {str(e)}")
return False


def main():
    pass
"""Main function."""
logger.info("Starting database structure fix...")
if not backup_database():
    pass
logger.warning("Could not create a backup, proceeding without it.")
if check_storage_table_structure():
    pass
logger.info("Storage table structure is correct.")
else:
logger.warning("Storage table structure needs fixing.")
response = input(
"Would you like to fix the storage table structure? (y/n): ")
if response.lower() == "y":
    pass
if fix_storage_table():
    pass
logger.info("Storage table structure fixed successfully.")
response = input(
"Would you like to add sample data to the storage table? (y/n): "
)
if response.lower() == "y":
    pass
if add_sample_data():
    pass
logger.info("Sample data added successfully.")
else:
logger.error("Failed to add sample data.")
else:
logger.error("Failed to fix storage table structure.")
else:
logger.info("No changes made to table structure.")


if __name__ == "__main__":
    pass
main()
